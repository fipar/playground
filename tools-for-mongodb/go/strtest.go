package main

import "fmt"

func main() {
        data := [100]byte{5, 0, 0, 0, 0}
	fmt.Println(string(data[:]))
}
