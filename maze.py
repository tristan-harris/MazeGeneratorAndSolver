from graphics import *
import random
from sys import getrecursionlimit, setrecursionlimit
from time import sleep
from collections import deque

'''
    Generates a maze of a given row and column amount, and can find the answer using a BFS or DFS
    Press 'R' to clear the screen and make a new maze, 'B' to do a BFS and 'D' to do a DFS
    @author Tristan Harris
'''

# ======================================================================================================

# show search process if True, otherwise just show solution if False
VISUALISE = True

# rows = height, columns = width (of maze)
ROWS    = 35
COLUMNS = 35

# this can be used to get a maze up to 100 x 100
setrecursionlimit(5000)

# use this to get the same maze generated every time
# random.seed(1234)

# ======================================================================================================

# adds up to 15, representing walls using a bitmask
NORTH = 0b1000 # 8
EAST  = 0b0100 # 4
SOUTH = 0b0010 # 2
WEST  = 0b0001 # 1

# relative positions for compass directions
NORTH_MOVEMENT = [-1,0] 
EAST_MOVEMENT  = [0, 1]
SOUTH_MOVEMENT = [1, 0]
WEST_MOVEMENT  = [0,-1]

MOVEMENTS = [NORTH_MOVEMENT,EAST_MOVEMENT,SOUTH_MOVEMENT,WEST_MOVEMENT]

# ======================================================================================================

# both width and height
WINDOW_RESOLUTION = 500

# the (x,y) pixel coordinate of the top left of the maze 
ORIGIN_POINT = 10

# how many pixels long a wall is
WALL_DISTANCE = (WINDOW_RESOLUTION)//max(ROWS, COLUMNS)
WALL_DISTANCE *= 0.95

# the pixel radius of the red circles
PATH_CIRCLE_RADIUS = WALL_DISTANCE//5

# ======================================================================================================

# generates a full maze with every wall
def generate_full_maze(width,height):
    # a list comprehension for a 2D list
    return [[int(0b1111) for __ in range(width)] for __ in range(height)]

# draws a line for a maze wall
def draw_maze_wall(start_x,start_y,finish_x,finish_y, window,line_width=1):

    # drawing a line on the screen
    wall_starting_point = Point(start_x,start_y)
    wall_finishing_point = Point(finish_x,finish_y) 

    wall_line = Line(wall_starting_point,wall_finishing_point)
    wall_line.setFill('white')
    wall_line.setWidth(line_width)
    wall_line.draw(window)     

# draws a red path circle at the cell
def draw_path_circle(row,column,window,colour='red'):

    # the pixel centre of a maze cell
    circle_point = Point(ORIGIN_POINT + WALL_DISTANCE/2 + (column*WALL_DISTANCE),ORIGIN_POINT + WALL_DISTANCE/2 + (row*WALL_DISTANCE))

    path_circle = Circle(circle_point,PATH_CIRCLE_RADIUS)
    path_circle.setOutline('black')
    path_circle.setFill(colour)
    path_circle.draw(window)

    return path_circle

# draws the whole maze
def draw_maze(maze,window):
    
    maze_rows = len(maze)
    maze_columns = len(maze[0])

    # drawing the left and top edges of the maze
    draw_maze_wall(ORIGIN_POINT,ORIGIN_POINT,ORIGIN_POINT+(WALL_DISTANCE*maze_columns),ORIGIN_POINT,window)
    # + WALL_DISTANCE for the gap at the top left
    draw_maze_wall(ORIGIN_POINT,ORIGIN_POINT+WALL_DISTANCE,ORIGIN_POINT,ORIGIN_POINT+(WALL_DISTANCE*maze_rows),window)

    for row in range(len(maze)):
        for column in range(len(maze[row])):
            
            # like 1101 or 0110
            wall_bitmask = maze[row][column]

            # a list of two booleans for east and south walls, e.g [True, False]
            walls = \
            [
                (wall_bitmask & EAST) > 0, 
                (wall_bitmask & SOUTH) > 0
            ]

            # if at the bottom right of maze
            if row == maze_rows-1 and column == maze_columns-1:
                # don't draw eastern wall (exit)
                walls[0] = False

            # dictionary of positionings for different compass directions of walls
            wall_modifiers = \
            {
                # not needed
                NORTH: {
                    'start_x':0,
                    'start_y':0,
                    'end_x':WALL_DISTANCE,
                    'end_y':0
                },
                EAST: {
                    'start_x':WALL_DISTANCE,
                    'start_y':0,
                    'end_x':WALL_DISTANCE,
                    'end_y':WALL_DISTANCE+1
                },
                SOUTH: { 
                    'start_x':0,
                    'start_y':WALL_DISTANCE,
                    'end_x':WALL_DISTANCE+1,
                    'end_y':WALL_DISTANCE
                },
                # not needed
                WEST: {
                    'start_x':0,
                    'start_y':0,
                    'end_x':0,
                    'end_y':WALL_DISTANCE
                }
            }

            for wall in range(len(walls)):

                # only need to draw south and east walls, otherwise drawing walls twice
                if walls[wall]:
                    if wall == 0:
                        direction = EAST
                    else:
                        direction = SOUTH

                    # acessing appropriate wall facing, based off position in list of booleans
                    wall_modifier = wall_modifiers[direction]

                    # line starting x and y
                    wall_starting_x_point = ORIGIN_POINT+(WALL_DISTANCE*column) + wall_modifier['start_x']
                    wall_starting_y_point = ORIGIN_POINT+(WALL_DISTANCE*row) + wall_modifier['start_y']

                    # line finishing x and y
                    wall_finishing_x_point = ORIGIN_POINT+(WALL_DISTANCE*column) + wall_modifier['end_x']
                    wall_finishing_y_point = ORIGIN_POINT+(WALL_DISTANCE*row) + wall_modifier['end_y']
                
                    draw_maze_wall(wall_starting_x_point,wall_starting_y_point,wall_finishing_x_point,wall_finishing_y_point,window)

# returns either [-1,0], [1,0], [0,-1], [0,1]
def move_position(coord_list):

    # 0 appears twice to properly weight probability
    horizontal_shift = random.choice([0,0,-1,1])
    
    # if no change horizontally, then change vertically
    if horizontal_shift == 0:
        vertical_shift = random.choice([-1,1])
    else:
        vertical_shift = 0

    # returning modified coordinates
    return [coord_list[0] + vertical_shift,coord_list[1] + horizontal_shift]

# converts a list [x,y] into a string "x,y", so it can be added to a visited set
def coords_to_string(coords):
    return f"{coords[0]},{coords[1]}"

# beginning of recursive passage generation
def generate_passages(maze):

    # coords as [row, column]

    maze_rows = len(maze)
    maze_columns = len(maze[0])
    
    # to keep track of maze cells that have already been visited
    seen = set()

    # starting in the top left of the maze
    current_coords = [0,0]
    
    # adding the starting point to seen (using string hashing)
    seen.add(coords_to_string(current_coords))

    # random choosing the order of the directions, so that the same maze isn't generated every time
    movements = MOVEMENTS.copy()
    random.shuffle(movements)

    for movement in movements:
        knock_through_wall(current_coords,movement,seen,maze)

    return maze

# knocks through a wall in the maze, and calls itself on neighbouring cells (like flood fill)
def knock_through_wall(coords,direction,seen,maze):

    current_coords = coords # [row, column]
    new_coords = [current_coords[0] + direction[0],current_coords[1] + direction[1]]

    maze_rows = len(maze)
    maze_columns = len(maze[0])
    
    # if within the bounds of the maze
    if (-1 < new_coords[0] < maze_rows) and (-1 < new_coords[1] < maze_columns):
        # if at a cell that has not been visited before
        if coords_to_string(new_coords) not in seen:
            # marking cell has visited
            seen.add(coords_to_string(new_coords))

            # if new row is greater than current row (MOVING SOUTH)
            if new_coords[0] > current_coords[0]:
                # subtracting a direction such as SOUTH (2), removes the southern wall from the bitmask
                maze[current_coords[0]][current_coords[1]] -= SOUTH
                maze[new_coords[0]][new_coords[1]] -= NORTH

            # if new row is less than current row (MOVING NORTH)
            elif new_coords[0] < current_coords[0]:
                maze[current_coords[0]][current_coords[1]] -= NORTH
                maze[new_coords[0]][new_coords[1]] -= SOUTH

            # if new column is greater than current column (MOVING EAST)
            elif new_coords[1] > current_coords[1]:
                maze[current_coords[0]][current_coords[1]] -= EAST
                maze[new_coords[0]][new_coords[1]] -= WEST

            # if new column is less than current column (MOVING WEST)
            else:
                maze[current_coords[0]][current_coords[1]] -= WEST
                maze[new_coords[0]][new_coords[1]] -= EAST

            # if not at the exit
            if new_coords != [maze_rows-1,maze_columns-1]:
                
                # add directions to stack or queue in random order
                movements = MOVEMENTS.copy()
                random.shuffle(movements)

                for movement in movements:
                    knock_through_wall(new_coords,movement,seen,maze)

# conducts a BFS or DFS of the maze
def maze_search(maze,window,search_method,visualise_search=False):

    # number of seconds between adding dots for visualisation
    TIME_DELAY = 0.015
    
    maze_rows = len(maze)
    maze_columns = len(maze[0])
    path_circles = list()

    # a dictionary storing the coords of the previous coords, for each coords but the first
    came_from = dict()

    # at the entrance of the maze, top left
    start = [0,0]

    if search_method == 'bfs':
        # a queue for the breadth first search
        search_data_structure = deque()
        search_data_structure.append(start)
    else:
        # a stack (list) for the depth first search
        search_data_structure = list()
        search_data_structure.append(start)
    
    # starting point does not have a previous coords
    came_from[coords_to_string(start)] = None

    # while data structure is not empty
    while len(search_data_structure) > 0:
        
        # get next cell to search
        if search_method == 'bfs':
            cell = search_data_structure.popleft()
        else:
            cell = search_data_structure.pop()

        # draw red circles visualising bfs
        if visualise_search: 
            path_circles.append(draw_path_circle(cell[0],cell[1],window))
            sleep(TIME_DELAY)

        # if gotten to exit, quit
        if cell == [maze_rows-1,maze_columns-1]:
            break

        wall_bitmask = maze[cell[0]][cell[1]]

        # a list of booleans of whether that cell has a wall or not
        walls = \
        [
            (wall_bitmask & NORTH) > 0, 
            (wall_bitmask & EAST) > 0, 
            (wall_bitmask & SOUTH) > 0,
            (wall_bitmask & WEST) > 0
        ]

        for wall in range(len(walls)):
            # if there is not a wall
            if not walls[wall]:
                # new coord moves through to the new cell
                new_cell = [cell[0] + MOVEMENTS[wall][0],cell[1] + MOVEMENTS[wall][1]]
                # adding to the came from dictionary, recording each cells past cell position
                if coords_to_string(new_cell) not in came_from:
                    search_data_structure.append(new_cell)
                    came_from[coords_to_string(new_cell)] = cell

    # path to exit is a list of the coords from the entrance to the exit
    path_to_exit = list()
    path_to_exit.append(cell)
    
    current_position = came_from[coords_to_string(cell)]

    # looping through the dictionary, tracing back to the beginning
    while current_position != None:
        path_to_exit.append(current_position)
        current_position = came_from[coords_to_string(current_position)]

    # reversing the path, so first list coords is at the beginning of the path
    path_to_exit = path_to_exit[::-1]

    if visualise_search:
        # pause to see the red circles
        sleep(1)
        # undrawing all of the red circles
        for circle in path_circles:
            circle.undraw()
            del circle

    # -1 at the len since you don't need to draw a line at the exit coord
    for index in range(len(path_to_exit)-1):
        
        # starting and finishing points of the line
        starting_point = Point(ORIGIN_POINT + WALL_DISTANCE/2 + (path_to_exit[index][1]*WALL_DISTANCE),ORIGIN_POINT + WALL_DISTANCE/2 + (path_to_exit[index][0]*WALL_DISTANCE))
        finishing_point = Point(ORIGIN_POINT + WALL_DISTANCE/2 + (path_to_exit[index+1][1]*WALL_DISTANCE),ORIGIN_POINT + WALL_DISTANCE/2 + (path_to_exit[index+1][0]*WALL_DISTANCE))

        the_line = Line(starting_point,finishing_point)
        the_line.setOutline('lime')
        the_line.draw(window)

def main():

    # creating the window
    window = GraphWin("My Maze Program", WINDOW_RESOLUTION, WINDOW_RESOLUTION)
    window.setBackground('black')

    maze = generate_full_maze(ROWS,COLUMNS)
    maze = generate_passages(maze)
    draw_maze(maze,window)

    # r = restart (generating a new maze), b = bread first search, d = depth first search
    keys = ['r','b','d']

    key_input = window.getKey().lower()

    # Pauses until a key that isn't 'R' is pressed
    while key_input in keys:
        
        # undraw the existing maze, generate a new one and draw it
        if key_input == 'r': 
            # https://stackoverflow.com/questions/45517677/graphics-py-how-to-clear-the-window
            for item in window.items[:]:
                item.undraw()
                window.update()

            maze = generate_full_maze(ROWS,COLUMNS)
            maze = generate_passages(maze)
            draw_maze(maze,window)

        # BFS or DFS
        elif key_input == 'b':
            maze_search(maze,window,'bfs',visualise_search=VISUALISE)
        elif key_input == 'd':
            maze_search(maze,window,'dfs',visualise_search=VISUALISE)

        key_input = window.getKey().lower()
     
    window.close()    # Close window when done

if __name__ == "__main__":
    main()
