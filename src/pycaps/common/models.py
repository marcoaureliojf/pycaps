from dataclasses import dataclass, field
from moviepy.editor import VideoClip, AudioFileClip
from typing import List, Optional, Set
from .types import ElementState

@dataclass(frozen=True)
class Tag:
    name: str

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
    x: int = 0
    y: int = 0

@dataclass
class ElementLayout:
    position: Position = field(default_factory=Position)
    size: Size = field(default_factory=Size)

    def get_center(self) -> Position:
        return Position(x=self.position.x + self.size.width / 2, y=self.position.y + self.size.height / 2)


# TODO: I should handle caching for methods like get_words.
#  It should be refreshed automatically when a child is added or removed.

@dataclass
class WordClip:
    _parent: Optional['Word'] = None
    states: List[ElementState] = field(default_factory=list)
    moviepy_clip: Optional[VideoClip] = None
    layout: ElementLayout = field(default_factory=ElementLayout)

    def has_state(self, state: ElementState) -> bool:
        return state in self.states

    def get_word(self) -> 'Word':
        return self._parent

    def get_line(self) -> 'Line':
        return self._parent.get_line()
    
    def get_segment(self) -> 'Segment':
        return self._parent.get_segment()
    
    def get_document(self) -> 'Document':
        return self._parent.get_document()

@dataclass
class Word:
    _parent: Optional['Line'] = None
    _clips: 'ElementContainer[WordClip]' = field(init=False)
    text: str = ""
    tags: Set[Tag] = field(default_factory=set)
    # IMPORTANT: it saves the maximum width/height of their clips (the word slot size)
    #            same with the position: it's the x,y of the word slot
    max_layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)

    def __post_init__(self):
        self._clips = ElementContainer(self)

    @property
    def clips(self) -> 'ElementContainer[WordClip]':
        return self._clips

    def get_moviepy_clips(self) -> List[VideoClip]:
        return [clip.moviepy_clip for clip in self.clips]

    def get_line(self) -> 'Line':
        return self._parent

    def get_segment(self) -> 'Segment':
        return self._parent.get_segment()
    
    def get_document(self) -> 'Document':
        return self._parent.get_document()
    
    def get_all_tags(self) -> Set[Tag]:
        return self.tags | self.get_line().tags | self.get_segment().tags

@dataclass
class Line:
    _parent: Optional['Segment'] = None
    _words: 'ElementContainer[Word]' = field(init=False)
    tags: Set[Tag] = field(default_factory=set)
    max_layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment) # TODO: We could calculate it using the words (same for segment)

    def __post_init__(self):
        self._words = ElementContainer(self)

    @property
    def words(self) -> 'ElementContainer[Word]':
        return self._words

    def get_text(self) -> str:
        return ' '.join([word.text for word in self.words])
    
    def get_moviepy_clips(self) -> List[VideoClip]:
        return [clip for word in self.words for clip in word.get_moviepy_clips()]
    
    def get_word_clips(self) -> List[WordClip]:
        return [clip for word in self.words for clip in word.clips]
    
    def get_segment(self) -> 'Segment':
        return self._parent
    
    def get_document(self) -> 'Document':
        return self._parent.get_document()

@dataclass
class Segment:
    _parent: Optional['Document'] = None
    _lines: 'ElementContainer[Line]' = field(init=False)
    tags: Set[Tag] = field(default_factory=set)
    max_layout: ElementLayout = field(default_factory=ElementLayout)
    time: TimeFragment = field(default_factory=TimeFragment)

    def __post_init__(self):
        self._lines = ElementContainer(self)

    @property
    def lines(self) -> 'ElementContainer[Line]':
        return self._lines

    def get_text(self) -> str:
        return ' '.join([line.get_text() for line in self.lines])
    
    def get_moviepy_clips(self) -> List[VideoClip]:
        return [clip for line in self.lines for clip in line.get_moviepy_clips()]
    
    def get_word_clips(self) -> List[WordClip]:
        return [clip for line in self.lines for clip in line.get_word_clips()]
    
    def get_words(self) -> List[Word]:
        return [word for line in self.lines for word in line.words]
    
    def get_document(self) -> 'Document':
        return self._parent

@dataclass
class Document:
    _segments: 'ElementContainer[Segment]' = field(init=False)
    sfxs: List[AudioFileClip] = field(default_factory=list)

    def __post_init__(self):
        self._segments = ElementContainer(self)

    @property
    def segments(self) -> 'ElementContainer[Segment]':
        return self._segments

    def get_moviepy_clips(self) -> List[VideoClip]:
        return [clip for segment in self.segments for clip in segment.get_moviepy_clips()]

    def get_word_clips(self) -> List[WordClip]:
        return [clip for segment in self.segments for clip in segment.get_word_clips()]
    
    def get_words(self) -> List[Word]:
        return [word for segment in self.segments for word in segment.get_words()]
    
    def get_lines(self) -> List[Line]:
        return [line for segment in self.segments for line in segment.lines]
    
    def get_text(self) -> str:
        return ' '.join([segment.get_text() for segment in self.segments])

from .element_container import ElementContainer