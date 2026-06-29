class HandlerRegistry:
    def __init__(self):
        self._handlers={}

    def register(self, message_type, handler):
        self._handlers[message_type]=handler

    def resolve(self, message_type):
        return self._handlers[message_type]
