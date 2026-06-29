from .container import Container
class Application:
    def __init__(self):
        self.container=Container()
        self.running=False
    def start(self): self.running=True
    def stop(self): self.running=False
