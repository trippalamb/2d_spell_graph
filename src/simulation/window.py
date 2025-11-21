"""Main simulation window for the spell graph."""
import arcade
import arcade.gui
from typing import List, Optional, Tuple
import json
import os
import re
import time

from src.core import Node, NodeType, Edge, EdgeDirection, SpellGraphEntity
from src.physics import update_node_forces
from src.simulation.cursor import CursorManager
from src.simulation.transform import CoordinateTransform
from src.simulation.info_window import InfoWindow


def parse_svg_path(path: str) -> List[Tuple[float, float]]:
    """
    Parse SVG path string into list of coordinate points.

    Args:
        path: SVG path string (e.g., "M 200,200 L 400,300 L 400,500")

    Returns:
        List of (x, y) tuples
    """
    points = []
    commands = re.findall(r'([ML])\s*([\d.]+)[,\s]+([\d.]+)', path)

    for cmd, x, y in commands:
        points.append((float(x), float(y)))

    return points


def find_node_by_position(nodes: List[Node], x: float, y: float, tolerance: float = 1.0) -> Optional[Node]:
    """
    Find a node at a specific position.

    Args:
        nodes: List of nodes to search
        x: X coordinate
        y: Y coordinate
        tolerance: Maximum distance to consider a match

    Returns:
        Node at that position, or None if not found
    """
    for node in nodes:
        dx = node.x - x
        dy = node.y - y
        distance = (dx * dx + dy * dy) ** 0.5
        if distance <= tolerance:
            return node
    return None


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

        # Panning state
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_start_offset_x = 0
        self.pan_start_offset_y = 0

        # Node dragging state
        self.dragged_node: Optional[Node] = None
        self.drag_offset_x = 0
        self.drag_offset_y = 0

        # Edge selection and bezier handle dragging
        self.selected_edge: Optional[Edge] = None
        self.dragged_handle: Optional[int] = None  # 1 or 2 for handle number
        self.last_click_time = 0.0
        self.double_click_threshold = 0.3  # seconds

        # Info window for entity hover
        self.info_window = InfoWindow()

        # Time scale for simulation speed (0.1x to 10x)
        self.time_scale = 1.0

        # UI Manager
        self.ui_manager = arcade.gui.UIManager()
        self.ui_manager.enable()

        # Create UI buttons
        self._setup_ui()

    def _select_edge(self, edge: Edge):
        """
        Select an edge and update is_selected state.

        Args:
            edge: The edge to select
        """
        # Deselect previous edge if any
        if self.selected_edge is not None:
            self.selected_edge.is_selected = False

        # Select new edge
        self.selected_edge = edge
        if edge is not None:
            edge.is_selected = True

    def _deselect_edge(self):
        """Deselect the currently selected edge."""
        if self.selected_edge is not None:
            self.selected_edge.is_selected = False
            self.selected_edge = None

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

        # Repath Edges button
        repath_button = arcade.gui.UIFlatButton(
            text="Repath Edges",
            width=120
        )
        repath_button.on_click = self._on_repath_edges
        v_box.add(repath_button)

        # Save button
        save_button = arcade.gui.UIFlatButton(
            text="Save Spell",
            width=120
        )
        save_button.on_click = self._on_save
        v_box.add(save_button)

        # Load button
        load_button = arcade.gui.UIFlatButton(
            text="Load Spell",
            width=120
        )
        load_button.on_click = self._on_load
        v_box.add(load_button)

        # Time scale label
        self.time_scale_label = arcade.gui.UILabel(
            text="Speed: 1.0x",
            width=120,
            text_color=(0, 0, 0)
        )
        v_box.add(self.time_scale_label)

        # Time scale slider (0.1x to 10x, logarithmic feel)
        # Slider value 0-100 maps to 0.1x-10x
        self.time_scale_slider = arcade.gui.UISlider(
            value=50,  # Default to 1.0x (middle)
            min_value=0,
            max_value=100,
            width=120
        )
        self.time_scale_slider.on_change = self._on_time_scale_change
        v_box.add(self.time_scale_slider)

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

    def _on_time_scale_change(self, event):
        """Handle time scale slider change."""
        # Map slider value (0-100) to time scale (0.1x to 10x) using logarithmic scale
        # At 0: 0.1x, at 50: 1.0x, at 100: 10x
        slider_value = event.new_value
        if slider_value <= 50:
            # 0-50 maps to 0.1-1.0 (logarithmic)
            t = slider_value / 50.0
            self.time_scale = 0.1 * (10 ** t)  # 0.1 to 1.0
        else:
            # 50-100 maps to 1.0-10.0 (logarithmic)
            t = (slider_value - 50) / 50.0
            self.time_scale = 1.0 * (10 ** t)  # 1.0 to 10.0

        # Update label
        self.time_scale_label.text = f"Speed: {self.time_scale:.1f}x"

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

    def _on_repath_edges(self, event):
        """Handle repath edges button click."""
        self.repath_all_edges()
        # Rebuild edge graph after repath
        self.cursor_manager.build_edge_graph(self.nodes, self.edges)

    def _on_save(self, event):
        """Handle save button click."""
        self.save_spell()

    def _on_load(self, event):
        """Handle load button click."""
        self.load_spell()

    def repath_all_edges(self, num_segments: int = 10):
        """
        Repath all edges by resetting bezier handles to straight lines.

        Args:
            num_segments: Number of segments to render bezier curve (default 10)
        """
        for edge in self.edges:
            # Reset bezier handles to straight-line positions
            edge.reset_bezier_handles()
            # Update segment count if needed
            edge.num_segments = num_segments

    def save_spell(self):
        """Save current spell configuration to a file."""
        root = None
        try:
            # Use tkinter for file dialog
            import tkinter as tk
            from tkinter import filedialog

            # Create a temporary root window (hidden)
            root = tk.Tk()
            root.withdraw()
            root.update_idletasks()
            root.attributes('-topmost', True)
            root.focus_force()

            # Show save dialog
            filename = filedialog.asksaveasfilename(
                parent=root,
                title="Save Spell",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir="configs"
            )

            # Proper cleanup of tkinter
            root.update()
            root.quit()
            root.destroy()
            root = None

            if filename:
                # Build configuration dictionary
                config = {
                    "window": {
                        "width": self.width,
                        "height": self.height,
                        "world_scale": self.transform.world_scale
                    },
                    "nodes": [],
                    "edges": []
                }

                # Save nodes
                for node in self.nodes:
                    config["nodes"].append({
                        "x": node.x,
                        "y": node.y,
                        "type": node.node_type.value
                    })

                # Save edges as SVG paths
                for edge in self.edges:
                    # Build SVG path string
                    points = edge.get_points()
                    if len(points) < 2:
                        continue

                    # Start with M (move to)
                    path = f"M {points[0][0]},{points[0][1]}"

                    # Add L (line to) for each subsequent point
                    for point in points[1:]:
                        path += f" L {point[0]},{point[1]}"

                    config["edges"].append({"path": path})

                # Write to file
                with open(filename, 'w') as f:
                    json.dump(config, f, indent=2)

                print(f"Spell saved to {filename}")

        except Exception as e:
            print(f"Error saving spell: {e}")
            # Ensure cleanup even on error
            if root is not None:
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass

    def load_spell(self):
        """Load a spell configuration from a file."""
        root = None
        try:
            # Use tkinter for file dialog
            import tkinter as tk
            from tkinter import filedialog

            # Create a temporary root window (hidden)
            root = tk.Tk()
            root.withdraw()
            root.update_idletasks()
            root.attributes('-topmost', True)
            root.focus_force()

            # Show open dialog
            filename = filedialog.askopenfilename(
                parent=root,
                title="Load Spell",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialdir="configs"
            )

            # Proper cleanup of tkinter
            root.update()
            root.quit()
            root.destroy()
            root = None

            if filename:
                # Load configuration
                self.load_config(filename)
                # Rebuild edge graph and restart cursors
                self.cursor_manager.build_edge_graph(self.nodes, self.edges)
                self.cursor_manager.restart(self.nodes)
                print(f"Spell loaded from {filename}")

        except Exception as e:
            print(f"Error loading spell: {e}")
            # Ensure cleanup even on error
            if root is not None:
                try:
                    root.quit()
                    root.destroy()
                except:
                    pass

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

        # Load edges and build node-edge relationships
        self.edges = []
        for edge_data in config.get('edges', []):
            path = edge_data['path']
            points = parse_svg_path(path)

            if len(points) < 2:
                continue  # Skip invalid edges

            # Find start and end nodes
            start_x, start_y = points[0]
            end_x, end_y = points[-1]

            start_node = find_node_by_position(self.nodes, start_x, start_y)
            end_node = find_node_by_position(self.nodes, end_x, end_y)

            if start_node is None or end_node is None:
                print(f"Warning: Could not find nodes for edge {path}")
                continue

            # Extract control points (intermediate waypoints)
            control_points = points[1:-1]  # Everything between start and end

            # Create edge with node references
            edge = Edge(start_node, end_node, control_points)
            self.edges.append(edge)

            # Register edge with nodes
            start_node.add_edge(edge, EdgeDirection.OUTGOING)
            end_node.add_edge(edge, EdgeDirection.INCOMING)

    def on_update(self, delta_time: float):
        """
        Update physics and simulation state.

        Args:
            delta_time: Time since last update in seconds
        """
        # Apply time scale to simulation
        scaled_delta = delta_time * self.time_scale

        # Update forces and instability for all nodes
        update_node_forces(self.nodes)

        # Update cursor traversal with scaled time
        self.cursor_manager.update(scaled_delta, self.nodes, self.edges)

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

        # Handle panning when right mouse button is held
        if self.is_panning:
            # Update the transform offset based on mouse movement
            self.transform.offset_x = self.pan_start_offset_x + (x - self.pan_start_x)
            self.transform.offset_y = self.pan_start_offset_y + (y - self.pan_start_y)

        # Handle node dragging when left mouse button is held
        if self.dragged_node is not None:
            # Convert screen position to world position
            world_x, world_y = self.transform.screen_to_world(x, y)
            # Update node position with drag offset
            self.dragged_node.x = world_x - self.drag_offset_x
            self.dragged_node.y = world_y - self.drag_offset_y

        # Handle bezier handle dragging
        if self.selected_edge is not None and self.dragged_handle is not None:
            world_x, world_y = self.transform.screen_to_world(x, y)
            self.selected_edge.set_handle_position(self.dragged_handle, world_x, world_y)

    def on_mouse_press(self, x: float, y: float, button: int, modifiers: int):
        """
        Handle mouse button press.

        Args:
            x: Mouse X position
            y: Mouse Y position
            button: Mouse button that was pressed
            modifiers: Keyboard modifiers
        """
        current_time = time.time()
        world_x, world_y = self.transform.screen_to_world(x, y)

        # Start node dragging on left mouse button
        if button == arcade.MOUSE_BUTTON_LEFT:
            # Priority 1: Check if clicking on a bezier handle (when edge is selected)
            if self.selected_edge is not None:
                handle_num = self.selected_edge.get_handle_at_point(world_x, world_y)
                if handle_num is not None:
                    # Check for double-click to reset handle
                    if current_time - self.last_click_time < self.double_click_threshold:
                        self.selected_edge.reset_handle(handle_num)
                    else:
                        # Start dragging the handle
                        self.dragged_handle = handle_num
                    self.last_click_time = current_time
                    return

            # Priority 2: Check if clicking on selected edge's arrow (to reverse direction)
            # Arrows are only clickable when their edge is selected
            if self.selected_edge is not None:
                if self.selected_edge.arrow_contains_point(world_x, world_y):
                    # Reverse the edge direction
                    self.selected_edge.reverse_direction()
                    # Rebuild edge graph after direction change
                    self.cursor_manager.build_edge_graph(self.nodes, self.edges)
                    self.last_click_time = current_time
                    return

            # Priority 3: Check if clicking on a node
            for node in self.nodes:
                if node.contains_point(world_x, world_y, self.transform):
                    self.dragged_node = node
                    # Store offset from node center to click position
                    self.drag_offset_x = world_x - node.x
                    self.drag_offset_y = world_y - node.y
                    # Deselect edge when dragging node
                    self._deselect_edge()
                    self.last_click_time = current_time
                    return

            # Priority 4: Check if clicking on an edge to select it
            for edge in self.edges:
                if edge.contains_point(world_x, world_y, self.transform):
                    self._select_edge(edge)
                    self.last_click_time = current_time
                    return

            # Clicked on empty space - deselect edge
            self._deselect_edge()
            self.last_click_time = current_time

        # Start panning on right mouse button
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.is_panning = True
            self.pan_start_x = x
            self.pan_start_y = y
            self.pan_start_offset_x = self.transform.offset_x
            self.pan_start_offset_y = self.transform.offset_y

    def on_mouse_release(self, x: float, y: float, button: int, modifiers: int):
        """
        Handle mouse button release.

        Args:
            x: Mouse X position
            y: Mouse Y position
            button: Mouse button that was released
            modifiers: Keyboard modifiers
        """
        # Stop node dragging on left mouse button release
        if button == arcade.MOUSE_BUTTON_LEFT:
            self.dragged_node = None
            self.dragged_handle = None

        # Stop panning on right mouse button release
        elif button == arcade.MOUSE_BUTTON_RIGHT:
            self.is_panning = False

    def on_mouse_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float):
        """
        Handle mouse scroll (zoom).

        Args:
            x: Mouse X position
            y: Mouse Y position
            scroll_x: Horizontal scroll amount
            scroll_y: Vertical scroll amount (positive = zoom in)
        """
        # Get world position of mouse before zoom
        world_x_before, world_y_before = self.transform.screen_to_world(x, y)

        # Update zoom level
        zoom_factor = 1.1
        if scroll_y > 0:
            # Zoom in
            self.transform.world_scale *= zoom_factor
        elif scroll_y < 0:
            # Zoom out
            self.transform.world_scale /= zoom_factor

        # Get world position of mouse after zoom (without offset adjustment)
        # We want: world_x_before = (x - new_offset_x) / new_scale
        # Solving: new_offset_x = x - world_x_before * new_scale
        self.transform.offset_x = x - world_x_before * self.transform.world_scale
        self.transform.offset_y = y - world_y_before * self.transform.world_scale

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

        # Draw bezier handles for selected edge
        if self.selected_edge is not None:
            self.selected_edge.draw_handles(self.transform)

        # Draw nodes
        for node in self.nodes:
            node.draw(self.transform)

        # Draw cursors
        self.cursor_manager.draw(self.transform)

        # Draw UI
        self.ui_manager.draw()

        # Draw info window (on top of everything)
        self.info_window.draw()
