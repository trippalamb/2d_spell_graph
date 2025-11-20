"""Coordinate transformation utilities for world-to-screen mapping."""
from typing import Tuple


class CoordinateTransform:
    """
    Handles transformation between world coordinates and screen coordinates.

    Attributes:
        world_scale: Scale factor from world units to screen pixels
        offset_x: X offset for camera/viewport (future use)
        offset_y: Y offset for camera/viewport (future use)
    """

    def __init__(self, world_scale: float = 1.0, offset_x: float = 0.0, offset_y: float = 0.0):
        """
        Initialize the coordinate transform.

        Args:
            world_scale: Scale factor (screen pixels per world unit)
            offset_x: X offset in screen pixels
            offset_y: Y offset in screen pixels
        """
        self.world_scale = world_scale
        self.offset_x = offset_x
        self.offset_y = offset_y

    def world_to_screen(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert world coordinates to screen coordinates.

        Args:
            x: World X coordinate
            y: World Y coordinate

        Returns:
            (screen_x, screen_y) tuple
        """
        screen_x = x * self.world_scale + self.offset_x
        screen_y = y * self.world_scale + self.offset_y
        return (screen_x, screen_y)

    def screen_to_world(self, x: float, y: float) -> Tuple[float, float]:
        """
        Convert screen coordinates to world coordinates.

        Args:
            x: Screen X coordinate
            y: Screen Y coordinate

        Returns:
            (world_x, world_y) tuple
        """
        world_x = (x - self.offset_x) / self.world_scale
        world_y = (y - self.offset_y) / self.world_scale
        return (world_x, world_y)

    def scale_distance(self, distance: float) -> float:
        """
        Scale a distance from world units to screen pixels.

        Args:
            distance: Distance in world units

        Returns:
            Distance in screen pixels
        """
        return distance * self.world_scale

    def scale_distance_inverse(self, distance: float) -> float:
        """
        Scale a distance from screen pixels to world units.

        Args:
            distance: Distance in screen pixels

        Returns:
            Distance in world units
        """
        return distance / self.world_scale
