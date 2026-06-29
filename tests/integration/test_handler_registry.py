from trading_platform.application.registry.handler_registry import HandlerRegistry

class Message:
    pass

def test_handler_registry():
    registry=HandlerRegistry()
    handler=lambda msg: "ok"
    registry.register(Message, handler)
    assert registry.resolve(Message)(Message()) == "ok"
