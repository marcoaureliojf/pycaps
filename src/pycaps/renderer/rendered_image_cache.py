from typing import Optional, List
from PIL.Image import Image

class RenderedImageCache:
    def __init__(self, css_content: str):
        self._css_content = css_content
        self._cache = {}

    def has(self, text: str, css_classes: List[str]) -> bool:
        key = self.__build_key(text, css_classes)
        return key in self._cache

    def get(self, text: str, css_classes: List[str]) -> Optional[Image]:
        if not self.has(text, css_classes):
            raise ValueError(f"No cached image found for text: {text} and CSS classes: {css_classes}")
        
        # Important, keep in mind that None is a valid cached value: it means that the image can't be generated (element probably hidden)
        key = self.__build_key(text, css_classes)
        return self._cache.get(key)

    def set(self, text: str, css_classes: List[str], image: Optional[Image]) -> None:
        key = self.__build_key(text, css_classes)
        self._cache[key] = image

    def __build_key(self, text: str, css_classes: List[str]) -> str:
        used_css_classes = [c for c in css_classes if c in self._css_content]
        return f"word:{text}|css_classes:{','.join(used_css_classes)}"
