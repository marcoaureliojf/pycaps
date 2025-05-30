from typing import List, Tuple, Callable, Dict
from ..tagger.models import WordState, Word
import numpy as np
from .animation_config import AnimationConfig
from ..element import EventType, ElementType
from moviepy.editor import VideoClip

class BaseAnimation:
    def __init__(self, config: AnimationConfig, element_type: ElementType, event_type: EventType) -> None:
        self._config = config
        self._element_type = element_type
        self._event_type = event_type

    def _apply_animation(self, state: WordState, offset: float) -> None:
        pass

    def run(self, word_states: List[WordState]) -> None:
        for state in word_states:
            # Important: note that the position of the clip is updated but the layout.x and layout.y are not updated
            #  We decided to keep the original position, since the word will have different clips in different positions (being narrated, not narrated, etc.)
            #  So, the position set in word.layout.position, is the original position for the word, before animating

            self._apply_animation(state, self.__get_time_offset(state))

    def _apply_position(self, state: WordState, offset: float, get_position_fn: Callable[[float], Tuple[float, float]]) -> None:
        start_pos = state.get_word().layout.position
        state.clip = state.clip.set_position(lambda t: get_position_fn(t + offset) if t + offset >= 0 else (start_pos.x, start_pos.y))

    def _apply_opacity(self, state: WordState, offset: float, get_opacity_fn: Callable[[float], float]) -> None:
        def fl(gf, t):
            # please, note that gf(t) is clip.get_frame(t), which was previously called (in blit_on) and memoized
            # so, getting it shouldn't be a performance issue
            # this function will be called when clip.mask.get_frame(t) is called
            clip_frame = gf(t)
            if t + offset < 0:
                return clip_frame
            return clip_frame * get_opacity_fn(t + offset)

        if state.clip.mask is None:
            state.clip = state.clip.add_mask()

        state.clip = state.clip.fl(fl, apply_to=['mask'])

    def __get_time_offset(self, state: WordState) -> float:
        if self._event_type == EventType.ON_NARRATION_STARTS:
            return self.__get_on_start_offset(state)
        elif self._event_type == EventType.ON_NARRATION_ENDS:
            return self.__get_on_end_offset(state)
    
    def __get_on_start_offset(self, state: WordState) -> float:
        start_time = 0
        if self._element_type == ElementType.LINE:
            start_time = state.get_line().time.start
        elif self._element_type == ElementType.SEGMENT:
            start_time = state.get_segment().time.start

        return state.clip.start - start_time - self._config.delay

    def __get_on_end_offset(self, state: WordState) -> float:
        end_time = 0
        if self._element_type == ElementType.LINE:
            end_time = state.get_line().time.end
        elif self._element_type == ElementType.SEGMENT:
            end_time = state.get_segment().time.end
        return -(end_time - self._config.duration - self._config.delay - state.clip.start)

class FadeInAnimationEffect(BaseAnimation):
    def _apply_animation(self, state: WordState, offset: float) -> None:
        self._apply_opacity(state, offset, lambda t: min(1, t / self._config.duration))

class FadeOutAnimationEffect(BaseAnimation):
    def _apply_animation(self, state: WordState, offset: float) -> None:
        self._apply_opacity(state, offset, lambda t: max(0, 1 - t / self._config.duration))

class BounceInAnimationEffect(BaseAnimation):
    def _apply_animation(self, state: WordState, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            pos = state.get_word().layout.position
            if t < 0:
                return pos.x, pos.y
            elif t < self._config.duration:
                y = pos.y + 50 * (1 - t / self._config.duration)**2 # TODO: use ease function
            else:
                y = pos.y
            return pos.x, y
        
        self._apply_position(state, offset, get_position)

class SlideInFromLeftAnimationEffect(BaseAnimation):
    def _apply_animation(self, state: WordState, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            pos = state.get_word().layout.position
            if t < 0:
                return pos.x - 100, pos.y
            elif t < self._config.duration:
                x = pos.x - 100 + (t / self._config.duration) * 100
            else:
                x = pos.x
            return x, pos.y
        
        self._apply_position(state, offset, get_position)

class WaveAnimationEffect(BaseAnimation):
    def _apply_animation(self, state: WordState, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            wave_amplitude = 7
            wave_period = 3
            y_offset = wave_amplitude * np.sin(2 * np.pi * t / wave_period)
            return state.get_word().layout.position.x, state.get_word().layout.position.y + y_offset
        
        self._apply_position(state, offset, get_position)
