class RuntimeHost:
    def __init__(self,application):
        self.application=application
    def start(self):
        self.application.start()
    def stop(self):
        self.application.stop()
