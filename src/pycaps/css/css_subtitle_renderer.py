from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from pathlib import Path
import tempfile
from typing import Optional
from ..models import RenderedSubtitle
from ..tagger.models import Word
from typing import List
from .css_class import CssClass
import shutil
import os
import webbrowser
from .rendered_image_cache import RenderedImageCache

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
        self._cache: RenderedImageCache = RenderedImageCache(self._custom_css)

    def set_custom_css(self, custom_css: str):
        self._custom_css = custom_css
        self._cache = RenderedImageCache(self._custom_css)

    def open(self, video_width: int, video_height: int):
        """Initializes Playwright and loads the base HTML page."""
        if self.page:
            raise RuntimeError("Renderer is already open. Call close() first.")

        calculated_vp_height = max(self.DEFAULT_MIN_VIEWPORT_HEIGHT, int(video_height * self.DEFAULT_VIEWPORT_HEIGHT_RATIO))

        self.tempdir = tempfile.TemporaryDirectory()
        self.playwright_context = sync_playwright().start()
        self.browser = self.playwright_context.chromium.launch()
        self.page = self.browser.new_page(viewport={"width": video_width, "height": calculated_vp_height})
        self._copy_resources_to_tempdir()
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
                <span id="subtitle-actual-text" class="{CssClass.WORD.value}">{text}</span>
            </div>
        </body>
        </html>
        """
        html_path = Path(self.tempdir.name) / "renderer_base.html"
        html_path.write_text(html_template, encoding="utf-8")
        return html_path

    def _copy_resources_to_tempdir(self) -> None:
        if not self.tempdir:
            raise RuntimeError("Temp directory must be initialized before copying resources.")

        cwd = Path(os.getcwd())
        resources_dir = cwd / "resources"
        if not resources_dir.exists():
            return

        destination = Path(self.tempdir.name)
        shutil.copytree(resources_dir, destination, dirs_exist_ok=True)

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

        css_classes = [CssClass.WORD.value] + css_classes
        css_classes_str = ' '.join(css_classes)
        self.page.evaluate(script, [text, css_classes_str])

    def render(self, word: Word, state_css_classes: List[CssClass] = []) -> Optional[RenderedSubtitle]:
        if not self.page:
            raise RuntimeError("Renderer is not open open() with video dimensions first.")
        
        css_classes = list(word.tags) + [c.value for c in state_css_classes]
        if self._cache.has(word.text, css_classes):
            return self._cache.get(word.text, css_classes)

        self.__update_text_and_style(word.text, css_classes)
        
        locator = self.page.locator("#subtitle-actual-text")
        try:
            bounding_box = locator.bounding_box()
            if not bounding_box or bounding_box['width'] <= 0 or bounding_box['height'] <= 0:
                # HTML element is not visible (probably hidden by CSS).
                self._cache.set(word.text, css_classes, None)
                return None

            png_bytes = locator.screenshot(omit_background=True, type="png")
            rendered_subtitle = RenderedSubtitle(png_bytes, bounding_box['width'], bounding_box['height'])
            self._cache.set(word.text, css_classes, rendered_subtitle)
            return rendered_subtitle
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
