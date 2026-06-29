from collections import defaultdict

class EventBus:
    def __init__(self):
        self._handlers=defaultdict(list)

    def subscribe(self,event_name,handler):
        self._handlers[event_name].append(handler)

    def publish(self,event):
        for h in self._handlers.get(event.name,()):
            h(event)
