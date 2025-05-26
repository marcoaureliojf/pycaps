from dataclasses import dataclass, field
from typing import List, Optional
from PIL import Image

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

@dataclass(frozen=True)
class VerticalAlignment:
    """Represents a vertical alignment."""
    align: str = "bottom"  # "bottom", "center", "top"
    offset: float = 0 # from -1.0 to 1.0 (0 means keep position established by the align parameter, negative means move up, positive means move down)

@dataclass(frozen=True)
class SubtitleLayoutOptions:
    """Options for configuring the subtitle layout."""
    word_spacing: int = 10
    max_width_ratio: float = 0.8
    vertical_align: VerticalAlignment = field(default_factory=VerticalAlignment)

@dataclass(frozen=True)
class KaraokeEffectOptions:
    """Options for configuring the Karaoke subtitle effect."""
    layout_options: SubtitleLayoutOptions = field(default_factory=SubtitleLayoutOptions)
    active_word_fade_duration: float = 0.1
    active_word_css_rules: str = ""
    inactive_word_css_rules: str = ""

@dataclass(frozen=True)
class EmojiEffectOptions:
    """Options for configuring the Emoji subtitle effect."""
    chance_to_apply: float = 0.5
    css_rules: str = ""
    align: str = "random" # "bottom", "top", or "random"
    fade_in_duration: float = 0.1
    fade_out_duration: float = 0.1
    start_delay: float = 0.0
    hide_before_end: float = 0.0
    ignore_segments_with_duration_less_than: float = 1 # in seconds, 0 means no segments will be ignored
    max_uses_of_each_emoji: int = 2 # 0 means no limit
    max_consecutive_segments_with_emoji: int = 3 # 0 means no limit
