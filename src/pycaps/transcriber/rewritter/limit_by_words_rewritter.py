from .base_segment_rewritter import BaseSegmentRewritter
from pycaps.common import Document, Segment, Line, TimeFragment

class LimitByWordsRewritter(BaseSegmentRewritter):
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

    def rewrite(self, document: Document) -> None:
        new_segments = []
        segment_index = 0
        word_index = 0
        segments = document.segments
        while segment_index < len(segments):
            segment = segments[segment_index]
            segment_words = segment.lines[0].words
            current_words = segment_words[word_index:word_index + self.limit]
            if len(current_words) == 0:
                segment_index += 1
                word_index = 0
                continue

            segment_time = TimeFragment(start=current_words[0].time.start, end=current_words[-1].time.end)
            new_segment = Segment(time=segment_time, parent=document)
            new_line = Line(words=current_words, time=segment_time, parent=new_segment)
            for word in current_words: word.parent = new_line
            new_segment.lines.append(new_line)
            new_segments.append(new_segment)
            word_index += self.limit

        document.segments = new_segment