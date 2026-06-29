class HealthService:
    def __init__(self):
        self._checks=[]

    def register(self, check):
        self._checks.append(check)

    def run(self):
        return [c() for c in self._checks]
