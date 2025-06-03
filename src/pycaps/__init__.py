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
    FirstSegmentPerSentenceEffectDecorator,
    EmojiInWordEffect,
    Effect,
    EmojiInSegmentEffect,
    EmojiAlign
)
from .models import (
    TranscriptionSegment,
    WordData,
    SubtitleLayoutOptions,
    EmojiEffectOptions,
    VerticalAlignment,
    VerticalAlignmentType,
    TextOverflowStrategy,
)
from .segment import LimitByWordsRewritter, LimitByCharsRewritter
from .animation import *
from .element import (
    ElementType,
    EventType,
    WordClipSelector,
)
from .tag import Tag, TagCondition, BuiltinTag, BuiltinTagCondition, TagConditionFactory
from .tagger.semantic_tagger import get_default_tagger

__version__ = "0.1.0" 