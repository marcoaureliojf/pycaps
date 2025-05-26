from .base_segmenter import BaseSegmenter
from typing import List
from ..models import TranscriptionSegment, WordData

class LimitByCharsSegmenter(BaseSegmenter):
    """
    A segmenter that limits the number of characters in each segment.
    It will divide each segment received into chunks of a maximum of `limit` characters.
    If the last chunk generated has less than `limit` characters, it will not use the next segment for completion.

    For example,
    limit = 10
    segment 1: "Hello world"
    segment 2: "This is a test"

    The segmenter will return:
    segment 1: "Hello"
    segment 2: "world"
    segment 3: "This is a"
    segment 4: "test"
    """
    def __init__(self, max_limit: int, min_limit: int = 0):
        '''
        max_limit: the maximum number of characters in each segment
        min_limit: the minimum number of characters in each segment. 
        If the segment has less than min_limit characters, the previous segment will be used for completion, ignoring the max_limit.
        '''
        self.max_limit = max_limit
        self.min_limit = min_limit

    def map(self, segments: List[TranscriptionSegment]) -> List[TranscriptionSegment]:
        new_segments = []
        segment_index = 0
        word_index = 0
        while segment_index < len(segments):
            segment = segments[segment_index]
            word_end_index = self.__get_word_end_index(word_index, segment.words)
            current_words = segment.words[word_index:word_end_index]
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
            word_index = word_end_index

        return new_segments
    
    def __get_word_end_index(self, start_index: int, words: List[WordData]) -> int:
        current_index = start_index
        chars_count = 0
        while current_index < len(words):
            current_word = words[current_index]
            if chars_count + len(current_word.text) > self.max_limit:
                break
            
            chars_count += len(current_word.text)
            current_index += 1
        
        remaning_chars_count = sum([len(word.text) for word in words[current_index:]])
        if remaning_chars_count < self.min_limit:
            return len(words)

        return current_index
