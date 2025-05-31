from typing import List
from ..tagger.models import ElementState
from ..models import SubtitleLayoutOptions
from ..utils.alignment_utils import AlignmentUtils
from ..tagger.models import Document, Line

class PositionsCalculator:
    def __init__(self, layout_options: SubtitleLayoutOptions):
        self._options = layout_options

    def calculate(self, document: Document, video_width: int, video_height: int) -> None:
        """
        Calculates the positions of the words in the document.
        """
        for segment in document.segments:
            self._calculate_words_positions(segment.lines, video_width, video_height)
        
    def _calculate_words_positions(self, lines: List[Line], video_width: int, video_height: int) -> None:
        y = self._calculate_base_y_position(lines, video_height)
        line_states = ElementState.get_all_line_states()

        for line in lines:
            for state in line_states:
                line_width = 0
                x_gaps = []
                for word in line.words:
                    max_clip_width = 0
                    for clip in word.clips:
                        if state in clip.states:
                            max_clip_width = max(max_clip_width, clip.layout.size.width)
                    line_width += max_clip_width + self._options.word_spacing
                    x_gaps.append(max_clip_width + self._options.word_spacing)
                
                start_x_for_line = (video_width - line_width) // 2
                slot_x = start_x_for_line
                for i, word in enumerate(line.words):
                    slot_width = x_gaps[i]
                    for clip in word.clips:
                        if state in clip.states:
                            # the clip is located in the center of the slot
                            clip.layout.position.x = slot_x + (slot_width - clip.layout.size.width) // 2
                            clip.layout.position.y = y + (line.max_layout.size.height - clip.layout.size.height) // 2
                            clip.image_clip = clip.image_clip.set_position((clip.layout.position.x, clip.layout.position.y))

                    slot_x += slot_width

            y += line.max_layout.size.height

    def _calculate_base_y_position(self, lines: List[Line], video_height: int) -> float:
        """Calculates the base Y position for the subtitle block."""
        if not lines:
            return 0.0
            
        total_block_height = sum(line.max_layout.size.height for line in lines)
        return AlignmentUtils.get_vertical_alignment_position(self._options.vertical_align, total_block_height, video_height)
