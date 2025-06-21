import subprocess
from typing import Optional
from imageio_ffmpeg import get_ffmpeg_exe

ffmpeg_exe = get_ffmpeg_exe()

def extract_audio_for_whisper(video: str, output: str, start: Optional[float] = None, end: Optional[float] = None) -> None:
    cmd = [ffmpeg_exe, "-y"]

    if start is not None:
        cmd += ["-ss", str(start)]

    cmd += ["-i", video]

    if end is not None:
        cmd += ["-to", str(end)]

    cmd += [
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        output,
        "-loglevel", "error",
        "-hide_banner",
    ]

    subprocess.run(cmd, check=True)
