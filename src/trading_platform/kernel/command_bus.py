class CommandBus:
    def __init__(self):
        self._handlers={}
    def register(self,command_type,handler):
        self._handlers[command_type]=handler
    def dispatch(self,command):
        return self._handlers[type(command)](command)
