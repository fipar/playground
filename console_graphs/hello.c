#include <ncurses.h>
#define DATA_SET_SIZE 12

/*
 * Things I hope to learn here: 
 * - Display text at some screen pos
 * - Replace text on the screen
 * - Change colors
 * - Graphing something
 * */


int main()
{
	initscr();
	mvprintw(10,5,"3");
	refresh();
	sleep(1);
	mvprintw(10,5,"2");
	initscr();
	refresh();
	sleep(1);
	mvprintw(10,5,"1");
	initscr();
	refresh();
	sleep(1);
	start_color();
	// hardcoded graph attempt
	// graph starts at 10,5 too
	// to keep this one-off example simple, I won't include values out of range
	int xorigin = 5;
	int yorigin = 10;
	init_pair(1,COLOR_GREEN, COLOR_WHITE);
	init_pair(2,COLOR_YELLOW, COLOR_WHITE);
	init_pair(3,COLOR_RED, COLOR_WHITE);
	int data_points[DATA_SET_SIZE] = {0,1,2,5,1,0,0,1,2,3,2,0};
	for (int i=0; i<DATA_SET_SIZE; i++) {
		// init color
		int color_pair = 3;
		switch (data_points[i]) {
			case 0 :
		    case 1 :
				color_pair = 1; 
				break;
			case 2 :
			case 3 : 
				color_pair = 2;
				break;
			default :
				break; 
		}
		attron(COLOR_PAIR(color_pair));
		mvprintw(yorigin+data_points[i], xorigin+i, ".");
		attroff(COLOR_PAIR(color_pair));
	}
	attron(COLOR_PAIR(3));
	mvprintw(20,5,"ncurses test. type something to exit");
	attroff(COLOR_PAIR(1));
	initscr();
	refresh();
	getch();
	endwin();

	return 0;
}

