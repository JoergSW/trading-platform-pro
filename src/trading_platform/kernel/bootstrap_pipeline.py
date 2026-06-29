class BootstrapPipeline:
    def __init__(self):
        self._steps=[]
    def add_step(self, step):
        self._steps.append(step)
    def execute(self):
        for step in self._steps:
            step()
