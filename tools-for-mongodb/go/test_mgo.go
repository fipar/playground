package main

import (
	"fmt"
	"labix.org/v2/mgo"
	"labix.org/v2/mgo/bson"
)

type Presentation struct {
	ID         bson.ObjectId `bson:"_id,omitempty"`
	Title      string
	Conference string
	Author     string
}

func main() {
	session, err := mgo.Dial("127.0.0.1")
	if err != nil {
		panic(err)
	}
	defer session.Close()
	col := session.DB("examples").C("presentations")

	err = col.Insert(
		&Presentation{Title: "An example from Go", Conference: "Imaginary Conference 2015", Author: "fipar"},
		&Presentation{Title: "Another example from Go", Conference: "Imaginary Conference 2015", Author: "fipar"})

	if err != nil {
		panic(err)
	}
	fmt.Println("Inserted OK")

	result := Presentation{}

	err = col.Find(bson.M{"author": "fipar"}).One(&result)
	if err != nil {
		panic(err)
	}
	fmt.Println("Result: ", result)

	var results []Presentation
	err = col.Find(bson.M{"author": "fipar"}).All(&results)

	if err != nil {
		panic(err)
	}

	updateQuery := bson.M{"conference": "Imaginary Conference 2015"}
	updateChange := bson.M{"$set": bson.M{"conference": "Imaginary Strange Loop 2015"}}
	err = col.Update(updateQuery, updateChange)
	if err != nil {
		panic(err)
	}

	fmt.Println("Updated OK")
}
