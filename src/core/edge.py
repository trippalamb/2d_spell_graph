"""Edge class for the spell graph simulation."""
import math
import re
import arcade
from typing import List, Tuple


class Edge:
    """
    Represents an edge in the spatial physics graph.

    Edges are defined by SVG-like path strings (D3 format) and have
    tension values based on the angles of their bending.

    Attributes:
        path: SVG path string (e.g., "M 0,0 L 100,100 L 200,50")
        points: List of (x, y) coordinate tuples parsed from path
        tension_values: List of tension values at each bend point
    """

    def __init__(self, path: str):
        """
        Initialize an edge from a path string.

        Args:
            path: SVG path string (D3 format)
        """
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

    def draw(self):
        """Draw the edge on screen."""
        if len(self.points) < 2:
            return

        color = self.get_color()

        # Draw line segments
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            arcade.draw_line(p1[0], p1[1], p2[0], p2[1], color, 3)
