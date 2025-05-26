from .base_generator import SubtitleEffectGenerator
from ..renderers.base_subtitle_renderer import BaseSubtitleRenderer
from ..models import TranscriptionSegment, KaraokeEffectOptions, SubtitleImage
from moviepy.editor import VideoClip, ImageClip
from typing import List, Dict, Tuple, Optional
import numpy as np
from PIL import Image
import io

class KaraokeEffectGenerator(SubtitleEffectGenerator[KaraokeEffectOptions]):

    ACTIVE_WORD_STYLE_KEY = "active"
    INACTIVE_WORD_STYLE_KEY = "normal"

    def __init__(self, renderer: BaseSubtitleRenderer, options: KaraokeEffectOptions):
        """
        Generates karaoke-style subtitle effects.

        Args:
            renderer: An instance of a SubtitleRenderer implementation.
        """
        super().__init__(renderer)
        # Cache for rendered word images: (word_text, style_key) -> SubtitleImage
        self.word_render_cache: Dict[Tuple[str, str], SubtitleImage] = {}
        self.options = options

        self.renderer.register_style(self.ACTIVE_WORD_STYLE_KEY, options.active_word_css_rules)
        self.renderer.register_style(self.INACTIVE_WORD_STYLE_KEY, options.inactive_word_css_rules)

    def generate(self, segments: List[TranscriptionSegment], video_clip: VideoClip) -> List[VideoClip]:
        """
        Generates MoviePy ImageClips for karaoke-style subtitles.
        """
        print("Generating Karaoke-style subtitle clips...")

        video_w = video_clip.w
        video_h = video_clip.h
        all_subtitle_clips: List[VideoClip] = []

        for segment in segments:
            word_layout_infos = self.__get_word_layout_infos(segment)
            lines = self.__get_lines(word_layout_infos, video_w)
            if not lines: continue

            current_y = self.__get_base_y_pos(lines, video_h)

            # --- Clip Creation per Line and Word --- 
            for line_info in lines:
                if not line_info["words"]: continue
                
                line_actual_height = max(w["height"] for w in line_info["words"])
                start_x_for_line = (video_w - line_info["width"]) / 2.0
                current_x_in_line = start_x_for_line

                for word_detail in line_info["words"]:
                    active_clip = self.__generate_active_word_clip(word_detail, current_x_in_line, current_y, line_actual_height)
                    all_subtitle_clips.append(active_clip)

                    # Inactive word clip (after being spoken)
                    inactive_clip = self.__generate_inactive_word_clip(
                        word_detail,
                        current_x_in_line,
                        current_y,
                        line_actual_height,
                        segment.end
                    )
                    if inactive_clip:
                        all_subtitle_clips.append(inactive_clip)
                    
                    current_x_in_line += word_detail["width"] + self.options.word_spacing
                current_y += line_actual_height
        
        return all_subtitle_clips
    
    def __get_lines(self, word_layout_infos: List[Dict], video_width: int) -> List[Dict]:
        lines = []
        current_line_words_info = []
        current_line_total_width = 0
        max_w = video_width * self.options.max_line_width_ratio
        word_spacing = self.options.word_spacing
        
        for dim_data in word_layout_infos:
            word_w = dim_data["width"]
            width_to_add = word_w + word_spacing

            if current_line_total_width + width_to_add <= max_w:
                current_line_words_info.append(dim_data)
                current_line_total_width += width_to_add
            else:
                if current_line_words_info:
                    line_width = current_line_total_width - word_spacing
                    lines.append({"words": list(current_line_words_info), "width": line_width})
                current_line_words_info = [dim_data]
                current_line_total_width = word_w
        
        if current_line_words_info:
            line_width = current_line_total_width - word_spacing
            lines.append({"words": list(current_line_words_info), "width": line_width})
        
        return lines
        
    def __get_word_layout_infos(self, segment: TranscriptionSegment) -> List[Dict]:
        word_layout_infos = [] 
        for word_time in segment.words:
            subtitle_image = self.__get_subtitle_image(word_time.word, self.INACTIVE_WORD_STYLE_KEY)
            word_layout_infos.append({
                "text": word_time.word,
                "width": subtitle_image.width, 
                "height": subtitle_image.height,
                "start": word_time.start,
                "end": word_time.end
            })
        return word_layout_infos
    
    def __get_base_y_pos(self, lines: List[Dict], video_height: int) -> float:
        total_block_height = sum(max(w["height"] for w in line["words"]) for line in lines)
        if self.options.line_vertical_align == "center":
            return (video_height - total_block_height) / 2
        if self.options.line_vertical_align == "top":
            return video_height * (1.0 - self.options.line_vertical_offset_ratio) # offset from top
        
        # Default to bottom
        return video_height * self.options.line_vertical_offset_ratio - total_block_height
    
    def __generate_inactive_word_clip(self, word_detail: Dict, pos_x: float, pos_y: float, line_height: float, segment_end: float) -> Optional[VideoClip]:
        if word_detail["end"] >= segment_end:
            return None
        
        inactive_subtitle = self.__get_subtitle_image(word_detail["text"], self.INACTIVE_WORD_STYLE_KEY)
        
        pil_img_inactive = Image.open(io.BytesIO(inactive_subtitle.image)).convert("RGBA")
        np_img_inactive = np.array(pil_img_inactive)

        pos_x_inactive = pos_x - (inactive_subtitle.width - word_detail["width"]) / 2.0
        pos_y_inactive = pos_y + (line_height - inactive_subtitle.height) / 2.0
        
        return (
            ImageClip(np_img_inactive)
            .set_start(word_detail["end"])
            .set_duration(segment_end - word_detail["end"])
            .set_position((pos_x_inactive, pos_y_inactive)) 
        )
    
    def __generate_active_word_clip(self, word_detail: Dict, pos_x: float, pos_y: float, line_height: float) -> VideoClip:
        active_word_subtitle = self.__get_subtitle_image(word_detail["text"], self.ACTIVE_WORD_STYLE_KEY)
                    
        pil_img_active = Image.open(io.BytesIO(active_word_subtitle.image)).convert("RGBA")
        np_img_active = np.array(pil_img_active)
        
        pos_x_active = pos_x - (active_word_subtitle.width - word_detail["width"]) / 2.0
        pos_y_active = pos_y + (line_height - active_word_subtitle.height) / 2.0

        return (
            ImageClip(np_img_active)
            .set_start(word_detail["start"])
            .set_duration(word_detail["end"] - word_detail["start"])
            .set_position((pos_x_active, pos_y_active))
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