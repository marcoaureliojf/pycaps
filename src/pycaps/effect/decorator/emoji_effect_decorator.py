from ..base_effect_generator import BaseEffectGenerator
from ...models import TranscriptionSegment, EmojiEffectOptions, EmojiAlign
from typing import List, Optional
import random
from moviepy.editor import VideoClip, ImageClip
from ...renderer.base_subtitle_renderer import BaseSubtitleRenderer
import numpy as np
from PIL import Image
import io
from ...utils.alignment_utils import AlignmentUtils
from ...layout.models import SegmentClipData, LineClipData, WordClipData, WordData, ElementLayout
from ...utils.layout_utils import LayoutUtils
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# TODO: instead of using a LLM to get the emoji, we could use embeddings to get the most similar emoji to the segment text
class EmojiEffectDecorator(BaseEffectGenerator):
    '''
    Decorator that adds a context emoji for each segment.
    The chance to apply the effect is defined by the chance_to_apply parameter.
    The emoji is selected using a LLM to understand the context.
    '''

    EMOJI_STYLE_KEY = "emoji"

    def __init__(self, effect_generator: BaseEffectGenerator, renderer: BaseSubtitleRenderer, options: EmojiEffectOptions):
        self.effect_generator = effect_generator
        self.renderer = renderer
        self.options = options
        self.emojies_frequencies = {}
        self.last_emoji = None
        self.consecutive_segments_with_emoji = 0
        self.renderer.register_style(self.EMOJI_STYLE_KEY, self.options.css_rules)

    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[SegmentClipData]:
        effect_clips_data = self.effect_generator.generate(segments, video_clip)
        print("Generating emojies for segments...")
        all_segment_clips: List[SegmentClipData] = []

        for segment_data in effect_clips_data:
            if random.random() > self.options.chance_to_apply:
                self.consecutive_segments_with_emoji = 0
                all_segment_clips.append(segment_data)
                continue

            # TODO: validate it is a valid emoji before using it (only needed if we use the LLM to get the emoji)
            emoji = self.__get_relevant_emoji(segment_data)
            if emoji is None:
                self.consecutive_segments_with_emoji = 0
                all_segment_clips.append(segment_data)
                continue
            
            # TODO: this assumes that the emoji will be in a new line
            #  So, it only can be located below or over the segment text (but not at the left or right side)
            emoji_clip: VideoClip = self.__generate_emoji_clip(emoji, segment_data)
            emoji_layout = self.__get_emoji_layout(video_clip, emoji_clip, segment_data.layout)
            emoji_clip = emoji_clip.set_position((emoji_layout.x, emoji_layout.y))
            word_data = WordData(text=emoji, start=emoji_clip.start, end=emoji_clip.end)
            word_clip_data = WordClipData(word=word_data, layout=emoji_layout, clips=[emoji_clip])
            line_clip_data = LineClipData(words=[word_clip_data], layout=emoji_layout)
            segment_data.lines.append(line_clip_data)
            new_layout = LayoutUtils.calculate_lines_layout(segment_data.lines)
            new_segment_data = SegmentClipData(lines=segment_data.lines, layout=new_layout, start=segment_data.start, end=segment_data.end)
            all_segment_clips.append(new_segment_data)

        return all_segment_clips
    
    def __get_relevant_emoji(self, segment: SegmentClipData) -> Optional[str]:
        # return random.choice(["🎶", "🎵", "🎼", "🎹", "🎺", "🎷", "🎸", "🎻", "🎺", "🎷", "🎸", "🎻"])

        if self.options.ignore_segments_with_duration_less_than > 0 and \
            segment.end - segment.start < self.options.ignore_segments_with_duration_less_than:
            return None
        
        if self.options.max_consecutive_segments_with_emoji > 0 and \
            self.consecutive_segments_with_emoji >= self.options.max_consecutive_segments_with_emoji:
            return None

        text = segment.get_text()
        response = client.responses.create(
            model="gpt-4.1-nano",
            input=f"""
            Given the following subtitle text, decide whether it meaningfully conveys an emotion, action, or idea that can be represented with an emoji.
            If it does, respond with a single, appropriate emoji only.
            If it does not (e.g., it is too vague, neutral, or generic), respond only with the word "None".
            Subtitle: "{text}"
            """
        )
        text_response = response.output_text
        if text_response == "None":
            return None
        
        emoji_frequency = self.emojies_frequencies.get(text_response, 0)
        if self.options.max_uses_of_each_emoji > 0 and emoji_frequency >= self.options.max_uses_of_each_emoji:
            return None
        
        if self.last_emoji is not None and self.last_emoji == text_response:
            return None

        self.emojies_frequencies[text_response] = emoji_frequency + 1
        self.consecutive_segments_with_emoji += 1
        self.last_emoji = text_response
        return text_response


    def __generate_emoji_clip(self, emoji: str, segment: SegmentClipData) -> VideoClip:
        emoji_image = self.renderer.render(emoji, self.EMOJI_STYLE_KEY)
        pil_image = Image.open(io.BytesIO(emoji_image.image)).convert("RGBA")
        np_image = np.array(pil_image)
        start_time = segment.start + self.options.start_delay
        end_time = segment.end - self.options.hide_before_end
        return (
            ImageClip(np_image)
            .set_start(start_time)
            .set_duration(end_time - start_time)
            .crossfadein(self.options.fade_in_duration)
            .crossfadeout(self.options.fade_out_duration)
        )
    
    def __get_emoji_layout(self, container_clip: VideoClip, emoji_clip: VideoClip, segment_layout: ElementLayout) -> ElementLayout:
        horizontal_center = (container_clip.w - emoji_clip.w) / 2.0
        vertical_position = self.__get_vertical_position(segment_layout, emoji_clip)
        return ElementLayout(x=horizontal_center, y=vertical_position, width=emoji_clip.w, height=emoji_clip.h)
    
    def __get_vertical_position(self, segment_layout: ElementLayout, emoji_clip: VideoClip) -> float:
        align = self.options.align
        if align == EmojiAlign.RANDOM:
            align = random.choice([EmojiAlign.BOTTOM, EmojiAlign.TOP])

        if align == EmojiAlign.BOTTOM:
            return segment_layout.y + segment_layout.height
        elif align == EmojiAlign.TOP:
            return segment_layout.y - emoji_clip.h
        else:
            raise ValueError(f"Invalid align value: {align}")
