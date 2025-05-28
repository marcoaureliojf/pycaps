from enum import Enum

# TODO: rename to BuiltinWordTag
class CssClass(Enum):
    WORD = "word"
    WORD_BEING_NARRATED = "word-being-narrated"
    WORD_NOT_NARRATED_YET = "word-not-narrated-yet"
    WORD_ALREADY_NARRATED = "word-already-narrated"
