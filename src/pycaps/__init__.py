# src/pycaps/__init__.py
# Este archivo puede estar vacío o usarse para exponer partes de la librería.

# Podríamos exponer las clases principales aquí para facilitar la importación
from .caps_pipeline import CapsPipeline, CapsPipelineBuilder
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
from .segmenter import LimitByWordsSegmenter, LimitByCharsSegmenter

__version__ = "0.1.0" 