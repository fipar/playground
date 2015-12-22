package main

import (
	"fmt"
	"math"

	tm "github.com/buger/goterm"
)

func main() {
	chart := tm.NewLineChart(100, 20)

	data := new(tm.DataTable)
	data.AddColumn("Time")
	data.AddColumn("Sin(x)")
	data.AddColumn("Cos(x+1)")

	for i := 0.1; i < 10; i += 0.1 {
		tm.Clear()
		data.AddRow(i, math.Sin(i), math.Cos(i+1))
		tm.Println(chart.Draw(data))
		tm.Flush()
	}

	//tm.Println(chart.Draw(data))
	//tm.Flush()
	fmt.Scan()
}
