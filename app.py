# app.py

import heapq
import time
from flask import Flask, render_template, request, jsonify
from collections import deque # Import deque for BFS queue

app = Flask(__name__)

# --- Configuration ---
TERRAIN_COSTS = { 
    0: 1,            # Plain
    1: float('inf'), # Wall
    2: 5,            # Water
    3: 10,           # Mud
    4: 3             # Forest
}

class Node:
    """A node class for all pathfinding algorithms"""
    def __init__(self, parent=None, position=None):
        self.parent = parent
        self.position = position
        self.g = 0  # Cost from start
        self.h = 0  # Heuristic cost to end
        self.f = 0  # Total cost (g + h)

    def __eq__(self, other):
        return self.position == other.position

    def __lt__(self, other):
        # A* and Dijkstra use f-score for priority
        return self.f < other.f

    def __repr__(self):
        return f"Node({self.position}, f={self.f})"

# --- Pathfinding Algorithms ---

def astar(terrain_grid, start_pos, end_pos):
    """A* Search Algorithm"""
    start_node, end_node = Node(None, start_pos), Node(None, end_pos)
    open_list, closed_list = [], set()
    heapq.heappush(open_list, (start_node.f, start_node))
    visited_nodes_in_order = []
    rows, cols = len(terrain_grid), len(terrain_grid[0])

    while len(open_list) > 0:
        _, current_node = heapq.heappop(open_list)
        visited_nodes_in_order.append({
            'pos': current_node.position, 'g': current_node.g, 
            'h': current_node.h, 'f': current_node.f
        })
        closed_list.add(current_node.position)

        if current_node == end_node:
            path = []
            while current_node is not None:
                path.append(current_node.position)
                current_node = current_node.parent
            return visited_nodes_in_order, path[::-1]

        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
            
            terrain_type = terrain_grid[node_position[0]][node_position[1]]
            if TERRAIN_COSTS.get(terrain_type, float('inf')) == float('inf'): continue
            
            child = Node(current_node, node_position)
            if child.position in closed_list: continue
            
            movement_cost = TERRAIN_COSTS.get(terrain_type, 1)
            child.g = current_node.g + movement_cost
            child.h = abs(child.position[0] - end_node.position[0]) + abs(child.position[1] - end_node.position[1]) # Heuristic
            child.f = child.g + child.h

            if any(child == open_node and child.g >= open_node.g for f, open_node in open_list): continue
            heapq.heappush(open_list, (child.f, child))

    return visited_nodes_in_order, []

def gbfs(terrain_grid, start_pos, end_pos):
    """Greedy Best-First Search Algorithm"""
    start_node, end_node = Node(None, start_pos), Node(None, end_pos)
    open_list, closed_list = [], set()
    # Priority for GBFS is h_score
    heapq.heappush(open_list, (start_node.h, start_node)) # Use h_score for priority
    visited_nodes_in_order = []
    rows, cols = len(terrain_grid), len(terrain_grid[0])

    start_node.h = abs(start_node.position[0] - end_node.position[0]) + abs(start_node.position[1] - end_node.position[1])
    start_node.f = start_node.h # f can be set to h for consistency or ignored

    while len(open_list) > 0:
        _, current_node = heapq.heappop(open_list) # Priority is h_score
        visited_nodes_in_order.append({
            'pos': current_node.position, 'g': current_node.g, 
            'h': current_node.h, 'f': current_node.f # f might be h, g+h, or just h
        })
        closed_list.add(current_node.position)

        if current_node == end_node:
            path = []
            while current_node is not None:
                path.append(current_node.position)
                current_node = current_node.parent
            return visited_nodes_in_order, path[::-1]

        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
            
            terrain_type = terrain_grid[node_position[0]][node_position[1]]
            if TERRAIN_COSTS.get(terrain_type, float('inf')) == float('inf'): continue
            
            child = Node(current_node, node_position)
            if child.position in closed_list: continue
            
            movement_cost = TERRAIN_COSTS.get(terrain_type, 1)
            child.g = current_node.g + movement_cost # g is actual cost from start
            child.h = abs(child.position[0] - end_node.position[0]) + abs(child.position[1] - end_node.position[1]) # Heuristic
            child.f = child.h # For GBFS, f can be considered as h, or g+h if needed for display

            # Check if child is in open_list and if new path is better (lower h for GBFS)
            # For GBFS, we typically don't need to update nodes already in open_list based on g-score,
            # because the priority is solely h. However, if a node with the same position
            # is re-added, heapq handles multiple entries, and we'll pick the one with lowest h.
            # A simple check to avoid redundant nodes if their h might differ (e.g. different parents)
            # but for simple grid heuristic, h is fixed.
            # The main check is `if child.position in closed_list: continue`
            
            # If we want to update if a "better" path to an existing node in open list is found (not typical for pure GBFS):
            # found_in_open = False
            # for i, (h_val, open_node_item) in enumerate(open_list):
            #     if open_node_item == child:
            #         if child.h < h_val: # or child.g < open_node_item.g if considering path cost to it
            #             open_list[i] = (child.h, child) # Update with new priority
            #             heapq.heapify(open_list) # Re-sort
            #         found_in_open = True
            #         break
            # if not found_in_open:
            #      heapq.heappush(open_list, (child.h, child))
            # else: # simple add, duplicates are fine as lowest h is picked.
            heapq.heappush(open_list, (child.h, child))


    return visited_nodes_in_order, []

def reconstruct_bi_path(node_fwd, node_bwd):
    """Reconstructs path for bidirectional search from meeting nodes."""
    path_fwd = []
    curr = node_fwd
    while curr:
        path_fwd.append(curr.position)
        curr = curr.parent
    path_fwd.reverse()

    path_bwd = []
    curr = node_bwd
    while curr:
        path_bwd.append(curr.position)
        curr = curr.parent
    # path_bwd is already from meeting_node to end_node's original start (which is end_pos)
    # but the parents are set from end_pos towards meeting_node, so it also needs reversing.
    # No, the parent for backward search point from a child to its parent (towards end_pos)
    # Example: end_pos <- child.parent <- child <- meeting_node_bwd_parent
    # So path_bwd will be [meeting_node_bwd.position, meeting_node_bwd.parent.position, ..., end_pos]
    # This list is already in the correct order (from meeting node to end_pos via bwd search parents).
    # No reversal needed for path_bwd.

    # The meeting node (node_fwd.position or node_bwd.position) is included in both paths.
    # Remove one instance to avoid duplication.
    if path_fwd and path_bwd and path_fwd[-1] == path_bwd[0]:
        path_bwd.pop(0)
        
    return path_fwd + path_bwd

def bidirectional_astar(terrain_grid, start_pos, end_pos):
    """Bidirectional A* Search Algorithm"""
    rows, cols = len(terrain_grid), len(terrain_grid[0])

    # Node initialization for forward search (from start to end)
    start_node_fwd = Node(None, start_pos)
    end_node_fwd = Node(None, end_pos) # Target for forward search
    
    # Node initialization for backward search (from end to start)
    start_node_bwd = Node(None, end_pos) # Starting point for backward search
    end_node_bwd = Node(None, start_pos) # Target for backward search

    # open_list_fwd: Priority queue for nodes to be evaluated in the forward search. Stores (f_score, node).
    # open_list_bwd: Priority queue for nodes to be evaluated in the backward search. Stores (f_score, node).
    open_list_fwd, open_list_bwd = [], []
    
    # closed_list_fwd: Dictionary to store nodes already evaluated in the forward search {position: node}.
    #                  Used to avoid reprocessing nodes and for path reconstruction.
    # closed_list_bwd: Dictionary to store nodes already evaluated in the backward search {position: node}.
    closed_list_fwd, closed_list_bwd = {}, {} 
    
    visited_nodes_in_order = [] # Stores visited nodes for visualization, with direction.

    # Heuristic calculation for forward search: Manhattan distance from current node to end_pos.
    # h_fwd = abs(current_node.position[0] - end_node_fwd.position[0]) + abs(current_node.position[1] - end_node_fwd.position[1])
    start_node_fwd.h = abs(start_pos[0] - end_pos[0]) + abs(start_pos[1] - end_pos[1]) # h_fwd for start node
    start_node_fwd.f = start_node_fwd.h # g is 0 for start node
    heapq.heappush(open_list_fwd, (start_node_fwd.f, start_node_fwd))

    # Heuristic calculation for backward search: Manhattan distance from current node to start_pos.
    # h_bwd = abs(current_node.position[0] - end_node_bwd.position[0]) + abs(current_node.position[1] - end_node_bwd.position[1])
    start_node_bwd.h = abs(end_pos[0] - start_pos[0]) + abs(end_pos[1] - start_pos[1]) # h_bwd for start node (which is end_pos)
    start_node_bwd.f = start_node_bwd.h # g is 0 for start node of backward search
    heapq.heappush(open_list_bwd, (start_node_bwd.f, start_node_bwd))

    meeting_node_pos = None # Stores the position of the meeting node if a path is found
    path_cost = float('inf') # Cost of the best path found so far, initialized to infinity

    # Main loop: continues as long as there are nodes to explore in both search directions.
    # The search can terminate early if a condition (min_f_fwd + min_f_bwd >= path_cost) is met.
    while open_list_fwd and open_list_bwd:
        # Forward search step
        if open_list_fwd: # Check if there are nodes to process in the forward search
            f_fwd, current_node_fwd = heapq.heappop(open_list_fwd) # Get node with smallest f-score
            
            # If this node position is already in closed_list_fwd with a better or equal f-score, skip.
            if current_node_fwd.position in closed_list_fwd and \
               closed_list_fwd[current_node_fwd.position].f <= f_fwd:
                pass 
            else:
                # Add current node to closed list of forward search
                closed_list_fwd[current_node_fwd.position] = current_node_fwd
                # Record visited node for visualization
                visited_nodes_in_order.append({'pos': current_node_fwd.position, 'g': current_node_fwd.g, 'h': current_node_fwd.h, 'f': current_node_fwd.f, 'dir': 'fwd'})

                # Check if the current node from forward search is in the closed list of backward search.
                # This indicates a meeting point of the two searches.
                if current_node_fwd.position in closed_list_bwd:
                    node_from_bwd_search = closed_list_bwd[current_node_fwd.position]
                    current_total_cost = current_node_fwd.g + node_from_bwd_search.g # g-cost from start + g-cost from end
                    
                    # If this path is better than any previously found path, update path_cost and meeting details.
                    if current_total_cost < path_cost:
                        path_cost = current_total_cost
                        meeting_node_pos = current_node_fwd.position
                        # These nodes represent the meeting point from both directions for the best path found so far.
                        # They are used by reconstruct_bi_path.
                        final_fwd_node = current_node_fwd 
                        final_bwd_node = node_from_bwd_search
                    # The search continues even after finding a meeting point because a shorter path might still be discovered.
                    # The termination condition (min_f_fwd + min_f_bwd >= path_cost) ensures optimality.

                # Explore neighbors of the current forward search node
                for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]: # Adjacent squares
                    node_position = (current_node_fwd.position[0] + new_position[0], current_node_fwd.position[1] + new_position[1])
                    
                    # Boundary check
                    if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
                    
                    # Wall check
                    terrain_type = terrain_grid[node_position[0]][node_position[1]]
                    cost_val = TERRAIN_COSTS.get(terrain_type, float('inf'))
                    if cost_val == float('inf'): continue

                    # Create new node for forward search
                    child_fwd = Node(current_node_fwd, node_position)
                    child_fwd.g = current_node_fwd.g + cost_val # Cost from start to child
                    # Heuristic for forward search: Manhattan distance to end_node_fwd (target)
                    child_fwd.h = abs(child_fwd.position[0] - end_node_fwd.position[0]) + abs(child_fwd.position[1] - end_node_fwd.position[1])
                    child_fwd.f = child_fwd.g + child_fwd.h

                    # If child is in closed_list_fwd and the existing node has a better or equal f-score, skip.
                    if node_position in closed_list_fwd and closed_list_fwd[node_position].f <= child_fwd.f:
                        continue
                    
                    # If child is in open_list_fwd with a better or equal f-score, skip.
                    # This check is complex with heapq. Simpler to add and let heappop find the best.
                    # The closed list check above handles cases where a node is re-expanded.
                    heapq.heappush(open_list_fwd, (child_fwd.f, child_fwd))

        # Backward search step (similar logic to forward search, but directions and targets are reversed)
        if open_list_bwd: # Check if there are nodes to process in the backward search
            f_bwd, current_node_bwd = heapq.heappop(open_list_bwd) # Get node with smallest f-score

            # If this node position is already in closed_list_bwd with a better or equal f-score, skip.
            if current_node_bwd.position in closed_list_bwd and \
               closed_list_bwd[current_node_bwd.position].f <= f_bwd:
                pass
            else:
                # Add current node to closed list of backward search
                closed_list_bwd[current_node_bwd.position] = current_node_bwd
                # Record visited node for visualization
                visited_nodes_in_order.append({'pos': current_node_bwd.position, 'g': current_node_bwd.g, 'h': current_node_bwd.h, 'f': current_node_bwd.f, 'dir': 'bwd'})

                # Check if the current node from backward search is in the closed list of forward search.
                if current_node_bwd.position in closed_list_fwd:
                    node_from_fwd_search = closed_list_fwd[current_node_bwd.position]
                    current_total_cost = current_node_bwd.g + node_from_fwd_search.g # g-cost from end + g-cost from start
                    
                    # If this path is better, update path_cost and meeting details.
                    if current_total_cost < path_cost:
                        path_cost = current_total_cost
                        meeting_node_pos = current_node_bwd.position
                        # These nodes represent the meeting point from both directions for the best path found so far.
                        final_fwd_node = node_from_fwd_search
                        final_bwd_node = current_node_bwd
                
                # Explore neighbors of the current backward search node
                for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]: # Adjacent squares
                    node_position = (current_node_bwd.position[0] + new_position[0], current_node_bwd.position[1] + new_position[1])

                    # Boundary check
                    if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
                    
                    # Wall check
                    terrain_type = terrain_grid[node_position[0]][node_position[1]]
                    cost_val = TERRAIN_COSTS.get(terrain_type, float('inf'))
                    if cost_val == float('inf'): continue

                    # Create new node for backward search
                    child_bwd = Node(current_node_bwd, node_position)
                    child_bwd.g = current_node_bwd.g + cost_val # Cost from end to child (following path backward)
                    # Heuristic for backward search: Manhattan distance to end_node_bwd (which is start_pos)
                    child_bwd.h = abs(child_bwd.position[0] - end_node_bwd.position[0]) + abs(child_bwd.position[1] - end_node_bwd.position[1])
                    child_bwd.f = child_bwd.g + child_bwd.h
                    
                    # If child is in closed_list_bwd and the existing node has a better or equal f-score, skip.
                    if node_position in closed_list_bwd and closed_list_bwd[node_position].f <= child_bwd.f:
                        continue
                    heapq.heappush(open_list_bwd, (child_bwd.f, child_bwd))
        
        # Termination Condition:
        # The loop breaks if a path has been found (meeting_node_pos is not None) AND
        # the sum of the minimum f-scores from both open lists (min_f_fwd + min_f_bwd)
        # is greater than or equal to the cost of the best path found so far (path_cost).
        # This ensures that any potential path explored further will not be better than the current best path.
        # This condition relies on the heuristic being admissible (never overestimating the true cost).
        if open_list_fwd and open_list_bwd and meeting_node_pos: # Check only if open lists are not empty and a path exists
            min_f_fwd = open_list_fwd[0][0] # Smallest f-score in forward open list
            min_f_bwd = open_list_bwd[0][0] # Smallest f-score in backward open list
            if min_f_fwd + min_f_bwd >= path_cost:
                break # Terminate: no better path can be found.
    
    # Path Reconstruction:
    # If a meeting_node_pos was set (meaning a path was found and path_cost < infinity),
    # reconstruct the path.
    if meeting_node_pos:
        # final_fwd_node and final_bwd_node were stored when the best path_cost was updated.
        # These are the nodes at the meeting point from their respective search directions.
        path = reconstruct_bi_path(final_fwd_node, final_bwd_node)
        return visited_nodes_in_order, path, path_cost
        
    return visited_nodes_in_order, [], float('inf') # No path found or one of the lists became empty before meeting


def dijkstra(terrain_grid, start_pos, end_pos):
    """Dijkstra's Algorithm: A* where heuristic is always 0."""
    start_node, end_node = Node(None, start_pos), Node(None, end_pos)
    open_list, closed_list = [], set()
    heapq.heappush(open_list, (start_node.f, start_node))
    visited_nodes_in_order = []
    rows, cols = len(terrain_grid), len(terrain_grid[0])

    while len(open_list) > 0:
        _, current_node = heapq.heappop(open_list)
        visited_nodes_in_order.append({
            'pos': current_node.position, 'g': current_node.g,
            'h': 0, 'f': current_node.g # h=0, f=g
        })
        closed_list.add(current_node.position)

        if current_node == end_node:
            path = []
            while current_node is not None: path.append(current_node.position); current_node = current_node.parent
            return visited_nodes_in_order, path[::-1]

        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
            terrain_type = terrain_grid[node_position[0]][node_position[1]]
            if TERRAIN_COSTS.get(terrain_type, float('inf')) == float('inf'): continue
            
            child = Node(current_node, node_position)
            if child.position in closed_list: continue
            
            movement_cost = TERRAIN_COSTS.get(terrain_type, 1)
            child.g = current_node.g + movement_cost
            child.h = 0  # The only difference from A*!
            child.f = child.g

            if any(child == open_node and child.g >= open_node.g for f, open_node in open_list): continue
            heapq.heappush(open_list, (child.f, child))

    return visited_nodes_in_order, []

def bfs(terrain_grid, start_pos, end_pos):
    """Breadth-First Search: Ignores costs, finds shortest path in steps."""
    start_node, end_node = Node(None, start_pos), Node(None, end_pos)
    open_list, closed_list = deque([start_node]), set([start_node.position])
    visited_nodes_in_order = []
    rows, cols = len(terrain_grid), len(terrain_grid[0])

    while len(open_list) > 0:
        current_node = open_list.popleft()
        visited_nodes_in_order.append({
            'pos': current_node.position, 'g': current_node.g, 'h': 0, 'f': 0
        })
        
        if current_node == end_node:
            path, total_cost = [], 0
            temp = current_node
            # Calculate cost from entering nodes, excluding the start node's own cost.
            # The path reconstruction will go from end_node to start_node.
            # We add costs of nodes in path until we reach the start_node's child.
            path_reconstruction_list = []
            while temp.parent is not None: # Iterate until temp is the child of the start node
                path_reconstruction_list.append(temp.position)
                terrain_type = terrain_grid[temp.position[0]][temp.position[1]]
                total_cost += TERRAIN_COSTS.get(terrain_type, 1)
                temp = temp.parent
            path_reconstruction_list.append(temp.position) # Add the start node position

            path = path_reconstruction_list[::-1] # Reverse to get path from start to end
            visited_nodes_in_order[-1]['g'] = total_cost # Store the calculated total_cost
            return visited_nodes_in_order, path

        for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            node_position = (current_node.position[0] + new_position[0], current_node.position[1] + new_position[1])
            if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
            terrain_type = terrain_grid[node_position[0]][node_position[1]]
            if TERRAIN_COSTS.get(terrain_type, float('inf')) == float('inf'): continue
            if node_position in closed_list: continue
            
            child = Node(current_node, node_position)
            child.g = current_node.g + 1 # g is just the number of steps
            closed_list.add(child.position)
            open_list.append(child)
            
    return visited_nodes_in_order, []

# --- Flask Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve_maze():
    data = request.get_json()

    # Input Validation
    if not data:
        return jsonify({'error': 'Invalid input: No data provided.'}), 400
    
    required_keys = ['grid', 'start', 'end']
    for key in required_keys:
        if key not in data:
            return jsonify({'error': f'Invalid input: Missing key: {key}.'}), 400

    terrain_grid = data['grid']
    start_pos_list = data['start']
    end_pos_list = data['end']
    algorithm = data.get('algorithm', 'astar') # Default to astar if not provided

    if not isinstance(terrain_grid, list) or not all(isinstance(row, list) for row in terrain_grid):
        return jsonify({'error': 'Invalid input: Grid must be a list of lists.'}), 400
    
    if not terrain_grid or not terrain_grid[0]: # Check if grid is empty or rows are empty
        return jsonify({'error': 'Invalid input: Grid cannot be empty.'}), 400

    rows = len(terrain_grid)
    cols = len(terrain_grid[0])

    for r_idx, row in enumerate(terrain_grid):
        if len(row) != cols:
            return jsonify({'error': f'Invalid input: All grid rows must have the same length. Row {r_idx} has length {len(row)}, expected {cols}.'}), 400
        for c_idx, cell in enumerate(row):
            if not isinstance(cell, int) and not isinstance(cell, float): # Allow float for potential future use, though current TERRAIN_COSTS uses int keys
                return jsonify({'error': f'Invalid input: Grid cells must be numbers. Cell at ({r_idx},{c_idx}) is not a number.'}), 400
            # Further check if cell value is a valid key in TERRAIN_COSTS could be added if strict adherence to defined terrain types is required.
            # For now, we assume unknown terrain types will default to a high cost or be handled by TERRAIN_COSTS.get()

    if not (isinstance(start_pos_list, list) or isinstance(start_pos_list, tuple)) or len(start_pos_list) != 2:
        return jsonify({'error': 'Invalid input: Start position must be a list or tuple of two integers.'}), 400
    if not all(isinstance(coord, int) for coord in start_pos_list):
        return jsonify({'error': 'Invalid input: Start coordinates must be integers.'}), 400
    
    if not (isinstance(end_pos_list, list) or isinstance(end_pos_list, tuple)) or len(end_pos_list) != 2:
        return jsonify({'error': 'Invalid input: End position must be a list or tuple of two integers.'}), 400
    if not all(isinstance(coord, int) for coord in end_pos_list):
        return jsonify({'error': 'Invalid input: End coordinates must be integers.'}), 400

    start_pos = tuple(start_pos_list)
    end_pos = tuple(end_pos_list)

    if not (0 <= start_pos[0] < rows and 0 <= start_pos[1] < cols):
        return jsonify({'error': 'Invalid input: Start coordinates out of bounds.'}), 400
    if not (0 <= end_pos[0] < rows and 0 <= end_pos[1] < cols):
        return jsonify({'error': 'Invalid input: End coordinates out of bounds.'}), 400

    start_terrain_type = terrain_grid[start_pos[0]][start_pos[1]]
    if TERRAIN_COSTS.get(start_terrain_type, float('inf')) == float('inf'):
        return jsonify({'error': 'Invalid input: Start position is on a wall.'}), 400
    
    end_terrain_type = terrain_grid[end_pos[0]][end_pos[1]]
    if TERRAIN_COSTS.get(end_terrain_type, float('inf')) == float('inf'):
        return jsonify({'error': 'Invalid input: End position is on a wall.'}), 400
    
    # All validations passed, proceed with pathfinding
    start_time = time.time()
    path_cost_val = None # Initialize path_cost_val
    
    if algorithm == 'dijkstra':
        visited_nodes, path = dijkstra(terrain_grid, start_pos, end_pos)
    elif algorithm == 'bfs':
        visited_nodes, path = bfs(terrain_grid, start_pos, end_pos)
    elif algorithm == 'gbfs':
        visited_nodes, path = gbfs(terrain_grid, start_pos, end_pos)
    elif algorithm == 'bidirectional_astar':
        visited_nodes, path, path_cost_val = bidirectional_astar(terrain_grid, start_pos, end_pos)
    else: # Default to astar
        visited_nodes, path = astar(terrain_grid, start_pos, end_pos)
        
    execution_time = (time.time() - start_time) * 1000

    response_data = {
        'visited_nodes': visited_nodes,
        'path': path,
        'execution_time_ms': round(execution_time, 2)
    }
    if algorithm == 'bidirectional_astar' and path: # Only add path_cost if path was found
        response_data['path_cost'] = path_cost_val
    
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')