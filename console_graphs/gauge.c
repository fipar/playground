#include <ncurses.h>
#include <cdk.h>
#define BAR 'O'
#define BLANK ' '
#define DATA_SET_SIZE 12 
#define MAX 5

/**
 *  alternative to histogram: gauge bars for a few metrics 
 */

int main()
{
	initscr();
	start_color();
	assume_default_colors(-1,-1);
	refresh();
	// hardcoded graph attempt
	// graph starts at 10,5 too
	// to keep this one-off example simple, I won't include values out of range
	int roworigin = 10;
	int colorigin = 5;
	init_pair(1,COLOR_GREEN, -1);
	init_pair(2,COLOR_YELLOW, -1);
	init_pair(3,COLOR_RED, -1);
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
			mvaddch(roworigin - j, colorigin, BAR);
		}
		attroff(COLOR_PAIR(color_pair));
		for (int j=data_points[i]; j<MAX; j++) {
			mvaddch(roworigin - j, colorigin, BLANK);
		}
		refresh();
		sleep(1);
	}
	refresh();
	move(0,0);
	getch();
	endwin();

	return 0;
}

