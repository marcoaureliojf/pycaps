from ..tagger.models import Document, WordState
from .animation_config import AnimationConfig, AnimationType
from .animation import BaseAnimation, FadeInAnimationEffect, FadeOutAnimationEffect, BounceInAnimationEffect, SlideInFromLeftAnimationEffect
from typing import Dict, Callable, List
from ..utils.word_state_finder import WordStateFinder
from ..css.css_class import CssClass

class ElementAnimator:
    '''
    Animates elements of the document based on the tags.
    The clips animated are those that match all the tags received in the constructor.
    '''
    def __init__(self, tags: List[str], config: AnimationConfig) -> None:
        self._tags = tags
        self._config = config

    def animate(self, document: Document) -> None:
        target_word_states = WordStateFinder.find_word_states_matching_all_tags(document, self._tags)
        animation = self.__get_animation(self._config.type)
        animation.run(target_word_states)

    def __get_animation(self, type: AnimationType) -> BaseAnimation:
        return self.__get_registered_animations()[type](self._config)

    def __get_registered_animations(self) -> Dict[AnimationType, Callable[[AnimationConfig], BaseAnimation]]:
        return {
            AnimationType.FADE_IN: lambda c: FadeInAnimationEffect(c),
            AnimationType.FADE_OUT: lambda c: FadeOutAnimationEffect(c),
            AnimationType.BOUNCE_IN: lambda c: BounceInAnimationEffect(c),
            AnimationType.SLIDE_IN: lambda c: SlideInFromLeftAnimationEffect(c),
        }
