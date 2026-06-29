from .entity import Entity

class AggregateRoot(Entity):
    def __init__(self, id:str):
        super().__init__(id)
        self._events=[]

    def add_event(self,event):
        self._events.append(event)

    def pull_events(self):
        events=list(self._events)
        self._events.clear()
        return events
