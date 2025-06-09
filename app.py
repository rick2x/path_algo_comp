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
    3: 10            # Mud
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

    start_node_fwd = Node(None, start_pos)
    end_node_fwd = Node(None, end_pos) # Target for forward search
    
    start_node_bwd = Node(None, end_pos) # Starting point for backward search
    end_node_bwd = Node(None, start_pos) # Target for backward search

    open_list_fwd, open_list_bwd = [], []
    # Using dicts for closed_lists to store the node itself for path reconstruction and g-score checks
    closed_list_fwd, closed_list_bwd = {}, {} 
    
    visited_nodes_in_order = []

    # Heuristics
    start_node_fwd.h = abs(start_pos[0] - end_pos[0]) + abs(start_pos[1] - end_pos[1])
    start_node_fwd.f = start_node_fwd.h
    heapq.heappush(open_list_fwd, (start_node_fwd.f, start_node_fwd))

    start_node_bwd.h = abs(end_pos[0] - start_pos[0]) + abs(end_pos[1] - start_pos[1])
    start_node_bwd.f = start_node_bwd.h
    heapq.heappush(open_list_bwd, (start_node_bwd.f, start_node_bwd))

    meeting_node_pos = None
    path_cost = float('inf')

    while open_list_fwd and open_list_bwd:
        # Forward search step
        if open_list_fwd:
            f_fwd, current_node_fwd = heapq.heappop(open_list_fwd)
            
            if current_node_fwd.position in closed_list_fwd and closed_list_fwd[current_node_fwd.position].f < f_fwd:
                pass # Already found a better path to this node
            else:
                closed_list_fwd[current_node_fwd.position] = current_node_fwd
                visited_nodes_in_order.append({'pos': current_node_fwd.position, 'g': current_node_fwd.g, 'h': current_node_fwd.h, 'f': current_node_fwd.f, 'dir': 'fwd'})

                if current_node_fwd.position in closed_list_bwd:
                    # Meeting point found
                    node_from_bwd_search = closed_list_bwd[current_node_fwd.position]
                    current_total_cost = current_node_fwd.g + node_from_bwd_search.g
                    if current_total_cost < path_cost:
                        path_cost = current_total_cost
                        meeting_node_pos = current_node_fwd.position
                        # Store the nodes that met for path reconstruction
                        final_fwd_node = current_node_fwd
                        final_bwd_node = node_from_bwd_search
                    # Potential optimization: check if f_fwd + f_bwd_min >= path_cost, if so, break.
                    # For now, we continue until one list is empty or a tighter condition is met.


                for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    node_position = (current_node_fwd.position[0] + new_position[0], current_node_fwd.position[1] + new_position[1])
                    if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
                    
                    terrain_type = terrain_grid[node_position[0]][node_position[1]]
                    cost_val = TERRAIN_COSTS.get(terrain_type, float('inf'))
                    if cost_val == float('inf'): continue

                    child_fwd = Node(current_node_fwd, node_position)
                    child_fwd.g = current_node_fwd.g + cost_val
                    child_fwd.h = abs(child_fwd.position[0] - end_node_fwd.position[0]) + abs(child_fwd.position[1] - end_node_fwd.position[1])
                    child_fwd.f = child_fwd.g + child_fwd.h

                    if node_position in closed_list_fwd and closed_list_fwd[node_position].f <= child_fwd.f:
                        continue
                    
                    # Check if in open list and if new path is worse
                    # This check is more complex for heapq. A simpler way is to allow duplicates and rely on heappop to get the best.
                    # Or, if a node is already in open_list_fwd with a smaller f value, skip.
                    # For simplicity, we push and let heapq sort it out. If a better path is found later, closed_list check will handle it.
                    heapq.heappush(open_list_fwd, (child_fwd.f, child_fwd))

        # Backward search step
        if open_list_bwd:
            f_bwd, current_node_bwd = heapq.heappop(open_list_bwd)

            if current_node_bwd.position in closed_list_bwd and closed_list_bwd[current_node_bwd.position].f < f_bwd:
                pass
            else:
                closed_list_bwd[current_node_bwd.position] = current_node_bwd
                visited_nodes_in_order.append({'pos': current_node_bwd.position, 'g': current_node_bwd.g, 'h': current_node_bwd.h, 'f': current_node_bwd.f, 'dir': 'bwd'})

                if current_node_bwd.position in closed_list_fwd:
                     # Meeting point found
                    node_from_fwd_search = closed_list_fwd[current_node_bwd.position]
                    current_total_cost = current_node_bwd.g + node_from_fwd_search.g
                    if current_total_cost < path_cost:
                        path_cost = current_total_cost
                        meeting_node_pos = current_node_bwd.position
                        final_fwd_node = node_from_fwd_search
                        final_bwd_node = current_node_bwd

                for new_position in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                    node_position = (current_node_bwd.position[0] + new_position[0], current_node_bwd.position[1] + new_position[1])
                    if not (0 <= node_position[0] < rows and 0 <= node_position[1] < cols): continue
                    
                    terrain_type = terrain_grid[node_position[0]][node_position[1]]
                    cost_val = TERRAIN_COSTS.get(terrain_type, float('inf'))
                    if cost_val == float('inf'): continue

                    child_bwd = Node(current_node_bwd, node_position)
                    child_bwd.g = current_node_bwd.g + cost_val
                    child_bwd.h = abs(child_bwd.position[0] - end_node_bwd.position[0]) + abs(child_bwd.position[1] - end_node_bwd.position[1])
                    child_bwd.f = child_bwd.g + child_bwd.h
                    
                    if node_position in closed_list_bwd and closed_list_bwd[node_position].f <= child_bwd.f:
                        continue
                    heapq.heappush(open_list_bwd, (child_bwd.f, child_bwd))
        
        # Termination condition improvement: if the sum of smallest f-values in both open lists >= path_cost found so far
        if open_list_fwd and open_list_bwd and meeting_node_pos:
            min_f_fwd = open_list_fwd[0][0]
            min_f_bwd = open_list_bwd[0][0]
            if min_f_fwd + min_f_bwd >= path_cost: # Heuristic admissibility adjustment might be needed here for correctness in some variants.
                                                 # For standard A*, f = g+h. If h is admissible, this should be fine.
                                                 # The path_cost is g1+g2. We are comparing f1+f2 with g1+g2.
                                                 # This condition is more complex than simple meeting. A simpler stop is when one search meets a closed node of another.
                                                 # The provided logic already updates path_cost when a meeting occurs.
                                                 # The loop will continue to find potentially better meeting points.
                break # Terminate the while loop if no better path can be found
                # pass # Continue searching for better paths if any -> Old behavior

    if meeting_node_pos: # This means path_cost is not float('inf')
        # Reconstruct path using the stored final_fwd_node and final_bwd_node corresponding to the best path_cost
        # Need to ensure these nodes are correctly captured when path_cost is updated.
        # Re-fetch from closed lists using meeting_node_pos to be sure.
        node_fwd_at_meet = closed_list_fwd[meeting_node_pos]
        node_bwd_at_meet = closed_list_bwd[meeting_node_pos]
        
        path = reconstruct_bi_path(node_fwd_at_meet, node_bwd_at_meet)
        # The g-value for the final path needs to be correctly reported.
        # The 'g' in visited_nodes_in_order for the meeting node might be from one direction.
        # We can add a final entry for the meeting node with the total cost.
        # For now, the path_cost variable holds the correct total g-cost.
        # The last element in visited_nodes_in_order might not be the meeting node or have the final g.
        # This can be refined if specific display of final path cost at meeting point is needed.
        return visited_nodes_in_order, path, path_cost
        
    return visited_nodes_in_order, [], float('inf') # Return inf cost if no path


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
            while temp is not None:
                path.append(temp.position)
                terrain_type = terrain_grid[temp.position[0]][temp.position[1]]
                total_cost += TERRAIN_COSTS.get(terrain_type, 1)
                temp = temp.parent
            visited_nodes_in_order[-1]['g'] = total_cost
            return visited_nodes_in_order, path[::-1]

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
    terrain_grid = data['grid']
    start_pos = tuple(data['start'])
    end_pos = tuple(data['end'])
    algorithm = data.get('algorithm', 'astar')

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