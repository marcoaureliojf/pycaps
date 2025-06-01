from typing import List, Tuple
from ..tagger.models import Line, ElementLayout, Size, Position, WordClip
from ..element import ElementType

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
    
    @staticmethod
    def get_clip_container_center(clip: WordClip, target_container: ElementType) -> Tuple[float, float]:
        '''
        Get the center of the container (line, segment, word) of the clip
        Important: keep in mind it returns float values.
        If you need using it for final position or size, you should use int() (we are working with pixels)
        '''
        if target_container == ElementType.LINE:
            line = clip.get_line()
            return (
                line.max_layout.position.x + line.max_layout.size.width / 2,
                line.max_layout.position.y + line.max_layout.size.height / 2
            )
        
        if target_container == ElementType.SEGMENT:
            segment = clip.get_segment()
            return (
                segment.max_layout.position.x + segment.max_layout.size.width / 2,
                segment.max_layout.position.y + segment.max_layout.size.height / 2
            )

        # default to word container
        word = clip.get_word()
        return (
            word.max_layout.position.x + word.max_layout.size.width / 2,
            word.max_layout.position.y + word.max_layout.size.height / 2
        )
