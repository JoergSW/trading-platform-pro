from trading_platform.application.mediators.mediator import Mediator

class D:
    def dispatch(self,k,m): return (k,m)

def test_mediator():
    med=Mediator(D())
    assert med.send("x",1)==("x",1)
