"""Physics calculations for the spell graph simulation."""
import math
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.node import Node

# Gravitational constant (scaled for simulation)
# Increased to make color changes visible at typical screen distances (100-1000px)
G = 500000.0

# Repulsion constant for simulation mode
REPULSION_CONSTANT = 5000.0


def calculate_gravitational_force(node1: 'Node', node2: 'Node') -> float:
    """
    Calculate gravitational force between two nodes.

    Uses F = G * f1 * f2 / r^2
    where f1 and f2 are the inherent force values of the nodes.

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

    # Calculate force using node force values
    force = G * node1.force * node2.force / (distance * distance)

    return force


def calculate_repulsion_vector(node1: 'Node', node2: 'Node') -> Tuple[float, float]:
    """
    Calculate repulsion force vector from node2 pushing on node1.

    Uses F = k * f1 * f2 / r^2, direction away from node2.

    Args:
        node1: Node being pushed
        node2: Node doing the pushing

    Returns:
        Tuple of (fx, fy) force components
    """
    dx = node1.x - node2.x
    dy = node1.y - node2.y
    distance = math.sqrt(dx * dx + dy * dy)

    # Prevent division by zero
    if distance < 1.0:
        distance = 1.0

    # Calculate force magnitude using node force values
    force_magnitude = REPULSION_CONSTANT * node1.force * node2.force / (distance * distance)

    # Normalize direction and apply force
    fx = (dx / distance) * force_magnitude
    fy = (dy / distance) * force_magnitude

    return (fx, fy)


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


def apply_repulsion_forces(nodes: List['Node'], dt: float) -> List[Tuple[float, float]]:
    """
    Calculate position deltas from repulsion forces between all nodes.

    Args:
        nodes: List of all nodes in the graph
        dt: Delta time in seconds

    Returns:
        List of (dx, dy) position deltas for each node
    """
    # Initialize velocity accumulator for each node
    velocities = [(0.0, 0.0) for _ in nodes]

    # Calculate repulsion forces between all pairs
    for i, node1 in enumerate(nodes):
        for j, node2 in enumerate(nodes):
            if i != j:
                fx, fy = calculate_repulsion_vector(node1, node2)
                vx, vy = velocities[i]
                velocities[i] = (vx + fx * dt, vy + fy * dt)

    return velocities
