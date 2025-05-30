from typing import Optional
from ..tagger.models import Document, Word, WordState
from ..css.css_subtitle_renderer import CssSubtitleRenderer
from moviepy.editor import VideoClip
from PIL import Image
import io
import numpy as np
from moviepy.editor import ImageClip
from ..tag.builtin_tag import BuiltinTag
from ..models import RenderedSubtitle
from ..tag.tag import Tag

class SubtitleClipsGenerator:

    def __init__(self, renderer: CssSubtitleRenderer):
        self._renderer = renderer
        self._should_do_word_reposition = False

    def should_do_word_reposition(self) -> bool:
        return self._should_do_word_reposition
    
    def update_word_clips_position(self, document: Document) -> None:
        """
        Updates the position of the moviepy clips of the words in the document.
        """
        for word in document.get_words():
            for state in word.states:
                state.clip = state.clip.set_position((word.layout.position.x, word.layout.position.y))

    def generate(self, document: Document) -> None:
        """
        Adds the MoviePy ImageClips for each word in the document received.
        """
        for segment in document.segments:
            for word in segment.get_words():
                being_narrated = self.__generate_being_narrated_word_state(word)
                if being_narrated:
                    word.states.append(being_narrated)

                already_narrated = self.__generate_already_narrated_word_state(word, segment.time.end)
                if already_narrated:
                    word.states.append(already_narrated)

                not_narrated = self.__generate_not_narrated_word_state(word, segment.time.start)
                if not_narrated:
                    word.states.append(not_narrated)
   
    def __generate_already_narrated_word_state(self, word: Word, segment_end_time: float) -> Optional[WordState]:
        # the last word will never be in the "already narrated" state
        if word.time.end >= segment_end_time:
            return None
        
        image = self.__render_word(word, BuiltinTag.WORD_ALREADY_NARRATED)
        if not image:
            return None
        
        pil_image = Image.open(io.BytesIO(image.image)).convert("RGBA")
        np_image = np.array(pil_image)

        clip = (
            ImageClip(np_image)
            .set_start(word.time.end)
            .set_duration(segment_end_time - word.time.end)
            .set_position((word.layout.position.x, word.layout.position.y)) 
        )
        return WordState(tag=BuiltinTag.WORD_ALREADY_NARRATED, clip=clip, parent=word)
    
    def __generate_being_narrated_word_state(self, word: Word) -> Optional[WordState]:
        image = self.__render_word(word, BuiltinTag.WORD_BEING_NARRATED)
        if not image:
            return None
        
        pil_mage = Image.open(io.BytesIO(image.image)).convert("RGBA")
        np_image = np.array(pil_mage)
        
        clip = (
            ImageClip(np_image)
            .set_start(word.time.start)
            .set_duration(word.time.end - word.time.start)
            .set_position((word.layout.position.x, word.layout.position.y))
        )
        return WordState(tag=BuiltinTag.WORD_BEING_NARRATED, clip=clip, parent=word)
    
    def __generate_not_narrated_word_state(self, word: Word, segment_start_time: float) -> Optional[WordState]:
        # the first word will never be in the "not narrated" state
        if word.time.start <= segment_start_time:
            return None
        
        image = self.__render_word(word, BuiltinTag.WORD_NOT_NARRATED_YET)
        if not image:
            return None
        
        pil_image = Image.open(io.BytesIO(image.image)).convert("RGBA")
        np_image = np.array(pil_image)
        
        clip: ImageClip = (
            ImageClip(np_image)
            .set_start(segment_start_time)
            .set_duration(word.time.start - segment_start_time)
            .set_position((word.layout.position.x, word.layout.position.y))
        )
        return WordState(tag=BuiltinTag.WORD_NOT_NARRATED_YET, clip=clip, parent=word)
    
    def __render_word(self, word: Word, tag: Tag) -> Optional[RenderedSubtitle]:
        image = self._renderer.render(word, [tag])
        if not image:
            return None
        
        self.__set_should_do_word_reposition(word, image)
        return image
    
    def __set_should_do_word_reposition(self, word: Word, word_image: RenderedSubtitle) -> None:
        has_word_width_changed = word.layout.size.width != word_image.width
        has_word_height_changed = word.layout.size.height != word_image.height
        self._should_do_word_reposition = self._should_do_word_reposition or has_word_width_changed or has_word_height_changed
        
        word.layout.size.width = word_image.width
        word.layout.size.height = word_image.height
