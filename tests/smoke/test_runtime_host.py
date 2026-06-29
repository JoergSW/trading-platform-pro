from trading_platform.runtime.runtime_host import RuntimeHost
class App:
    def __init__(self): self.running=False
    def start(self): self.running=True
    def stop(self): self.running=False
def test_runtime():
    a=App(); h=RuntimeHost(a); h.start(); assert a.running; h.stop(); assert not a.running
