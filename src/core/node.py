"""Node class for the spell graph simulation."""
from enum import Enum
import arcade
import math
from typing import Dict, Any, List, Tuple, TYPE_CHECKING

from src.core.entity import SpellGraphEntity

if TYPE_CHECKING:
    from src.simulation.transform import CoordinateTransform
    from src.core.edge import Edge, EdgeDirection


class NodeType(Enum):
    """Types of nodes in the graph."""
    BASIC = "basic"


# Inherent force values for each node type
NODE_TYPE_FORCES = {
    NodeType.BASIC: 10.0,  # Base force value for basic nodes
}


class Node(SpellGraphEntity):
    """
    Represents a node in the spatial physics graph.

    Attributes:
        x: X position in world coordinates
        y: Y position in world coordinates
        node_type: Type of the node (enum)
        force: Current force value
        instability: Accumulated force from other nodes
        edges: List of (edge, direction) tuples for attached edges
    """

    def __init__(self, x: float, y: float, node_type: NodeType = NodeType.BASIC, entity_id: str = None):
        """
        Initialize a node.

        Args:
            x: X position in world coordinates
            y: Y position in world coordinates
            node_type: Type of node (default: BASIC)
            entity_id: Unique identifier (auto-generated if None)
        """
        if entity_id is None:
            entity_id = f"node_{id(self)}"
        super().__init__(entity_id)

        self.x = x
        self.y = y
        self.node_type = node_type
        # Inherent force based on node type (used for repulsion in simulation)
        self.force = NODE_TYPE_FORCES.get(node_type, 10.0)
        self.instability = 0.0
        self.radius = 15  # Visual radius in world units
        self.edges: List[Tuple['Edge', 'EdgeDirection']] = []  # List of (edge, direction) tuples

    def add_edge(self, edge: 'Edge', direction: 'EdgeDirection'):
        """
        Add an edge connected to this node.

        Args:
            edge: The edge to add
            direction: Whether this is incoming or outgoing
        """
        self.edges.append((edge, direction))

    def get_color(self) -> tuple:
        """
        Calculate node color based on instability value.

        Uses a gradient from blue (low instability) to red (high instability).

        Returns:
            RGB tuple (0-255 range)
        """
        # Normalize instability to 0-1 range (clamped at max of 100)
        normalized = min(self.instability / 100.0, 1.0)

        # Blue to red gradient
        r = int(normalized * 255)
        g = 0
        b = int((1.0 - normalized) * 255)

        return (r, g, b)

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this node for display.

        Returns:
            Dictionary containing node information
        """
        return {
            "ID": self.entity_id,
            "Type": "Node",
            "Node Type": self.node_type.value,
            "Position": f"({self.x:.1f}, {self.y:.1f})",
            "Force": f"{self.force:.2f}",
            "Instability": f"{self.instability:.2f}",
            "Radius": f"{self.radius:.1f}"
        }

    def contains_point(self, x: float, y: float, transform: 'CoordinateTransform') -> bool:
        """
        Check if a point (in world coordinates) is within this node.

        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            transform: Coordinate transform (not used for nodes, but required by interface)

        Returns:
            True if point is within node's radius
        """
        distance = math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)
        return distance <= self.radius

    def draw(self, transform: 'CoordinateTransform'):
        """
        Draw the node on screen.

        Args:
            transform: Coordinate transform for world-to-screen conversion
        """
        color = self.get_color()

        # Convert world coordinates to screen coordinates
        screen_x, screen_y = transform.world_to_screen(self.x, self.y)
        screen_radius = transform.scale_distance(self.radius)

        # Draw filled circle
        arcade.draw_circle_filled(screen_x, screen_y, screen_radius, color)

        # Draw black outline
        arcade.draw_circle_outline(screen_x, screen_y, screen_radius, arcade.color.BLACK, 2)
