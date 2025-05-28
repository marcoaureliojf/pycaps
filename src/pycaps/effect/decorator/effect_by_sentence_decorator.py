from ..base_effect_generator import BaseEffectGenerator
from typing import List
from ...models import TranscriptionSegment
from ...layout.models import SegmentClipData
from moviepy.editor import VideoClip
from ...css.css_subtitle_renderer import CssSubtitleRenderer

class FirstSegmentPerSentenceEffectDecorator(BaseEffectGenerator):
    '''
    This effect decorator applies a special effect only to the beginning of each sentence.
    For the rest of the sentence, it will apply a different effect.
    The supported sentence delimiters are: '.', '?', '!', '...'
    '''

    SENTENCE_DELIMITERS = ['.', '?', '!', '...']

    def __init__(self, effect_for_first_segment_of_sentence: BaseEffectGenerator, effect_for_remaining_segments: BaseEffectGenerator, renderer: CssSubtitleRenderer):
        super().__init__(renderer)
        self.effect_for_first_segment_of_sentence = effect_for_first_segment_of_sentence
        self.effect_for_remaining_segments = effect_for_remaining_segments

    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[SegmentClipData]:
        print("Generating effect by sentence...")
        is_sentence_start = True
        sentence_start_segments = []
        remaining_segments = []
        for i in range(len(segments)):
            segment_transcription = segments[i]
            if is_sentence_start:
                sentence_start_segments.append(segment_transcription)
            else:
                remaining_segments.append(segment_transcription)

            is_sentence_start = segment_transcription.text.endswith(tuple(self.SENTENCE_DELIMITERS))

        return self.effect_for_first_segment_of_sentence.generate(sentence_start_segments, video_clip) + \
               self.effect_for_remaining_segments.generate(remaining_segments, video_clip)
