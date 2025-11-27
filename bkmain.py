import API
import sys
import time
from collections import deque

# --- CONFIGURATION ---
MAZE_SIZE = 16
# The center destination cells (Standard Micromouse Goal)
GOALS = [(7, 7), (7, 8), (8, 7), (8, 8)]

# Since the code can't "see" the simulator settings, you must type them here:
MOUSE_NAME = "Flood_Fill_Standard" 
MAZE_NAME = "example4"  
OUTPUT_FILE = "speed_test.txt"

# Global variables to track robot state
x = 0
y = 0
d = 0  # 0: North, 1: East, 2: South, 3: West

# 16x16 grid to store walls. 
# walls[x][y] = [North, East, South, West] (True if wall exists)
walls = [[[False, False, False, False] for _ in range(MAZE_SIZE)] for _ in range(MAZE_SIZE)]

# 16x16 grid to store distance values
costs = [[999 for _ in range(MAZE_SIZE)] for _ in range(MAZE_SIZE)]

def log(string):
    sys.stderr.write("{}\n".format(string))
    sys.stderr.flush()

def save_result_to_file(duration):
    """Appends the run details to a text file."""
    try:
        with open(OUTPUT_FILE, "a") as f:
            f.write(f"mode: {MOUSE_NAME}\n")
            f.write(f"maze: {MAZE_NAME}\n")
            f.write(f"speed: {duration:.4f}\n")
            f.write("-" * 20 + "\n") 
        log(f"Saved result to {OUTPUT_FILE}")
    except Exception as e:
        log(f"Error saving to file: {e}")

def update_walls():
    """Checks actual sensors and updates the internal wall map."""
    global x, y, d, walls
    
    # Check Front
    if API.wallFront():
        walls[x][y][d] = True
        if d == 0 and y < 15: walls[x][y+1][2] = True
        if d == 1 and x < 15: walls[x+1][y][3] = True
        if d == 2 and y > 0:  walls[x][y-1][0] = True
        if d == 3 and x > 0:  walls[x-1][y][1] = True

    # Check Right
    if API.wallRight():
        d_right = (d + 1) % 4
        walls[x][y][d_right] = True
        if d_right == 0 and y < 15: walls[x][y+1][2] = True
        if d_right == 1 and x < 15: walls[x+1][y][3] = True
        if d_right == 2 and y > 0:  walls[x][y-1][0] = True
        if d_right == 3 and x > 0:  walls[x-1][y][1] = True

    # Check Left
    if API.wallLeft():
        d_left = (d + 3) % 4
        walls[x][y][d_left] = True
        if d_left == 0 and y < 15: walls[x][y+1][2] = True
        if d_left == 1 and x < 15: walls[x+1][y][3] = True
        if d_left == 2 and y > 0:  walls[x][y-1][0] = True
        if d_left == 3 and x > 0:  walls[x-1][y][1] = True

def flood_fill():
    """Recalculates the distance to the goal for every cell."""
    global costs, walls
    
    # 1. Reset all costs to infinity
    for i in range(MAZE_SIZE):
        for j in range(MAZE_SIZE):
            costs[i][j] = 999
    
    # 2. Initialize the goal cells to 0
    queue = deque()
    for gx, gy in GOALS:
        costs[gx][gy] = 0
        queue.append((gx, gy))

    # 3. Process the queue (BFS Algorithm)
    while queue:
        cx, cy = queue.popleft()
        current_cost = costs[cx][cy]

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for direction, (dx, dy) in enumerate(directions):
            nx, ny = cx + dx, cy + dy

            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE:
                if not walls[cx][cy][direction]: 
                    if costs[nx][ny] > current_cost + 1:
                        costs[nx][ny] = current_cost + 1
                        queue.append((nx, ny))

def move_robot():
    """Decides where to move based on lowest cost neighbor."""
    global x, y, d
    
    min_val = 999
    best_dir = -1

    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    for direction, (dx, dy) in enumerate(directions):
        nx, ny = x + dx, y + dy
        
        if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE:
            if not walls[x][y][direction]:
                if costs[nx][ny] < min_val:
                    min_val = costs[nx][ny]
                    best_dir = direction

    if best_dir == -1:
        return

    if best_dir == d:
        pass
    elif best_dir == (d + 1) % 4:
        API.turnRight()
        d = (d + 1) % 4
    elif best_dir == (d + 3) % 4:
        API.turnLeft()
        d = (d + 3) % 4
    else:
        API.turnRight()
        API.turnRight()
        d = (d + 2) % 4

    API.moveForward()
    if d == 0: y += 1
    if d == 1: x += 1
    if d == 2: y -= 1
    if d == 3: x -= 1

def main():
    log("Starting Search Run...")
    API.setColor(0, 0, "G")
    API.setText(0, 0, "START")

    start_time = time.time()
    log("Timer Started!")

    while True:
        # 1. Read Sensors & Update Wall Map
        update_walls()

        # 2. Recalculate Numbers (Flood Fill)
        flood_fill()
        
        # 3. Draw numbers
        API.setText(x, y, str(costs[x][y]))
        API.setColor(x, y, "G") 

        # 4. Check if we reached the goal (Center)
        if costs[x][y] == 0:
            end_time = time.time()
            duration = end_time - start_time
            log(f"GOAL REACHED! Search Time: {duration:.4f} seconds")
            
            # --- SAVE TO FILE ---
            save_result_to_file(duration)
            # --------------------

            API.setText(x, y, "GOAL")
            API.setColor(x, y, "R")
            break 

        # 5. Move to the best neighbor
        move_robot()

if __name__ == "__main__":
    main()