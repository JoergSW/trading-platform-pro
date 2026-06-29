class Dispatcher:
    def __init__(self):
        self._handlers = {}

    def register(self, key, handler):
        self._handlers[key] = handler

    def dispatch(self, key, message):
        return self._handlers[key](message)
