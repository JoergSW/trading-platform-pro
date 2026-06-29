class BootstrapSequence:
    def __init__(self):
        self._steps=[]
    def add(self,step):
        self._steps.append(step)
    def run(self):
        for step in self._steps:
            step()
