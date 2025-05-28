from dataclasses import dataclass, field
from typing import List, Optional, Set
from moviepy.editor import VideoClip
from ..tag.tag import Tag
from ..tag.builtin_tag import BuiltinTag

# TODO: we should somehow assure that whenever a child is added to a parent, the parent is set.
#  For example, if segment.lines.append(line), then line.parent should be set to segment.
#  The same if segment.lines = [line1, line2], then line1.parent, and line2.parent should be set to segment.

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
class WordState:
    tag: Tag
    clip: VideoClip
    parent: 'Word' = field(default_factory='Word')

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
    tags: Set[Tag] = field(default_factory=lambda: {BuiltinTag.WORD})
    layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)
    states: List[WordState] = field(default_factory=list)
    parent: 'Line' = field(default_factory='Line')

    def add_state(self, state: WordState) -> None:
        self.states.append(state)
        state.parent = self

    def get_clips(self) -> List[VideoClip]:
        return [state.clip for state in self.states]

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
    time: TimeFragment = field(default_factory=TimeFragment)
    parent: 'Segment' = field(default_factory='Segment')

    def add_word(self, word: Word) -> None:
        self.words.append(word)
        word.parent = self

    def get_text(self) -> str:
        return ' '.join([word.text for word in self.words])
    
    def get_clips(self) -> List[VideoClip]:
        return [clip for word in self.words for clip in word.get_clips()]
    
    def get_word_states(self) -> List[WordState]:
        return [word_state for word in self.words for word_state in word.states]
    
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
    
    def get_clips(self) -> List[VideoClip]:
        return [clip for line in self.lines for clip in line.get_clips()]
    
    def get_word_states(self) -> List[WordState]:
        return [word_state for line in self.lines for word_state in line.get_word_states()]
    
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

    def get_clips(self) -> List[VideoClip]:
        return [clip for segment in self.segments for clip in segment.get_clips()]

    def get_word_states(self) -> List[WordState]:
        return [word_state for segment in self.segments for word_state in segment.get_word_states()]
    
    def get_words(self) -> List[Word]:
        return [word for segment in self.segments for word in segment.get_words()]
    
    def get_lines(self) -> List[Line]:
        return [line for segment in self.segments for line in segment.lines]
    
    def get_text(self) -> str:
        return ' '.join([segment.get_text() for segment in self.segments])

