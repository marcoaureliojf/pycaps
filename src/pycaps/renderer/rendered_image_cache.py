from typing import Optional, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from PIL.Image import Image

class RenderedImageCache:
    def __init__(self, css_content: str):
        self._css_content = css_content
        self._cache = {}
        self._can_ignore_word_indexes = not self.__css_uses_position_dependent_backgrounds(css_content)

    def has(self, index: int, text: str, css_classes: str) -> bool:
        key = self.__build_key(index, text, css_classes)
        return key in self._cache

    def get(self, index: int, text: str, css_classes: str) -> Optional['Image']:
        if not self.has(index, text, css_classes):
            raise ValueError(f"No cached image found for text: {text} and CSS classes: {css_classes}")
        
        # Important, keep in mind that None is a valid cached value: it means that the image can't be generated (element probably hidden)
        key = self.__build_key(index, text, css_classes)
        return self._cache.get(key)

    def set(self, index: int, text: str, css_classes: str, image: Optional['Image']) -> None:
        key = self.__build_key(index, text, css_classes)
        self._cache[key] = image

    def __build_key(self, index: int, text: str, css_classes: str) -> str:
        if self._can_ignore_word_indexes:
            index = -1
        used_css_classes = [c for c in css_classes.split() if c in self._css_content]
        return f"word:{text}|index:{index}|css_classes:{','.join(used_css_classes)}"

    def __css_uses_position_dependent_backgrounds(self, css_content: str) -> bool:
        css_str = css_content.lower()

        # Removing comments 
        css_str = re.sub(r'/\*.*?\*/', '', css_str, flags=re.DOTALL)

        # We search for patterns that creates a dependency for the word position
        # (if the line has a gradient, the same word in different positions are different images)
        # This is a naive approach, since we are not checking it for line classes
        # We could improve it, doing a calculation using JS in open_line()
        # However, this approach should be good enough for now.
        patterns = [
            r'linear-gradient\s*\(',
            r'radial-gradient\s*\(',
            r'conic-gradient\s*\(',
            r'repeating-(linear|radial|conic)-gradient\s*\(',
            r'background(-image)?\s*:\s*url\s*\(',
        ]

        return any(re.search(pattern, css_str) for pattern in patterns)