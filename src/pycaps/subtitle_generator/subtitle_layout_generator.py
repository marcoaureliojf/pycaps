from typing import List
from ..models import SubtitleLayoutOptions
from .subtitle_models import LineLayoutData, SubtitleLayout, WordInfo, WordLayoutData

class SubtitleLayoutService:
    def __init__(self, subtitle_layout_options: SubtitleLayoutOptions, video_width: int, video_height: int):
        self.options = subtitle_layout_options
        self.video_width = video_width
        self.video_height = video_height

    def calculate_layout(self, 
                         word_layouts: List[WordInfo], 
                         segment_start_time: float, 
                         segment_end_time: float) -> SubtitleLayout:
        """Calculates the subtitle layout for a given segment based on pre-measured words."""
        
        if not word_layouts:
            return SubtitleLayout(lines=[], segment_start=segment_start_time, segment_end=segment_end_time)

        lines = self._split_words_into_lines(word_layouts)
        lines = self._calculate_words_positions(lines)
        return SubtitleLayout(lines=lines, segment_start=segment_start_time, segment_end=segment_end_time)

    def _split_words_into_lines(self, words: List[WordInfo]) -> List[LineLayoutData]:
        """Splits pre-measured words into lines based on the maximum allowed width."""
        lines: List[LineLayoutData] = []
        current_line_words: List[WordInfo] = []
        current_line_total_width = 0
        max_w = self.video_width * self.options.max_line_width_ratio
        word_spacing = self.options.word_spacing

        for word in words:
            word_layout = WordLayoutData(word=word, x=0, y=0)
            word_width_with_spacing = word.width + word_spacing

            if current_line_total_width + word_width_with_spacing <= max_w:
                current_line_words.append(word_layout)
                current_line_total_width += word_spacing + word.width
            else:
                self._add_line_layout_data_if_needed(lines, current_line_words, current_line_total_width)
                current_line_words = [word_layout]
                current_line_total_width = word.width
        
        # Add the last line if it contains words
        self._add_line_layout_data_if_needed(lines, current_line_words, current_line_total_width)
        return lines
    
    def _calculate_words_positions(self, lines: List[LineLayoutData]) -> List[LineLayoutData]:
        new_lines = []
        y = self._calculate_base_y_position(lines)

        for line in lines:
            start_x_for_line = (self.video_width - line.width) / 2.0
            x = start_x_for_line
            new_word_layouts: List[WordLayoutData] = []
            for old_word_layout in line.word_layouts:
                new_word_layouts.append(WordLayoutData(word=old_word_layout.word, x=x, y=y))
                x += old_word_layout.word.width + self.options.word_spacing

            y += line.height
            new_lines.append(LineLayoutData(word_layouts=new_word_layouts, width=line.width, height=line.height))
        
        return new_lines
    
    def _add_line_layout_data_if_needed(self, lines: List[LineLayoutData], words: List[WordLayoutData], line_width: int) -> None:
        if not words:
            return

        line_actual_height = max(w.word.height for w in words)
        line_layout = LineLayoutData(word_layouts=words, width=line_width, height=line_actual_height)
        lines.append(line_layout)

    def _calculate_base_y_position(self, lines: List[LineLayoutData]) -> float:
        """Calculates the base Y position for the subtitle block."""
        if not lines:
            return 0.0
            
        total_block_height = sum(line.height for line in lines)
        
        if self.options.line_vertical_align == "center":
            return (self.video_height - total_block_height) / 2.0
        elif self.options.line_vertical_align == "top":
            return self.video_height * self.options.line_vertical_offset_ratio
        # Default to "bottom"
        return self.video_height * self.options.line_vertical_offset_ratio - total_block_height