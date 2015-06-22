package main

import (
	"fmt"
	"labix.org/v2/mgo"
	"labix.org/v2/mgo/bson"
	"time"
)

type OpInfo map[string]string

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
# Time: 150402 14:02:44
# User@Host: [fernandoipar] @ localhost []
# Thread_id: 13  Schema:   Last_errno: 0  Killed: 0
# Query_time: 0.000052  Lock_time: 0.000000  Rows_sent: 1  Rows_examined: 0  Rows_affected: 0  Rows_read: 0
# Bytes_sent: 90
SET timestamp=1427994164;
db.sample.find({a:"test", b:"another test"});

Mon Jan 2 15:04:05 -0700 MST 2006


*/

func initSlowQueryLogHeaderVars(input OpInfo) (millis string, sent string, user string, host string, inserted string, scanned string) {
	millis = "n/a"
	sent = "n/a"
	user = ""
	host = ""
	inserted = "0"
	scanned = "0"
	if v, ok := input["millis"]; ok {
		millis = v
	}
	if v, ok := input["sent"]; ok {
		sent = v
	}
	if v, ok := input["user"]; ok {
		user = v
	}
	if v, ok := input["client"]; ok {
		host = v
	}
	if v, ok := input["ninserted"]; ok {
		inserted = v
	}
	if v, ok := input["nscanned"]; ok {
		scanned = v
	}
	return millis, sent, user, host, inserted, scanned
}

func getSlowQueryLogHeader(input OpInfo) (output string) {

	millis, sent, user, host, inserted, scanned := initSlowQueryLogHeaderVars(input)
	now := time.Now().Format("060102 15:04:05")
	output = fmt.Sprintf("# Time: %v\n", now)
	output += fmt.Sprintf("# User@Host: %v @ %v []\n", user, host)
	output += "# Thread_id: 1 Schema: Last_errno: 0 Killed: 0\n"
	output += fmt.Sprintf("# Query_time: %v Lock_time: 0 Rows_sent: 1 Rows_examined: %v Rows_affected: %v Rows_read: 1\n", millis, scanned, inserted)
	output += fmt.Sprintf("# Bytes_sent: %v\n", sent)
	output += fmt.Sprintf("SET timestamp=%v;\n", time.Now().Unix())
	return output
}

func recurseJsonMap(json map[string]interface{}) (output string, query string, info OpInfo) {
	i := 0
	info = make(OpInfo)
	for k, v := range json {
		if k == "user" || k == "ns" || k == "millis" || k == "responseLength" || k == "client" || k == "nscanned" || k == "ntoreturn" || k == "ntoskip" || k == "nreturned" || k == "op" || k == "ninserted" || k == "nModified" {
			info[k] = fmt.Sprint(v)
		}
		if k == "query" {
			query, _, _ = recurseJsonMap(v.(map[string]interface{}))
		}
		if k =="updateobj" {
			updateobj, _, _ := recurseJsonMap(v.(map[string]interface{}))
			info[k] = updateobj
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

func main() {
	session, err := mgo.Dial("127.0.0.1")
	if err != nil {
		panic(err)
	}
	defer session.Close()
	col := session.DB("examples").C("system.profile")

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
			switch v {
			case "query":
				limit := info["ntoreturn"]
				skip := info["ntoskip"]
				if ns, present := info["ns"]; present {
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
				} else {
					query = fmt.Sprintf("<unknown>.find{%v}%v%v;", _query, skip, limit)
				}
			case "insert":
				ns := info["ns"]
				query = fmt.Sprintf("%v.insert{%v}",ns, _query)
			case "update":
				ns := info["ns"]
				updateObject := info["updateobj"]
				query = fmt.Sprintf("%v.update({%v},{%v})", ns, _query, updateObject)
			case "remove":
			case "getmore":
			case "command":
			default:
				query = fmt.Sprintf("{%v};", _query)
			}
		}
		fmt.Print(getSlowQueryLogHeader(info), query, "\n")
	}

}
