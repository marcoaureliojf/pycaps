from .base_segment_rewritter import BaseSegmentRewritter
from typing import List
from ..tagger.models import Document, Segment, Line, Word, TimeFragment

class LimitByCharsRewritter(BaseSegmentRewritter):
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
    def __init__(self, max_limit: int, min_limit: int = 0, avoid_finishing_segment_with_word_shorter_than: int = 4):
        '''
        max_limit: the maximum number of characters in each segment
        min_limit: the minimum number of characters in each segment. 
            If the segment has less than min_limit characters, the previous segment will be used for completion, ignoring the max_limit.
        avoid_finishing_segment_with_word_shorter_than: if the last word in the segment is shorter than this value, the segment will be completed with the next available word.
            This is useful to avoid finishing a segment in an unnatural way.
            If the value is 0, it will not be used.
        '''
        self.max_limit = max_limit
        self.min_limit = min_limit
        self.avoid_finishing_segment_with_word_shorter_than = avoid_finishing_segment_with_word_shorter_than

    def rewrite(self, document: Document) -> None:
        new_segments = []
        segment_index = 0
        word_index = 0
        segments = document.segments
        while segment_index < len(segments):
            segment = segments[segment_index]
            segment_words = segment.lines[0].words
            word_end_index = self.__get_word_end_index(word_index, segment_words)
            current_words = segment_words[word_index:word_end_index]
            if len(current_words) == 0:
                segment_index += 1
                word_index = 0
                continue

            segment_time = TimeFragment(start=current_words[0].time.start, end=current_words[-1].time.end)
            new_segment = Segment(
                lines=[Line(words=current_words, time=segment_time)],
                time=segment_time
            )
            new_segments.append(new_segment)
            word_index = word_end_index

        document.segments = new_segments
    
    def __get_word_end_index(self, start_index: int, words: List[Word]) -> int:
        current_index = start_index
        chars_count = 0
        while current_index < len(words):
            current_word = words[current_index]
            if chars_count + len(current_word.text) > self.max_limit:
                break
            
            chars_count += len(current_word.text)
            current_index += 1
        
        if self.avoid_finishing_segment_with_word_shorter_than > 0:
            last_word = words[current_index - 1]
            while current_index < len(words) and len(last_word.text) < self.avoid_finishing_segment_with_word_shorter_than:
                current_index += 1
                last_word = words[current_index - 1]

        remaning_chars_count = sum([len(word.text) for word in words[current_index:]])
        if remaning_chars_count < self.min_limit:
            return len(words)

        return current_index
