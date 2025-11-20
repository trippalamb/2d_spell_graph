"""Cursor for traversing the graph along directed edges."""
import arcade
from typing import List, Tuple, Optional
from src.core import Node, Edge


class Cursor:
    """
    A cursor that traverses the graph along directed edges.

    Attributes:
        current_node_index: Index of the current node
        current_edge_index: Index of the edge being traversed (None if at a node)
        progress: Progress along current edge (0.0 to 1.0)
        speed: Traversal speed (progress units per second)
        color: Color of the cursor
        radius: Visual radius of the cursor
    """

    def __init__(self, start_node_index: int, speed: float = 0.5, color: tuple = (255, 0, 255)):
        """
        Initialize a cursor.

        Args:
            start_node_index: Index of the starting node
            speed: Traversal speed (edges per second)
            color: RGB tuple for cursor color
        """
        self.current_node_index = start_node_index
        self.current_edge_index: Optional[int] = None
        self.progress = 0.0
        self.speed = speed
        self.color = color
        self.radius = 8
        self.position: Tuple[float, float] = (0, 0)

    def get_position(self, nodes: List[Node], edges: List[Edge],
                     edge_graph: dict) -> Tuple[float, float]:
        """
        Get the current visual position of the cursor.

        Args:
            nodes: List of all nodes
            edges: List of all edges
            edge_graph: Mapping from node index to list of edge indices

        Returns:
            (x, y) position tuple
        """
        if self.current_edge_index is None:
            # Cursor is at a node
            node = nodes[self.current_node_index]
            return (node.x, node.y)
        else:
            # Cursor is on an edge
            edge = edges[self.current_edge_index]
            return edge._get_point_at_distance(
                self.progress * edge._get_total_length()
            )[0]

    def update(self, dt: float, nodes: List[Node], edges: List[Edge],
               edge_graph: dict) -> Optional['Cursor']:
        """
        Update cursor position and handle traversal logic.

        Args:
            dt: Delta time in seconds
            nodes: List of all nodes
            edges: List of all edges
            edge_graph: Mapping from node index to list of edge indices

        Returns:
            New cursor if branching occurs, None otherwise
        """
        if self.current_edge_index is None:
            # At a node, pick an outgoing edge
            outgoing_edges = edge_graph.get(self.current_node_index, [])

            if len(outgoing_edges) == 0:
                # Dead end - stay at node
                return None
            elif len(outgoing_edges) == 1:
                # Single edge - follow it
                self.current_edge_index = outgoing_edges[0]
                self.progress = 0.0
            else:
                # Branch - follow first edge, create new cursor for second
                self.current_edge_index = outgoing_edges[0]
                self.progress = 0.0

                # Create new cursor for the branch
                new_cursor = Cursor(self.current_node_index, self.speed, self.color)
                new_cursor.current_edge_index = outgoing_edges[1]
                new_cursor.progress = 0.0
                return new_cursor
        else:
            # On an edge, advance along it
            self.progress += self.speed * dt

            if self.progress >= 1.0:
                # Reached end of edge
                edge = edges[self.current_edge_index]
                # Find destination node
                end_point = edge.points[-1]

                # Find which node this edge leads to
                for i, node in enumerate(nodes):
                    if abs(node.x - end_point[0]) < 1 and abs(node.y - end_point[1]) < 1:
                        self.current_node_index = i
                        self.current_edge_index = None
                        self.progress = 0.0
                        break

        return None

    def draw(self):
        """Draw the cursor."""
        # Draw cursor as filled circle with outline
        arcade.draw_circle_filled(self.position[0], self.position[1],
                                 self.radius, self.color)
        arcade.draw_circle_outline(self.position[0], self.position[1],
                                   self.radius, arcade.color.BLACK, 2)


class CursorManager:
    """
    Manages multiple cursors traversing the graph.

    Attributes:
        cursors: List of active cursors
        edge_graph: Mapping from node index to list of outgoing edge indices
        is_playing: Whether cursors are currently moving
    """

    def __init__(self):
        """Initialize the cursor manager."""
        self.cursors: List[Cursor] = []
        self.edge_graph: dict = {}
        self.is_playing = False

    def build_edge_graph(self, nodes: List[Node], edges: List[Edge]):
        """
        Build a graph mapping nodes to their outgoing edges.

        Args:
            nodes: List of all nodes
            edges: List of all edges
        """
        self.edge_graph = {i: [] for i in range(len(nodes))}

        for edge_idx, edge in enumerate(edges):
            # Find the starting node of this edge
            start_point = edge.points[0]

            for node_idx, node in enumerate(nodes):
                if abs(node.x - start_point[0]) < 1 and abs(node.y - start_point[1]) < 1:
                    self.edge_graph[node_idx].append(edge_idx)
                    break

    def restart(self, nodes: List[Node]):
        """
        Restart cursor traversal from the first node.

        Args:
            nodes: List of all nodes
        """
        self.cursors = []
        if len(nodes) > 0:
            self.cursors.append(Cursor(0))
        self.is_playing = True

    def toggle_play_pause(self):
        """Toggle between playing and paused states."""
        self.is_playing = not self.is_playing

    def update(self, dt: float, nodes: List[Node], edges: List[Edge]):
        """
        Update all cursors.

        Args:
            dt: Delta time in seconds
            nodes: List of all nodes
            edges: List of all edges
        """
        if not self.is_playing:
            # Update positions but don't advance
            for cursor in self.cursors:
                cursor.position = cursor.get_position(nodes, edges, self.edge_graph)
            return

        new_cursors = []

        for cursor in self.cursors:
            # Update cursor position
            cursor.position = cursor.get_position(nodes, edges, self.edge_graph)

            # Advance cursor and check for branching
            branch_cursor = cursor.update(dt, nodes, edges, self.edge_graph)
            if branch_cursor is not None:
                branch_cursor.position = branch_cursor.get_position(nodes, edges, self.edge_graph)
                new_cursors.append(branch_cursor)

        # Add any new cursors from branching
        self.cursors.extend(new_cursors)

    def draw(self):
        """Draw all cursors."""
        for cursor in self.cursors:
            cursor.draw()
