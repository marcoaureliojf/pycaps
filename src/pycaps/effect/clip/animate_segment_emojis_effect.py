from .clip_effect import ClipEffect
from pycaps.common import Document, WordClip
from pycaps.tag import TagConditionFactory, BuiltinTag
import os

class AnimateSegmentEmojisEffect(ClipEffect):

    ANIMATED_EMOJIS_PATH = os.path.join(os.path.dirname(__file__), "emojis")
    
    def run(self, document: Document) -> None:
        tag_condition = TagConditionFactory.HAS(BuiltinTag.EMOJI_FOR_SEGMENT)
        for word in document.get_words():
            if not tag_condition.evaluate(word.tags):
                continue
            for clip in word.clips:
                self.__animate_emoji_if_possible(clip)

    def __animate_emoji_if_possible(self, clip: WordClip) -> None:
        from moviepy.editor import VideoFileClip

        emoji = clip.get_word().text
        unicode_hex = self._emoji_to_unicode_hex(emoji)
        animated_emoji_path = os.path.join(self.ANIMATED_EMOJIS_PATH, f"{unicode_hex}.mov")
        if not os.path.exists(animated_emoji_path):
            return
    
        clip.moviepy_clip = (
            VideoFileClip(animated_emoji_path, has_mask=True)
            .resize(height=clip.layout.size.height)
            .set_duration(clip.moviepy_clip.duration)
            .set_start(clip.moviepy_clip.start)
            .set_position((clip.layout.position.x, clip.layout.position.y))
        )

    def _emoji_to_unicode_hex(self, emoji: str) -> str:
        codepoints = [f"{ord(char):x}" for char in emoji]
        return "_".join(codepoints)
