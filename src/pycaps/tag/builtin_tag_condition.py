from ..tag.tag_condition import TagCondition
from ..tag.tag_condition import TagConditionFactory as TCF
from .builtin_tag import BuiltinTag
from .tag import Tag

# TODO: we should review if this is actually needed
class BuiltinTagCondition:

    @staticmethod
    def with_tag(tag: Tag) -> TagCondition:
        return TCF.HAS(tag)