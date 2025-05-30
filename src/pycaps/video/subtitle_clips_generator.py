from typing import Optional, List
from ..tagger.models import Document, Word, WordClip
from ..css.css_subtitle_renderer import CssSubtitleRenderer
from moviepy.editor import ImageClip
from PIL import Image
import io
import numpy as np
from ..tag.builtin_tag import BuiltinTag
from ..models import RenderedSubtitle
from ..tagger.models import ElementState

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
            for clip in word.clips:
                clip.image_clip = clip.image_clip.set_position((word.layout.position.x, word.layout.position.y))

    def generate(self, document: Document) -> None:
        """
        Adds the MoviePy ImageClips for each word in the document received.
        """
        for segment in document.segments:
            for line in segment.lines:
                for word in line.words:
                    line_not_narrated_yet = self.__create_word_clip(
                        word,
                        [ElementState.LINE_NOT_NARRATED_YET, ElementState.WORD_NOT_NARRATED_YET],
                        segment.time.start,
                        line.time.start
                    )
                    if line_not_narrated_yet:
                        word.clips.append(line_not_narrated_yet)

                    line_being_narrated_word_not_narrated_yet = self.__create_word_clip(
                        word,
                        [ElementState.LINE_BEING_NARRATED, ElementState.WORD_NOT_NARRATED_YET],
                        line.time.start,
                        word.time.start
                    )
                    if line_being_narrated_word_not_narrated_yet:
                        word.clips.append(line_being_narrated_word_not_narrated_yet)

                    line_being_narrated_word_being_narrated = self.__create_word_clip(
                        word,
                        [ElementState.LINE_BEING_NARRATED, ElementState.WORD_BEING_NARRATED],
                        word.time.start,
                        word.time.end
                    )
                    if line_being_narrated_word_being_narrated:
                        word.clips.append(line_being_narrated_word_being_narrated)

                    line_being_narrated_word_already_narrated = self.__create_word_clip(
                        word,
                        [ElementState.LINE_BEING_NARRATED, ElementState.WORD_ALREADY_NARRATED],
                        word.time.end,
                        line.time.end
                    )
                    if line_being_narrated_word_already_narrated:
                        word.clips.append(line_being_narrated_word_already_narrated)

                    line_already_narrated_word_already_narrated = self.__create_word_clip(
                        word,
                        [ElementState.LINE_ALREADY_NARRATED, ElementState.WORD_ALREADY_NARRATED],
                        line.time.end,
                        segment.time.end
                    )
                    if line_already_narrated_word_already_narrated:
                        word.clips.append(line_already_narrated_word_already_narrated)
       
    def __create_word_clip(self, word: Word, states: List[ElementState], start: float, end: float) -> Optional[WordClip]:
        if end <= start:
            return None
    
        image = self.__render_word(word, states)
        if not image:
            return None
        
        pil_image = Image.open(io.BytesIO(image.image)).convert("RGBA")
        np_image = np.array(pil_image)
        
        clip: ImageClip = (
            ImageClip(np_image)
            .set_start(start)
            .set_duration(end - start)
            .set_position((word.layout.position.x, word.layout.position.y))
        )
        return WordClip(states=states, image_clip=clip, parent=word)

    def __render_word(self, word: Word, states: List[ElementState]) -> Optional[RenderedSubtitle]:
        image = self._renderer.render(word, states)
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
