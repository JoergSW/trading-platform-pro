from trading_platform.kernel.service_registry import ServiceRegistry
def test_registry():
    r=ServiceRegistry()
    obj=object()
    r.register("x",obj)
    assert r.resolve("x") is obj
