from ..tagger.models import Document
from .animation_config import AnimationConfig, AnimationType
from .animation import BaseAnimation, FadeInAnimationEffect, FadeOutAnimationEffect, BounceInAnimationEffect, SlideInFromLeftAnimationEffect
from typing import Dict, Callable, Optional
from ..tag.tag_condition import TagCondition
from ..element.models import ElementType, EventType
from ..element.word_state_selector import WordStateSelector

class ElementAnimator:
    def __init__(
            self,
            config: AnimationConfig,
            what: ElementType = ElementType.WORD,
            when: EventType = EventType.STARTS_NARRATION,
            tag_condition: Optional[TagCondition] = None,
        ) -> None:
        """
        You can:
        - Provide what (word, line, segment) and when (starts narration, ends narration)
        - Optionally, provide a tag_condition to filter the elements (for example, only first line for segment)

        If no filter is provided, the default is to animate all words when their narration starts.
        """
        self._config = config
        self._what = what
        self._when = when

        self.selector = WordStateSelector().filter_by_time(when, what, self._config.duration, self._config.delay)
        if tag_condition:
            self.selector = self.selector.filter_by_tag(tag_condition)

    def animate(self, document: Document) -> None:
        target_word_states = self.selector.select(document)
        animation = self.__get_animation()
        animation.run(target_word_states)

    def __get_animation(self) -> BaseAnimation:
        return self.__get_registered_animations()[self._config.type]()

    def __get_registered_animations(self) -> Dict[AnimationType, Callable[[AnimationConfig], BaseAnimation]]:
        return {
            AnimationType.FADE_IN: lambda: FadeInAnimationEffect(self._config, self._what, self._when),
            AnimationType.FADE_OUT: lambda: FadeOutAnimationEffect(self._config, self._what, self._when),
            AnimationType.BOUNCE_IN: lambda: BounceInAnimationEffect(self._config, self._what, self._when),
            AnimationType.SLIDE_IN: lambda: SlideInFromLeftAnimationEffect(self._config, self._what, self._when),
        }
