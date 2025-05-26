from .transcribers.base_transcriber import AudioTranscriber
from .renderers.base_subtitle_renderer import BaseSubtitleRenderer
from .subtitle_generator.base_generator import SubtitleEffectGenerator
from moviepy.editor import VideoFileClip, CompositeVideoClip
from typing import Dict, Optional, Any
import os
import tempfile

class VideoSubtitleProcessor:
    def __init__(self, 
                 transcriber: AudioTranscriber, 
                 renderer: BaseSubtitleRenderer, 
                 effect_generator: SubtitleEffectGenerator):
        """
        Main class for processing videos and adding styled subtitles.

        Args:
            transcriber: An instance of a class derived from AudioTranscriber.
            renderer: An instance of a class derived from SubtitleRenderer.
            effect_generator: An instance of a class derived from SubtitleEffectGenerator.
        """
        self.transcriber = transcriber
        self.renderer = renderer
        self.effect_generator = effect_generator

    def process_video(self, 
                      video_path: str, 
                      output_path: str, 
                      audio_path: Optional[str] = None,
                      moviepy_write_options: Optional[Dict[str, Any]] = None) -> None:
        """
        Processes a video to add subtitles.

        Args:
            video_path: Path to the input video file.
            output_path: Path where the processed video will be saved.
            audio_path: (Optional) Path to an external audio file for transcription.
                        If None, audio will be extracted from the video.
            moviepy_write_options: (Optional) Dictionary of options for VideoClip.write_videofile.
        """
        if not os.path.exists(video_path):
            print(f"Error: Input video file not found: {video_path}")
            return

        print(f"Starting video processing: {video_path}")
        video_clip = VideoFileClip(video_path)
        
        temp_audio_file_path: Optional[str] = None
        audio_to_transcribe: str
        final_video = None

        if audio_path:
            if not os.path.exists(audio_path):
                print(f"Error: External audio file not found: {audio_path}")
                video_clip.close()
                return
            audio_to_transcribe = audio_path
            print(f"Using external audio: {audio_to_transcribe}")
        else:
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
                audio_to_transcribe = temp_audio_file_path
                print(f"Audio extracted to: {audio_to_transcribe}")
            except Exception as e:
                print(f"Error extracting audio: {e}")
                video_clip.close()
                if os.path.exists(temp_audio_file_path):
                    os.remove(temp_audio_file_path)
                return

        segments = self.transcriber.transcribe(audio_to_transcribe)
        if not segments:
            print("Transcription returned no segments. Subtitles will not be added.")
            video_clip.close()
            if temp_audio_file_path and os.path.exists(temp_audio_file_path):
                os.remove(temp_audio_file_path)
            return

        try:
            print(f"Opening renderer for video dimensions: {video_clip.w}x{video_clip.h}")
            self.renderer.open(video_width=video_clip.w, video_height=video_clip.h)

            print("Generating subtitle clips...")
            subtitle_clips = self.effect_generator.generate(segments, video_clip)

            if not subtitle_clips:
                print("No subtitle clips were generated. The original video (or with external audio if provided) will be saved.")
                final_video = video_clip 
            else:
                print("Compositing final video with subtitles...")
                video_with_subtitles = video_clip.set_audio(None)
                final_video = CompositeVideoClip([video_with_subtitles] + subtitle_clips, size=video_clip.size)
                if video_clip.audio:
                    final_video = final_video.set_audio(video_clip.audio)
                else:
                    print("Warning: Original video had no audio. Final video will also have no audio.")

            print(f"Writing final video to: {output_path}")
            default_write_options = {
                "codec": "libx264",
                "audio_codec": "aac",
                "threads": os.cpu_count() or 2, # Use available cores or default to 2
                "logger": "bar"
            }
            if moviepy_write_options:
                default_write_options.update(moviepy_write_options)
            
            final_video.write_videofile(output_path, **default_write_options)
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
            
            self.renderer.close()
            
            if temp_audio_file_path and os.path.exists(temp_audio_file_path):
                try:
                    os.remove(temp_audio_file_path)
                    print(f"Temporary audio file deleted: {temp_audio_file_path}")
                except Exception as e_clean:
                    print(f"Error deleting temporary audio file {temp_audio_file_path}: {e_clean}")
            print("Cleanup finished.") 