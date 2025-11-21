"""Edge class for the spell graph simulation."""
import math
import re
import arcade
from typing import List, Tuple, Dict, Any, TYPE_CHECKING, Optional
from enum import Enum

from src.core.entity import SpellGraphEntity

if TYPE_CHECKING:
    from src.simulation.transform import CoordinateTransform
    from src.core.node import Node


class EdgeDirection(Enum):
    """Direction of edge relative to a node."""
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class Edge(SpellGraphEntity):
    """
    Represents an edge in the spatial physics graph.

    Edges dynamically connect two nodes using cubic bezier curves.
    The edge path is recalculated whenever nodes or bezier handles move.

    Attributes:
        start_node: The source node
        end_node: The target node
        bezier_handle1: First bezier control handle (near start)
        bezier_handle2: Second bezier control handle (near end)
        num_segments: Number of segments to render the bezier curve
        is_selected: Whether this edge is currently selected
    """

    def __init__(self, start_node: 'Node', end_node: 'Node',
                 control_points: Optional[List[Tuple[float, float]]] = None,
                 entity_id: str = None):
        """
        Initialize an edge between two nodes.

        Args:
            start_node: Source node
            end_node: Target node
            control_points: Optional list of intermediate waypoints (legacy, converted to bezier)
            entity_id: Unique identifier (auto-generated if None)
        """
        if entity_id is None:
            entity_id = f"edge_{id(self)}"
        super().__init__(entity_id)

        self.start_node = start_node
        self.end_node = end_node
        self.num_segments = 10  # Number of segments to render bezier curve
        self.is_selected = False  # Whether this edge is currently selected

        # Arrow properties (cached for hit detection)
        self._arrow_position: Optional[Tuple[float, float]] = None
        self._arrow_angle: float = 0.0
        self._arrow_size: float = 14  # Slightly larger for visibility

        # Initialize bezier handles at 1/3 and 2/3 positions (straight line)
        self.bezier_handle1: Optional[Tuple[float, float]] = None
        self.bezier_handle2: Optional[Tuple[float, float]] = None
        self.reset_bezier_handles()

        # Legacy control_points support (ignored, using bezier instead)
        self.control_points = []

    def reset_bezier_handles(self):
        """Reset bezier handles to straight-line positions (1/3 and 2/3 along edge)."""
        start_x, start_y = self.start_node.x, self.start_node.y
        end_x, end_y = self.end_node.x, self.end_node.y

        # Handle 1 at 1/3 position
        self.bezier_handle1 = (
            start_x + (end_x - start_x) / 3,
            start_y + (end_y - start_y) / 3
        )
        # Handle 2 at 2/3 position
        self.bezier_handle2 = (
            start_x + 2 * (end_x - start_x) / 3,
            start_y + 2 * (end_y - start_y) / 3
        )

    def get_points(self) -> List[Tuple[float, float]]:
        """
        Get the current path points by calculating cubic bezier curve.

        Returns:
            List of (x, y) tuples representing the bezier curve
        """
        p0 = (self.start_node.x, self.start_node.y)
        p1 = self.bezier_handle1
        p2 = self.bezier_handle2
        p3 = (self.end_node.x, self.end_node.y)

        points = []
        for i in range(self.num_segments + 1):
            t = i / self.num_segments
            # Cubic bezier formula: B(t) = (1-t)³P0 + 3(1-t)²tP1 + 3(1-t)t²P2 + t³P3
            x = (1-t)**3 * p0[0] + 3*(1-t)**2*t * p1[0] + 3*(1-t)*t**2 * p2[0] + t**3 * p3[0]
            y = (1-t)**3 * p0[1] + 3*(1-t)**2*t * p1[1] + 3*(1-t)*t**2 * p2[1] + t**3 * p3[1]
            points.append((x, y))

        return points

    def get_handle_at_point(self, x: float, y: float, threshold: float = 15) -> Optional[int]:
        """
        Check if a point is near a bezier handle.

        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            threshold: Distance threshold for hit detection

        Returns:
            1 for handle1, 2 for handle2, None if not near any handle
        """
        # Check handle 1
        dx1 = x - self.bezier_handle1[0]
        dy1 = y - self.bezier_handle1[1]
        if math.sqrt(dx1*dx1 + dy1*dy1) <= threshold:
            return 1

        # Check handle 2
        dx2 = x - self.bezier_handle2[0]
        dy2 = y - self.bezier_handle2[1]
        if math.sqrt(dx2*dx2 + dy2*dy2) <= threshold:
            return 2

        return None

    def set_handle_position(self, handle_num: int, x: float, y: float):
        """
        Set the position of a bezier handle.

        Args:
            handle_num: 1 or 2
            x: New X coordinate
            y: New Y coordinate
        """
        if handle_num == 1:
            self.bezier_handle1 = (x, y)
        elif handle_num == 2:
            self.bezier_handle2 = (x, y)

    def reset_handle(self, handle_num: int):
        """
        Reset a single bezier handle to its straight-line position.

        Args:
            handle_num: 1 or 2
        """
        start_x, start_y = self.start_node.x, self.start_node.y
        end_x, end_y = self.end_node.x, self.end_node.y

        if handle_num == 1:
            self.bezier_handle1 = (
                start_x + (end_x - start_x) / 3,
                start_y + (end_y - start_y) / 3
            )
        elif handle_num == 2:
            self.bezier_handle2 = (
                start_x + 2 * (end_x - start_x) / 3,
                start_y + 2 * (end_y - start_y) / 3
            )

    def get_arrow_position(self) -> Tuple[Tuple[float, float], float]:
        """
        Get the current arrow position and angle.

        Returns:
            Tuple of ((x, y), angle) for the arrow
        """
        points = self.get_points()
        if len(points) < 2:
            return ((0, 0), 0.0)

        # Find which segment contains the 50% distance mark
        total_length = self._get_total_length()
        if total_length <= 0:
            return ((points[0][0], points[0][1]), 0.0)

        target_distance = total_length * 0.5
        current_distance = 0.0
        middle_segment_idx = 0

        # Find the segment that contains the midpoint
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            segment_length = math.sqrt(dx * dx + dy * dy)

            if current_distance + segment_length >= target_distance:
                middle_segment_idx = i
                break

            current_distance += segment_length

        # Get the two points of the segment containing the midpoint
        p1 = points[middle_segment_idx]
        p2 = points[middle_segment_idx + 1]

        # Position arrow at midpoint of this segment
        arrow_x = (p1[0] + p2[0]) / 2
        arrow_y = (p1[1] + p2[1]) / 2

        # Calculate direction angle
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        arrow_angle = math.atan2(dy, dx)

        # Offset perpendicular to the path for visibility
        offset_distance = 12  # world units offset from the path
        offset_angle = arrow_angle + math.pi / 2  # perpendicular to path
        offset_x = arrow_x + offset_distance * math.cos(offset_angle)
        offset_y = arrow_y + offset_distance * math.sin(offset_angle)

        # Cache the position for hit detection
        self._arrow_position = (offset_x, offset_y)
        self._arrow_angle = arrow_angle

        return ((offset_x, offset_y), arrow_angle)

    def arrow_contains_point(self, x: float, y: float, threshold: float = 18) -> bool:
        """
        Check if a point is near the direction arrow.

        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            threshold: Distance threshold for hit detection

        Returns:
            True if point is within threshold of the arrow
        """
        # Update arrow position
        self.get_arrow_position()

        if self._arrow_position is None:
            return False

        # Check distance from point to arrow center
        dx = x - self._arrow_position[0]
        dy = y - self._arrow_position[1]
        distance = math.sqrt(dx * dx + dy * dy)

        return distance <= threshold

    def reverse_direction(self):
        """
        Reverse the direction of this edge by swapping start and end nodes.
        Also updates the node-edge relationships.
        """
        # Swap the nodes
        self.start_node, self.end_node = self.end_node, self.start_node

        # Swap the bezier handles (so the curve shape is preserved but reversed)
        self.bezier_handle1, self.bezier_handle2 = self.bezier_handle2, self.bezier_handle1

        # Update node-edge relationships
        # Remove old relationships and add new ones
        for node_edge_pair in self.start_node.edges[:]:
            edge, direction = node_edge_pair
            if edge == self:
                self.start_node.edges.remove(node_edge_pair)
                break

        for node_edge_pair in self.end_node.edges[:]:
            edge, direction = node_edge_pair
            if edge == self:
                self.end_node.edges.remove(node_edge_pair)
                break

        # Add new relationships
        self.start_node.add_edge(self, EdgeDirection.OUTGOING)
        self.end_node.add_edge(self, EdgeDirection.INCOMING)

    def draw_handles(self, transform: 'CoordinateTransform'):
        """
        Draw bezier control handles (when edge is selected).

        Args:
            transform: Coordinate transform for world-to-screen conversion
        """
        # Get screen positions
        start_screen = transform.world_to_screen(self.start_node.x, self.start_node.y)
        end_screen = transform.world_to_screen(self.end_node.x, self.end_node.y)
        handle1_screen = transform.world_to_screen(self.bezier_handle1[0], self.bezier_handle1[1])
        handle2_screen = transform.world_to_screen(self.bezier_handle2[0], self.bezier_handle2[1])

        # Draw lines from nodes to handles
        arcade.draw_line(start_screen[0], start_screen[1],
                        handle1_screen[0], handle1_screen[1],
                        (100, 100, 100), 1)
        arcade.draw_line(end_screen[0], end_screen[1],
                        handle2_screen[0], handle2_screen[1],
                        (100, 100, 100), 1)

        # Draw handle circles
        handle_radius = 8
        arcade.draw_circle_filled(handle1_screen[0], handle1_screen[1],
                                  handle_radius, (255, 100, 100))
        arcade.draw_circle_outline(handle1_screen[0], handle1_screen[1],
                                   handle_radius, (200, 0, 0), 2)
        arcade.draw_circle_filled(handle2_screen[0], handle2_screen[1],
                                  handle_radius, (100, 100, 255))
        arcade.draw_circle_outline(handle2_screen[0], handle2_screen[1],
                                   handle_radius, (0, 0, 200), 2)

    def _calculate_tensions(self) -> List[float]:
        """
        Calculate tension values based on angles between segments.

        Tension is calculated as the angle difference at each intermediate point.
        Sharper angles create higher tension.

        Returns:
            List of tension values (0.0 to 1.0)
        """
        points = self.get_points()
        if len(points) < 3:
            return []

        tensions = []

        for i in range(1, len(points) - 1):
            p0 = points[i - 1]
            p1 = points[i]
            p2 = points[i + 1]

            # Calculate vectors
            v1 = (p1[0] - p0[0], p1[1] - p0[1])
            v2 = (p2[0] - p1[0], p2[1] - p1[1])

            # Calculate angle between vectors
            angle1 = math.atan2(v1[1], v1[0])
            angle2 = math.atan2(v2[1], v2[0])

            # Angle difference (0 to π)
            angle_diff = abs(angle2 - angle1)
            if angle_diff > math.pi:
                angle_diff = 2 * math.pi - angle_diff

            # Normalize to 0-1 range (π = max tension)
            tension = angle_diff / math.pi

            tensions.append(tension)

        return tensions

    def get_average_tension(self) -> float:
        """
        Get the average tension across the entire edge.

        Returns:
            Average tension value (0.0 to 1.0)
        """
        tension_values = self._calculate_tensions()
        if not tension_values:
            return 0.0
        return sum(tension_values) / len(tension_values)

    def get_color(self) -> tuple:
        """
        Calculate edge color based on average tension.

        Uses a gradient from green (low tension) to yellow to red (high tension).

        Returns:
            RGB tuple (0-255 range)
        """
        tension = self.get_average_tension()

        if tension < 0.5:
            # Green to yellow
            normalized = tension * 2  # 0 to 1
            r = int(normalized * 255)
            g = 255
            b = 0
        else:
            # Yellow to red
            normalized = (tension - 0.5) * 2  # 0 to 1
            r = 255
            g = int((1.0 - normalized) * 255)
            b = 0

        return (r, g, b)

    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this edge for display.

        Returns:
            Dictionary containing edge information
        """
        total_length = self._get_total_length()
        avg_tension = self.get_average_tension()
        tension_values = self._calculate_tensions()
        points = self.get_points()

        return {
            "ID": self.entity_id,
            "Type": "Edge",
            "Start Node": self.start_node.entity_id,
            "End Node": self.end_node.entity_id,
            "Points": f"{len(points)} points",
            "Length": f"{total_length:.1f}",
            "Avg Tension": f"{avg_tension:.3f}",
            "Max Tension": f"{max(tension_values):.3f}" if tension_values else "0.000"
        }

    def contains_point(self, x: float, y: float, transform: 'CoordinateTransform') -> bool:
        """
        Check if a point (in world coordinates) is near this edge.

        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            transform: Coordinate transform for distance calculations

        Returns:
            True if point is within threshold distance of the edge
        """
        threshold = 10  # world units
        points = self.get_points()

        # Check distance to each line segment
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            # Calculate distance from point to line segment
            dist = self._point_to_segment_distance(x, y, p1[0], p1[1], p2[0], p2[1])
            if dist <= threshold:
                return True

        return False

    def _point_to_segment_distance(self, px: float, py: float,
                                   x1: float, y1: float, x2: float, y2: float) -> float:
        """
        Calculate distance from a point to a line segment.

        Args:
            px, py: Point coordinates
            x1, y1: Segment start
            x2, y2: Segment end

        Returns:
            Distance from point to segment
        """
        # Vector from segment start to end
        dx = x2 - x1
        dy = y2 - y1

        # Length squared of segment
        length_sq = dx * dx + dy * dy

        if length_sq == 0:
            # Segment is a point
            return math.sqrt((px - x1) ** 2 + (py - y1) ** 2)

        # Calculate projection parameter
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / length_sq))

        # Calculate closest point on segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # Return distance to closest point
        return math.sqrt((px - closest_x) ** 2 + (py - closest_y) ** 2)

    def _get_total_length(self) -> float:
        """
        Calculate the total length of the edge path.

        Returns:
            Total path length in pixels
        """
        points = self.get_points()
        total_length = 0.0
        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            total_length += math.sqrt(dx * dx + dy * dy)
        return total_length

    def _get_point_at_distance(self, target_distance: float) -> Tuple[Tuple[float, float], float]:
        """
        Get the point along the path at a specific distance from the start.

        Args:
            target_distance: Distance along path from start

        Returns:
            Tuple of (point, angle) where angle is the direction of the path at that point
        """
        points = self.get_points()
        current_distance = 0.0

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            segment_length = math.sqrt(dx * dx + dy * dy)

            if current_distance + segment_length >= target_distance:
                # The target point is on this segment
                remaining = target_distance - current_distance
                t = remaining / segment_length if segment_length > 0 else 0

                # Interpolate position
                x = p1[0] + t * dx
                y = p1[1] + t * dy

                # Calculate angle (direction of the segment)
                angle = math.atan2(dy, dx)

                return ((x, y), angle)

            current_distance += segment_length

        # If we get here, return the last point
        if len(points) >= 2:
            p1 = points[-2]
            p2 = points[-1]
            angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            return (p2, angle)

        return (points[0], 0.0)

    def _draw_arrow(self, position: Tuple[float, float], angle: float, color: tuple,
                    transform: 'CoordinateTransform', arrow_size: float = 14):
        """
        Draw a directional arrow (isosceles triangle) at a specific position.

        The arrow is an isosceles triangle - longer and narrower than equilateral
        to make direction more obvious.

        Args:
            position: (x, y) position of the arrow in world coordinates
            angle: Angle in radians for arrow direction
            color: RGB tuple for arrow color
            transform: Coordinate transform for world-to-screen conversion
            arrow_size: Length of the arrow in world units
        """
        x, y = position

        # Arrow tip is at the position
        tip_x, tip_y = x, y

        # Isosceles triangle: narrower angle (pi/10 = 18 degrees instead of pi/6 = 30 degrees)
        # This makes the arrow longer and more pointy
        half_angle = math.pi / 10  # 18 degrees for a narrower, more obvious arrow
        back_angle1 = angle + math.pi - half_angle
        back_angle2 = angle + math.pi + half_angle

        back_x1 = tip_x + arrow_size * math.cos(back_angle1)
        back_y1 = tip_y + arrow_size * math.sin(back_angle1)

        back_x2 = tip_x + arrow_size * math.cos(back_angle2)
        back_y2 = tip_y + arrow_size * math.sin(back_angle2)

        # Convert to screen coordinates
        screen_tip = transform.world_to_screen(tip_x, tip_y)
        screen_back1 = transform.world_to_screen(back_x1, back_y1)
        screen_back2 = transform.world_to_screen(back_x2, back_y2)

        # Draw filled triangle
        arcade.draw_triangle_filled(
            screen_tip[0], screen_tip[1],
            screen_back1[0], screen_back1[1],
            screen_back2[0], screen_back2[1],
            color
        )

        # Draw outline for better visibility
        arcade.draw_triangle_outline(
            screen_tip[0], screen_tip[1],
            screen_back1[0], screen_back1[1],
            screen_back2[0], screen_back2[1],
            (0, 0, 0),  # Black outline
            2
        )

    def draw(self, transform: 'CoordinateTransform'):
        """
        Draw the edge on screen with directional arrow.

        Args:
            transform: Coordinate transform for world-to-screen conversion
        """
        points = self.get_points()
        if len(points) < 2:
            return

        color = self.get_color()
        line_width = 3

        # Highlight selected edge with cyan color and thicker line
        if self.is_selected:
            highlight_color = (0, 200, 255)  # Cyan highlight
            line_width = 5

            # Draw highlight outline behind the edge
            for i in range(len(points) - 1):
                p1_world = points[i]
                p2_world = points[i + 1]
                p1_screen = transform.world_to_screen(p1_world[0], p1_world[1])
                p2_screen = transform.world_to_screen(p2_world[0], p2_world[1])
                arcade.draw_line(p1_screen[0], p1_screen[1], p2_screen[0], p2_screen[1],
                                highlight_color, line_width + 4)

        # Draw line segments (converting world to screen coordinates)
        for i in range(len(points) - 1):
            p1_world = points[i]
            p2_world = points[i + 1]

            p1_screen = transform.world_to_screen(p1_world[0], p1_world[1])
            p2_screen = transform.world_to_screen(p2_world[0], p2_world[1])

            arcade.draw_line(p1_screen[0], p1_screen[1], p2_screen[0], p2_screen[1], color, line_width)

        # Draw directional arrow at path midpoint
        if len(points) >= 2:
            arrow_pos, arrow_angle = self.get_arrow_position()
            arrow_color = (0, 200, 255) if self.is_selected else color
            self._draw_arrow(arrow_pos, arrow_angle, arrow_color, transform, arrow_size=self._arrow_size)
