from ..tag.tag_condition import TagCondition
from ..tag.tag_condition import TagConditionFactory as TCF
from .builtin_tag import BuiltinTag
from .tag import Tag

class BuiltinTagCondition:
    @staticmethod
    def when_segment_appears() -> TagCondition:
        return TCF.OR(
            TCF.AND(BuiltinTag.FIRST_WORD_IN_SEGMENT, BuiltinTag.WORD_BEING_NARRATED),
            BuiltinTag.WORD_NOT_NARRATED_YET
        )
    
    @staticmethod
    def with_tag(tag: Tag) -> TagCondition:
        return TCF.HAS(tag)