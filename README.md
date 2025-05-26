# PyCaps

`pycaps` is a Python library designed to automatically transcribe audio from videos, generate subtitles, and apply various visual effects.

It leverages powerful tools like OpenAI's Whisper for transcription, MoviePy for video manipulation, and Playwright for advanced CSS-based text rendering.

## Prerequisites

Before installing `pycaps`, you need to ensure the following external dependencies are installed on your system:

1.  **Python:** Version 3.8 or higher. You can download it from [python.org](https://www.python.org/).
2.  **FFmpeg:** Whisper requires FFmpeg for audio processing.
    *   **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add the `bin` directory to your system's PATH.
    *   **macOS (using Homebrew):** `brew install ffmpeg`
    *   **Linux (using apt):** `sudo apt update && sudo apt install ffmpeg`
3.  **Playwright Browsers:** The CSS rendering capabilities rely on Playwright, which needs browser binaries.
    After installing `pycaps` (or just the `playwright` library), run the following command in your terminal to install the necessary browser (Chromium is often sufficient for rendering tasks):
    ```bash
    python -m playwright install chromium
    ```
    Or, to install all default browsers:
    ```bash
    python -m playwright install
    ```

## Installation

It's highly recommended to install `pycaps` within a Python virtual environment.

1.  **Clone the repository (if you want to contribute or run examples directly):**
    ```bash
    git clone https://github.com/francozanardi/pycaps.git
    cd pycaps
    ```

2.  **Install `pycaps`:**
    ```bash
    pip install -e .
    ```

## Usage Example

Here's a basic example of how to use `pycaps` to generate a video with karaoke subtitles. Ensure you have a video file (e.g., `input.mp4`) in your script's directory or provide the correct path.

```python
from pycaps import (
    VideoSubtitleProcessor,
    WhisperAudioTranscriber,
    CssSubtitleRenderer,
    KaraokeEffectGenerator,
    KaraokeEffectOptions,
)

video_file = "input.mp4"  # Replace with your video file
output_file = "output_karaoke.mp4"

transcriber = WhisperAudioTranscriber(model_size="base", language="en") # Choose model and language
renderer = CssSubtitleRenderer()

inactive_word_css_rules = """
    font-size: 42px; color: white; font-family: 'Arial Black';
    text-shadow: 2px 2px 0px black, -2px 2px 0px black, 2px -2px 0px black, -2px -2px 0px black;
"""
active_word_css_rules = """
    font-size: 42px; color: yellow; font-family: 'Arial Black';
    text-shadow: 2px 2px 0px black, -2px 2px 0px black, 2px -2px 0px black, -2px -2px 0px black;
"""

subtitle_effect_options = KaraokeEffectOptions(active_word_css_rules, inactive_word_css_rules)
effect_generator = KaraokeEffectGenerator(renderer, subtitle_effect_options)
processor = VideoSubtitleProcessor(transcriber, renderer, effect_generator)

print(f"Processing '{video_file}' to '{output_file}'...")
processor.process_video(video_file, output_file)
```

See the `examples/` directory for more detailed use cases.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
