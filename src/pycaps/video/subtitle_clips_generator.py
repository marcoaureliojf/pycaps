from typing import Optional, List, Callable
from pycaps.common import Document, Word, WordClip, ElementState, Line
from pycaps.renderer import CssSubtitleRenderer

class SubtitleClipsGenerator:

    def __init__(self, renderer: CssSubtitleRenderer):
        self._renderer = renderer

    def generate(self, document: Document) -> None:
        """
        Adds the MoviePy ImageClips for each word in the document received.
        """

        for segment in document.segments:
            for line in segment.lines:
                self.__generate_word_clips_for_line(
                    line,
                    ElementState.LINE_NOT_NARRATED_YET,
                    ElementState.WORD_NOT_NARRATED_YET,
                    lambda _: segment.time.start,
                    lambda _: line.time.start
                )
                
                self.__generate_word_clips_for_line(
                    line,
                    ElementState.LINE_BEING_NARRATED,
                    ElementState.WORD_NOT_NARRATED_YET,
                    lambda _: line.time.start,
                    lambda word: word.time.start
                )

                self.__generate_word_clips_for_line(
                    line,
                    ElementState.LINE_BEING_NARRATED,
                    ElementState.WORD_BEING_NARRATED,
                    lambda word: word.time.start,
                    lambda word: word.time.end
                )

                self.__generate_word_clips_for_line(
                    line,
                    ElementState.LINE_BEING_NARRATED,
                    ElementState.WORD_ALREADY_NARRATED,
                    lambda word: word.time.end,
                    lambda _: line.time.end
                )

                self.__generate_word_clips_for_line(
                    line,
                    ElementState.LINE_ALREADY_NARRATED,
                    ElementState.WORD_ALREADY_NARRATED,
                    lambda _: line.time.end,
                    lambda _: segment.time.end
                )

    def __generate_word_clips_for_line(
            self,
            line: Line,
            line_state: ElementState,
            word_state: ElementState,
            start_fn: Callable[[Word], float],
            end_fn: Callable[[Word], float]
        ) -> None:
        self._renderer.open_line(line, line_state)
        for i, word in enumerate(line.words):
            word_clip = self.__create_word_clip(i, word, word_state, start_fn(word), end_fn(word))
            if word_clip:
                word_clip.states = [line_state, word_state]
                word.clips.add(word_clip)
        self._renderer.close_line()

    def __create_word_clip(self, word_index: int, word: Word, word_state: ElementState, start: float, end: float) -> Optional[WordClip]:
        from moviepy.editor import ImageClip
        import numpy as np
        
        if end <= start:
            return None
    
        image = self._renderer.render_word(word_index, word, word_state)
        if not image:
            return None
        
        clip: ImageClip = (
            ImageClip(np.array(image))
            .set_start(start)
            .set_duration(end - start)
        )
        word_clip = WordClip(moviepy_clip=clip, _parent=word)
        word_clip.layout.size.width = image.width
        word_clip.layout.size.height = image.height
        return word_clip
