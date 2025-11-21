"""Info window for displaying entity information on hover."""
import arcade
from typing import Dict, Any, Optional, List


class InfoWindow:
    """
    Displays information about entities in a hover popup window.

    Uses arcade.Text objects for better performance instead of draw_text.

    Attributes:
        position: (x, y) position of the window in screen coordinates
        info: Dictionary of information to display
        padding: Padding around text
        line_height: Height of each line of text
        font_size: Font size for text
        background_color: Background color of the window
        text_color: Text color
    """

    def __init__(self):
        """Initialize the info window."""
        self.position: Optional[tuple] = None
        self.info: Optional[Dict[str, Any]] = None
        self.padding = 10
        self.line_height = 18
        self.font_size = 11
        self.background_color = (245, 245, 245, 230)  # Light gray with transparency
        self.text_color = arcade.color.BLACK
        self.border_color = arcade.color.BLACK

        # Cached Text objects for performance
        self._text_objects: List[arcade.Text] = []
        self._cached_info: Optional[Dict[str, Any]] = None
        self._cached_position: Optional[tuple] = None

    def set_info(self, info: Dict[str, Any], mouse_x: float, mouse_y: float):
        """
        Set the information to display and position.

        Args:
            info: Dictionary of key-value pairs to display
            mouse_x: Mouse X position in screen coordinates
            mouse_y: Mouse Y position in screen coordinates
        """
        self.info = info
        # Offset the window slightly from the mouse cursor
        self.position = (mouse_x + 15, mouse_y + 15)

    def clear(self):
        """Clear the info window."""
        self.info = None
        self.position = None

    def is_visible(self) -> bool:
        """Check if the window should be visible."""
        return self.info is not None and self.position is not None

    def _update_text_objects(self):
        """Update cached Text objects if info or position changed."""
        if self.info == self._cached_info and self.position == self._cached_position:
            return

        self._cached_info = dict(self.info) if self.info else None
        self._cached_position = self.position

        # Clear old text objects
        self._text_objects.clear()

        if not self.info or not self.position:
            return

        x, y = self.position
        current_y = y - self.padding - self.font_size

        for key, value in self.info.items():
            text = f"{key}: {value}"
            text_obj = arcade.Text(
                text,
                x + self.padding,
                current_y,
                self.text_color,
                self.font_size,
                font_name="Arial"
            )
            self._text_objects.append(text_obj)
            current_y -= self.line_height

    def draw(self):
        """Draw the info window if visible."""
        if not self.is_visible():
            return

        # Update text objects if needed
        self._update_text_objects()

        # Calculate window dimensions
        max_key_length = max(len(str(key)) for key in self.info.keys())
        max_value_length = max(len(str(value)) for value in self.info.values())

        # Estimate window width based on text
        char_width = 7  # Approximate character width
        window_width = (max_key_length + max_value_length + 2) * char_width + self.padding * 2
        window_height = len(self.info) * self.line_height + self.padding * 2

        x, y = self.position

        # Draw background rectangle (Arcade 3.0 API uses left, right, bottom, top)
        arcade.draw_lrbt_rectangle_filled(
            x,
            x + window_width,
            y - window_height,
            y,
            self.background_color
        )

        # Draw border
        arcade.draw_lrbt_rectangle_outline(
            x,
            x + window_width,
            y - window_height,
            y,
            self.border_color,
            2
        )

        # Draw cached text objects
        for text_obj in self._text_objects:
            text_obj.draw()
