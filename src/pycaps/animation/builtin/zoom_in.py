from ..base_animation import BaseAnimation
from ...tagger.models import WordClip
from typing import Tuple
from ...utils.layout_utils import LayoutUtils

class ZoomIn(BaseAnimation):

    def _apply_animation(self, clip: WordClip, offset: float) -> None:
        group_center = LayoutUtils.get_clip_container_center(clip, self._what)
        word_final_center = (
            clip.layout.position.x + clip.layout.size.width / 2,
            clip.layout.position.y + clip.layout.size.height / 2
        )
        relative_pos_vector = (
            word_final_center[0] - group_center[0],
            word_final_center[1] - group_center[1]
        )

        def get_size_factor(t: float) -> float:
            return 0.8 + 0.2 * (t**0.5)

        def get_position(t: float) -> Tuple[float, float]:
            progress = get_size_factor(t)
            
            current_width = clip.layout.size.width * progress
            current_height = clip.layout.size.height * progress

            current_center_x = group_center[0] + (relative_pos_vector[0] * progress)
            current_center_y = group_center[1] + (relative_pos_vector[1] * progress)

            final_x = current_center_x - (current_width / 2)
            final_y = current_center_y - (current_height / 2)
            
            return (final_x, final_y)

        self._apply_opacity(clip, offset, lambda t: t)
        self._apply_position(clip, offset, get_position)
        self._apply_size(clip, offset, get_size_factor)
