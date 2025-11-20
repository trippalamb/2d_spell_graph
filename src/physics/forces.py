"""Physics calculations for the spell graph simulation."""
import math
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.node import Node

# Gravitational constant (scaled for simulation)
G = 1000.0


def calculate_gravitational_force(node1: 'Node', node2: 'Node') -> float:
    """
    Calculate gravitational force between two nodes.

    Uses F = G * m1 * m2 / r^2
    where m1 and m2 are both 1.0 for simplicity.

    Args:
        node1: First node
        node2: Second node

    Returns:
        Force magnitude
    """
    # Calculate distance
    dx = node2.x - node1.x
    dy = node2.y - node1.y
    distance = math.sqrt(dx * dx + dy * dy)

    # Prevent division by zero
    if distance < 1.0:
        distance = 1.0

    # Calculate force (using mass = 1.0 for all nodes)
    force = G / (distance * distance)

    return force


def update_node_forces(nodes: List['Node']):
    """
    Update force and instability values for all nodes.

    Each node accumulates instability from forces exerted by all other nodes.

    Args:
        nodes: List of all nodes in the graph
    """
    # Reset instability for all nodes
    for node in nodes:
        node.instability = 0.0

    # Calculate forces between all pairs
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if i != j:
                force = calculate_gravitational_force(node1, node2)
                # Add force to node1's instability
                node1.instability += force
