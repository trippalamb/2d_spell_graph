"""Cursor for traversing the graph along directed edges."""
import arcade
import math
from typing import List, Tuple, Optional, Dict, Any, TYPE_CHECKING
from src.core import Node, Edge, SpellGraphEntity

if TYPE_CHECKING:
    from src.simulation.transform import CoordinateTransform


class Cursor(SpellGraphEntity):
    """
    A cursor that travels along an edge from one node to another.

    Cursors are born at a node, travel along a single edge, and die when
    they reach the destination node, spawning new cursors as needed.

    Attributes:
        source_node_index: Index of the starting node
        target_node_index: Index of the destination node
        edge_index: Index of the edge being traversed
        distance_traveled: Distance traveled along the edge path in pixels
        speed: Traversal speed in pixels per second
        color: Color of the cursor
        radius: Visual radius of the cursor
        is_alive: Whether this cursor is still active
    """

    def __init__(self, source_node_index: int, target_node_index: int,
                 edge_index: int, speed: float = 100.0, color: tuple = (255, 0, 255), entity_id: str = None):
        """
        Initialize a cursor.

        Args:
            source_node_index: Index of the starting node
            target_node_index: Index of the destination node
            edge_index: Index of the edge to traverse
            speed: Traversal speed in pixels per second
            color: RGB tuple for cursor color
            entity_id: Unique identifier (auto-generated if None)
        """
        if entity_id is None:
            entity_id = f"cursor_{id(self)}"
        super().__init__(entity_id)

        self.source_node_index = source_node_index
        self.target_node_index = target_node_index
        self.edge_index = edge_index
        self.distance_traveled = 0.0
        self.speed = speed
        self.color = color
        self.radius = 8
        self.position: Tuple[float, float] = (0, 0)
        self.is_alive = True

    def update(self, dt: float, edges: List[Edge]) -> bool:
        """
        Update cursor position along its edge.

        Args:
            dt: Delta time in seconds
            edges: List of all edges

        Returns:
            True if cursor reached destination, False otherwise
        """
        edge = edges[self.edge_index]
        total_length = edge._get_total_length()

        # Move along the edge
        self.distance_traveled += self.speed * dt

        if self.distance_traveled >= total_length:
            # Reached destination
            self.is_alive = False
            return True
        else:
            # Update position along path
            self.position = edge._get_point_at_distance(self.distance_traveled)[0]
            return False

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this cursor for display.

        Returns:
            Dictionary containing cursor information
        """
        return {
            "ID": self.entity_id,
            "Type": "Cursor",
            "Source Node": f"#{self.source_node_index}",
            "Target Node": f"#{self.target_node_index}",
            "Edge": f"#{self.edge_index}",
            "Position": f"({self.position[0]:.1f}, {self.position[1]:.1f})",
            "Distance Traveled": f"{self.distance_traveled:.1f}",
            "Speed": f"{self.speed:.1f}",
            "Alive": str(self.is_alive)
        }

    def contains_point(self, x: float, y: float, transform: 'CoordinateTransform') -> bool:
        """
        Check if a point (in world coordinates) is within this cursor.

        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            transform: Coordinate transform (not used for cursors, but required by interface)

        Returns:
            True if point is within cursor's radius
        """
        if not self.is_alive:
            return False

        distance = math.sqrt((x - self.position[0]) ** 2 + (y - self.position[1]) ** 2)
        return distance <= self.radius

    def draw(self, transform: 'CoordinateTransform'):
        """
        Draw the cursor.

        Args:
            transform: Coordinate transform for world-to-screen conversion
        """
        if self.is_alive:
            # Convert world position to screen position
            screen_x, screen_y = transform.world_to_screen(self.position[0], self.position[1])
            screen_radius = transform.scale_distance(self.radius)

            # Draw cursor as filled circle with outline
            arcade.draw_circle_filled(screen_x, screen_y, screen_radius, self.color)
            arcade.draw_circle_outline(screen_x, screen_y, screen_radius, arcade.color.BLACK, 2)


class CursorManager:
    """
    Manages multiple cursors traversing the graph.

    Attributes:
        cursors: List of active cursors
        edge_graph: Mapping from node index to list of (edge_index, target_node_index) tuples
        is_playing: Whether cursors are currently moving
        speed: Global cursor speed in pixels per second
    """

    def __init__(self, speed: float = 100.0):
        """
        Initialize the cursor manager.

        Args:
            speed: Cursor traversal speed in pixels per second
        """
        self.cursors: List[Cursor] = []
        self.edge_graph: dict = {}
        self.is_playing = False
        self.speed = speed

    def build_edge_graph(self, nodes: List[Node], edges: List[Edge]):
        """
        Build a graph mapping nodes to their outgoing edges.

        Args:
            nodes: List of all nodes
            edges: List of all edges
        """
        self.edge_graph = {i: [] for i in range(len(nodes))}

        for edge_idx, edge in enumerate(edges):
            # Edges now have direct references to start_node and end_node
            # Find the indices of these nodes in the nodes list
            source_idx = None
            target_idx = None

            for node_idx, node in enumerate(nodes):
                if node is edge.start_node:
                    source_idx = node_idx
                if node is edge.end_node:
                    target_idx = node_idx

            # Add to edge graph
            if source_idx is not None and target_idx is not None:
                self.edge_graph[source_idx].append((edge_idx, target_idx))

    def spawn_cursors_at_node(self, node_index: int):
        """
        Spawn cursors for all outgoing edges from a node.

        Args:
            node_index: Index of the node to spawn cursors from
        """
        outgoing_edges = self.edge_graph.get(node_index, [])

        for edge_idx, target_idx in outgoing_edges:
            cursor = Cursor(node_index, target_idx, edge_idx, self.speed)
            self.cursors.append(cursor)

    def restart(self, nodes: List[Node], edges: List[Edge] = None):
        """
        Restart cursor traversal from the first node.

        Args:
            nodes: List of all nodes
            edges: List of all edges (optional, rebuilds edge graph if provided)
        """
        self.cursors = []
        # Rebuild edge graph if edges provided (accounts for node movement)
        if edges is not None:
            self.build_edge_graph(nodes, edges)
        if len(nodes) > 0:
            # Spawn initial cursors from node 0
            self.spawn_cursors_at_node(0)
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
            return

        # Limit max cursors to prevent infinite growth with cyclical graphs
        MAX_CURSORS = 100

        cursors_to_remove = []
        nodes_to_spawn_from = []

        # Iterate over a COPY of the list to avoid issues with modification during iteration
        for cursor in self.cursors[:]:
            # Update cursor and check if it reached destination
            reached_destination = cursor.update(dt, edges)

            if reached_destination:
                cursors_to_remove.append(cursor)
                # Queue node for spawning (don't spawn during iteration)
                nodes_to_spawn_from.append(cursor.target_node_index)

        # Remove dead cursors
        for cursor in cursors_to_remove:
            if cursor in self.cursors:
                self.cursors.remove(cursor)

        # Spawn new cursors from destination nodes (after iteration is complete)
        for node_index in nodes_to_spawn_from:
            if len(self.cursors) < MAX_CURSORS:
                self.spawn_cursors_at_node(node_index)

    def draw(self, transform: 'CoordinateTransform'):
        """
        Draw all cursors.

        Args:
            transform: Coordinate transform for world-to-screen conversion
        """
        for cursor in self.cursors:
            cursor.draw(transform)
