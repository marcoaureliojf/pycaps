from ..base_animation import BaseAnimation
from ...tagger.models import WordClip
from typing import Tuple, Optional
from ...element import ElementType, EventType
from ...tag.tag_condition import TagCondition
from ..animation_config import SlideInConfig

class SlideIn(BaseAnimation):

    def __init__(
            self,
            config: SlideInConfig,
            what: ElementType = ElementType.WORD,
            when: EventType = EventType.ON_NARRATION_STARTS,
            tag_condition: Optional[TagCondition] = None,
        ) -> None:
        super().__init__(config, what, when, tag_condition)
        self._config: SlideInConfig = config

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        def get_position(t: float) -> Tuple[float, float]:
            if self._config.direction == "left":
                pos = clip.layout.position
                return pos.x - 100 + t * 100, pos.y
            elif self._config.direction == "right":
                pos = clip.layout.position
                return pos.x + 100 - t * 100, pos.y
            elif self._config.direction == "up":
                pos = clip.layout.position
                return pos.x, pos.y - 100 + t * 100
            elif self._config.direction == "down":
                pos = clip.layout.position
                return pos.x, pos.y + 100 - t * 100
            else:
                raise ValueError(f"Invalid direction: {self._config.direction}")

        self._apply_position(clip, offset, get_position)
