# src/pycaps/__init__.py
# Este archivo puede estar vacío o usarse para exponer partes de la librería.

# Podríamos exponer las clases principales aquí para facilitar la importación
from .processor import VideoSubtitleProcessor
from .renderer import CssSubtitleRenderer, BaseSubtitleRenderer # Exponer base y una implementación
from .transcriber import WhisperAudioTranscriber, AudioTranscriber # Exponer base y una implementación
from .effect import KaraokeEffectGenerator, BaseEffectGenerator, EmojiEffectDecorator # Exponer base y una implementación
from .models import (
    KaraokeEffectOptions,
    TranscriptionSegment,
    WordData,
    SubtitleLayoutOptions,
    EmojiEffectOptions,
    VerticalAlignment
) # Exponer data classes
from .segmenter import LimitWordsSegmenter

__version__ = "0.1.0" 