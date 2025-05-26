from ..base_effect_generator import BaseEffectGenerator
from ...models import TranscriptionSegment, EmojiEffectOptions, RenderedSubtitle
from typing import List
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

        self.renderer.register_style(self.EMOJI_STYLE_KEY, self.options.css_rules)

    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[SegmentClipData]:
        effect_clips_data = self.effect_generator.generate(segments, video_clip)
        all_segment_clips: List[SegmentClipData] = []

        for segment_data in effect_clips_data:
            if random.random() > self.options.chance_to_apply:
                all_segment_clips.append(segment_data)
                continue

            # TODO: this assumes that the emoji will be in a new line
            #  So, it only can be located below or over the segment text (but not at the left or right side)
            emoji = self.__get_relevant_emoji(segment_data.get_text())
            # TODO: validate it is a valid emoji before using it
            emoji_clip: VideoClip = self.__generate_emoji_clip(emoji, segment_data)
            emoji_layout = self.__get_emoji_layout(video_clip, emoji_clip, segment_data.layout)
            emoji_clip = emoji_clip.set_position((emoji_layout.x, emoji_layout.y))
            word_data = WordData(text=emoji, start=segment_data.start, end=segment_data.end)
            word_clip_data = WordClipData(word=word_data, layout=emoji_layout, clips=[emoji_clip])
            line_clip_data = LineClipData(words=[word_clip_data], layout=emoji_layout)
            segment_data.lines.append(line_clip_data)
            new_layout = LayoutUtils.calculate_lines_layout(segment_data.lines)
            new_segment_data = SegmentClipData(lines=segment_data.lines, layout=new_layout, start=segment_data.start, end=segment_data.end)
            all_segment_clips.append(new_segment_data)

        return all_segment_clips
    
    def __get_relevant_emoji(self, text: str) -> str:
        # return random.choice(["🎶", "🎵", "🎼", "🎹", "🎺", "🎷", "🎸", "🎻", "🎺", "🎷", "🎸", "🎻"])
        response = client.responses.create(
            model="gpt-4.1-nano",
            input=f"""
            Given the following text, respond with a single emoji that represents the mood, emotion, or meaning of the text
            Do not explain. Respond with only the emoji.
            Text: "{text}"
            """
        )
        return response.output_text


    def __generate_emoji_clip(self, emoji: str, segment: SegmentClipData) -> VideoClip:
        emoji_image = self.renderer.render(emoji, self.EMOJI_STYLE_KEY)
        pil_image = Image.open(io.BytesIO(emoji_image.image)).convert("RGBA")
        np_image = np.array(pil_image)
        return (
            ImageClip(np_image)
            .set_start(segment.start)
            .set_duration(segment.end - segment.start)
        )
    
    def __get_emoji_layout(self, container_clip: VideoClip, emoji_clip: VideoClip, segment_layout: ElementLayout) -> ElementLayout:
        horizontal_center = (container_clip.w - emoji_clip.w) / 2.0
        vertical_position = self.__get_vertical_position(segment_layout, emoji_clip)
        return ElementLayout(x=horizontal_center, y=vertical_position, width=emoji_clip.w, height=emoji_clip.h)
    
    def __get_vertical_position(self, segment_layout: ElementLayout, emoji_clip: VideoClip) -> float:
        align = self.options.align
        if align == "random":
            align = random.choice(["bottom", "top"])

        if align == "bottom":
            return segment_layout.y + segment_layout.height
        elif align == "top":
            return segment_layout.y - emoji_clip.h
        else:
            raise ValueError(f"Invalid align value: {align}")
