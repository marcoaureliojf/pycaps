from typing import List
from ..tagger.models import WordClip
from ..tag.tag_condition import TagCondition

class TagBasedSelector:
    def __init__(self, tag_condition: TagCondition):
        """
        Filters WordClips based on the tags of their associated Word.
        Keeps only WordClips where the parent Word matches the tag condition.
        """
        self._tag_condition = tag_condition

    def select(self, clips: List[WordClip]) -> List[WordClip]:
        return [
            clip for clip in clips
            if self._tag_condition.evaluate(clip.get_word().tags)
        ]
