from .tag import Tag

# TODO: tenemos que dividir esto en tres conceptos: 1. default class (word), states (los 3 mencionados), tags (sirven para identificar un elemento)
class BuiltinTag:
    WORD = Tag("word")
    # TODO: estos no deberían ser tags, dado que son estados. No deberían usarse para seleccionar palabras.
    WORD_BEING_NARRATED = Tag("word-being-narrated")
    WORD_NOT_NARRATED_YET = Tag("word-not-narrated-yet")
    WORD_ALREADY_NARRATED = Tag("word-already-narrated")

    FIRST_WORD_IN_DOCUMENT = Tag("first-word-in-document")
    FIRST_WORD_IN_SEGMENT = Tag("first-word-in-segment")
    FIRST_WORD_IN_LINE = Tag("first-word-in-line")
    LAST_WORD_IN_DOCUMENT = Tag("last-word-in-document")
    LAST_WORD_IN_SEGMENT = Tag("last-word-in-segment")
    LAST_WORD_IN_LINE = Tag("last-word-in-line")

    FIRST_LINE_IN_DOCUMENT = Tag("first-line-in-document")
    FIRST_LINE_IN_SEGMENT = Tag("first-line-in-segment")
    LAST_LINE_IN_DOCUMENT = Tag("last-line-in-document")
    LAST_LINE_IN_SEGMENT = Tag("last-line-in-segment")

    FIRST_SEGMENT_IN_DOCUMENT = Tag("first-segment-in-document")
    LAST_SEGMENT_IN_DOCUMENT = Tag("last-segment-in-document")
