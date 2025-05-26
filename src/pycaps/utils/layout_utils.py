from ..layout.models import LineClipData, ElementLayout, WordClipData
from typing import List

class LayoutUtils:
    @staticmethod
    def calculate_lines_layout(lines: List[LineClipData]) -> ElementLayout:
        total_height = sum(line.layout.height for line in lines)
        max_width = max(line.layout.width for line in lines)
        base_y = min(line.layout.y for line in lines)
        base_x = min(line.layout.x for line in lines)
        return ElementLayout(x=base_x, y=base_y, width=max_width, height=total_height)
    