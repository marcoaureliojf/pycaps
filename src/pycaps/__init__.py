# src/pycaps/__init__.py
# Este archivo puede estar vacío o usarse para exponer partes de la librería.

# Podríamos exponer las clases principales aquí para facilitar la importación
from .processor import VideoSubtitleProcessor
from .renderers import CssSubtitleRenderer, BaseSubtitleRenderer # Exponer base y una implementación
from .transcribers import WhisperAudioTranscriber, AudioTranscriber # Exponer base y una implementación
from .subtitle_generator import KaraokeEffectGenerator, SubtitleEffectGenerator # Exponer base y una implementación
from .models import KaraokeEffectOptions, TranscriptionSegment, WordTiming, SubtitleLayoutOptions # Exponer data classes

__version__ = "0.1.0" 