from .base_generator import SubtitleEffectGenerator
from ..renderers.base_subtitle_renderer import BaseSubtitleRenderer
from ..models import TranscriptionSegment, KaraokeEffectOptions, SubtitleImage, WordTiming
from moviepy.editor import VideoClip, ImageClip
from typing import List, Tuple, Optional, Dict
import numpy as np
from PIL import Image
import io
from .subtitle_layout_generator import SubtitleLayoutService
from .subtitle_models import SubtitleLayout, WordInfo, WordLayoutData

class KaraokeEffectGenerator(SubtitleEffectGenerator):

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
        self.word_render_cache: Dict[Tuple[str, str], SubtitleImage] = {}
        self.options = options

        # Register styles for active and inactive words
        self.renderer.register_style(self.ACTIVE_WORD_STYLE_KEY, options.active_word_css_rules)
        self.renderer.register_style(self.INACTIVE_WORD_STYLE_KEY, options.inactive_word_css_rules)

    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[VideoClip]:
        """
        Generates MoviePy ImageClips for karaoke-style subtitles.
        """
        print("Generating Karaoke-style subtitle clips...")

        all_subtitle_clips: List[VideoClip] = []
        layout_generator = SubtitleLayoutService(self.options.layout_options, video_clip.w, video_clip.h)

        for segment_data in segments:
            if not segment_data.words:
                continue

            words_info: List[WordInfo] = self.__map_segment_word_to_word_info(segment_data.words)
            subtitle_layout: SubtitleLayout = layout_generator.calculate_layout(words_info, segment_data.start, segment_data.end)
            if not subtitle_layout.lines:
                continue

            for line in subtitle_layout.lines:
                for word_layout in line.word_layouts:
                    active_clip = self.__generate_active_word_clip(word_layout)
                    all_subtitle_clips.append(active_clip)

                    inactive_clip = self.__generate_inactive_word_clip(word_layout, subtitle_layout.segment_end)
                    if inactive_clip:
                        all_subtitle_clips.append(inactive_clip)
        
        return all_subtitle_clips
    
    def __map_segment_word_to_word_info(self, segment_words: List[WordTiming]) -> List[WordInfo]:
        words: List[WordInfo] = []
        for segment_word in segment_words:
            base_image_for_layout = self.__get_subtitle_image(segment_word.word, self.INACTIVE_WORD_STYLE_KEY)
            words.append(
                WordInfo(
                    text=segment_word.word,
                    start=segment_word.start,
                    end=segment_word.end,
                    width=base_image_for_layout.width,
                    height=base_image_for_layout.height
                )
            )
        return words
    
    def __generate_inactive_word_clip(self, word_layout: WordLayoutData, segment_end_time: float) -> Optional[VideoClip]:
        if word_layout.word.end >= segment_end_time:
            return None
        
        inactive_subtitle_image = self.__get_subtitle_image(word_layout.word.text, self.INACTIVE_WORD_STYLE_KEY)
        pil_img_inactive = Image.open(io.BytesIO(inactive_subtitle_image.image)).convert("RGBA")
        np_img_inactive = np.array(pil_img_inactive)

        return (
            ImageClip(np_img_inactive)
            .set_start(word_layout.word.end)
            .set_duration(segment_end_time - word_layout.word.end)
            .set_position((word_layout.x, word_layout.y)) 
        )
    
    def __generate_active_word_clip(self, word_layout: WordLayoutData) -> VideoClip:
        active_word_image = self.__get_subtitle_image(word_layout.word.text, self.ACTIVE_WORD_STYLE_KEY)
        pil_img_active = Image.open(io.BytesIO(active_word_image.image)).convert("RGBA")
        np_img_active = np.array(pil_img_active)
        
        return (
            ImageClip(np_img_active)
            .set_start(word_layout.word.start)
            .set_duration(word_layout.word.end - word_layout.word.start)
            .set_position((word_layout.x, word_layout.y))
            .crossfadein(self.options.active_word_fade_duration) 
        )

    def __get_subtitle_image(self, word_text: str, style_key: str) -> SubtitleImage:
        """Retrieves or renders a word image, utilizing a cache."""
        cache_key = (word_text, style_key)
        if cache_key in self.word_render_cache:
            return self.word_render_cache[cache_key]
        
        subtitleImage = self.renderer.render(word_text, style_key)
        self.word_render_cache[cache_key] = subtitleImage
        return subtitleImage
