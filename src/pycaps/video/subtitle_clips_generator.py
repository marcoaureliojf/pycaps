from typing import Optional, List
from pycaps.common import Document, Word, WordClip, ElementState
from pycaps.renderer import CssSubtitleRenderer
from moviepy.editor import ImageClip
import numpy as np

class SubtitleClipsGenerator:

    def __init__(self, renderer: CssSubtitleRenderer):
        self._renderer = renderer

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
            ImageClip(np.array(image))
            .set_start(start)
            .set_duration(end - start)
        )
        word_clip = WordClip(states=states, image_clip=clip, parent=word)
        word_clip.layout.size.width = image.width
        word_clip.layout.size.height = image.height
        return word_clip
