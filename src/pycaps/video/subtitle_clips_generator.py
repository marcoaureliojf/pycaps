from typing import Optional, List
from ..tagger.models import Document, Word, WordClip
from ..css.css_subtitle_renderer import CssSubtitleRenderer
from moviepy.editor import ImageClip
from PIL import Image
import io
import numpy as np
from ..tagger.models import ElementState

class SubtitleClipsGenerator:

    def __init__(self, renderer: CssSubtitleRenderer):
        self._renderer = renderer

    def update_word_clips_position(self, document: Document) -> None:
        """
        Updates the position of the moviepy clips of the words in the document.
        """
        for word in document.get_words():
            for clip in word.clips:
                word_slot_size = word.layout.size
                word_slot_position = word.layout.position
                word_clip_size = clip.image_clip.size
                word_clip_position = (
                    word_slot_position.x + (word_slot_size.width - word_clip_size[0]) // 2,
                    word_slot_position.y + (word_slot_size.height - word_clip_size[1]) // 2
                )
                clip.image_clip = clip.image_clip.set_position(word_clip_position)

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
    
        image = self._renderer.render(word, states)
        if not image:
            return None
        
        clip: ImageClip = (
            ImageClip(np.array(image.image))
            .set_start(start)
            .set_duration(end - start)
        )
        return WordClip(states=states, image_clip=clip, parent=word)
