from .base_effect_generator import BaseEffectGenerator
from ..renderer.base_subtitle_renderer import BaseSubtitleRenderer
from ..models import TranscriptionSegment, KaraokeEffectOptions, RenderedSubtitle, WordData
from moviepy.editor import VideoClip, ImageClip
from typing import List, Tuple, Optional, Dict
import numpy as np
from PIL import Image
import io
from ..layout.subtitle_layout_service import SubtitleLayoutService
from ..layout.models import SegmentClipData, WordClipData

class KaraokeEffectGenerator(BaseEffectGenerator):

    ACTIVE_WORD_STYLE_KEY = "active"
    INACTIVE_WORD_STYLE_KEY = "normal"

    def __init__(self, renderer: BaseSubtitleRenderer, options: KaraokeEffectOptions):
        """
        Generates karaoke-style subtitle effects.

        Args:
            renderer: An instance of a SubtitleRenderer implementation.
            options: KaraokeEffectOptions.
        """
        super().__init__(renderer)
        self.word_render_cache: Dict[Tuple[str, str], RenderedSubtitle] = {}
        self.options = options

        # Register styles for active and inactive words
        self.renderer.register_style(self.ACTIVE_WORD_STYLE_KEY, options.active_word_css_rules)
        self.renderer.register_style(self.INACTIVE_WORD_STYLE_KEY, options.inactive_word_css_rules)

    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[SegmentClipData]:
        """
        Generates MoviePy ImageClips for karaoke-style subtitles.
        """
        print("Generating Karaoke-style subtitle clips...")

        all_segment_clips: List[SegmentClipData] = []
        layout_generator = SubtitleLayoutService(self.options.layout_options, video_clip.w, video_clip.h)

        for segment in segments:
            if not segment.words:
                continue

            words_sizes: List[Tuple[int, int]] = self.__get_sizes_for_all_words(segment.words)
            segment_clip_data = layout_generator.calculate_layout(segment.words, words_sizes, segment.start, segment.end)

            for line in segment_clip_data.lines:
                for word in line.words:
                    active_clip = self.__generate_active_word_clip(word)
                    word.clips.append(active_clip)

                    inactive_clip = self.__generate_inactive_word_clip(word, segment.end)
                    if inactive_clip:
                        word.clips.append(inactive_clip)
            
            all_segment_clips.append(segment_clip_data)

        return all_segment_clips
    
    def __get_sizes_for_all_words(self, words: List[WordData]) -> List[Tuple[int, int]]:
        words_sizes: List[Tuple[int, int]] = []
        for word in words:
            word_image = self.__get_subtitle_image(word.text, self.INACTIVE_WORD_STYLE_KEY)
            words_sizes.append(
                (
                    word_image.width,
                    word_image.height
                )
            )
        return words_sizes
    
    def __generate_inactive_word_clip(self, word_clip: WordClipData, segment_end_time: float) -> Optional[VideoClip]:
        if word_clip.word.end >= segment_end_time:
            return None
        
        inactive_subtitle_image = self.__get_subtitle_image(word_clip.word.text, self.INACTIVE_WORD_STYLE_KEY)
        pil_img_inactive = Image.open(io.BytesIO(inactive_subtitle_image.image)).convert("RGBA")
        np_img_inactive = np.array(pil_img_inactive)

        return (
            ImageClip(np_img_inactive)
            .set_start(word_clip.word.end)
            .set_duration(segment_end_time - word_clip.word.end)
            .set_position((word_clip.layout.x, word_clip.layout.y)) 
        )
    
    def __generate_active_word_clip(self, word_clip: WordClipData) -> VideoClip:
        active_word_image = self.__get_subtitle_image(word_clip.word.text, self.ACTIVE_WORD_STYLE_KEY)
        pil_img_active = Image.open(io.BytesIO(active_word_image.image)).convert("RGBA")
        np_img_active = np.array(pil_img_active)
        
        return (
            ImageClip(np_img_active)
            .set_start(word_clip.word.start)
            .set_duration(word_clip.word.end - word_clip.word.start)
            .set_position((word_clip.layout.x, word_clip.layout.y))
            .crossfadein(self.options.active_word_fade_duration) 
        )

    # TODO: Move this cache to the renderer
    def __get_subtitle_image(self, word_text: str, style_key: str) -> RenderedSubtitle:
        """Retrieves or renders a word image, utilizing a cache."""
        cache_key = (word_text, style_key)
        if cache_key in self.word_render_cache:
            return self.word_render_cache[cache_key]
        
        subtitleImage = self.renderer.render(word_text, style_key)
        self.word_render_cache[cache_key] = subtitleImage
        return subtitleImage
