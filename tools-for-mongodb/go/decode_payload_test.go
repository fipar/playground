package main

import (
	"fmt"
	"gopkg.in/mgo.v2/bson"
	"unsafe"
)

func main() {
	data := [500]byte{79, 0, 0, 0, 189, 0, 0, 0, 0, 0, 0, 0, 212, 7, 0, 0, 0, 0, 0, 0, 116, 101, 115, 116, 46, 36, 99, 109, 100, 0, 0, 0, 0, 0, 255, 255, 255, 255, 41, 0, 0, 0, 1, 105, 115, 77, 97, 115, 116, 101, 114, 0, 0, 0, 0, 0, 0, 0, 240, 63, 1, 102, 111, 114, 83, 104, 101, 108, 108, 0, 0, 0, 0, 0, 0, 0, 240, 63, 0}
	sub := data[20:]
	current := sub[0]
	docStartsAt := 0
	for i := 0; current != 0; i++ {
		current = sub[i]
		docStartsAt = i
	}
	collectionName := sub[0:docStartsAt]
	docStartsAt++
	fmt.Print("Raw data: ")
	fmt.Println(data)
	fmt.Printf("Querying collection %v\n",collectionName)
	mybson := sub[docStartsAt+8:]
	docEndsAt := mybson[0]
	bdoc := mybson[:docEndsAt]
	json := make(map[string]interface{})
	bson.Unmarshal(bdoc, json)
	fmt.Print("Unmarshalled json: ")
	fmt.Println(json)
	for k, v := range json {
		fmt.Printf("%v:%v\n",k,v)
	}
	fmt.Print("mybson bytes: ")
	fmt.Println(mybson)
	fmt.Print("Document bytes:")
	fmt.Println(bdoc)
	fmt.Print("Document size in bytes: ")
	fmt.Println(unsafe.Sizeof(bdoc))
}
