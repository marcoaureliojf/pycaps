from enum import Enum
from dataclasses import dataclass, field

class VerticalAlignmentType(Enum):
    BOTTOM = "bottom"
    CENTER = "center"
    TOP = "top"

class TextOverflowStrategy(Enum):
    EXCEED_MAX_NUMBER_OF_LINES = "exceed_max_number_of_lines"
    EXCEED_MAX_WIDTH_RATIO_IN_LAST_LINE = "exceed_max_width_ratio_in_last_line"

@dataclass(frozen=True)
class VerticalAlignment:
    """Represents a vertical alignment."""
    align: VerticalAlignmentType = VerticalAlignmentType.BOTTOM
    offset: float = 0.0 # from -1.0 to 1.0 (0 means keep position established by the align parameter, negative means move up, positive means move down)

@dataclass(frozen=True)
class SubtitleLayoutOptions:
    """Options for configuring the subtitle layout."""
    word_spacing: int = 0 # it's recommended to use padding via css instead of this parameter
    max_width_ratio: float = 0.8
    max_number_of_lines: int = 2
    min_number_of_lines: int = 1
    on_text_overflow_strategy: TextOverflowStrategy = TextOverflowStrategy.EXCEED_MAX_NUMBER_OF_LINES
    vertical_align: VerticalAlignment = field(default_factory=VerticalAlignment)
