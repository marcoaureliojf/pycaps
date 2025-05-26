from .base_segmenter import BaseSegmenter
from typing import List
from ..models import TranscriptionSegment

class LimitByWordsSegmenter(BaseSegmenter):
    """
    A segmenter that limits the number of words in each segment.
    It will divide each segment received into chunks of a maximum of `limit` words.
    If the last chunk generated has less than `limit` words, it will not use the next segment for completion.

    For example,
    limit = 3
    segment 1: "Hello world"
    segment 2: "This is a test"

    The segmenter will return:
    segment 1: "Hello world"
    segment 2: "This is a"
    segment 3: "test"
    """
    def __init__(self, limit: int):
        self.limit = limit

    def map(self, segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        new_segments = []
        segment_index = 0
        word_index = 0
        while segment_index < len(segments):
            segment = segments[segment_index]
            current_words = segment.words[word_index:word_index + self.limit]
            if len(current_words) == 0:
                segment_index += 1
                word_index = 0
                continue

            new_segment = TranscriptionSegment(
                text=" ".join([word.text for word in current_words]),
                start=current_words[0].start,
                end=current_words[-1].end,
                words=current_words
            )
            new_segments.append(new_segment)
            word_index += self.limit

        return new_segments
