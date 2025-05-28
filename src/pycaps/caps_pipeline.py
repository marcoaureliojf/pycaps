from .transcriber.base_transcriber import AudioTranscriber
from moviepy.editor import VideoFileClip, CompositeVideoClip
from typing import Dict, Optional, Any
import os
import tempfile
from .transcriber.whisper_audio_transcriber import WhisperAudioTranscriber
from .css.css_subtitle_renderer import CssSubtitleRenderer
from .video.subtitle_clips_generator import SubtitleClipsGenerator
from .layout.word_width_calculator import WordWidthCalculator
from .layout.layout_calculator import LayoutCalculator
from .tagger.semantic_tagger import get_default_tagger
from .models import SubtitleLayoutOptions

class CapsPipeline:
    def __init__(self):
        self._transcriber: AudioTranscriber = WhisperAudioTranscriber()
        self._renderer: CssSubtitleRenderer = CssSubtitleRenderer()
        self._clips_generator: SubtitleClipsGenerator = SubtitleClipsGenerator(self._renderer)
        self._word_width_calculator: WordWidthCalculator = WordWidthCalculator(self._renderer)
        self._layout_calculator: LayoutCalculator = LayoutCalculator(SubtitleLayoutOptions())
        self._semantic_tagger = get_default_tagger()

        self._input_video_path: Optional[str] = None
        self._output_video_path: Optional[str] = None
        self._audio_path: Optional[str] = None
        self._moviepy_write_options: Optional[Dict[str, Any]] = None

    def run(self) -> None:
        """
        Runs the pipeline to process a video.
        """
        if not os.path.exists(self._input_video_path):
            print(f"Error: Input video file not found: {self._input_video_path}")
            return

        print(f"Starting video processing: {self._input_video_path}")
    
        video_clip = VideoFileClip(self._input_video_path)
        final_video = None
        audio_to_transcribe = self._get_audio_path_to_transcribe(video_clip)
        is_temp_audio_file = self._audio_path is None and audio_to_transcribe is not None and os.path.exists(audio_to_transcribe)

        document = self._transcriber.transcribe(audio_to_transcribe)
        if len(document.segments) == 0:
            print("Transcription returned no segments. Subtitles will not be added.")
            video_clip.close()
            if is_temp_audio_file:
                os.remove(audio_to_transcribe)
            return

        try:
            print(f"Opening renderer for video dimensions: {video_clip.w}x{video_clip.h}")
            self._renderer.open(video_width=video_clip.w, video_height=video_clip.h)

            print("Calculating word widths...")
            self._word_width_calculator.calculate(document)

            print("Calculating layout for each segment...")
            self._layout_calculator.calculate(document, video_clip.w, video_clip.h)

            print("Tagging words with semantic information...")
            self._semantic_tagger.tag(document)

            print("Generating subtitle clips...")
            self._clips_generator.generate(document)

            clips = document.get_clips()

            # TODO: Move this logic to a new class: VideoGenerator.
            #  This class should have a start() method, a get_audio_path() method, a generate(document) method, and a close() method.
            #  The close() method should remove every temporary file created by the class
            #  for example, the audio file, even if it still does not generate the video (it could be called before because of an unexpected error).

            if not clips:
                print("No subtitle clips were generated. The original video (or with external audio if provided) will be saved.")
                final_video = video_clip 
            else:
                print("Compositing final video with subtitles...")
                video_with_subtitles = video_clip.set_audio(None)
                final_video = CompositeVideoClip([video_with_subtitles] + clips, size=video_clip.size)
                if video_clip.audio:
                    final_video = final_video.set_audio(video_clip.audio)
                else:
                    print("Warning: Original video had no audio. Final video will also have no audio.")

            print(f"Writing final video to: {self._output_video_path}")
            default_write_options = {
                "codec": "libx264",
                "audio_codec": "aac",
                "threads": os.cpu_count() or 2, # Use available cores or default to 2
                "logger": "bar"
            }
            if self._moviepy_write_options:
                default_write_options.update(self._moviepy_write_options)
            
            final_video.write_videofile(self._output_video_path, **default_write_options)
            print("Video processing successful!")

        except Exception as e:
            print(f"An error occurred during video processing: {e}")
            raise e
        finally:
            print("Cleaning up resources...")
            if hasattr(video_clip, 'close') and video_clip.reader is not None : video_clip.close()
            
            # For final_video (which can be VideoFileClip or CompositeVideoClip)
            # If final_video is a CompositeVideoClip, it doesn't have a .reader attribute.
            # Its close() method handles closing subclips.
            # If final_video is a VideoFileClip (potentially same as video_clip),
            # its close() is safe to call again (idempotent due to self.reader being set to None by the first call if applicable).
            if final_video and hasattr(final_video, 'close'): 
                final_video.close()
            
            self._renderer.close()
            
            if is_temp_audio_file:
                try:
                    os.remove(audio_to_transcribe)
                    print(f"Temporary audio file deleted: {audio_to_transcribe}")
                except Exception as e_clean:
                    print(f"Error deleting temporary audio file {audio_to_transcribe}: {e_clean}")
            print("Cleanup finished.") 
    
    def _get_audio_path_to_transcribe(self, video_clip: VideoFileClip) -> str:
        if self._audio_path:
            if not os.path.exists(self._audio_path):
                print(f"Error: External audio file not found: {self._audio_path}")
                video_clip.close()
                return
            print(f"Using external audio: {self._audio_path}")
            return self._audio_path
        
        print("Extracting audio from video...")
        # Create a temporary file that is not deleted immediately for Whisper to access
        fd, temp_audio_file_path = tempfile.mkstemp(suffix=".wav")
        os.close(fd) # Close the file descriptor as MoviePy will open/write to the path
        try:
            if video_clip.audio is None:
                print("Error: The video does not contain an audio track.")
                video_clip.close()
                if os.path.exists(temp_audio_file_path):
                        os.remove(temp_audio_file_path)
                return
            video_clip.audio.write_audiofile(temp_audio_file_path, verbose=False, logger=None)
            print(f"Audio extracted to: {temp_audio_file_path}")
            return temp_audio_file_path
        except Exception as e:
            print(f"Error extracting audio: {e}")
            video_clip.close()
            if os.path.exists(temp_audio_file_path):
                os.remove(temp_audio_file_path)
            raise e

class CapsPipelineBuilder:

    def __init__(self):
        self._caps_pipeline: CapsPipeline = CapsPipeline()
    
    def with_input_video_path(self, input_video_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._input_video_path = input_video_path
        return self
    
    def with_output_video_path(self, output_video_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._output_video_path = output_video_path
        return self
    
    def with_custom_audio_file(self, audio_path: str) -> "CapsPipelineBuilder":
        self._caps_pipeline._audio_path = audio_path
        return self
    
    def with_moviepy_write_options(self, moviepy_write_options: Dict[str, Any]) -> "CapsPipelineBuilder":
        self._caps_pipeline._moviepy_write_options = moviepy_write_options
        return self
    
    def with_layout_options(self, layout_options: SubtitleLayoutOptions) -> "CapsPipelineBuilder":
        self._caps_pipeline._layout_calculator = LayoutCalculator(layout_options)
        return self
    
    def with_css(self, css_file_path: str) -> "CapsPipelineBuilder":
        if not os.path.exists(css_file_path):
            raise ValueError(f"CSS file not found: {css_file_path}")
        css_content = open(css_file_path, "r").read()
        self._caps_pipeline._renderer.set_custom_css(css_content)
        return self
    
    def with_audio_transcriber(self, audio_transcriber: AudioTranscriber) -> "CapsPipelineBuilder":
        self._caps_pipeline._transcriber = audio_transcriber
        return self

    def build(self) -> CapsPipeline:
        if not self._caps_pipeline._input_video_path:
            raise ValueError("Input video path is required")
        if not self._caps_pipeline._output_video_path:
            raise ValueError("Output video path is required")
        return self._caps_pipeline