from pycaps.common import ElementState, Tag
import webview
import os
from ..renderer_page import RendererPage

class _Api:
    def __init__(self, custom_css: str):
        self._renderer_page: RendererPage = RendererPage()
        self._custom_css = custom_css

    def get_renderer_html(self, current_segment_data: dict) -> str:
        segment = current_segment_data
        line = segment['line']
        words = line['words']
        return self._renderer_page.get_html(
            custom_css=self._custom_css,
            segment_tags=segment['tags'],
            line_tags=line['tags'],
            line_state=ElementState(line['state']),
            words=[word['text'] for word in words],
            word_tags=[[Tag(tag) for tag in word['tags']] for word in words],
            word_states=[ElementState(word['state']) for word in words],
        )

class CssSubtitlePreviewer:

    def run(self, custom_css: str) -> None:
        html_file_path = os.path.join(os.path.dirname(__file__), 'previewer.html')
        html_content = open(html_file_path, 'r', encoding='utf-8').read()

        window_title = "Subtitle Previewer"
        api = _Api(custom_css)
        webview.create_window(
            window_title,
            html=html_content,
            width=1200,
            height=800,
            resizable=True,
            js_api=api
        )
        webview.start(debug=True)
