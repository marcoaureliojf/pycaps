from abc import ABC, abstractmethod
from ..models import SubtitleImage

class BaseSubtitleRenderer(ABC):
    @abstractmethod
    def open(self, video_width: int, video_height: int):
        """Initializes and prepares the rendering engine."""
        pass

    @abstractmethod
    def close(self):
        """Cleans up and closes the rendering engine."""
        pass

    @abstractmethod
    def render(self, text: str, style_type: str) -> SubtitleImage:
        """
        Renders a text fragment with a specific style.

        Args:
            text: The text to be rendered.
            style_type: An identifier for the style to apply (e.g., 'normal', 'active').
                        Specific styles are configured in the renderer's implementation.

        Returns a SubtitleImage object containing the rendered image, width, and height.
        """
        pass

    @abstractmethod
    def register_style(self, style_key: str, css_rules: str):
        """
        Registers a custom style for the renderer.

        Args:
            style_key: The key to identify the style.
            css_rules: The CSS rules to apply to the style.
        """ 
        pass
