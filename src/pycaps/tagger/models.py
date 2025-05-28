from dataclasses import dataclass, field
from typing import List
from moviepy.editor import VideoClip

# TODO: WE MUST TO UNIFY THESE MODELS IN THE OTHER PACKAGES. PLEASE.
#  Plus, we could remove the frozen=True from these dataclasses.
#  Doing that, we could add all the needed properties to them, and populate them in the different steps of the pipeline.
#  For example, the layout is unknown first, and is populated later.

@dataclass
class TimeFragment:
    start: float = 0
    end: float = 0

@dataclass
class Size:
    width: int = 0
    height: int = 0

@dataclass
class Position:
    x: float = 0
    y: float = 0

@dataclass
class ElementLayout:
    position: Position = field(default_factory=Position)
    size: Size = field(default_factory=Size)

@dataclass
class Word:
    text: str = ""
    tags: List[str] = field(default_factory=list)
    layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)
    clips: List[VideoClip] = field(default_factory=list)

@dataclass
class Line:
    words: List[Word] = field(default_factory=list)
    layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)

    def get_text(self) -> str:
        return ' '.join([word.text for word in self.words])
    
    def get_clips(self) -> List[VideoClip]:
        return [clip for word in self.words for clip in word.clips]

@dataclass
class Segment:
    lines: List[Line] = field(default_factory=list)
    layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)

    def get_words(self) -> List[Word]:
        return [word for line in self.lines for word in line.words]

    def get_text(self) -> str:
        return ' '.join([line.get_text() for line in self.lines])
    
    def get_clips(self) -> List[VideoClip]:
        return [clip for line in self.lines for clip in line.get_clips()]

@dataclass
class Document:
    segments: List[Segment] = field(default_factory=list)

    def get_words(self) -> List[Word]:
        return [word for segment in self.segments for word in segment.get_words()]
    
    def get_lines(self) -> List[Line]:
        return [line for segment in self.segments for line in segment.lines]
    
    def get_text(self) -> str:
        return ' '.join([segment.get_text() for segment in self.segments])
    
    def get_clips(self) -> List[VideoClip]:
        return [clip for segment in self.segments for clip in segment.get_clips()]
