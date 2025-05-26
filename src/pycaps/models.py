from dataclasses import dataclass, field
from typing import List, Optional
from PIL import Image

@dataclass(frozen=True)
class SubtitleImage:
    """Represents a rendered subtitle image."""
    image: Image.Image
    width: int
    height: int

@dataclass(frozen=True)
class WordTiming:
    """Represents the timing for a single word."""
    word: str
    start: float
    end: float

@dataclass(frozen=True)
class TranscriptionSegment:
    """Represents a segment of transcribed audio, including text and word timings."""
    text: str
    start: float
    end: float
    words: List[WordTiming] = field(default_factory=list)

@dataclass(frozen=True)
class SubtitleLayoutOptions:
    """Options for configuring the subtitle layout."""
    word_spacing: int = 10
    max_line_width_ratio: float = 0.8
    line_vertical_align: str = "bottom"  # "bottom", "center", "top"
    line_vertical_offset_ratio: float = 0.95

@dataclass(frozen=True)
class KaraokeEffectOptions:
    """Options for configuring the Karaoke subtitle effect."""
    layout_options: SubtitleLayoutOptions
    active_word_fade_duration: float = 0.1
    active_word_css_rules: str = ""
    inactive_word_css_rules: str = ""
