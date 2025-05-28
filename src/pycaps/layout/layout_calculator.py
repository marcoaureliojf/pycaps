from typing import List
from ..models import SubtitleLayoutOptions, TextOverflowStrategy
from ..utils.alignment_utils import AlignmentUtils
from ..utils.layout_utils import LayoutUtils
from ..tagger.models import Document, Line, Word, TimeFragment, ElementLayout, Size, Position

class LayoutCalculator:
    def __init__(self, layout_options: SubtitleLayoutOptions):
        self.options = layout_options

    def refresh_lines_and_segments_sizes(self, document: Document) -> None:
        """
        Refreshes the lines and segments sizes, using the words sizes as reference.
        """
        for segment in document.segments:
            for line in segment.lines:
                line.layout.size.width = sum(w.layout.size.width for w in line.words) + (len(line.words) - 1) * self.options.word_spacing
                line.layout.size.height = max(w.layout.size.height for w in line.words)

            segment.layout.size.width = max(l.layout.size.width for l in segment.lines)
            segment.layout.size.height = sum(l.layout.size.height for l in segment.lines)

    def update_words_positions(self, document: Document, video_width: int, video_height: int) -> None:
        """
        Repositions the words in the document.
        It doesn't modify the structure of the document, only the positions of the words.
        """
        for segment in document.segments:
            self._calculate_words_positions(segment.lines, video_width, video_height)
            segment.layout = LayoutUtils.calculate_segment_layout(segment.lines)

    def calculate(self, document: Document, video_width: int, video_height: int) -> None:
        """
        Splits the segments into lines and calculates the positions of the words.
        """
        for segment in document.segments:
            words = segment.get_words()
            lines = self._split_words_into_lines(words, video_width)
            self._calculate_words_positions(lines, video_width, video_height)
            layout = LayoutUtils.calculate_segment_layout(lines)
            segment.lines = lines
            segment.layout = layout

    def _split_words_into_lines(self, words: List[Word], video_width: int) -> List[Line]:
        """Splits pre-measured words into lines based on layout options."""
        lines: List[Line] = []
        current_line_words: List[Word] = []
        current_line_total_width = 0
        max_w = video_width * self.options.max_width_ratio
        word_spacing = self.options.word_spacing

        for word in words:
            word_size = word.layout.size
            word_width_with_spacing = word_size.width + word_spacing

            if (len(lines) >= self.options.max_number_of_lines - 1 and 
                self.options.on_text_overflow_strategy == TextOverflowStrategy.EXCEED_MAX_WIDTH_RATIO_IN_LAST_LINE):
                current_line_words.append(word)
                current_line_total_width += word_spacing + word_size.width
                continue

            if current_line_total_width + word_width_with_spacing <= max_w:
                current_line_words.append(word)
                current_line_total_width += word_spacing + word_size.width
            else:
                self._add_line_layout_data_if_needed(lines, current_line_words, current_line_total_width)
                current_line_words = [word]
                current_line_total_width = word_size.width
        
        self._add_line_layout_data_if_needed(lines, current_line_words, current_line_total_width)
        self._adjust_lines_to_constraints(lines)
        return lines

    def _adjust_lines_to_constraints(self, lines: List[Line]) -> None:
        """Adjusts lines according to min/max constraints and overflow strategy."""
        if len(lines) >= self.options.min_number_of_lines:
            return
        
        # If we have fewer lines than minimum, split the longest line
        while len(lines) < self.options.min_number_of_lines:
            longest_line = max(lines, key=lambda l: l.layout.size.width)
            number_of_words = len(longest_line.words)
            if number_of_words <= 1:
                break
            mid_point = number_of_words // 2
            
            first_half = longest_line.words[:mid_point]
            second_half = longest_line.words[mid_point:]
            
            first_line_width = sum(w.layout.size.width for w in first_half) + (len(first_half) - 1) * self.options.word_spacing
            second_line_width = sum(w.layout.size.width for w in second_half) + (len(second_half) - 1) * self.options.word_spacing
            
            first_line = Line(
                words=first_half,
                layout=ElementLayout(size=Size(width=first_line_width, height=max(w.layout.size.height for w in first_half))),
                time=TimeFragment(start=first_half[0].time.start, end=first_half[-1].time.end)
            )
            second_line = Line(
                words=second_half,
                layout=ElementLayout(size=Size(width=second_line_width, height=max(w.layout.size.height for w in second_half))),
                time=TimeFragment(start=second_half[0].time.start, end=second_half[-1].time.end)
            )
            
            lines.remove(longest_line)
            lines.extend([first_line, second_line])
        
    def _calculate_words_positions(self, lines: List[Line], video_width: int, video_height: int) -> None:
        y = self._calculate_base_y_position(lines, video_height)

        for line in lines:
            start_x_for_line = (video_width - line.layout.size.width) / 2.0
            x = start_x_for_line
            line_height = line.layout.size.height
            for word in line.words:
                word_y = y + (line_height - word.layout.size.height) / 2.0
                word.layout.position.x = x
                word.layout.position.y = word_y
                x += word.layout.size.width + self.options.word_spacing

            line.layout.position.x = start_x_for_line
            line.layout.position.y = y
            y += line_height
    
    def _add_line_layout_data_if_needed(self, lines: List[Line], words: List[Word], line_width: int) -> None:
        if not words:
            return

        height = max(w.layout.size.height for w in words)
        size = Size(width=line_width, height=height)
        layout = ElementLayout(size=size)
        time = TimeFragment(start=words[0].time.start, end=words[-1].time.end)
        line = Line(words=words, layout=layout, time=time)
        lines.append(line)

    def _calculate_base_y_position(self, lines: List[Line], video_height: int) -> float:
        """Calculates the base Y position for the subtitle block."""
        if not lines:
            return 0.0
            
        total_block_height = sum(line.layout.size.height for line in lines)
        return AlignmentUtils.get_vertical_alignment_position(self.options.vertical_align, total_block_height, video_height)
