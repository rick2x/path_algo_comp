# tests/test_app.py
import unittest
import sys
import os

# Add the parent directory to the Python path to import app.py
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import TERRAIN_COSTS, Node, astar, dijkstra, bfs, gbfs, bidirectional_astar

class TestPathfindingWithForest(unittest.TestCase):
    def setUp(self):
        # Define Forest terrain type and cost for clarity in tests
        self.forest_type = 4
        self.forest_cost = TERRAIN_COSTS[self.forest_type] # Should be 3
        self.plain_cost = TERRAIN_COSTS[0] # Should be 1
        self.wall_type = 1

    def test_forest_terrain_cost_astar(self):
        # Grid: S P F E  (Start, Plain, Forest, End)
        # S at (0,0), P at (0,1), F at (0,2), E at (0,3)
        # Path: S -> P -> F -> E
        # Cost: 1 (P) + 3 (F) + 1 (E's plain cost, assuming end is also plain for movement cost) = 5
        # Or, if movement cost is for entering the cell: Cost to enter P from S is 1. Cost to enter F from P is 3. Cost to enter E from F is 1. Total g at E should be 1+3 = 4.
        # Let's clarify: the cost is associated with *entering* a cell.
        # So, S(0) -> P(1) -> F(1+3=4) -> E(4+1=5).
        grid = [[0, 0, self.forest_type, 0]]
        start = (0,0)
        end = (0,3)

        visited, path = astar(grid, start, end)
        self.assertTrue(len(path) > 0, "A* did not find a path.")

        end_node_data = next((n for n in visited if tuple(n['pos']) == end), None)
        self.assertIsNotNone(end_node_data, "End node not in visited list for A*.")
        # The 'g' cost at the end node is the total cost of the path.
        # Path is S(0,0) -> (0,1) -> (0,2) -> (0,3)
        # Cost to enter (0,1) is 1 (plain_cost). g at (0,1) is 1.
        # Cost to enter (0,2) from (0,1) is 3 (forest_cost). g at (0,2) is 1+3 = 4.
        # Cost to enter (0,3) from (0,2) is 1 (plain_cost). g at (0,3) is 4+1 = 5.
        expected_g_at_end = self.plain_cost + self.forest_cost + self.plain_cost
        self.assertEqual(end_node_data['g'], expected_g_at_end, f"A* path cost with forest incorrect. Expected {expected_g_at_end}, Got {end_node_data['g']}")

    def test_forest_terrain_cost_dijkstra(self):
        grid = [[0, self.forest_type, 0]]
        start = (0,0)
        end = (0,2)
        # Path: S(0,0) -> F(0,1) -> E(0,2)
        # Cost to enter F from S = 3 (forest_cost). g at F = 3.
        # Cost to enter E from F = 1 (plain_cost). g at E = 3+1 = 4.
        expected_g_at_end = self.forest_cost + self.plain_cost

        visited, path = dijkstra(grid, start, end)
        self.assertTrue(len(path) > 0, "Dijkstra did not find a path.")
        end_node_data = next((n for n in visited if tuple(n['pos']) == end), None)
        self.assertIsNotNone(end_node_data, "End node not in visited list for Dijkstra.")
        self.assertEqual(end_node_data['g'], expected_g_at_end, f"Dijkstra path cost with forest incorrect. Expected {expected_g_at_end}, Got {end_node_data['g']}")

    def test_forest_preference_astar(self):
        # Grid:
        # S . E  (S=(0,0), E=(0,2))
        # . F .  (F=(1,1) is Forest)
        # Path 1: S -> (0,1) -> E. Cost = cost(0,1) + cost(E) = plain_cost + plain_cost = 1 + 1 = 2
        # Path 2: S -> (1,0) -> F(1,1) -> (1,2) -> E(0,2) (if E is reachable from (1,2) and (0,1))
        # Cost for Path 2 (S->(1,0)->(1,1)(F)->(1,2)->(0,2)(E)):
        # Enter (1,0) from (0,0) = 1
        # Enter (1,1)(F) from (1,0) = 3
        # Enter (1,2) from (1,1)(F) = 1
        # Enter (0,2)(E) from (1,2) = 1. Total = 1+3+1+1 = 6
        # A* should choose path S->(0,1)->E
        grid = [
            [0, 0, 0], # S . E
            [0, self.forest_type, 0]  # . F .
        ]
        start = (0,0)
        end = (0,2)
        expected_path = [(0,0), (0,1), (0,2)]
        expected_g_at_end = self.plain_cost + self.plain_cost

        visited, path = astar(grid, start, end)
        self.assertEqual(path, expected_path, "A* did not choose the cheaper plain path over a path potentially involving forest.")
        end_node_data = next((n for n in visited if tuple(n['pos']) == end), None)
        self.assertIsNotNone(end_node_data, "End node data not found in A* visited")
        self.assertEqual(end_node_data['g'], expected_g_at_end, "A* cost for cheaper path incorrect.")

    def test_bfs_path_ignores_forest_cost_for_path_choice(self):
        # BFS should choose the 2-step path SFE regardless of forest cost.
        grid_bfs = [
            [0, self.forest_type, 0], # S(0,0) -> F(0,1) -> E(0,2)
        ]
        start_bfs = (0,0)
        end_bfs = (0,2)
        expected_path_bfs = [(0,0), (0,1), (0,2)]

        visited, path = bfs(grid_bfs, start_bfs, end_bfs)
        self.assertEqual(path, expected_path_bfs, "BFS did not choose the shortest path in steps.")

        # The 'g' in the last element of visited_nodes_in_order for BFS if path found is updated to total_cost.
        if path:
            end_node_data_bfs = visited[-1]
            # Cost to enter F(0,1) from S(0,0) is forest_cost (3)
            # Cost to enter E(0,2) from F(0,1) is plain_cost (1)
            # Total cost = 3 + 1 = 4
            expected_bfs_total_cost = self.forest_cost + self.plain_cost
            self.assertEqual(end_node_data_bfs['g'], expected_bfs_total_cost, "BFS path cost calculation using terrain costs is incorrect.")


    def test_gbfs_influenced_by_forest(self):
        # GBFS might choose a path through forest if it looks heuristically closer, even if costly.
        # S(0,0) E(2,2)
        # Grid:
        # S P P
        # P F P  (F at (1,1) is Forest, cost 3)
        # P P E
        # Path via plain: S(0,0)->P(0,1)->P(0,2)->P(1,2)->E(2,2). Cost = 1+1+1+1=4. Heuristic for P(0,1) to E(2,2) is 3.
        # Path via forest: S(0,0)->P(1,0)->F(1,1)->P(2,1)->E(2,2). Cost = 1+3+1+1=6. Heuristic for P(1,0) to E(2,2) is 3.
        # Heuristic for F(1,1) to E(2,2) is 2.
        # GBFS explores based on h score.
        # S(0,0) h=4. Neighbors: (0,1) h=3, (1,0) h=3.
        # Assume (0,1) is picked. From (0,1) h=3. Neighbors: (0,0)[closed], (0,2) h=2, (1,1)(F) h=2.
        # If (1,1)(F) is picked (due to tie-breaking or order), path might go through forest.
        # Path (0,0)->(0,1)->(1,1)(F)->(2,1)->(2,2)(E). Cost: 1+3+1+1 = 6
        grid = [
            [0,0,0],
            [0,self.forest_type,0],
            [0,0,0]
        ]
        start = (0,0)
        end = (2,2)

        visited, path = gbfs(grid, start, end)
        self.assertTrue(len(path) > 0, "GBFS did not find a path.")

        forest_node_pos = (1,1)
        forest_in_path = any(p == forest_node_pos for p in path)

        end_node_data = next((n for n in visited if tuple(n['pos']) == end), None)
        self.assertIsNotNone(end_node_data, "End node data not found in GBFS visited")

        if forest_in_path:
            # Path S->(0,1)->F(1,1)->(2,1)->E(2,2)  g = 1 (to 0,1) + 3 (to 1,1) + 1 (to 2,1) + 1 (to 2,2) = 6
            # Path S->(1,0)->F(1,1)->(1,2)->E(2,2)  g = 1 (to 1,0) + 3 (to 1,1) + 1 (to 1,2) + 1 (to 2,2) = 6
            # Path S->(0,1)->F(1,1)->(1,2)->E(2,2)
            # Check if (0,1) is parent of (1,1) then (1,1) is parent of (1,2) etc.
            # Need to reconstruct parent chain to verify exact path and cost if it goes through forest.
            # For this test, we're satisfied if it finds a path and the cost is consistent.
            # If path is (0,0)-(0,1)-(1,1)-(2,1)-(2,2), g at (2,2) should be 1+3+1+1 = 6
            # If path is (0,0)-(1,0)-(1,1)-(1,2)-(2,2), g at (2,2) should be 1+3+1+1 = 6
            # If path is (0,0)-(0,1)-(0,2)-(1,2)-(2,2), g at (2,2) should be 1+1+1+1 = 4
            # If path is (0,0)-(1,0)-(2,0)-(2,1)-(2,2), g at (2,2) should be 1+1+1+1 = 4

            # For GBFS, g-cost is still calculated correctly, even if path choice is suboptimal.
            # So, if it went through forest, the cost reflects that.
            # Example: (0,0)->(0,1)->(1,1)(F)->(1,2)->(2,2)(E) -> g at E is 1(0,1)+3(1,1)+1(1,2)+1(2,2) = 6
            # Example: (0,0)->(0,1)->(1,1)(F)->(2,1)->(2,2)(E) -> g at E is 1(0,1)+3(1,1)+1(2,1)+1(2,2) = 6
            # If it chose the plain path S(0,0)->P(0,1)->P(0,2)->P(1,2)->E(2,2), cost is 4.
            # This test is more about ensuring forest doesn't break GBFS and costs are noted.

            # We'll check if the reported g cost is one of the possibilities.
            possible_costs = [
                self.plain_cost * 4, # All plain path
                self.plain_cost + self.forest_cost + self.plain_cost + self.plain_cost # Path through forest
            ]
            self.assertIn(end_node_data['g'], possible_costs, f"GBFS path cost {end_node_data['g']} not one of expected {possible_costs}")

        def test_bidirectional_astar_forest_cost(self):
            grid = [[0, self.forest_type, 0]] # S F E
            start = (0,0)
            end = (0,2)
            # Cost to enter F(0,1) from S(0,0) is forest_cost (3)
            # Cost to enter E(0,2) from F(0,1) is plain_cost (1)
            # Total path_cost = 3 + 1 = 4
            expected_path_cost = self.forest_cost + self.plain_cost

            visited_nodes, path, path_cost_val = bidirectional_astar(grid, start, end)
            self.assertTrue(len(path) > 0, "Bidirectional A* did not find a path.")
            self.assertEqual(path_cost_val, expected_path_cost, f"Bidirectional A* path cost with forest incorrect. Expected {expected_path_cost}, Got {path_cost_val}")

if __name__ == '__main__':
    unittest.main()
