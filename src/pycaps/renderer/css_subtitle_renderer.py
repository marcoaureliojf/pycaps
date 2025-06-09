from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from pathlib import Path
import tempfile
from PIL.Image import Image
from typing import Optional, List
from pycaps.common import Word, ElementState, Line
import shutil
import webbrowser
from .rendered_image_cache import RenderedImageCache
from .playwright_screenshot_capturer import PlaywrightScreenshotCapturer

class CssSubtitleRenderer():

    DEFAULT_DEVICE_SCALE_FACTOR: int = 2
    DEFAULT_VIEWPORT_HEIGHT_RATIO: float = 0.25
    DEFAULT_MIN_VIEWPORT_HEIGHT: int = 150
    DEFAULT_CSS_CLASS_FOR_EACH_WORD: str = "word"
    DEFAULT_CSS_CLASS_FOR_EACH_LINE: str = "line"

    def __init__(self):
        """
        Renders subtitles using HTML and CSS via Playwright.
        """

        self.playwright_context: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.tempdir: Optional[tempfile.TemporaryDirectory] = None
        self._custom_css: str = ""
        self._cache: RenderedImageCache = RenderedImageCache(self._custom_css)
        self._current_line: Optional[Line] = None
        self._current_line_state: Optional[ElementState] = None

    def set_custom_css(self, custom_css: str):
        self._custom_css = custom_css
        self._cache = RenderedImageCache(self._custom_css)

    def open(self, video_width: int, video_height: int, resources_dir: Optional[Path] = None):
        """Initializes Playwright and loads the base HTML page."""
        if self.page:
            raise RuntimeError("Renderer is already open. Call close() first.")

        calculated_vp_height = max(self.DEFAULT_MIN_VIEWPORT_HEIGHT, int(video_height * self.DEFAULT_VIEWPORT_HEIGHT_RATIO))

        self.tempdir = tempfile.TemporaryDirectory()
        self.playwright_context = sync_playwright().start()
        self.browser = self.playwright_context.chromium.launch()
        context = self.browser.new_context(device_scale_factor=self.DEFAULT_DEVICE_SCALE_FACTOR, viewport={"width": video_width, "height": calculated_vp_height})
        self.page = context.new_page()
        self._copy_resources_to_tempdir(resources_dir)
        path = self._create_html_page()
        self.page.goto(path.as_uri())
    
    # TODO: improve preview
    def preview(self) -> None:
        if not self.tempdir:
            self.tempdir = tempfile.TemporaryDirectory()

        self._copy_resources_to_tempdir()
        path = self._create_html_page("Hello, world")
        webbrowser.open(path.as_uri())

    def _create_html_page(self, text: str = "") -> Path:
        if not self.tempdir:
            raise RuntimeError("self.tempdir is not defined. Do you call open() first?")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                html, body {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    font-family: sans-serif;
                }} 

                #subtitle-container {{
                    display: inline-block;
                }}

                .{self.DEFAULT_CSS_CLASS_FOR_EACH_LINE} {{
                    display: flex;
                    width: fit-content;
                }}

                {self._custom_css}
            </style>
        </head>
        <body>
            <div id="subtitle-container">
                <div class="{self.DEFAULT_CSS_CLASS_FOR_EACH_LINE}">
                    <span class="{self.DEFAULT_CSS_CLASS_FOR_EACH_WORD}">{text}</span>
                </div>
            </div>
        </body>
        </html>
        """
        html_path = Path(self.tempdir.name) / "renderer_base.html"
        html_path.write_text(html_template, encoding="utf-8")
        return html_path

    def _copy_resources_to_tempdir(self, resources_dir: Optional[Path] = None) -> None:
        if not self.tempdir:
            raise RuntimeError("Temp directory must be initialized before copying resources.")
        if not resources_dir:
            return
        if not resources_dir.exists():
            raise RuntimeError(f"Resources directory does not exist: {resources_dir}")
        if not resources_dir.is_dir():
            raise RuntimeError(f"Resources path is not a directory: {resources_dir}")

        destination = Path(self.tempdir.name)
        shutil.copytree(resources_dir, destination, dirs_exist_ok=True)

    def open_line(self, line: Line, line_state: ElementState):
        if not self.page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if self._current_line:
            raise RuntimeError("A line is already open. Call close_line() first.")
        
        self._current_line = line
        self._current_line_state = line_state

        script = f"""
        ([text, cssClassesForWords, cssClassesForLine, lineState]) => {{
            const line = document.querySelector('.{self.DEFAULT_CSS_CLASS_FOR_EACH_LINE}');
            line.innerHTML = '';
            line.className = `{self.DEFAULT_CSS_CLASS_FOR_EACH_LINE} ${{cssClassesForLine}} ${{lineState}}`;
            const words = text.split(' ');
            words.forEach((word, index) => {{
                const wordElement = document.createElement('span');
                const cssClasses = cssClassesForWords[index];
                wordElement.textContent = word;
                wordElement.className = `{self.DEFAULT_CSS_CLASS_FOR_EACH_WORD} word-${{index}}-in-line ${{cssClasses}}`;
                line.appendChild(wordElement);
            }});
        }}
        """
        tags_to_string = lambda tags: " ".join([t.name for t in tags])
        tags_per_word = [word.tags for word in line.words]
        css_classes_for_words = [tags_to_string(tags) for tags in tags_per_word]
        css_classes_for_line = tags_to_string(line.get_segment().tags) + " " + tags_to_string(line.tags)
        self.page.evaluate(script, [line.get_text(), css_classes_for_words, css_classes_for_line, line_state.value])
   
    def render_word(self, index: int, word: Word, state: ElementState, first_n_letters: Optional[int] = None) -> Optional[Image]:
        if not self.page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if not self._current_line:
            raise RuntimeError("No line is open. Call open_line() first.")
        
        # if self._cache.has(word.text, [self._current_line_state.value, state.value]):
        #     return self._cache.get(word.text, [self._current_line_state.value, state.value])

        # Why are we doing this?
        # When the typewriting effect is applied, we need to render the word partially (first n letters).
        # However, if we have some line background that depends on the size (like a gradient),
        # since the word was cropped, the background will be incorrect.
        # It can be specially noticeable in the last word of the line.
        # The same would happen if we use border-radius, since we crop the word,
        # it will show the rounded corners in each word fragment of the last word
        # To fix this, we create a new span with the remaining part of the word and make it invisible.
        # This way, the line is rendered with the final width it will have, and the background will be correct.

        script = f"""
        ([index, state, wordText, first_n_letters]) => {{
            const word = document.querySelector(`.word-${{index}}-in-line`);
            const wordCodePoints = Array.from(wordText); // to avoid issues with multibyte characters
            word.textContent = wordCodePoints.slice(0, first_n_letters).join('');
            word.classList.add(state);

            // the rest remains there but invisible
            if (first_n_letters < wordCodePoints.length) {{
                remaining_word = word.dataset.isNextNodeRemaining ? word.nextSibling : document.createElement('span');
                remaining_word.textContent = wordCodePoints.slice(first_n_letters).join('');
                remaining_word.className = word.className;
                remaining_word.style.visibility = 'hidden';
                if (!word.dataset.isNextNodeRemaining) {{
                    word.parentNode.insertBefore(remaining_word, word.nextSibling);
                    word.dataset.isNextNodeRemaining = true;
                }}
            }} else if (word.dataset.isNextNodeRemaining) {{
                word.parentNode.removeChild(word.nextSibling);
                delete word.dataset.isNextNodeRemaining;
            }}
        }}
        """
        self.page.evaluate(script, [index, state.value, word.text, first_n_letters if first_n_letters else len(word.text)])

        locator = self.page.locator(f".word-{index}-in-line").first
        try:
            bounding_box = locator.bounding_box()
            if not bounding_box or bounding_box['width'] <= 0 or bounding_box['height'] <= 0:
                # HTML element is not visible (probably hidden by CSS).
                return None

            image = PlaywrightScreenshotCapturer.capture(locator)
            # TODO: two entries with same text but different indexes should be different entries
            # self._cache.set(word.text, [self._current_line_state.value, state.value], image)
            return image
        except Exception as e:
            raise RuntimeError(f"Error rendering word '{word.text}': {e}")
        finally:
            self.page.evaluate(f"""
            ([index, state]) => {{
                const word = document.querySelector(`.word-${{index}}-in-line`);
                word.classList.remove(state);
            }}
            """, [index, state.value])
    
    def close_line(self):
        if not self.page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if not self._current_line:
            raise RuntimeError("No line is open. Call open_line() first.")
        
        self._current_line = None
        self._current_line_state = None
        
    def get_word_size(self, word: Word, states: List[ElementState] = []) -> int:
        if not self.page:
            raise RuntimeError("Renderer is not open. Call open() first.")
        if self._current_line:
            raise RuntimeError("A line process is in progress. Call close_line() first.")
        
        css_classes = [t.name for t in word.tags] + [s.value for s in states]
        if self._cache.has(word.text, css_classes):
            return self._cache.get(word.text, css_classes)

        script = f"""
        ([text, cssClasses]) => {{
            const line = document.querySelector('.{self.DEFAULT_CSS_CLASS_FOR_EACH_LINE}');
            line.innerHTML = '';
            const wordElement = document.createElement('span');
            wordElement.textContent = text;
            wordElement.className = `{self.DEFAULT_CSS_CLASS_FOR_EACH_WORD} ${{cssClasses}}`;
            line.appendChild(wordElement);
        }}
        """
        self.page.evaluate(script, [word.text, " ".join(css_classes)])
        
        locator = self.page.locator(f".{self.DEFAULT_CSS_CLASS_FOR_EACH_LINE} > .{self.DEFAULT_CSS_CLASS_FOR_EACH_WORD}")
        bounding_box = locator.bounding_box()
        if not bounding_box or bounding_box['width'] <= 0 or bounding_box['height'] <= 0:
            return None

        return int(bounding_box['width'] * self.DEFAULT_DEVICE_SCALE_FACTOR), int(bounding_box['height'] * self.DEFAULT_DEVICE_SCALE_FACTOR)

    def close(self):
        """Closes Playwright and cleans up resources."""
        if self.browser:
            self.browser.close()
            self.browser = None
        if self.playwright_context:
            self.playwright_context.stop()
            self.playwright_context = None
        if self.tempdir:
            self.tempdir.cleanup()
            self.tempdir = None
        self.page = None

    def __enter__(self):
        # Video dimensions are expected to be provided via an explicit call to open().
        # Using this class as a context manager ensures close() is called,
        # but open() must still be managed by the user if specific dimensions are needed upfront.
        # Typical usage:
        # with HTMLCSSRenderer(...) as renderer:
        #    renderer.open(video_w, video_h) # Call open with dimensions
        #    ...
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close() 
