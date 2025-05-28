from dataclasses import dataclass, field
from typing import List, Optional
from PIL import Image
from enum import Enum

@dataclass(frozen=True)
class RenderedSubtitle:
    """Represents a rendered subtitle image."""
    image: Image.Image
    width: int
    height: int

@dataclass(frozen=True)
class WordData:
    """Represents the timing for a single word."""
    text: str
    start: float
    end: float

@dataclass(frozen=True)
class TranscriptionSegment:
    """Represents a segment of transcribed audio, including text and word timings."""
    text: str
    start: float
    end: float
    words: List[WordData] = field(default_factory=list)

class VerticalAlignmentType(Enum):
    BOTTOM = "bottom"
    CENTER = "center"
    TOP = "top"

@dataclass(frozen=True)
class VerticalAlignment:
    """Represents a vertical alignment."""
    align: VerticalAlignmentType = VerticalAlignmentType.BOTTOM
    offset: float = 0.0 # from -1.0 to 1.0 (0 means keep position established by the align parameter, negative means move up, positive means move down)

class TextOverflowStrategy(Enum):
    EXCEED_MAX_NUMBER_OF_LINES = "exceed_max_number_of_lines"
    EXCEED_MAX_WIDTH_RATIO_IN_LAST_LINE = "exceed_max_width_ratio_in_last_line"

@dataclass(frozen=True)
class SubtitleLayoutOptions:
    """Options for configuring the subtitle layout."""
    word_spacing: int = 10
    max_width_ratio: float = 0.8
    max_number_of_lines: int = 2
    min_number_of_lines: int = 1
    on_text_overflow_strategy: TextOverflowStrategy = TextOverflowStrategy.EXCEED_MAX_NUMBER_OF_LINES
    vertical_align: VerticalAlignment = field(default_factory=VerticalAlignment)

@dataclass(frozen=True)
class KaraokeEffectOptions:
    """Options for configuring the Karaoke subtitle effect."""
    layout_options: SubtitleLayoutOptions = field(default_factory=SubtitleLayoutOptions)
    active_word_fade_duration: float = 0.1
    active_word_css_rules: str = ""
    inactive_word_css_rules: str = ""

class EmojiAlign(Enum):
    BOTTOM = "bottom"
    TOP = "top"
    RANDOM = "random"

@dataclass(frozen=True)
class EmojiEffectOptions:
    """Options for configuring the Emoji subtitle effect."""
    chance_to_apply: float = 0.5
    css_rules: str = ""
    align: EmojiAlign = EmojiAlign.RANDOM
    fade_in_duration: float = 0.1
    fade_out_duration: float = 0.1
    start_delay: float = 0.0
    hide_before_end: float = 0.0
    ignore_segments_with_duration_less_than: float = 1 # in seconds, 0 means no segments will be ignored
    max_uses_of_each_emoji: int = 2 # 0 means no limit
    max_consecutive_segments_with_emoji: int = 3 # 0 means no limit
