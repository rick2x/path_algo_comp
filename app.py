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
    
    if algorithm == 'dijkstra':
        visited_nodes, path = dijkstra(terrain_grid, start_pos, end_pos)
    elif algorithm == 'bfs':
        visited_nodes, path = bfs(terrain_grid, start_pos, end_pos)
    else:
        visited_nodes, path = astar(terrain_grid, start_pos, end_pos)
        
    execution_time = (time.time() - start_time) * 1000

    return jsonify({
        'visited_nodes': visited_nodes,
        'path': path,
        'execution_time_ms': round(execution_time, 2)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')