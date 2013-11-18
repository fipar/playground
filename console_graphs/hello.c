#include <ncurses.h>
#define DATA_SET_SIZE 12
#define BAR '\219'

/**
 * throwaway code while I work on a console histogram
 */

int main()
{
	initscr();
	refresh();
	start_color();
	// hardcoded graph attempt
	// graph starts at 10,5 too
	// to keep this one-off example simple, I won't include values out of range
	int roworigin = 10;
	int colorigin = 5;
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
		for (int j=0; j<data_points[i]; j++) {
			mvaddch(roworigin - j, colorigin + i, BAR);
		}
		attroff(COLOR_PAIR(color_pair));
		refresh();
	}
	refresh();
	getch();
	endwin();

	return 0;
}

