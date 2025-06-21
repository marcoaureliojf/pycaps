class AudioElement:
    def __init__(self, path: str, start: float):
        self._path = path
        self._start = start

    @property
    def path(self):
        return self._path
    
    @property
    def start(self):
        return self._start
