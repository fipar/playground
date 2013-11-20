package main

import (
	term "github.com/buger/goterm"
	"math/rand"
	"strconv"
	"time"
	"unicode/utf8"
	"fmt"
)

// for now let's only display integers
func LabeledOutput(label string, source chan int, x int, y int) {
	for {
		box := term.NewBox(utf8.RuneCountInString(label) + 10, 3,0)
		term.MoveCursor(x, y)
		fmt.Fprint(box, label + strconv.Itoa(<-source))
		term.Print(term.MoveTo(box.String(), x, y))
		//term.Print(label + strconv.Itoa(<-source))
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
