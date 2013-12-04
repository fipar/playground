package main

import term "github.com/buger/goterm"

func main() {
	term.Clear()
	term.MoveCursor(1,1)
	term.Print("test at 1,1")
	term.Flush()
	term.MoveCursor(6,1)
	term.Print("test at 6,1")
	term.Flush()
	term.MoveCursor(10,1)
	term.Print("test at 10,1")
	term.Flush()
}
