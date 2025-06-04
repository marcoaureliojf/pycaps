from pycaps.layout import SubtitleLayoutOptions
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pycaps.common import EventType, ElementType, VideoResolution
from pycaps.effect import EmojiAlign
from typing import Literal, Annotated, Optional
from pycaps.animation import Direction, OvershootConfig

# TODO: we are copying the default values that receive the classes, we should avoid that
class BaseConfigModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

class VideoConfig(BaseConfigModel):
    fps: int = 30
    resolution: Optional[VideoResolution] = None

class WhisperConfig(BaseConfigModel):
    language: Optional[str] = None
    model: Literal["tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en", "large", "turbo"] = "base"

class LimitByWordsRewriterConfig(BaseConfigModel):
    type: Literal["limit_by_words"]
    limit: int

class LimitByCharsRewriterConfig(BaseConfigModel):
    type: Literal["limit_by_chars"]
    min_chars: int = 15
    max_chars: int = 30
    avoid_finishing_segment_with_word_shorter_than: int = 4

    @field_validator("min_chars", "max_chars", "avoid_finishing_segment_with_word_shorter_than")
    @classmethod
    def validate_positive_int(cls, v: int, info) -> int:
        if v < 0:
            raise ValueError(f"{info.name} must be greater than 0")
        return v
    
    @field_validator("max_chars")
    @classmethod
    def validate_max_chars(cls, v: int, info) -> int:
        min_chars = info.data.get("min_chars")
        if min_chars is not None and v < min_chars:
            raise ValueError(f"{info.name} must be greater than {min_chars}")
        return v

RewriterConfig = Annotated[LimitByCharsRewriterConfig | LimitByWordsRewriterConfig, Field(discriminator="type")]

class EmojiInSegmentEffectConfig(BaseConfigModel):
    type: Literal["emoji_in_segment"]
    chance_to_apply: float = 0.5
    align: EmojiAlign = EmojiAlign.RANDOM
    ignore_segments_with_duration_less_than: float = 1
    max_uses_of_each_emoji: int = 2
    max_consecutive_segments_with_emoji: int = 3

class EmojiInWordEffectConfig(BaseConfigModel):
    type: Literal["emoji_in_word"]
    emojies: list[str]
    has_tags: list[str] = []
    avoid_use_same_emoji_in_a_row: bool = True

class ToUppercaseEffectConfig(BaseConfigModel):
    type: Literal["to_uppercase"]
    has_tags: list[str] = []

EffectConfig = Annotated[EmojiInSegmentEffectConfig | EmojiInWordEffectConfig | ToUppercaseEffectConfig, Field(discriminator="type")]

class BaseAnimationConfig(BaseConfigModel):
    type: Literal["fade_in", "fade_out", "zoom_in", "zoom_out", "pop_in", "pop_out", "pop_in_bounce"]
    duration: float = 0.2
    delay: float = 0.0
    when: EventType
    what: ElementType
    has_tags: list[str] = []

class SlideAnimationConfig(BaseAnimationConfig):
    type: Literal["slide_in", "slide_out"]
    direction: Direction = Direction.LEFT

class BaseAnimationPrimitiveConfig(BaseConfigModel):
    type: Literal["fade_in_primitive"]
    duration: float = 0.2
    delay: float = 0.0
    transformer: Literal["linear", "ease_in", "ease_out", "ease_in_out", "inverse"] = "linear"
    what: ElementType
    when: EventType
    has_tags: list[str] = []

class PopInPrimitiveAnimationConfig(BaseAnimationPrimitiveConfig):
    type: Literal["pop_in_primitive"]
    init_scale: float = 0.7
    min_scale: float = 0.3
    min_scale_at: float = 0.5
    overshoot: Optional[OvershootConfig] = None

class SlideInPrimitiveAnimationConfig(BaseAnimationPrimitiveConfig):
    type: Literal["slide_in_primitive"]
    direction: Direction = Direction.LEFT
    distance: float = 100
    overshoot: Optional[OvershootConfig] = None

class ZoomInPrimitiveAnimationConfig(BaseAnimationPrimitiveConfig):
    type: Literal["zoom_in_primitive"]
    init_scale: float = 0.5
    overshoot: Optional[OvershootConfig] = None

AnimationConfig = Annotated[
    BaseAnimationConfig |
    SlideAnimationConfig |
    BaseAnimationPrimitiveConfig |
    SlideInPrimitiveAnimationConfig |
    ZoomInPrimitiveAnimationConfig |
    PopInPrimitiveAnimationConfig,
    Field(discriminator="type")
]

class LlmTaggerRuleConfig(BaseConfigModel):
    type: Literal["llm"]
    tag: str
    topic: str

class RegexTaggerRuleConfig(BaseConfigModel):
    type: Literal["regex"]
    tag: str
    regex: str

TaggerRule = Annotated[LlmTaggerRuleConfig | RegexTaggerRuleConfig, Field(discriminator="type")]

class JsonSchema(BaseConfigModel):
    input: str
    output: Optional[str] = None
    css: str
    video: Optional[VideoConfig] = None
    whisper: Optional[WhisperConfig] = None
    layout: Optional[SubtitleLayoutOptions] = None
    rewriter: Optional[RewriterConfig] = None
    effects: list[EffectConfig] = []
    animations: list[AnimationConfig] = []
    tagger_rules: list[TaggerRule] = []
