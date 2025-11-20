"""Main simulation window for the spell graph."""
import arcade
import arcade.gui
from typing import List, Optional
import json
import os

from src.core import Node, NodeType, Edge, SpellGraphEntity
from src.physics import update_node_forces
from src.simulation.cursor import CursorManager
from src.simulation.transform import CoordinateTransform
from src.simulation.info_window import InfoWindow


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

        # Cursor system
        self.cursor_manager = CursorManager()

        # Coordinate transform (world scale defaults to 1.0)
        self.transform = CoordinateTransform(world_scale=1.0)

        # Mouse tracking
        self.mouse_x = 0
        self.mouse_y = 0
        self.hovered_entity: Optional[SpellGraphEntity] = None

        # Info window for entity hover
        self.info_window = InfoWindow()

        # UI Manager
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

        # Create UI buttons
        self._setup_ui()

    def _setup_ui(self):
        """Set up UI buttons for cursor control."""
        # Create a vertical box for buttons
        v_box = arcade.gui.UIBoxLayout(vertical=True, space_between=10)

        # Play/Pause button
        self.play_pause_button = arcade.gui.UIFlatButton(
            text="Play",
            width=120
        )
        self.play_pause_button.on_click = self._on_play_pause
        v_box.add(self.play_pause_button)

        # Restart button
        restart_button = arcade.gui.UIFlatButton(
            text="Restart",
            width=120
        )
        restart_button.on_click = self._on_restart
        v_box.add(restart_button)

        # Zoom in button
        zoom_in_button = arcade.gui.UIFlatButton(
            text="Zoom In (+)",
            width=120
        )
        zoom_in_button.on_click = self._on_zoom_in
        v_box.add(zoom_in_button)

        # Zoom out button
        zoom_out_button = arcade.gui.UIFlatButton(
            text="Zoom Out (-)",
            width=120
        )
        zoom_out_button.on_click = self._on_zoom_out
        v_box.add(zoom_out_button)

        # Create an anchor layout to position the buttons
        anchor = arcade.gui.UIAnchorLayout()
        anchor.add(
            child=v_box,
            anchor_x="left",
            anchor_y="top",
            align_x=20,
            align_y=-20
        )

        self.ui_manager.add(anchor)

    def _on_play_pause(self, event):
        """Handle play/pause button click."""
        self.cursor_manager.toggle_play_pause()
        if self.cursor_manager.is_playing:
            self.play_pause_button.text = "Pause"
        else:
            self.play_pause_button.text = "Play"

    def _on_restart(self, event):
        """Handle restart button click."""
        self.cursor_manager.restart(self.nodes)
        self.play_pause_button.text = "Pause"

    def _on_zoom_in(self, event):
        """Handle zoom in button click."""
        self.transform.world_scale *= 1.2

    def _on_zoom_out(self, event):
        """Handle zoom out button click."""
        self.transform.world_scale /= 1.2

    def setup(self, config_path: str = "configs/default.json"):
        """
        Set up the simulation from a configuration file.

        Args:
            config_path: Path to configuration JSON file
        """
        self.load_config(config_path)

        # Build edge graph and initialize cursor
        self.cursor_manager.build_edge_graph(self.nodes, self.edges)
        self.cursor_manager.restart(self.nodes)

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

            # Load world scale
            world_scale = window_config.get('world_scale', 1.0)
            self.transform = CoordinateTransform(world_scale=world_scale)

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

        # Update cursor traversal
        self.cursor_manager.update(delta_time, self.nodes, self.edges)

        # Update hovered entity
        self._update_hovered_entity()

    def on_mouse_motion(self, x: float, y: float, dx: float, dy: float):
        """
        Handle mouse motion.

        Args:
            x: Mouse X position
            y: Mouse Y position
            dx: Change in X
            dy: Change in Y
        """
        self.mouse_x = x
        self.mouse_y = y

    def _update_hovered_entity(self):
        """Update which entity is currently being hovered."""
        # Convert screen coordinates to world coordinates
        world_x, world_y = self.transform.screen_to_world(self.mouse_x, self.mouse_y)

        # Check all entities in priority order (cursor > node > edge)
        # Check cursors first (highest priority)
        for cursor in self.cursor_manager.cursors:
            if cursor.contains_point(world_x, world_y, self.transform):
                if self.hovered_entity != cursor:
                    self.hovered_entity = cursor
                    self.info_window.set_info(cursor.get_info(), self.mouse_x, self.mouse_y)
                return

        # Check nodes
        for node in self.nodes:
            if node.contains_point(world_x, world_y, self.transform):
                if self.hovered_entity != node:
                    self.hovered_entity = node
                    self.info_window.set_info(node.get_info(), self.mouse_x, self.mouse_y)
                return

        # Check edges (lowest priority)
        for edge in self.edges:
            if edge.contains_point(world_x, world_y, self.transform):
                if self.hovered_entity != edge:
                    self.hovered_entity = edge
                    self.info_window.set_info(edge.get_info(), self.mouse_x, self.mouse_y)
                return

        # No entity hovered
        if self.hovered_entity is not None:
            self.hovered_entity = None
            self.info_window.clear()

    def on_draw(self):
        """Render the graph."""
        # Clear the screen
        self.clear()

        # Draw edges first (so they appear behind nodes)
        for edge in self.edges:
            edge.draw(self.transform)

        # Draw nodes
        for node in self.nodes:
            node.draw(self.transform)

        # Draw cursors
        self.cursor_manager.draw(self.transform)

        # Draw UI
        self.ui_manager.draw()

        # Draw info window (on top of everything)
        self.info_window.draw()
