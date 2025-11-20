"""Edge class for the spell graph simulation."""
import math
import re
import arcade
from typing import List, Tuple, Dict, Any, TYPE_CHECKING

from src.core.entity import SpellGraphEntity

if TYPE_CHECKING:
    from src.simulation.transform import CoordinateTransform


class Edge(SpellGraphEntity):
    """
    Represents an edge in the spatial physics graph.

    Edges are defined by SVG-like path strings (D3 format) and have
    tension values based on the angles of their bending.

    Attributes:
        path: SVG path string (e.g., "M 0,0 L 100,100 L 200,50")
        points: List of (x, y) coordinate tuples parsed from path
        tension_values: List of tension values at each bend point
    """

    def __init__(self, path: str, entity_id: str = None):
        """
        Initialize an edge from a path string.

        Args:
            path: SVG path string (D3 format)
            entity_id: Unique identifier (auto-generated if None)
        """
        if entity_id is None:
            entity_id = f"edge_{id(self)}"
        super().__init__(entity_id)

        self.path = path
        self.points = self._parse_path(path)
        self.tension_values = self._calculate_tensions()

    def _parse_path(self, path: str) -> List[Tuple[float, float]]:
        """
        Parse SVG path string into list of points.

        Currently supports:
        - M x,y (move to)
        - L x,y (line to)

        Args:
            path: SVG path string

        Returns:
            List of (x, y) tuples
        """
        points = []
        # Simple regex parser for M and L commands
        commands = re.findall(r'([ML])\s*([\d.]+)[,\s]+([\d.]+)', path)

        for cmd, x, y in commands:
            points.append((float(x), float(y)))

        return points

    def _calculate_tensions(self) -> List[float]:
        """
        Calculate tension values based on angles between segments.

        Tension is calculated as the angle difference at each intermediate point.
        Sharper angles create higher tension.

        Returns:
            List of tension values (0.0 to 1.0)
        """
        if len(self.points) < 3:
            return []

        tensions = []

        for i in range(1, len(self.points) - 1):
            p0 = self.points[i - 1]
            p1 = self.points[i]
            p2 = self.points[i + 1]

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
        if not self.tension_values:
            return 0.0
        return sum(self.tension_values) / len(self.tension_values)

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

        return {
            "ID": self.entity_id,
            "Type": "Edge",
            "Path": self.path[:40] + "..." if len(self.path) > 40 else self.path,
            "Points": f"{len(self.points)} points",
            "Length": f"{total_length:.1f}",
            "Avg Tension": f"{avg_tension:.3f}",
            "Max Tension": f"{max(self.tension_values):.3f}" if self.tension_values else "0.000"
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

        # Check distance to each line segment
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]

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
        total_length = 0.0
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
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
        current_distance = 0.0

        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]

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
        if len(self.points) >= 2:
            p1 = self.points[-2]
            p2 = self.points[-1]
            angle = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
            return (p2, angle)

        return (self.points[0], 0.0)

    def _draw_arrow(self, position: Tuple[float, float], angle: float, color: tuple,
                    transform: 'CoordinateTransform', arrow_size: float = 12):
        """
        Draw a directional arrow at a specific position.

        Args:
            position: (x, y) position of the arrow in world coordinates
            angle: Angle in radians for arrow direction
            color: RGB tuple for arrow color
            transform: Coordinate transform for world-to-screen conversion
            arrow_size: Size of the arrow in world units
        """
        x, y = position

        # Arrow tip is at the position
        tip_x, tip_y = x, y

        # Calculate the two back points of the arrow
        back_angle1 = angle + math.pi - math.pi / 6  # 150 degrees
        back_angle2 = angle + math.pi + math.pi / 6  # 210 degrees

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

    def draw(self, transform: 'CoordinateTransform'):
        """
        Draw the edge on screen with directional arrow.

        Args:
            transform: Coordinate transform for world-to-screen conversion
        """
        if len(self.points) < 2:
            return

        color = self.get_color()

        # Draw line segments (converting world to screen coordinates)
        for i in range(len(self.points) - 1):
            p1_world = self.points[i]
            p2_world = self.points[i + 1]

            p1_screen = transform.world_to_screen(p1_world[0], p1_world[1])
            p2_screen = transform.world_to_screen(p2_world[0], p2_world[1])

            arcade.draw_line(p1_screen[0], p1_screen[1], p2_screen[0], p2_screen[1], color, 3)

        # Draw directional arrow at path midpoint (on the containing segment)
        if len(self.points) >= 2:
            # Find which segment contains the 50% distance mark
            total_length = self._get_total_length()
            if total_length > 0:
                target_distance = total_length * 0.5
                current_distance = 0.0
                middle_segment_idx = 0

                # Find the segment that contains the midpoint
                for i in range(len(self.points) - 1):
                    p1 = self.points[i]
                    p2 = self.points[i + 1]
                    dx = p2[0] - p1[0]
                    dy = p2[1] - p1[1]
                    segment_length = math.sqrt(dx * dx + dy * dy)

                    if current_distance + segment_length >= target_distance:
                        middle_segment_idx = i
                        break

                    current_distance += segment_length

                # Get the two points of the segment containing the midpoint
                p1 = self.points[middle_segment_idx]
                p2 = self.points[middle_segment_idx + 1]

                # Position arrow at midpoint of this segment (not at the exact distance point)
                arrow_x = (p1[0] + p2[0]) / 2
                arrow_y = (p1[1] + p2[1]) / 2

                # Calculate direction angle
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                arrow_angle = math.atan2(dy, dx)

                # Small offset perpendicular to the path for visibility
                offset_distance = 12  # world units offset from the path
                offset_angle = arrow_angle + math.pi / 2  # perpendicular to path
                offset_x = arrow_x + offset_distance * math.cos(offset_angle)
                offset_y = arrow_y + offset_distance * math.sin(offset_angle)

                self._draw_arrow((offset_x, offset_y), arrow_angle, color, transform, arrow_size=10)
