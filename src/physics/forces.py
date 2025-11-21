"""Physics calculations for the spell graph simulation."""
import math
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.node import Node
    from src.core.edge import Edge

# Charge interaction constant (scaled for simulation)
# Increased to make color changes visible at typical screen distances (100-1000px)
CHARGE_CONSTANT = 500000.0

# Repulsion constant for simulation mode (like charges repel)
REPULSION_CONSTANT = 5000.0

# Edge spring constant - how strongly edges pull nodes together
EDGE_SPRING_CONSTANT = 50.0


def get_charge_product(node1: 'Node', node2: 'Node', charge_type: str = "alpha") -> float:
    """
    Get the product of charge values for a specific charge type.

    Args:
        node1: First node
        node2: Second node
        charge_type: The charge type to use (e.g., "alpha", "beta")

    Returns:
        Product of charge values, or 0 if either node lacks this charge type
    """
    charge1 = node1.charges.get(charge_type, 0.0)
    charge2 = node2.charges.get(charge_type, 0.0)
    return charge1 * charge2


def calculate_charge_force(node1: 'Node', node2: 'Node') -> float:
    """
    Calculate charge-based force between two nodes.

    Uses F = k * c1 * c2 / r^2
    where c1 and c2 are the charge values of the nodes.
    Currently sums forces from all matching charge types.

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

    # Sum forces from all charge types that both nodes share
    total_force = 0.0
    all_charge_types = set(node1.charges.keys()) | set(node2.charges.keys())

    for charge_type in all_charge_types:
        charge_product = get_charge_product(node1, node2, charge_type)
        if charge_product != 0:
            force = CHARGE_CONSTANT * charge_product / (distance * distance)
            total_force += force

    return total_force


def calculate_repulsion_vector(node1: 'Node', node2: 'Node') -> Tuple[float, float]:
    """
    Calculate repulsion force vector from node2 pushing on node1.

    Uses F = k * c1 * c2 / r^2, direction away from node2.
    Like charges repel each other.

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

    # Sum repulsion from all matching charge types
    total_force = 0.0
    all_charge_types = set(node1.charges.keys()) | set(node2.charges.keys())

    for charge_type in all_charge_types:
        charge_product = get_charge_product(node1, node2, charge_type)
        if charge_product != 0:
            force = REPULSION_CONSTANT * charge_product / (distance * distance)
            total_force += force

    # Normalize direction and apply force
    fx = (dx / distance) * total_force
    fy = (dy / distance) * total_force

    return (fx, fy)


def calculate_edge_spring_force(edge: 'Edge') -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """
    Calculate spring force from an edge pulling its connected nodes together.

    Uses Hooke's law: F = -k * (current_length - rest_length)
    The force pulls nodes toward each other when the edge is stretched.

    Args:
        edge: The edge connecting two nodes

    Returns:
        Tuple of ((fx1, fy1), (fx2, fy2)) force vectors for start and end nodes
    """
    if edge.is_broken:
        return ((0.0, 0.0), (0.0, 0.0))

    start_node = edge.start_node
    end_node = edge.end_node

    # Calculate current distance between nodes
    dx = end_node.x - start_node.x
    dy = end_node.y - start_node.y
    current_length = math.sqrt(dx * dx + dy * dy)

    # Use rest_length if physics is initialized, otherwise use current length as rest
    rest_length = edge.rest_length if edge.rest_length > 0 else current_length

    # Prevent division by zero
    if current_length < 1.0:
        current_length = 1.0

    # Calculate displacement from rest length
    displacement = current_length - rest_length

    # Spring force magnitude (positive when stretched, pulls nodes together)
    force_magnitude = EDGE_SPRING_CONSTANT * displacement

    # Normalize direction vector
    nx = dx / current_length
    ny = dy / current_length

    # Force on start node (toward end node when stretched)
    fx_start = nx * force_magnitude
    fy_start = ny * force_magnitude

    # Force on end node (toward start node when stretched, opposite direction)
    fx_end = -nx * force_magnitude
    fy_end = -ny * force_magnitude

    return ((fx_start, fy_start), (fx_end, fy_end))


def update_node_forces(nodes: List['Node']):
    """
    Update instability values for all nodes based on charge interactions.

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
                force = calculate_charge_force(node1, node2)
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


def apply_edge_spring_forces(nodes: List['Node'], edges: List['Edge'], dt: float) -> List[Tuple[float, float]]:
    """
    Calculate position deltas from edge spring forces pulling connected nodes together.

    Args:
        nodes: List of all nodes in the graph
        edges: List of all edges in the graph
        dt: Delta time in seconds

    Returns:
        List of (dx, dy) position deltas for each node
    """
    # Initialize velocity accumulator for each node
    velocities = {node: (0.0, 0.0) for node in nodes}

    # Calculate spring forces from all edges
    for edge in edges:
        (fx_start, fy_start), (fx_end, fy_end) = calculate_edge_spring_force(edge)

        # Apply to start node
        vx, vy = velocities[edge.start_node]
        velocities[edge.start_node] = (vx + fx_start * dt, vy + fy_start * dt)

        # Apply to end node
        vx, vy = velocities[edge.end_node]
        velocities[edge.end_node] = (vx + fx_end * dt, vy + fy_end * dt)

    # Convert back to list in same order as input nodes
    return [velocities[node] for node in nodes]
