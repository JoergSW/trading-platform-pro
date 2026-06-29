from trading_platform.application.dispatching.dispatcher import Dispatcher

def test_dispatcher():
    d = Dispatcher()
    d.register("x", lambda m: m + 1)
    assert d.dispatch("x", 1) == 2
