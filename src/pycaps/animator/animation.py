from typing import List, Tuple
from ..tagger.models import WordState, Word
import numpy as np
from .animation_config import AnimationConfig
from ..element import EventType, ElementType

class BaseAnimation:
    def __init__(self, config: AnimationConfig, element_type: ElementType, event_type: EventType) -> None:
        self._config = config
        self._element_type = element_type
        self._event_type = event_type

    def _get_position_in_time(self, word: Word, t: float) -> Tuple[float, float]:
        return word.layout.position.x, word.layout.position.y

    def run(self, word_states: List[WordState]) -> None:
        for state in word_states:
            # Important: note that the position of the clip is updated but the layout.x and layout.y are not updated
            #  We decided to keep the original position, since the word will have different clips in different positions (being narrated, not narrated, etc.)
            #  So, the position set in word.layout.position, is the original position for the word, before animating

            if self._event_type == EventType.STARTS_NARRATION:
                self.__run_for_starts_narration(state)
            elif self._event_type == EventType.ENDS_NARRATION:
                self.__run_for_ends_narration(state)
    
    def __run_for_starts_narration(self, state: WordState) -> None:
        start_time = 0
        if self._element_type == ElementType.LINE:
            start_time = state.get_line().time.start
        elif self._element_type == ElementType.SEGMENT:
            start_time = state.get_segment().time.start
        offset = state.clip.start - start_time - self._config.delay
        
        word = state.get_word()
        state.clip = state.clip.set_position(
            lambda t, offset=offset: self._get_position_in_time(word, t+offset) if t+offset >= 0 else (word.layout.position.x, word.layout.position.y)
        )

    def __run_for_ends_narration(self, state: WordState) -> None:
        end_time = 0
        if self._element_type == ElementType.LINE:
            end_time = state.get_line().time.end
        elif self._element_type == ElementType.SEGMENT:
            end_time = state.get_segment().time.end
        offset = end_time - self._config.duration - self._config.delay - state.clip.start

        word = state.get_word()
        state.clip = state.clip.set_position(
            lambda t, offset=offset: self._get_position_in_time(word, t-offset) if t-offset >= 0 else (word.layout.position.x, word.layout.position.y)
        )

class FadeInAnimationEffect(BaseAnimation):
    def run(self, word_states: List[WordState]) -> None:
        for word_state in word_states:
            word_state.clip = word_state.clip.crossfadein(self._config.duration)

class FadeOutAnimationEffect(BaseAnimation):
    def run(self, word_states: List[WordState]) -> None:
        for word_state in word_states:
            word_state.clip = word_state.clip.crossfadeout(self._config.duration)

class BounceInAnimationEffect(BaseAnimation):
    def _get_position_in_time(self, word: Word, t: float) -> Tuple[float, float]:
        pos = word.layout.position
        if t < 0:
            return pos.x, pos.y + 50
        elif t < 0.3:
            y = pos.y + 50 * (1 - t / 0.3)**2
        else:
            y = pos.y
        return pos.x, y

class SlideInFromLeftAnimationEffect(BaseAnimation):
    def _get_position_in_time(self, word: Word, t: float) -> Tuple[float, float]:
        pos = word.layout.position
        if t < 0:
            return pos.x - 100, pos.y
        elif t < 0.3:
            x = pos.x - 100 + (t / 0.3) * 100
        else:
            x = pos.x
        return x, pos.y

class WaveAnimationEffect(BaseAnimation):
    def _get_position_in_time(self, word: Word, t: float) -> Tuple[float, float]:
        wave_amplitude = 7
        wave_period = 3
        y_offset = wave_amplitude * np.sin(2 * np.pi * t / wave_period)
        return word.layout.position.x, word.layout.position.y + y_offset
