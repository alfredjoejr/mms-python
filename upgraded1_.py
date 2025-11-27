import API
import sys
import time
import heapq  # <--- NEW IMPORT for Priority Queue

# --- CONFIGURATION ---
MAZE_SIZE = 16
CENTER_GOALS = [(7, 7), (7, 8), (8, 7), (8, 8)]
START_GOAL = [(0, 0)]

# --- LOGGING CONFIGURATION ---
MOUSE_NAME = "Python_Weighted_FloodFill" 
MAZE_NAME = "example4"  
OUTPUT_FILE = "speed_test.txt"

# --- STATE MANAGEMENT ---
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

def save_result_to_file(duration):
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

# --- NEW: WEIGHTED FLOOD FILL ---
def flood_fill(targets):
    """
    Calculates costs using Dijkstra's Algorithm to penalize turns.
    Cost = Distance + (Turn_Penalty * Number_of_Turns)
    """
    global costs, walls
    
    # 1. Reset costs to infinity
    for i in range(MAZE_SIZE):
        for j in range(MAZE_SIZE):
            costs[i][j] = 999
    
    # Priority Queue stores: (cost, x, y, arrival_direction)
    # arrival_direction is needed to calculate turn penalties
    pq = []
    
    # Initialize targets
    for tx, ty in targets:
        costs[tx][ty] = 0
        # For the goal, we assume we could arrive from any direction, so add all
        for direction in range(4):
            heapq.heappush(pq, (0, tx, ty, direction))

    while pq:
        cost, cx, cy, arrival_dir = heapq.heappop(pq)
        
        # If we found a faster way to this cell already, skip
        if cost > costs[cx][cy]:
            continue
        
        costs[cx][cy] = cost

        # Check neighbors (Inverse logic: We are flowing FROM goal TO start)
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)] # N, E, S, W
        
        for move_dir, (dx, dy) in enumerate(directions):
            nx, ny = cx + dx, cy + dy
            
            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE:
                # We are looking strictly at connectivity
                # Since we are flooding backwards from goal, we check if the neighbor 
                # can enter the current cell.
                # Neighbor (nx,ny) moving in 'move_dir' should land on (cx,cy)? 
                # No, we need to check the wall strictly between them.
                
                # Let's verify wall between current(cx,cy) and neighbor(nx,ny)
                # The wall is defined by move_dir relative to cx,cy
                if not walls[cx][cy][move_dir]:
                    
                    # Calculate Cost
                    # 1. Base movement cost
                    new_cost = cost + 1
                    
                    # 2. Turn Penalty?
                    # The path flows FROM goal TO start.
                    # If the 'arrival_dir' (how we got to current) is different 
                    # from 'move_dir' (where neighbor is), that represents a turn 
                    # in the actual forward run.
                    
                    # If this is a straight line, it's cheap. If it's a turn, it's expensive.
                    # Note: We use the REVERSE direction because we are flooding backwards.
                    # But simpler logic: Just punish change of direction.
                    if move_dir != arrival_dir:
                        new_cost += 10 # PENALTY FOR TURNING! (Adjust this number)
                    
                    # If this path is better, record it
                    if new_cost < costs[nx][ny]:
                        costs[nx][ny] = new_cost
                        # The neighbor will "arrive" at us via the opposite of move_dir?
                        # Actually, for the queue, we just need to know how the flow continues.
                        heapq.heappush(pq, (new_cost, nx, ny, move_dir))

# --- NEW: MOMENTUM MOVEMENT ---
def move_best_step():
    global x, y, d
    
    min_val = 9999
    best_dir = -1
    
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
    
    for direction, (dx, dy) in enumerate(directions):
        nx, ny = x + dx, y + dy
        if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE:
            if not walls[x][y][direction]:
                
                cost = costs[nx][ny]
                
                # TIE BREAKER:
                # If the cost is the same, ALWAYS prefer the direction we are already facing.
                # This prevents the robot from jittering.
                if direction != d:
                    cost += 0.1
                
                if cost < min_val:
                    min_val = cost
                    best_dir = direction

    if best_dir != -1:
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
    global STATE
    log("Running Weighted Flood Fill...")
    API.setText(0, 0, "START")
    API.setColor(0, 0, "G")
    start_time = 0

    while True:
        if STATE == 0: # Search to Center
            update_walls()
            flood_fill(CENTER_GOALS)
            if costs[x][y] == 0:
                log("Center Found! Return Mode.")
                STATE = 1
                continue 
        elif STATE == 1: # Search to Start
            update_walls()
            flood_fill(START_GOAL)
            if costs[x][y] == 0:
                log("Back at Start! SPEED RUN.")
                start_time = time.time()
                STATE = 2
                continue
        elif STATE == 2: # Speed Run
            update_walls() 
            flood_fill(CENTER_GOALS)
            if costs[x][y] == 0:
                end_time = time.time()
                duration = end_time - start_time
                log(f"SPEED RUN COMPLETE! Time: {duration:.4f}")
                save_result_to_file(duration)
                API.setText(x, y, "WIN")
                API.setColor(x, y, "R")
                break

        API.setText(x, y, str(costs[x][y]))
        API.setColor(x, y, "R" if STATE==2 else "G")
        move_best_step()

if __name__ == "__main__":
    main()