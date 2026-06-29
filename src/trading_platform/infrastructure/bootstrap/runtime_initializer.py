class RuntimeInitializer:
    def __init__(self):
        self._steps = []

    def add(self, step):
        self._steps.append(step)

    def initialize(self):
        for step in self._steps:
            step()
