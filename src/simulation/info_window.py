"""Info window for displaying entity information on hover."""
import arcade
from typing import Dict, Any, Optional


class InfoWindow:
    """
    Displays information about entities in a hover popup window.

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

    def draw(self):
        """Draw the info window if visible."""
        if not self.is_visible():
            return

        # Calculate window dimensions
        max_key_length = max(len(str(key)) for key in self.info.keys())
        max_value_length = max(len(str(value)) for value in self.info.values())

        # Estimate window width based on text
        char_width = 7  # Approximate character width
        window_width = (max_key_length + max_value_length + 2) * char_width + self.padding * 2
        window_height = len(self.info) * self.line_height + self.padding * 2

        x, y = self.position

        # Draw background rectangle
        arcade.draw_rectangle_filled(
            x + window_width / 2,
            y - window_height / 2,
            window_width,
            window_height,
            self.background_color
        )

        # Draw border
        arcade.draw_rectangle_outline(
            x + window_width / 2,
            y - window_height / 2,
            window_width,
            window_height,
            self.border_color,
            2
        )

        # Draw text lines
        current_y = y - self.padding - self.font_size
        for key, value in self.info.items():
            text = f"{key}: {value}"
            arcade.draw_text(
                text,
                x + self.padding,
                current_y,
                self.text_color,
                self.font_size,
                font_name="Arial"
            )
            current_y -= self.line_height
