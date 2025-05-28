from abc import ABC, abstractmethod
from .tag import Tag
from typing import List

class TagCondition(ABC):
    @abstractmethod
    def evaluate(self, tags: List[Tag]) -> bool:
        pass

class TagHasCondition(TagCondition):
    def __init__(self, tag: Tag):
        self.tag = tag

    def evaluate(self, tags: List[Tag]) -> bool:
        return any(self.tag.name == t.name for t in tags)

class TagNotCondition(TagCondition):
    def __init__(self, condition: TagCondition):
        self.condition = condition
    
    def evaluate(self, tags: List[Tag]) -> bool:
        return not self.condition.evaluate(tags)

class TagAndCondition(TagCondition):
    def __init__(self, *conditions: TagCondition):
        self.conditions = list(conditions)
    
    def evaluate(self, tags: List[Tag]) -> bool:
        return all(condition.evaluate(tags) for condition in self.conditions)

class TagOrCondition(TagCondition):
    def __init__(self, *conditions: TagCondition):
        self.conditions = list(conditions)
    
    def evaluate(self, tags: List[Tag]) -> bool:
        return any(condition.evaluate(tags) for condition in self.conditions)
    
class TagConditionFactory:
    @staticmethod
    def HAS(tag: Tag) -> TagCondition:
        return TagHasCondition(tag)
    
    @staticmethod
    def NOT(condition: 'TagCondition|Tag') -> TagCondition:
        if isinstance(condition, Tag):
            return TagHasCondition(condition)
        return TagNotCondition(condition)

    @staticmethod
    def AND(*conditions: 'TagCondition|Tag') -> TagCondition:
        conditions = [condition if isinstance(condition, TagCondition) else TagHasCondition(condition) for condition in conditions]
        return TagAndCondition(*conditions)
    
    @staticmethod
    def OR(*conditions: 'TagCondition|Tag') -> TagCondition:
        conditions = [condition if isinstance(condition, TagCondition) else TagHasCondition(condition) for condition in conditions]
        return TagOrCondition(*conditions)
