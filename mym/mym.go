package main

/*
What I want to do here is provide an live overview of the work a MySQL server is doing.
The basic idea is to have data display points that constantly read data from a channel to display it, and
data source points, that read data from some MySQL query (or potentally another location) and write it to a channel.
*/

// I am keeping comments in the import section as I play with this
import (
	"database/sql"
	term "github.com/buger/goterm"
	_ "github.com/go-sql-driver/mysql"
	//	"strconv"
	"time"

	//	"unicode/utf8"
//	"fmt"
)

// Any will be used to make generic functions
type Any interface{}

// A global var for the connection seems the easiest at this stage
var db *sql.DB
var err error

// A global channel for status/error messages
var chan_status = make(chan Any)

/*
LabeledOutput runs forever, so it is desgined to be called like go LabeledOutput(...)
It displays label and the contents of the source channel at the screen positions x,y

usage would be like:
   source := make(chan Any)
   go LabeledOutput("Label: ", source, 1,1)

*/
func LabeledOutput(label string, source chan Any, x int, y int) {
	for {
		term.MoveCursor(x, y)
		term.Print(label, <-source)
		//term.Flush()
	}
}

/*
ThreadsRunning runs forever.
It writes the value of the Threads_running status variable to the dest channel.
If there is an error, it continues the loop, but sleeps a few seconds so it does not flood the server

I think data source points could match multiple data source displays, to, i.e., have a single ShowStatus function that receives a group of channels
so that multiple data source displays get updated with a single query.
Will probably use map[string]chan Any for this, where string == name of status variable, chan Any == channel to link that variable with a data point display
*/
func ThreadsRunning(dest chan Any) {
	var threads_running int
	for {
		rows, err_ := db.Query("show global status like 'Threads_running'")
		if err_ != nil {
			dest <- err_.Error()
			time.Sleep(5 * time.Second)
			continue
		}
		if !rows.Next() {
			time.Sleep(5 * time.Second)
			continue
		}
		defer rows.Close()
		var aux string
		err_ = rows.Scan(&aux, &threads_running)
		if err_ != nil {
			dest <- err_.Error()
			time.Sleep(5 * time.Second)
			continue
		}
		dest <- threads_running
		rows.Close()
		time.Sleep(1 * time.Second)
	}
}

// And this is POC for the ShowStatus function
// The crude idea is to run 'show global status', itereate over the result, and for anything that exists in the map, send the value
func ShowStatus(dests map[string]chan Any) {
	var value int
	var variable string
	for {
		rows, err_ := db.Query("show global status")
		if err_ != nil {
			chan_status <- err.Error()
			time.Sleep(5 * time.Second)
			continue
		}
		if !rows.Next() {
			time.Sleep(5 * time.Second)
			continue
		}
		defer rows.Close()
		for rows.Next() {
			err_ = rows.Scan(&variable, &value)
			if err_ != nil {
				chan_status <- err
				time.Sleep(5 * time.Second)
				continue
			}
			_, ok := dests[variable]
			if ok {
				chan_status <- value
				dests[variable] <- value
			} else {
				chan_status <- variable
			}
			time.Sleep(1 * time.Second)
		}
		rows.Close()
		time.Sleep(1 * time.Second)
	}
}

// main will be a mess while I test
// all will be hardcoded
func main() {
	db, err = sql.Open("mysql", "msandbox:msandbox@tcp(127.0.0.1:5527)/test")
	if err != nil {
		panic(err.Error())
	}
	term.Clear()
	chan_tr := make(chan Any)
	chan_extra := make(chan Any)
	dests := map[string]chan Any{
		"Threads_running":       chan_tr,
		"Binlog_cache_usek_use": chan_extra,
	}
	go LabeledOutput("Threads_running: ", chan_tr, 3, 10)
	go LabeledOutput("Status: ", chan_status, 3, 15)
	go LabeledOutput("Chan extra: ", chan_extra, 3, 20)
	//go ThreadsRunning(chan_tr)
	go ShowStatus(dests)
	for {
		//var input Any
		//fmt.Scan(&input)
		time.Sleep(1 * time.Second)
		term.Flush()
		//term.MoveCursor(5, 5)
		//term.Print(input)
	}
}
