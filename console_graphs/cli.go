package main

import (
	term "github.com/buger/goterm"
	"math/rand"
	"strconv"
	"time"
)

// for now let's only display integers
func LabeledOutput(label string, source chan int, x int, y int) {
	for {
		term.MoveCursor(x, y)
		term.Print(label + strconv.Itoa(<-source))
		term.Flush()
	}
}

func main() {
	term.Clear()
	source_random := make(chan int)
	go LabeledOutput("Random: ", source_random, 10, 20)
	r := rand.New(rand.NewSource(99))
	for {
		source_random <- r.Intn(1000)
		time.Sleep(1 * time.Second)
	}
}
