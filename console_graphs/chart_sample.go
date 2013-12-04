package main

import (
	tm "github.com/buger/goterm"
)

func main() {
	chart := tm.NewLineChart(100, 20)

	data := new(tm.DataTable)
	data.addColumn("Time")
	data.addColumn("Sin(x)")
	data.addColumn("Cos(x+1)")

	for i := 0.1; i < 10; i += 0.1 {
		data.addRow(i, math.Sin(i), math.Cos(i+1))
	}

	tm.Println(chart.Draw(data))
}
