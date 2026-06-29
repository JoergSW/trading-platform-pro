class Pipeline:
    def __init__(self):
        self._behaviors=[]

    def add(self, behavior):
        self._behaviors.append(behavior)

    def execute(self, request, handler):
        current = handler
        for behavior in reversed(self._behaviors):
            nxt = current
            current = lambda req, b=behavior, n=nxt: b.invoke(req, n)
        return current(request)
