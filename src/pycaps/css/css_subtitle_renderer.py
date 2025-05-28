from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from pathlib import Path
import tempfile
from typing import Optional
from ..models import RenderedSubtitle
from ..tagger.models import Word
from typing import List
from .css_classes import CssClasses

class CssSubtitleRenderer():

    DEFAULT_VIEWPORT_HEIGHT_RATIO: float = 0.25
    DEFAULT_MIN_VIEWPORT_HEIGHT: int = 150
    DEFAULT_CSS_CLASS_FOR_EACH_WORD: str = "word"

    def __init__(self):
        """
        Renders subtitles using HTML and CSS via Playwright.
        """

        self.playwright_context: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.tempdir: Optional[tempfile.TemporaryDirectory] = None
        self._custom_css: str = ""

    def set_custom_css(self, custom_css: str):
        self._custom_css = custom_css

    def open(self, video_width: int, video_height: int):
        """Initializes Playwright and loads the base HTML page."""
        if self.page:
            raise RuntimeError("Renderer is already open. Call close() first.")

        calculated_vp_height = max(self.DEFAULT_MIN_VIEWPORT_HEIGHT, int(video_height * self.DEFAULT_VIEWPORT_HEIGHT_RATIO))

        self.tempdir = tempfile.TemporaryDirectory()
        self.playwright_context = sync_playwright().start()
        self.browser = self.playwright_context.chromium.launch()
        self.page = self.browser.new_page(viewport={"width": video_width, "height": calculated_vp_height})
        self._init_page_content()

    def _init_page_content(self):
        if not self.page or not self.tempdir:
            raise RuntimeError("Renderer has not been properly initialized with open().")
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center; 
                    justify-content: center; 
                    overflow: hidden;
                    font-family: sans-serif; /* Default global font, can be overridden by specific styles */
                }}
                #subtitle-container {{
                    display: inline-block; /* So the container fits the span's content */
                }}
                {self._custom_css}
            </style>
        </head>
        <body>
            <div id="subtitle-container">
                <span id="subtitle-actual-text"></span>
            </div>
        </body>
        </html>
        """
        html_path = Path(self.tempdir.name) / "renderer_base.html"
        html_path.write_text(html_template, encoding="utf-8")
        self.page.goto(html_path.as_uri())

    def __update_text_and_style(self, text: str, css_classes: List[str]):
        if not self.page:
            raise RuntimeError("Renderer is not open. Call open() first.")

        script = f"""
        ([text, targetCls]) => {{
            const el = document.getElementById('subtitle-actual-text');
            el.textContent = text;
            el.className = targetCls;
        }}
        """

        css_classes = [CssClasses.WORD.value] + css_classes
        css_classes_str = ' '.join(css_classes)
        self.page.evaluate(script, [text, css_classes_str])

    def render(self, word: Word, state_css_classes: List[CssClasses] = []) -> Optional[RenderedSubtitle]:
        if not self.page:
            raise RuntimeError("Renderer is not open open() with video dimensions first.")

        css_classes = word.tags + [c.value for c in state_css_classes]
        self.__update_text_and_style(word.text, css_classes)
        
        locator = self.page.locator("#subtitle-actual-text")
        try:
            bounding_box = locator.bounding_box()
            if not bounding_box:
                # Text is not visible, return None to indicate that.
                return None

            # Bounding_box might have width/height 0 if text is only whitespace or CSS hides it.
            # Ensure a minimum size to prevent errors in MoviePy with zero-size clips.
            img_width = max(1, int(bounding_box['width']))
            img_height = max(1, int(bounding_box['height']))

            png_bytes = locator.screenshot(omit_background=True, type="png")
            return RenderedSubtitle(png_bytes, img_width, img_height)
        except Exception as e:
            raise RuntimeError(f"Error rendering '{word.text}' with tags '{word.tags}': {e}")

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
