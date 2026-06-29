class MessageDispatcher:
    def __init__(self) -> None:
        self._routes = {}

    def register(self, message_type, handler) -> None:
        self._routes[message_type] = handler

    def dispatch(self, message):
        handler = self._routes[type(message)]
        return handler(message)
