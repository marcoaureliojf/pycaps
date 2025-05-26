from typing import List, Tuple
from ..models import SubtitleLayoutOptions, WordData, TextOverflowStrategy
from .models import LineClipData, SegmentClipData, WordClipData, ElementLayout
from ..utils.alignment_utils import AlignmentUtils
from ..utils.layout_utils import LayoutUtils

class SubtitleLayoutService:
    def __init__(self, subtitle_layout_options: SubtitleLayoutOptions, video_width: int, video_height: int):
        self.options = subtitle_layout_options
        self.video_width = video_width
        self.video_height = video_height

    def calculate_layout(self, words: List[WordData], words_sizes: List[Tuple[int, int]], start: float, end: float) -> SegmentClipData:
        """Calculates the subtitle layout for a given segment based on pre-measured words."""
        
        if not words:
            return SegmentClipData()

        lines = self._split_words_into_lines(words, words_sizes)
        lines = self._calculate_words_positions(lines)
        layout = LayoutUtils.calculate_lines_layout(lines)
        return SegmentClipData(lines=lines, layout=layout, start=start, end=end)

    def _split_words_into_lines(self, words: List[WordData], words_sizes: List[Tuple[int, int]]) -> List[LineClipData]:
        """Splits pre-measured words into lines based on layout options."""
        lines: List[LineClipData] = []
        current_line_words: List[WordClipData] = []
        current_line_total_width = 0
        max_w = self.video_width * self.options.max_width_ratio
        word_spacing = self.options.word_spacing

        for word_index, word in enumerate(words):
            word_size = words_sizes[word_index]
            word_layout = WordClipData(word=word, layout=ElementLayout(width=word_size[0], height=word_size[1]))
            word_width_with_spacing = word_size[0] + word_spacing

            if (len(lines) >= self.options.max_number_of_lines - 1 and 
                self.options.on_text_overflow_strategy == TextOverflowStrategy.EXCEED_MAX_WIDTH_RATIO_IN_LAST_LINE):
                current_line_words.append(word_layout)
                current_line_total_width += word_spacing + word_size[0]
                continue

            if current_line_total_width + word_width_with_spacing <= max_w:
                current_line_words.append(word_layout)
                current_line_total_width += word_spacing + word_size[0]
            else:
                self._add_line_layout_data_if_needed(lines, current_line_words, current_line_total_width)
                current_line_words = [word_layout]
                current_line_total_width = word_size[0]
        
        self._add_line_layout_data_if_needed(lines, current_line_words, current_line_total_width)
        return self._adjust_lines_to_constraints(lines)

    def _adjust_lines_to_constraints(self, lines: List[LineClipData]) -> List[LineClipData]:
        """Adjusts lines according to min/max constraints and overflow strategy."""
        if len(lines) >= self.options.min_number_of_lines:
            return lines
        
        # If we have fewer lines than minimum, split the longest line
        while len(lines) < self.options.min_number_of_lines:
            longest_line = max(lines, key=lambda l: l.layout.width)
            number_of_words = len(longest_line.words)
            if number_of_words <= 1:
                break
            mid_point = number_of_words // 2
            
            first_half = longest_line.words[:mid_point]
            second_half = longest_line.words[mid_point:]
            
            first_line_width = sum(w.layout.width for w in first_half) + (len(first_half) - 1) * self.options.word_spacing
            second_line_width = sum(w.layout.width for w in second_half) + (len(second_half) - 1) * self.options.word_spacing
            
            first_line = LineClipData(
                words=first_half,
                layout=ElementLayout(width=first_line_width, height=max(w.layout.height for w in first_half))
            )
            second_line = LineClipData(
                words=second_half,
                layout=ElementLayout(width=second_line_width, height=max(w.layout.height for w in second_half))
            )
            
            lines.remove(longest_line)
            lines.extend([first_line, second_line])
        
        return lines
    
    def _calculate_words_positions(self, lines: List[LineClipData]) -> List[LineClipData]:
        new_lines = []
        y = self._calculate_base_y_position(lines)

        for line in lines:
            start_x_for_line = (self.video_width - line.layout.width) / 2.0
            x = start_x_for_line
            new_word_layouts: List[WordClipData] = []
            for old_word in line.words:
                word_layout = ElementLayout(x=x, y=y, width=old_word.layout.width, height=old_word.layout.height)
                new_word_layouts.append(WordClipData(word=old_word.word, layout=word_layout))
                x += old_word.layout.width + self.options.word_spacing

            line_layout = ElementLayout(x=start_x_for_line, y=y, width=line.layout.width, height=line.layout.height)
            new_lines.append(LineClipData(words=new_word_layouts, layout=line_layout))
            y += line.layout.height
        
        return new_lines
    
    def _add_line_layout_data_if_needed(self, lines: List[LineClipData], words: List[WordClipData], line_width: int) -> None:
        if not words:
            return

        line_actual_height = max(w.layout.height for w in words)
        line_layout = ElementLayout(width=line_width, height=line_actual_height)
        line_clip_data = LineClipData(words=words, layout=line_layout)
        lines.append(line_clip_data)

    def _calculate_base_y_position(self, lines: List[LineClipData]) -> float:
        """Calculates the base Y position for the subtitle block."""
        if not lines:
            return 0.0
            
        total_block_height = sum(line.layout.height for line in lines)
        return AlignmentUtils.get_vertical_alignment_position(self.options.vertical_align, total_block_height, self.video_height)
