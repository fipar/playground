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

func recurseJsonMap(json map[string]interface{}) (output string, query string, info OpInfo) {
	i := 0
	info = make(OpInfo)
	for k, v := range json {
		if k == "user" || k == "ns" || k == "responseLength" || k == "client" || k == "nscanned" || k == "nreturned" || k == "millis" {
			info[k] = fmt.Sprint(v)
		}
		if k == "query" {
			query,_,_ = recurseJsonMap(v.(map[string]interface{})) 
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
			info = mergeOpInfoMaps(info,auxOpInfo)
			output += fmt.Sprintf("%v:{%v}%v", k, auxstr, comma)
		case []interface{}:
			output += fmt.Sprintf("%v:%v%v",k, recurseArray(extracted_v), comma)
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
	fmt.Println("Will open collection")
	col := session.DB("examples").C("system.profile")

	var results []map[string]interface{}
	fmt.Println("Will run col.Find()")
	err = col.Find(bson.M{}).All(&results)

	if err != nil {
		panic(err)
	}

	fmt.Println("result has ",len(results)," elements")
	for k, v := range results {
		var info OpInfo = make(OpInfo)
//		fmt.Println(k, ":",reflect.TypeOf(v))
//		fmt.Println(v)
		fmt.Println("log entry # ", k)
		output, query, info := recurseJsonMap(v)
		fmt.Println(fmt.Sprintf("output: %v\nquery:{%v}\nextra info: %v",output,query,info))
		fmt.Println()
	}

}
