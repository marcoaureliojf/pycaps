from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class WordInfo:
    """Represents an individual word with its timings, width, and height."""
    text: str
    start: float
    end: float
    width: int
    height: int

@dataclass(frozen=True)
class WordLayoutData:
    """Represents an individual word with its timings, width, height and position."""
    word: WordInfo
    x: float
    y: float

@dataclass(frozen=True)
class LineLayoutData:
    """Layout information for a line of subtitles."""
    word_layouts: List[WordLayoutData]
    width: int
    height: int # Maximum height of the words in this line

@dataclass(frozen=True)
class SubtitleLayout:
    """Represents the calculated layout for a subtitle segment."""
    lines: List[LineLayoutData]
    segment_start: float
    segment_end: float
