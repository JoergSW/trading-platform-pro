class QueryBus:
    def __init__(self):
        self._handlers={}
    def register(self,query_type,handler):
        self._handlers[query_type]=handler
    def execute(self,query):
        return self._handlers[type(query)](query)
