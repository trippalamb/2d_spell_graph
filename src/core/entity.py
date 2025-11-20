"""Abstract base class for all spell graph entities."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.simulation.transform import CoordinateTransform


class SpellGraphEntity(ABC):
    """
    Abstract base class for all entities in the spell graph.

    All entities (nodes, edges, cursors) should inherit from this class
    and provide unique IDs and information for display.

    Attributes:
        entity_id: Unique identifier for this entity
    """

    def __init__(self, entity_id: str):
        """
        Initialize the entity.

        Args:
            entity_id: Unique identifier for this entity
        """
        self.entity_id = entity_id

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about this entity for display.

        Returns:
            Dictionary containing entity information (ID + stats)
        """
        pass

    @abstractmethod
    def contains_point(self, x: float, y: float, transform: 'CoordinateTransform') -> bool:
        """
        Check if a point (in world coordinates) is within/near this entity.

        Args:
            x: X coordinate in world space
            y: Y coordinate in world space
            transform: Coordinate transform for distance calculations

        Returns:
            True if point is within this entity's bounds
        """
        pass

    @abstractmethod
    def draw(self, transform: 'CoordinateTransform'):
        """
        Draw the entity on screen.

        Args:
            transform: Coordinate transform for world-to-screen conversion
        """
        pass
