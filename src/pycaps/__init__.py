# src/pycaps/__init__.py
# Este archivo puede estar vacío o usarse para exponer partes de la librería.

# Podríamos exponer las clases principales aquí para facilitar la importación
from .pipeline.caps_pipeline import CapsPipeline
from .pipeline.caps_pipeline_builder import CapsPipelineBuilder
from .css import CssSubtitleRenderer
from .transcriber import WhisperAudioTranscriber, AudioTranscriber
from .effect import (
    BaseEffectGenerator,
    EmojiEffectDecorator,
    BounceInAnimationEffect,
    SlideInFromLeftAnimationEffect,
    WaveAnimationEffect,
    FirstSegmentPerSentenceEffectDecorator
)
from .models import (
    TranscriptionSegment,
    WordData,
    SubtitleLayoutOptions,
    EmojiEffectOptions,
    VerticalAlignment,
    VerticalAlignmentType,
    TextOverflowStrategy,
    EmojiAlign
) # Exponer data classes
from .segment import LimitByWordsRewritter, LimitByCharsRewritter
from .animator import (
    AnimationType,
    AnimationConfig,
    ElementAnimator,
    FadeInAnimationEffect,
    FadeOutAnimationEffect,
    BounceInAnimationEffect,
    SlideInFromLeftAnimationEffect,
    WaveAnimationEffect,
    Easing
)
from .element import (
    ElementType,
    EventType,
    WordClipSelector,
)
from .tag import Tag, TagCondition, BuiltinTag, BuiltinTagCondition, TagConditionFactory

__version__ = "0.1.0" 