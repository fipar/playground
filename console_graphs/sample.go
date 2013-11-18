package main

/*
This idea can be expanded into a reusable gauge so you can graphically represent some info like cpu load, used mem, etc while sharing console real estate with textual information
*/

import (
	"github.com/tncardoso/gocurses"
	"math/rand"
	"strconv"
	"sync"
	"time"
)

const (
	GAUGE_MAX    = 5
	GAUGE_HEIGHT = 7
	GAUGE_WIDTH  = 3
	ITEM         = 'X'
	BLANK        = ' '
)

var wl sync.Mutex

// eventually this one will do any needed transformation to fit a (potentially floating point) number into a gauge
func normalize(num int) int {
	if num > GAUGE_MAX {
		return GAUGE_MAX
	} else {
		return num
	}
}

// for now, gauges will have a fixed height
// also, I'm not counting runes, just bytes, for label.
func gauge(datasource chan int, rowstart int, colstart int, label string) {
	win := gocurses.NewWindow(GAUGE_HEIGHT, GAUGE_WIDTH, rowstart, colstart)
	win.Box(0, 0)
	gocurses.Mvaddstr(rowstart+GAUGE_HEIGHT, colstart+1-(len(label)/2), label)
	for {
		wl.Lock()
		win.Refresh()
		wl.Unlock()
		num := <-datasource
		num = normalize(num)
		color_pair := 1
		switch num {
		default:
			color_pair = 1
		case 3, 4:
			color_pair = 2
		case 5:
			color_pair = 3
		}
		gocurses.Mvaddstr(rowstart+GAUGE_HEIGHT+4, colstart, strconv.Itoa(num))
		for i := rowstart + GAUGE_HEIGHT - 2; i >= rowstart+GAUGE_HEIGHT-6; i-- {
			if i > rowstart+GAUGE_MAX-num {
				gocurses.Attron(gocurses.ColorPair(color_pair))
				gocurses.Mvaddch(i, colstart+1, ITEM)
				gocurses.Attroff(gocurses.ColorPair(color_pair))
			} else {
				gocurses.Mvaddch(i, colstart+1, BLANK)
			}
		}
	}
}

func main() {
	gocurses.Initscr()
	defer gocurses.End()
	gocurses.Attron(gocurses.A_BOLD)
	gocurses.Addstr("Test gauge")
	gocurses.StartColor()
	gocurses.InitPair(1, gocurses.COLOR_GREEN, gocurses.COLOR_BLACK)
	gocurses.InitPair(2, gocurses.COLOR_YELLOW, gocurses.COLOR_BLACK)
	gocurses.InitPair(3, gocurses.COLOR_RED, gocurses.COLOR_BLACK)
	gocurses.Refresh()

	source := make(chan int)
	source2 := make(chan int)

	go gauge(source, 10, 10, "Random")
	go gauge(source2, 10, 20, "Random 2")
	r := rand.New(rand.NewSource(99))
	for {
		source <- r.Intn(7)
		source2 <- r.Intn(5)
		time.Sleep(1 * time.Second)
		gocurses.Refresh()
	}
}
