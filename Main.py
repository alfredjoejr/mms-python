
import API
import sys
import time
from collections import deque

# --- CONFIGURATION ---
MAZE_SIZE = 16
CENTER_GOALS = [(7, 7), (7, 8), (8, 7), (8, 8)]
START_GOAL = [(0, 0)]

# --- STATE MANAGEMENT ---
# 0 = Searching for Center
# 1 = Searching for Start (Return)
# 2 = Speed Run (Fastest Path)
STATE = 0 

# --- GLOBALS ---
x = 0
y = 0
d = 0  # 0:N, 1:E, 2:S, 3:W
walls = [[[False, False, False, False] for _ in range(MAZE_SIZE)] for _ in range(MAZE_SIZE)]
costs = [[999 for _ in range(MAZE_SIZE)] for _ in range(MAZE_SIZE)]

def log(string):
    sys.stderr.write("{}\n".format(string))
    sys.stderr.flush()

def update_walls():
    """Reads sensors and updates the wall map."""
    global x, y, d, walls
    if API.wallFront():
        walls[x][y][d] = True
        if d==0 and y<15: walls[x][y+1][2]=True
        if d==1 and x<15: walls[x+1][y][3]=True
        if d==2 and y>0:  walls[x][y-1][0]=True
        if d==3 and x>0:  walls[x-1][y][1]=True
    if API.wallRight():
        d_r = (d + 1) % 4
        walls[x][y][d_r] = True
        if d_r==0 and y<15: walls[x][y+1][2]=True
        if d_r==1 and x<15: walls[x+1][y][3]=True
        if d_r==2 and y>0:  walls[x][y-1][0]=True
        if d_r==3 and x>0:  walls[x-1][y][1]=True
    if API.wallLeft():
        d_l = (d + 3) % 4
        walls[x][y][d_l] = True
        if d_l==0 and y<15: walls[x][y+1][2]=True
        if d_l==1 and x<15: walls[x+1][y][3]=True
        if d_l==2 and y>0:  walls[x][y-1][0]=True
        if d_l==3 and x>0:  walls[x-1][y][1]=True

def flood_fill(targets):
    """Calculates distances to the specific targets provided."""
    global costs, walls
    
    # Reset costs
    for i in range(MAZE_SIZE):
        for j in range(MAZE_SIZE):
            costs[i][j] = 999
    
    queue = deque()
    for tx, ty in targets:
        costs[tx][ty] = 0
        queue.append((tx, ty))

    while queue:
        cx, cy = queue.popleft()
        current_cost = costs[cx][cy]
        
        # Directions: N, E, S, W
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for direction, (dx, dy) in enumerate(directions):
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE:
                # IMPORTANT: Only move if there is NO wall known in memory
                if not walls[cx][cy][direction]: 
                    if costs[nx][ny] > current_cost + 1:
                        costs[nx][ny] = current_cost + 1
                        queue.append((nx, ny))

def move_best_step():
    """Moves the robot to the neighbor with the lowest cost."""
    global x, y, d
    
    min_val = 999
    best_dir = -1
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    # Check all 4 neighbors
    for direction, (dx, dy) in enumerate(directions):
        nx, ny = x + dx, y + dy
        if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE:
            # If path is clear in memory
            if not walls[x][y][direction]:
                if costs[nx][ny] < min_val:
                    min_val = costs[nx][ny]
                    best_dir = direction

    if best_dir != -1:
        # Turn to face best direction
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
        # Update coordinates
        if d == 0: y += 1
        if d == 1: x += 1
        if d == 2: y -= 1
        if d == 3: x -= 1

def main():
    global STATE
    log("Running Search, Return, and Speed Run...")
    API.setText(0, 0, "START")
    API.setColor(0, 0, "G")
    
    start_time = 0

    while True:
        # --- STATE 0: SEARCH TO CENTER ---
        if STATE == 0:
            update_walls()
            flood_fill(CENTER_GOALS)
            if costs[x][y] == 0:
                log("Center Found! Switching to Return Mode.")
                STATE = 1
                continue 
                
        # --- STATE 1: SEARCH BACK TO START ---
        elif STATE == 1:
            update_walls()
            flood_fill(START_GOAL)
            if costs[x][y] == 0:
                log("Back at Start! BEGINNING SPEED RUN.")
                
                # Start Timer
                start_time = time.time()
                log("Timer Started!")
                
                STATE = 2
                continue

        # --- STATE 2: SPEED RUN (Safe Mode) ---
        elif STATE == 2:
            # We keep scanning walls to avoid crashing into unknown shortcuts
            update_walls() 
            flood_fill(CENTER_GOALS)
            
            # Check for win
            if costs[x][y] == 0:
                # Stop Timer
                end_time = time.time()
                duration = end_time - start_time
                log(f"SPEED RUN COMPLETE! Time: {duration:.4f} seconds")
                
                API.setText(x, y, "WIN")
                API.setColor(x, y, "R")
                break

        # --- VISUALS & MOVEMENT ---
        API.setText(x, y, str(costs[x][y]))
        if STATE == 2:
            API.setColor(x, y, "R") # Red for Speed Run
        else:
            API.setColor(x, y, "G") # Green for Search

        # Move
        move_best_step()

if __name__ == "__main__":
    main()
