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
	println("starting display for ", label)
	for {
		term.MoveCursor(x, y)
		println("will read from channel for ", label)
		term.Print(label, <-source)
		term.Flush()
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
			println("got error ", err.Error(), ", writing to chan_status and sleeping 5 seconds")
			chan_status <- err.Error()
			time.Sleep(5 * time.Second)
			continue
		}
		if !rows.Next() {
			println("did not get rows, sleeping 5 secs")
			time.Sleep(5 * time.Second)
			continue
		}
		defer rows.Close()
		for rows.Next() {
			err_ = rows.Scan(&variable, &value)
			if err_ != nil {
				// will ignore these for now. Will be an error whenever I read something that's not an int
				continue
			}
			_, ok := dests[variable]
			if ok {
				println("got ", value, " for ", variable)
				dests[variable] <- value
			}
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
	chan_tr := make(chan Any, 20)
	chan_tc := make(chan Any, 20)
	chan_com_select := make(chan Any, 20)
	dests := map[string]chan Any{
		"Threads_running":   chan_tr,
		"Threads_connected": chan_tc,
		"Com_select":        chan_com_select,
	}
	go LabeledOutput("Threads_running: ", chan_tr, 3, 1)
	go LabeledOutput("Threads_connected: ", chan_tc, 2, 1)
	go LabeledOutput("Status: ", chan_status, 20, 1)
	go LabeledOutput("Com_select: ", chan_com_select, 4, 1)
	//go ThreadsRunning(chan_tr)
	go ShowStatus(dests)
	for {
		time.Sleep(1 * time.Second)
	}
}
