from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from PIL.Image import Image

class RenderedImageCache:
    def __init__(self, css_content: str):
        self._css_content = css_content
        self._cache = {}

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
        used_css_classes = [c for c in css_classes.split() if c in self._css_content]
        return f"word:{text}|index:{index}|css_classes:{','.join(used_css_classes)}"
