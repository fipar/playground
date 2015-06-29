package main

import (
	"flag"
	"fmt"
	"time"

	"labix.org/v2/mgo"
	"labix.org/v2/mgo/bson"
)

// OpInfo is used to save data points that will be used when generating the slow query log entry header.
// Examples include response time, lock time, user, host, etc.
type OpInfo map[string]string

// Command line args are pretty self-explanatory: We only need a mongo url (to be used with mgo.Dial) and a database name. We default to 127.0.0.1/local
var MONGO = flag.String("mongo", "127.0.0.1", "The mongod/mongos instance to connect to")
var DB = flag.String("db", "local", "The database that has the system.profile collection we need to process")

// This walks an array and generates a string representation of its contents. It recurses down substructures as needed, provided they're one of
// a [string]interface{} map (i.e. a json doc) or another array.
// There are no depth controls, so a sufficiently deep structure could blow the stack
func recurseArray(input []interface{}) (output string) {
	output = "["
	i := 0
	for k, v := range input {
		i++
		comma := ", "
		if i == len(input) {
			comma = ""
		}
		switch extracted_v := v.(type) {
		case map[string]interface{}:
			aux, _, _ := recurseJsonMap(extracted_v)
			output += fmt.Sprintf("%v:{%v}%v", k, aux, comma)
		case []interface{}:
			output += fmt.Sprintf("%v:%v%v", k, recurseArray(extracted_v), comma)
		default:
			output += fmt.Sprintf("%v:%v%v", k, extracted_v, comma)
		}
	}
	output += fmt.Sprintf("]")
	return output
}

// This does the same as the previous function, but with a json document, and populating info on the way.
// The same stack disclaimer applies here.
// This is the point where data types are converted to their appropriate representation. Anything above this call
// will deal with strings only.
func recurseJsonMap(json map[string]interface{}) (output string, query string, info OpInfo) {
	i := 0
	info = make(OpInfo)
	for k, v := range json {
		if k == "user" || k == "ns" || k == "millis" || k == "responseLength" || k == "client" || k == "nscanned" || k == "ntoreturn" || k == "ntoskip" || k == "nreturned" || k == "op" || k == "ninserted" || k == "ndeleted" || k == "nModified" || k == "cursorid" {
			info[k] = fmt.Sprint(v)
		}
		if k == "query" {
			query, _, _ = recurseJsonMap(v.(map[string]interface{}))
		}
		if k == "updateobj" {
			updateobj, _, _ := recurseJsonMap(v.(map[string]interface{}))
			info[k] = updateobj
		}
		if k == "command" {
			command, _, _ := recurseJsonMap(v.(map[string]interface{}))
			info[k] = command
		}
		i++
		comma := ", "
		if i == len(json) {
			comma = ""
		}
		switch extracted_v := v.(type) {
		case string, time.Time, int, int32, int64:
			output += fmt.Sprintf("%v:%v%v", k, extracted_v, comma)
		case float64:
			output += fmt.Sprintf("%v:%v%v", k, float64(extracted_v), comma)
		case map[string]interface{}:
			auxstr, _query, auxOpInfo := recurseJsonMap(extracted_v)
			if _query != "" {
				query = _query
			}
			info = mergeOpInfoMaps(info, auxOpInfo)
			output += fmt.Sprintf("%v:{%v}%v", k, auxstr, comma)
		case []interface{}:
			output += fmt.Sprintf("%v:%v%v", k, recurseArray(extracted_v), comma)
		case bson.ObjectId:
			output += fmt.Sprintf("%v:%v%v", k, extracted_v.String(), comma)
		default:
			output += fmt.Sprintf("%v:%T%v", k, extracted_v, comma)
		}

	}
	return output, query, info
}

// This merges OpInfo maps, as we may create more than one while recursing down a document.
// It is a very primite merge because, in theory, there should be no colliding key names in the fields
// we're collecting.
func mergeOpInfoMaps(s1 OpInfo, s2 OpInfo) (result OpInfo) {
	result = make(OpInfo)
	for k, v := range s1 {
		if v2, ok := s2[v]; ok {
			result[k] = fmt.Sprintf("%v | %v", v, v2)
		} else {
			result[k] = v
		}
	}
	return result
}

/*

Sample slow query log entry header from MySQL

# Time: 150402 14:02:44
# User@Host: [fernandoipar] @ localhost []
# Thread_id: 13  Schema:   Last_errno: 0  Killed: 0
# Query_time: 0.000052  Lock_time: 0.000000  Rows_sent: 1  Rows_examined: 0  Rows_affected: 0  Rows_read: 0
# Bytes_sent: 90
SET timestamp=1427994164;
db.sample.find({a:"test", b:"another test"});

Header from Percona Server with log_slow_verbosity set to all:

# User@Host: [fernandoipar] @ localhost []
# Thread_id: 2  Schema:   Last_errno: 0  Killed: 0
# Query_time: 0.000003  Lock_time: 0.000000  Rows_sent: 0  Rows_examined: 0  Rows_affected: 0  Rows_read: 0
# Bytes_sent: 0  Tmp_tables: 0  Tmp_disk_tables: 0  Tmp_table_sizes: 0
# QC_Hit: No  Full_scan: No  Full_join: No  Tmp_table: No  Tmp_table_on_disk: No
# Filesort: No  Filesort_on_disk: No  Merge_passes: 0
# No InnoDB statistics available for this query
SET timestamp=1435605887;
# administrator command: Quit;

*/

// Canonical date for Golang's formatting
// Mon Jan 2 15:04:05 -0700 MST 2006

// This is just a helper function to not pollute the header generator with default initialazers
func initSlowQueryLogHeaderVars(input OpInfo) (output OpInfo) {
	//func initSlowQueryLogHeaderVars(input OpInfo) (millis string, sent string, user string, host string, inserted string, scanned string, deleted string, returned string) {
	output = make(OpInfo)
	output["millis"] = "n/a"
	output["sent"] = "n/a"
	output["user"] = ""
	output["host"] = ""
	output["inserted"] = "0"
	output["scanned"] = "0"
	output["deleted"] = "0"
	output["returned"] = "0"
	if v, ok := input["millis"]; ok {
		output["millis"] = v
	}
	if v, ok := input["sent"]; ok {
		output["sent"] = v
	}
	if v, ok := input["user"]; ok {
		output["user"] = v
	}
	if v, ok := input["client"]; ok {
		output["host"] = v
	}
	if v, ok := input["ninserted"]; ok {
		output["inserted"] = v
	}
	if v, ok := input["nscanned"]; ok {
		output["scanned"] = v
	}
	if v, ok := input["ndeleted"]; ok {
		output["deleted"] = v
	}
	if v, ok := input["nreturned"]; ok {
		output["returned"] = v
	}
	return output
	//	return millis, sent, user, host, inserted, scanned, deleted, returned
}

// This just formats a slow query log entry header.
func getSlowQueryLogHeader(input OpInfo) (output string) {

	//	millis, sent, user, host, inserted, scanned, deleted, returned := initSlowQueryLogHeaderVars(input)
	info := initSlowQueryLogHeaderVars(input)
	affected := info["inserted"]
	if input["op"] == "remove" {
		affected = info["deleted"]
	}
	now := time.Now().Format("060102 15:04:05")
	output = fmt.Sprintf("# Time: %v\n", now)
	output += fmt.Sprintf("# User@Host: %v @ %v []\n", info["user"], info["host"])
	output += "# Thread_id: 1 Schema: Last_errno: 0 Killed: 0\n"
	output += fmt.Sprintf("# Query_time: %v Lock_time: 0 Rows_sent: %v Rows_examined: %v Rows_affected: %v Rows_read: 1\n", info["millis"], info["returned"], info["scanned"], affected)
	output += fmt.Sprintf("# Bytes_sent: %v\n", info["sent"])
	output += fmt.Sprintf("SET timestamp=%v;\n", time.Now().Unix())
	return output
}

func main() {
	flag.Parse()
	session, err := mgo.Dial(*MONGO)
	if err != nil {
		panic(err)
	}
	defer session.Close()
	col := session.DB(*DB).C("system.profile")

	var results []map[string]interface{}
	err = col.Find(bson.M{}).All(&results)

	if err != nil {
		panic(err)
	}

	for _, v := range results {
		var info OpInfo = make(OpInfo)
		_, _query, info := recurseJsonMap(v)
		query := ""
		if v, ok := info["op"]; ok {
			ns := info["ns"] // ns is always there or we must just crash/behave erratically
			switch v {
			case "query":
				limit := info["ntoreturn"]
				skip := info["ntoskip"]
				if limit == "0" {
					limit = ""
				} else {
					limit = fmt.Sprintf(".limit(%v)", limit)
				}
				if skip == "0" {
					skip = ""
				} else {
					skip = fmt.Sprintf(".skip(%v)", skip)
				}
				query = fmt.Sprintf("%v.find{%v}%v%v;", ns, _query, skip, limit)
			case "insert":
				query = fmt.Sprintf("%v.insert{%v};", ns, _query)
			case "update":
				query = fmt.Sprintf("%v.update({%v},{%v});", ns, _query, info["updateobj"])
			case "remove":
				query = fmt.Sprintf("%v.remove({%v});", ns, _query)
			case "getmore":
				query = fmt.Sprintf("%v.getmore;", ns)
			case "command":
				query = fmt.Sprintf("%v({%v});", ns, info["command"])
			default:
				query = fmt.Sprintf("__UNIMPLEMENTED__ {%v};", _query)
			}
		}
		fmt.Print(getSlowQueryLogHeader(info), query, "\n")
	}

}
