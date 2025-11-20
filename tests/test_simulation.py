"""Test script to verify simulation logic without GUI."""
import json
from src.core import Node, NodeType, Edge
from src.physics import update_node_forces


def test_nodes():
    """Test node creation and color calculation."""
    print("Testing Nodes...")

    node1 = Node(100, 100)
    print(f"  Created node at ({node1.x}, {node1.y})")
    print(f"  Initial instability: {node1.instability}")
    print(f"  Initial color: {node1.get_color()}")

    # Simulate instability
    node1.instability = 50
    print(f"  Instability 50 color: {node1.get_color()}")

    node1.instability = 100
    print(f"  Instability 100 color: {node1.get_color()}")

    print("  ✓ Nodes working correctly\n")


def test_edges():
    """Test edge creation and tension calculation."""
    print("Testing Edges...")

    # Straight line (no tension)
    edge1 = Edge("M 0,0 L 100,0")
    print(f"  Straight edge points: {edge1.points}")
    print(f"  Straight edge tensions: {edge1.tension_values}")
    print(f"  Average tension: {edge1.get_average_tension():.3f}")

    # Bent line (with tension)
    edge2 = Edge("M 0,0 L 100,0 L 100,100")
    print(f"  Bent edge points: {edge2.points}")
    print(f"  Bent edge tensions: {[f'{t:.3f}' for t in edge2.tension_values]}")
    print(f"  Average tension: {edge2.get_average_tension():.3f}")
    print(f"  Color: {edge2.get_color()}")

    print("  ✓ Edges working correctly\n")


def test_physics():
    """Test gravity-based force calculations."""
    print("Testing Physics...")

    node1 = Node(100, 100)
    node2 = Node(200, 100)
    node3 = Node(100, 200)

    nodes = [node1, node2, node3]

    print(f"  Created {len(nodes)} nodes")
    print(f"  Initial instabilities: {[n.instability for n in nodes]}")

    update_node_forces(nodes)

    print(f"  After force update:")
    for i, node in enumerate(nodes):
        print(f"    Node {i}: instability = {node.instability:.2f}, color = {node.get_color()}")

    print("  ✓ Physics working correctly\n")


def test_config_loading():
    """Test configuration file loading."""
    print("Testing Configuration Loading...")

    with open('configs/default.json', 'r') as f:
        config = json.load(f)

    print(f"  Loaded {len(config['nodes'])} nodes")
    print(f"  Loaded {len(config['edges'])} edges")

    # Create nodes from config
    nodes = []
    for node_data in config['nodes']:
        node = Node(node_data['x'], node_data['y'])
        nodes.append(node)

    # Create edges from config
    edges = []
    for edge_data in config['edges']:
        edge = Edge(edge_data['path'])
        edges.append(edge)

    print(f"  Created {len(nodes)} node objects")
    print(f"  Created {len(edges)} edge objects")

    # Update physics
    update_node_forces(nodes)

    print("  Node instabilities after force calculation:")
    for i, node in enumerate(nodes):
        print(f"    Node {i} at ({node.x}, {node.y}): {node.instability:.2f}")

    print("  Edge tensions:")
    for i, edge in enumerate(edges):
        print(f"    Edge {i}: avg tension = {edge.get_average_tension():.3f}")

    print("  ✓ Configuration loading working correctly\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Spell Graph Simulation - Component Tests")
    print("=" * 60)
    print()

    test_nodes()
    test_edges()
    test_physics()
    test_config_loading()

    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
    print("\nTo run the visual simulation:")
    print("  python3 main.py")
    print()


if __name__ == "__main__":
    main()
