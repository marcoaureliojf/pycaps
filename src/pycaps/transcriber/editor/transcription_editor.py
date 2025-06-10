import json
import threading
from contextlib import closing
import socket
from pycaps.common import Document
import webview
import queue
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler

_result_queue = queue.Queue()
class _Api:
    def save(self, document_dict):
        print("API: save() called.")
        _result_queue.put(document_dict)
        if webview.active_window():
            webview.active_window().destroy()

    def cancel(self):
        print("API: cancel() called.")
        _result_queue.put(None)
        if webview.active_window():
            webview.active_window().destroy()

class _EditorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, document: str, **kwargs):
        self._document = document
        super().__init__(*args, **kwargs)

    def do_GET(self):
        if self.path != '/':
            return super().do_GET()

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        template_path = os.path.join(os.path.dirname(__file__), 'editor.html')
        with open(template_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        html_content = html_content.replace('{{document}}', self._document)
        self.wfile.write(html_content.encode())

class TranscriptionEditor:

    def run(self, document: Document) -> Document:
        port = self._find_free_port()
        doc_json_str = json.dumps(document.to_dict())
        doc_json_str = doc_json_str.replace('`', '\\`')
        
        server_started = threading.Event()
        server, thread = self._run_server(port, doc_json_str, server_started)
        
        server_started.wait()
        
        url = f"http://127.0.0.1:{port}"
        window_title = "Subtitle Editor"
        
        api = _Api()
        
        webview.create_window(
            window_title,
            url,
            width=1200,
            height=800,
            resizable=True,
            js_api=api
        )
        
        print(f"Launching pywebview window loading {url}...")
        webview.start()
        
        print("Window closed, application shutting down.")
        server.shutdown()
        thread.join()
        
        try:
            edited_doc_dict = _result_queue.get_nowait()
            if edited_doc_dict:
                return Document.from_dict(edited_doc_dict)
        except queue.Empty:
            print("Editor was closed without saving/cancelling.")
            return document
        
        return document
    
    def _run_server(self, port: int, document: str, server_started: threading.Event):
        handler = lambda *args: _EditorHandler(*args, document=document)
        server = HTTPServer(('127.0.0.1', port), handler)
        
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        server_started.set()
        return server, thread

    def _find_free_port(self):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            s.bind(('', 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            return s.getsockname()[1]