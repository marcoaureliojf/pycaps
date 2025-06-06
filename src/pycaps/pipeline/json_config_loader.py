import json
from .caps_pipeline_builder import CapsPipelineBuilder
from .caps_pipeline import CapsPipeline
from pycaps.transcriber import LimitByWordsRewriter, LimitByCharsRewriter
from pycaps.tag import TagConditionFactory, TagCondition
from pycaps.effect import *
from pycaps.animation import *
from .json_schema import JsonSchema, AnimationConfig
from pydantic import ValidationError
from pycaps.tag import SemanticTagger
from pycaps.common import Tag
from typing import overload, Literal
import os

class JsonConfigLoader:
    def __init__(self, json_path: str) -> None:
        with open(json_path, "r", encoding="utf-8") as f:
            self._data = json.load(f)
        self._json_path = json_path

    @overload
    def load(self, should_build_pipeline: Literal[True] = True) -> CapsPipeline:
        ...
    @overload
    def load(self, should_build_pipeline: Literal[False]) -> CapsPipelineBuilder:
        ...
    def load(self, should_build_pipeline: bool = True) -> CapsPipeline | CapsPipelineBuilder:
        try:
            base_path = os.path.dirname(self._json_path)
            self._config = JsonSchema(**self._data)
            self._builder = CapsPipelineBuilder()
            if self._config.css:
                self._builder.with_css(os.path.join(base_path, self._config.css))
            if self._config.input:
                self._builder.with_input_video(os.path.join(base_path, self._config.input))
            if self._config.output:
                self._builder.with_output_video(self._config.output)
            if self._config.resources:
                self._builder.with_resources(os.path.join(base_path, self._config.resources))

            self._load_video_config()
            self._load_whisper_config()
            self._load_layout_options()
            self._load_segment_rewriter()
            self._load_text_effects()
            self._load_clip_effects()
            self._load_sound_effects()
            self._load_animations()
            self._load_tagger()
            if should_build_pipeline:
                return self._builder.build()
            else:
                return self._builder
        except ValidationError as e:
            raise ValueError(f"Invalid config: {e}")

    def _load_video_config(self) -> None:
        if self._config.video is None:
            return
        video_data = self._config.video
        if video_data.resolution is not None:
            self._builder.with_video_resolution(video_data.resolution)
        self._builder.with_fps(video_data.fps)

    def _load_whisper_config(self) -> None:
        if self._config.whisper is None:
            return
        whisper_data = self._config.whisper
        self._builder.with_whisper_config(
            language=whisper_data.language,
            model_size=whisper_data.model
        )

    def _load_layout_options(self) -> None:
        if self._config.layout is None:
            return
        self._builder.with_layout_options(self._config.layout)

    def _load_segment_rewriter(self) -> None:
        if self._config.rewriter is None:
            return
        data = self._config.rewriter

        if data.type == "limit_by_words":
            self._builder.add_segment_rewriter(LimitByWordsRewriter(data.limit))
        elif data.type == "limit_by_chars":
            self._builder.add_segment_rewriter(LimitByCharsRewriter(data.max_chars, data.min_chars, data.avoid_finishing_segment_with_word_shorter_than))

    def _load_text_effects(self) -> None:
        for effect in self._config.text_effects:
            match effect.type:
                case "emoji_in_segment":
                    self._builder.add_text_effect(EmojiInSegmentEffect(effect.chance_to_apply, effect.align, effect.ignore_segments_with_duration_less_than, effect.max_uses_of_each_emoji, effect.max_consecutive_segments_with_emoji))
                case "emoji_in_word":
                    self._builder.add_text_effect(EmojiInWordEffect(effect.emojies, self._build_tag_condition(effect.has_tags), effect.avoid_use_same_emoji_in_a_row))
                case "to_uppercase":
                    self._builder.add_text_effect(ToUppercaseEffect(self._build_tag_condition(effect.has_tags)))

    def _load_clip_effects(self) -> None:
        for effect in self._config.clip_effects:
            match effect.type:
                case "typewriting":
                    self._builder.add_clip_effect(TypewritingEffect(self._build_tag_condition(effect.has_tags)))

    def _load_sound_effects(self) -> None:
        for effect in self._config.sound_effects:
            match effect.type:
                case "preset":
                    sound = BuiltinSound.get_by_name(effect.name)
                    if sound is None:
                        raise ValueError(f"Invalid preset sound: {effect.name}")
                    self._builder.add_sound_effect(
                        SoundEffect(
                            sound,
                            effect.what,
                            effect.when,
                            self._build_tag_condition(effect.has_tags),
                            effect.offset,
                            effect.volume,
                            effect.interpret_consecutive_words_as_one
                        )
                    )
                case "custom":
                    self._builder.add_sound_effect(
                        SoundEffect(
                            Sound(effect.path, effect.path),
                            effect.what,
                            effect.when,
                            self._build_tag_condition(effect.has_tags),
                            effect.offset,
                            effect.volume,
                            effect.interpret_consecutive_words_as_one
                        )
                    )

    def _load_animations(self) -> None:
        for animation_config in self._config.animations:
            tag_condition = self._build_tag_condition(animation_config.has_tags)
            animation = self._build_animation(animation_config)
            self._builder.add_animation(animation, animation_config.when, animation_config.what, tag_condition)

    def _build_tag_condition(self, tag_list: list[str]) -> TagCondition:
        return TagConditionFactory.AND(*[Tag(tag) for tag in tag_list])
    
    def _build_animation(self, animation: AnimationConfig) -> Animation:
        match animation.type:
            case "fade_in":
                return FadeIn(animation.duration, animation.delay)
            case "fade_out":
                return FadeOut(animation.duration, animation.delay)
            case "zoom_in":
                return ZoomIn(animation.duration, animation.delay)
            case "zoom_out":
                return ZoomOut(animation.duration, animation.delay)
            case "pop_in":
                return PopIn(animation.duration, animation.delay)
            case "pop_out":
                return PopOut(animation.duration, animation.delay)
            case "pop_in_bounce":
                return PopInBounce(animation.duration, animation.delay)
            case "slide_in":
                return SlideIn(animation.direction, animation.duration, animation.delay)
            case "slide_out":
                return SlideOut(animation.direction, animation.duration, animation.delay)
            case "zoom_in_primitive":
                return ZoomInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer),
                    animation.init_scale,
                    animation.overshoot
                )
            case "pop_in_primitive":
                return PopInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer),
                    animation.init_scale,
                    animation.min_scale,
                    animation.min_scale_at,
                    animation.overshoot
                )
            case "slide_in_primitive":
                return SlideInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer),
                    animation.direction,
                    animation.distance,
                    animation.overshoot
                )
            case "fade_in_primitive":
                return FadeInPrimitive(
                    animation.duration,
                    animation.delay,
                    self._build_transformer(animation.transformer)
                )
            case _:
                raise ValueError(f"Invalid animation type: {animation.type}")
            

    def _build_transformer(self, transformer: str) -> Transformer:
        match transformer:
            case "linear":
                return Transformer.LINEAR
            case "ease_in":
                return Transformer.EASE_IN
            case "ease_out":
                return Transformer.EASE_OUT
            case "ease_in_out":
                return Transformer.EASE_IN_OUT
            case "inverse":
                return Transformer.INVERT
            case _:
                raise ValueError(f"Invalid transformer: {transformer}")

    def _load_tagger(self) -> None:
        tagger = SemanticTagger()
        for rule in self._config.tagger_rules:
            if rule.type == "llm":
                tagger.add_llm_rule(Tag(rule.tag), rule.topic)
            elif rule.type == "regex":
                tagger.add_regex_rule(Tag(rule.tag), rule.regex)

        self._builder.with_semantic_tagger(tagger)

