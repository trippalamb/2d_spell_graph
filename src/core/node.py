"""Node class for the spell graph simulation."""
from enum import Enum
import arcade


class NodeType(Enum):
    """Types of nodes in the graph."""
    BASIC = "basic"


class Node:
    """
    Represents a node in the spatial physics graph.

    Attributes:
        x: X position in screen coordinates
        y: Y position in screen coordinates
        node_type: Type of the node (enum)
        force: Current force value
        instability: Accumulated force from other nodes
    """

    def __init__(self, x: float, y: float, node_type: NodeType = NodeType.BASIC):
        """
        Initialize a node.

        Args:
            x: X position
            y: Y position
            node_type: Type of node (default: BASIC)
        """
        self.x = x
        self.y = y
        self.node_type = node_type
        self.force = 0.0
        self.instability = 0.0
        self.radius = 15  # Visual radius for rendering

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

    def draw(self):
        """Draw the node on screen."""
        color = self.get_color()

        # Draw filled circle
        arcade.draw_circle_filled(self.x, self.y, self.radius, color)

        # Draw black outline
        arcade.draw_circle_outline(self.x, self.y, self.radius, arcade.color.BLACK, 2)
