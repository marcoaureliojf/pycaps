from dataclasses import dataclass, field
from typing import List, Optional, Set
from moviepy.editor import ImageClip
from ..tag.tag import Tag
from enum import Enum

# TODO: we should somehow assure that whenever a child is added to a parent, the parent is set.
#  For example, if segment.lines.append(line), then line.parent should be set to segment.
#  The same if segment.lines = [line1, line2], then line1.parent, and line2.parent should be set to segment.

class ElementState(Enum):
    WORD_BEING_NARRATED = "word-being-narrated"
    WORD_NOT_NARRATED_YET = "word-not-narrated-yet"
    WORD_ALREADY_NARRATED = "word-already-narrated"

    LINE_BEING_NARRATED = "line-being-narrated"
    LINE_NOT_NARRATED_YET = "line-not-narrated-yet"
    LINE_ALREADY_NARRATED = "line-already-narrated"    

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
class WordClip:
    states: List[ElementState]
    image_clip: ImageClip
    parent: 'Word' = field(default_factory='Word')

    def has_state(self, state: ElementState) -> bool:
        return state in self.states

    def get_word(self) -> 'Word':
        return self.parent

    def get_line(self) -> 'Line':
        return self.parent.get_line()
    
    def get_segment(self) -> 'Segment':
        return self.parent.get_segment()
    
    def get_document(self) -> 'Document':
        return self.parent.get_document()

@dataclass
class Word:
    text: str = ""
    tags: Set[Tag] = field(default_factory=set)
    layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)
    clips: List[WordClip] = field(default_factory=list)
    parent: 'Line' = field(default_factory='Line')

    def add_clip(self, clip: WordClip) -> None:
        self.clips.append(clip)
        clip.parent = self

    def get_image_clips(self) -> List[ImageClip]:
        return [clip.image_clip for clip in self.clips]

    def get_line(self) -> 'Line':
        return self.parent

    def get_segment(self) -> 'Segment':
        return self.parent.get_segment()
    
    def get_document(self) -> 'Document':
        return self.parent.get_document()

@dataclass
class Line:
    words: List[Word] = field(default_factory=list)
    layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment) # TODO: We could calculate it using the words (same for segment)
    parent: 'Segment' = field(default_factory='Segment')

    def add_word(self, word: Word) -> None:
        self.words.append(word)
        word.parent = self

    def get_text(self) -> str:
        return ' '.join([word.text for word in self.words])
    
    def get_image_clips(self) -> List[ImageClip]:
        return [clip for word in self.words for clip in word.get_image_clips()]
    
    def get_word_clips(self) -> List[WordClip]:
        return [clip for word in self.words for clip in word.clips]
    
    def get_segment(self) -> 'Segment':
        return self.parent
    
    def get_document(self) -> 'Document':
        return self.parent.get_document()

@dataclass
class Segment:
    lines: List[Line] = field(default_factory=list)
    layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)
    parent: 'Document' = field(default_factory='Document')

    def add_line(self, line: Line) -> None:
        self.lines.append(line)
        line.parent = self

    def get_text(self) -> str:
        return ' '.join([line.get_text() for line in self.lines])
    
    def get_image_clips(self) -> List[ImageClip]:
        return [clip for line in self.lines for clip in line.get_image_clips()]
    
    def get_word_clips(self) -> List[WordClip]:
        return [clip for line in self.lines for clip in line.get_word_clips()]
    
    def get_words(self) -> List[Word]:
        return [word for line in self.lines for word in line.words]
    
    def get_document(self) -> 'Document':
        return self.parent

@dataclass
class Document:
    segments: List[Segment] = field(default_factory=list)

    def add_segment(self, segment: Segment) -> None:
        self.segments.append(segment)
        segment.parent = self

    def get_image_clips(self) -> List[ImageClip]:
        return [clip for segment in self.segments for clip in segment.get_image_clips()]

    def get_word_clips(self) -> List[WordClip]:
        return [clip for segment in self.segments for clip in segment.get_word_clips()]
    
    def get_words(self) -> List[Word]:
        return [word for segment in self.segments for word in segment.get_words()]
    
    def get_lines(self) -> List[Line]:
        return [line for segment in self.segments for line in segment.lines]
    
    def get_text(self) -> str:
        return ' '.join([segment.get_text() for segment in self.segments])

