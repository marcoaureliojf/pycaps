from dataclasses import dataclass, field
from typing import List
from ..models import WordData
from moviepy.editor import VideoClip

@dataclass(frozen=True)
class ElementLayout:
    """Represents the layout of an element."""
    x: float = 0 # TODO: use Position instead
    y: float = 0
    width: int = 0 # TODO: use Size instead
    height: int = 0

@dataclass(frozen=True)
class WordClipData:
    """Represents an individual word with its clips."""
    word: WordData # TODO: remove this field and use text + TimeFragment object instead
    layout: ElementLayout
    clips: List[VideoClip] = field(default_factory=list)

@dataclass(frozen=True)
class LineClipData:
    """Layout and data information for a line of subtitles."""
    words: List[WordClipData]
    layout: ElementLayout

    def get_all_clips(self) -> List[VideoClip]:
        return [clip for word in self.words for clip in word.clips]
    
    def get_text(self) -> str:
        return " ".join([word.word.text for word in self.words])

@dataclass(frozen=True)
class SegmentClipData:
    """Represents the calculated layout for a subtitle segment."""
    lines: List[LineClipData] = field(default_factory=list)
    layout: ElementLayout = field(default_factory=ElementLayout)
    start: float = 0
    end: float = 0

    def get_all_clips(self) -> List[VideoClip]:
        return [clip for line in self.lines for clip in line.get_all_clips()]

    def get_text(self) -> str:
        return " ".join([line.get_text() for line in self.lines])
