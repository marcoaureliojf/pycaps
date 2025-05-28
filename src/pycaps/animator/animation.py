from typing import List, Tuple
from ..tagger.models import WordState, Word, ElementLayout
import numpy as np
from .animation_config import AnimationConfig

class BaseAnimation:
    def __init__(self, config: AnimationConfig) -> None:
        self.config = config

    def _get_position_in_time(self, word: Word, t: float, offset: float) -> Tuple[float, float]:
        '''
        Returns the position of the word in the time t, with the offset of the segment.
        You can use t + offset to get a synchronized animation between the words of the same segment.
        '''
        return word.layout.position.x, word.layout.position.y

    def run(self, word_states: List[WordState]) -> None:
        for state in word_states:
            segment = state.get_segment()
            word = state.get_word()
            # Important: note that the position of the clip is updated but the layout.x and layout.y are not updated
            #  We decided to keep the original position, since the word will have different clips in different positions (being narrated, not narrated, etc.)
            #  So, the position set in word.layout.position, is the original position for the word, before animating
            offset_time = state.clip.start - segment.time.start
            state.clip = state.clip.set_position(
                lambda t, word=word, offset_time=offset_time: self._get_position_in_time(word, t, offset_time)
            )

class FadeInAnimationEffect(BaseAnimation):
    def run(self, word_states: List[WordState]) -> None:
        for word_state in word_states:
            word_state.clip = word_state.clip.crossfadein(self.config.duration)

class FadeOutAnimationEffect(BaseAnimation):
    def run(self, word_states: List[WordState]) -> None:
        for word_state in word_states:
            word_state.clip = word_state.clip.crossfadeout(self.config.duration)

class BounceInAnimationEffect(BaseAnimation):
    def _get_position_in_time(self, word: Word, t: float, offset: float) -> Tuple[float, float]:
        pos = word.layout.position
        if t < 0:
            return pos.x, pos.y + 50
        elif t < 0.3:
            y = pos.y + 50 * (1 - t / 0.3)**2
        else:
            y = pos.y
        return pos.x, y

class SlideInFromLeftAnimationEffect(BaseAnimation):
    def _get_position_in_time(self, word: Word, t: float, offset: float) -> Tuple[float, float]:
        pos = word.layout.position
        if t < 0:
            return pos.x - 100, pos.y
        elif t < 0.3:
            x = pos.x - 100 + (t / 0.3) * 100
        else:
            x = pos.x
        return x, pos.y

class WaveAnimationEffect(BaseAnimation):
    def _get_position_in_time(self, word: Word, t: float, offset: float) -> Tuple[float, float]:
        wave_amplitude = 7
        wave_period = 3
        y_offset = wave_amplitude * np.sin(2 * np.pi * t / wave_period)
        return word.layout.position.x, word.layout.position.y + y_offset
