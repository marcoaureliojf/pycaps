from typing import List
from ..tagger.models import Line, ElementLayout, Size, Position

class LayoutUtils:
    @staticmethod
    def calculate_segment_layout(lines: List[Line]) -> ElementLayout:
        total_height = sum(line.max_layout.size.height for line in lines)
        max_width = max(line.max_layout.size.width for line in lines)
        base_y = min(line.max_layout.position.y for line in lines)
        base_x = min(line.max_layout.position.x for line in lines)
        position = Position(x=base_x, y=base_y)
        size = Size(width=max_width, height=total_height)
        return ElementLayout(position=position, size=size)
    