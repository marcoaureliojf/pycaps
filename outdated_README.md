# src/pycaps: Advanced Video Subtitle Styling

src/pycaps is a Python library for generating and compositing dynamically styled subtitles onto videos. It leverages HTML/CSS for rich text rendering via a headless browser (Playwright) and uses audio transcription (e.g., Whisper) to synchronize subtitles word by word. It's designed to be extensible for various subtitle effects, starting with a Karaoke-style effect.

## Key Features

*   **HTML/CSS Rendering**: Design complex subtitle styles using the power of CSS.
*   **Dynamic Text Updates**: Efficiently update text and styles in the browser using JavaScript, avoiding full page reloads for each word.
*   **In-Memory Image Handling**: Subtitle images are generated and processed in RAM, minimizing disk I/O for better performance.
*   **Word-by-Word Synchronization**: Create effects like Karaoke by timing individual words.
*   **Extensible Architecture**:
    *   **Audio Transcribers**: Pluggable modules for different audio transcription services/models (currently supports Whisper).
    *   **Subtitle Renderers**: Define how text is turned into images (currently HTML/CSS via Playwright).
    *   **Effect Generators**: Implement various subtitle styles and animations (currently Karaoke).
*   **Modular Design**: Clear separation of concerns between transcription, rendering, effect generation, and video processing.

## Prerequisites

*   Python 3.8+
*   FFmpeg: Required by `openai-whisper` for audio processing. Ensure it's installed and accessible in your system's PATH.
*   A Chromium-based browser (or other Playwright-supported browsers) for the `HTMLCSSRenderer`.

## Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <your-repository-url>
    cd src/pycaps
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install Playwright browsers:**
    This command will download the necessary browser binaries for Playwright.
    ```bash
    python -m playwright install chromium 
    # Or for all default browsers: python -m playwright install
    ```

## Quick Start: Karaoke Subtitle Generation

The `examples/run_karaoke_generation.py` script demonstrates how to use the library to add karaoke-style subtitles to a video.

1.  **Place a video file** (e.g., `ayuno.mp4`) in the `examples` directory or update the `video_file` variable in the script.
2.  **Run the example:**
    ```bash
    cd examples
    python run_karaoke_generation.py
    ```
    This will:
    *   Extract audio from `ayuno.mp4` (if no external audio is provided).
    *   Transcribe the audio using Whisper to get word timings.
    *   Render each word with "normal" and "active" (highlighted) styles using HTML/CSS.
    *   Generate karaoke effect clips where each word highlights as it's spoken.
    *   Composite these subtitle clips onto the original video.
    *   Save the output as `video_karaoke_from_library.mp4` in the `examples` directory.

## Core Components

The library is built around a few key components:

*   **`AudioTranscriber` (`src/pycaps.transcribers`)**:
    *   Abstract base class for audio transcription.
    *   `WhisperAudioTranscriber`: Implementation using OpenAI's Whisper model. It returns detailed word timings.

*   **`SubtitleRenderer` (`src/pycaps.renderers`)**:
    *   Abstract base class for rendering text into images.
    *   `HTMLCSSRenderer`: Renders text by dynamically updating an HTML page in a headless browser (Playwright) and taking screenshots of the relevant text elements. It accepts a dictionary of CSS styles.

*   **`SubtitleEffectGenerator` (`src/pycaps.subtitle_generator`)**:
    *   Abstract base class for creating specific subtitle visual effects.
    *   `KaraokeEffectGenerator`: Generates word-by-word highlighting (karaoke style). It handles line splitting, word positioning, and creating `ImageClip` objects for MoviePy.

*   **`VideoSubtitleProcessor` (`src/pycaps.processor`)**:
    *   The main orchestrator. It takes a video, uses the transcriber to get word timings, then employs the renderer and an effect generator to create subtitle clips, and finally composites them onto the video using MoviePy.

*   **Data Models (`src/pycaps.models`)**:
    *   `TranscriptionSegment`, `WordTiming`: Standardize the output from transcribers.
    *   `KaraokeEffectOptions`: Data class for configuring the `KaraokeEffectGenerator`.

## Customizing Subtitle Styles (CSS)

The `HTMLCSSRenderer` is configured with a dictionary of styles. Each key in the dictionary is a style name (e.g., `"normal"`, `"active"`), and the value is a string of CSS rules.

**Example from `run_karaoke_generation.py`:**
```python
css_styles = {
    "normal": """
        font-size: 42px;
        color: white;
        font-family: 'Arial Black', Gadget, sans-serif;
        font-weight: 900;
        text-shadow: 
            2px 2px 0px black, -2px 2px 0px black, 
            2px -2px 0px black, -2px -2px 0px black,
            3px 3px 5px rgba(0,0,0,0.7);
        padding: 5px 10px;
        background-color: rgba(0,0,0,0.0); /* Transparent background */
    """,
    "active": """
        font-size: 44px; /* Slightly larger for active word */
        color: yellow;   /* Highlight color */
        font-family: 'Arial Black', Gadget, sans-serif;
        font-weight: 900;
        text-shadow: 
            2px 2px 0px black, -2px 2px 0px black, 
            2px -2px 0px black, -2px -2px 0px black,
            3px 3px 5px rgba(0,0,0,0.7);
        padding: 5px 10px;
        background-color: rgba(0,0,0,0.0);
    """
}

renderer = HTMLCSSRenderer(styles=css_styles, default_style_key="normal")
```

The `KaraokeEffectGenerator` uses options like `active_word_style_key` and `inactive_word_style_key` (from `KaraokeEffectOptions`) to select which style from the renderer to use for different word states.

## Future Enhancements & Contributions

This library is a foundation. Here are some ideas for future development:

*   **More Effect Generators**:
    *   Simple subtitle display (full sentences at a time).
    *   Word-by-word appearance without karaoke highlighting.
    *   Pop-up/caption style effects.
    *   Advanced text animations (e.g., per-letter typing effects).
*   **More Transcribers**: Integrate with other local or cloud-based transcription services.
*   **More Renderers**: Explore other rendering engines (e.g., direct drawing with Pillow/Skia for simpler styles if performance is critical and CSS complexity isn't needed).
*   **Configuration Files**: Load styles and options from external files (e.g., JSON, YAML).
*   **Improved Error Handling and Logging**.
*   **Performance Optimizations**: Further optimize rendering and composition, especially for long videos.
*   **GUI/Web Interface**: A simple interface for easier use.
*   **Unit and Integration Tests**.

Contributions are welcome! Please feel free to fork the repository, create a feature branch, and submit a pull request.

## License

(To be added - e.g., MIT, Apache 2.0)
You should choose and add a license file to your repository. 