"""Main simulation window for the spell graph."""
import arcade
from typing import List
import json
import os

from src.core import Node, NodeType, Edge
from src.physics import update_node_forces


class GraphSimulation(arcade.Window):
    """
    Main simulation window.

    Manages the graph of nodes and edges, physics updates, and rendering.
    """

    def __init__(self, width: int = 1280, height: int = 720, title: str = "Spell Graph Simulation"):
        """
        Initialize the simulation window.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            title: Window title
        """
        super().__init__(width, height, title)

        # Set background color to white
        arcade.set_background_color(arcade.color.WHITE)

        self.nodes: List[Node] = []
        self.edges: List[Edge] = []

    def setup(self, config_path: str = "configs/default.json"):
        """
        Set up the simulation from a configuration file.

        Args:
            config_path: Path to configuration JSON file
        """
        self.load_config(config_path)

    def load_config(self, config_path: str):
        """
        Load graph configuration from JSON file.

        Expected format:
        {
            "window": {
                "width": 1920,
                "height": 1080
            },
            "nodes": [
                {"x": 100, "y": 100, "type": "basic"},
                ...
            ],
            "edges": [
                {"path": "M 100,100 L 200,200"},
                ...
            ]
        }

        Args:
            config_path: Path to configuration JSON file
        """
        with open(config_path, 'r') as f:
            config = json.load(f)

        # Load window settings if specified
        if 'window' in config:
            window_config = config['window']
            new_width = window_config.get('width', self.width)
            new_height = window_config.get('height', self.height)
            if new_width != self.width or new_height != self.height:
                self.set_size(new_width, new_height)

        # Load nodes
        self.nodes = []
        for node_data in config.get('nodes', []):
            node_type = NodeType(node_data.get('type', 'basic'))
            node = Node(node_data['x'], node_data['y'], node_type)
            self.nodes.append(node)

        # Load edges
        self.edges = []
        for edge_data in config.get('edges', []):
            edge = Edge(edge_data['path'])
            self.edges.append(edge)

    def on_update(self, delta_time: float):
        """
        Update physics and simulation state.

        Args:
            delta_time: Time since last update in seconds
        """
        # Update forces and instability for all nodes
        update_node_forces(self.nodes)

    def on_draw(self):
        """Render the graph."""
        # Clear the screen
        self.clear()

        # Draw edges first (so they appear behind nodes)
        for edge in self.edges:
            edge.draw()

        # Draw nodes
        for node in self.nodes:
            node.draw()
