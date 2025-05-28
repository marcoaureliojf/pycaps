from typing import Optional
from ..tagger.models import Document, Word
from ..css.css_subtitle_renderer import CssSubtitleRenderer
from moviepy.editor import VideoClip
from PIL import Image
import io
import numpy as np
from moviepy.editor import ImageClip
from ..css.css_class import CssClass
from ..models import RenderedSubtitle

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
            for i, clip in enumerate(word.clips):
                word.clips[i] = clip.set_position((word.layout.position.x, word.layout.position.y))

    def generate(self, document: Document) -> None:
        """
        Adds the MoviePy ImageClips for each word in the document received.
        """
        for segment in document.segments:
            for word in segment.get_words():
                being_narrated = self.__generate_being_narrated_word_clip(word)
                if being_narrated:
                    word.clips.append(being_narrated)

                already_narrated = self.__generate_already_narrated_word_clip(word, segment.time.end)
                if already_narrated:
                    word.clips.append(already_narrated)

                not_narrated = self.__generate_not_narrated_word_clip(word, segment.time.start)
                if not_narrated:
                    word.clips.append(not_narrated)
   
    def __generate_already_narrated_word_clip(self, word: Word, segment_end_time: float) -> Optional[VideoClip]:
        # the last word will never be in the "already narrated" state
        if word.time.end >= segment_end_time:
            return None
        
        image = self.__render_word(word, CssClass.WORD_ALREADY_NARRATED)
        if not image:
            return None
        
        pil_image = Image.open(io.BytesIO(image.image)).convert("RGBA")
        np_image = np.array(pil_image)

        return (
            ImageClip(np_image)
            .set_start(word.time.end)
            .set_duration(segment_end_time - word.time.end)
            .set_position((word.layout.position.x, word.layout.position.y)) 
        )
    
    def __generate_being_narrated_word_clip(self, word: Word) -> Optional[VideoClip]:
        image = self.__render_word(word, CssClass.WORD_BEING_NARRATED)
        if not image:
            return None
        
        pil_mage = Image.open(io.BytesIO(image.image)).convert("RGBA")
        np_image = np.array(pil_mage)
        
        return (
            ImageClip(np_image)
            .set_start(word.time.start)
            .set_duration(word.time.end - word.time.start)
            .set_position((word.layout.position.x, word.layout.position.y))
            # .crossfadein(self.options.active_word_fade_duration) # TODO: this should be available as a animation
        )
    
    def __generate_not_narrated_word_clip(self, word: Word, segment_start_time: float) -> Optional[VideoClip]:
        # the first word will never be in the "not narrated" state
        if word.time.start <= segment_start_time:
            return None
        
        image = self.__render_word(word, CssClass.WORD_NOT_NARRATED_YET)
        if not image:
            return None
        
        pil_image = Image.open(io.BytesIO(image.image)).convert("RGBA")
        np_image = np.array(pil_image)
        
        return (
            ImageClip(np_image)
            .set_start(segment_start_time)
            .set_duration(word.time.start - segment_start_time)
            .set_position((word.layout.position.x, word.layout.position.y))
        )
    
    def __render_word(self, word: Word, css_class: CssClass) -> Optional[RenderedSubtitle]:
        image = self._renderer.render(word, [css_class])
        if not image:
            return None
        
        self.__set_should_do_word_reposition(word, image)
        return image
    
    def __set_should_do_word_reposition(self, word: Word, word_image: RenderedSubtitle) -> None:        
        self._should_do_word_reposition = (self._should_do_word_reposition or
                                           word.layout.size.width != word_image.width or
                                           word.layout.size.height != word_image.height)
        word.layout.size.width = word_image.width
        word.layout.size.height = word_image.height
