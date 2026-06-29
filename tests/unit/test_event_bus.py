from trading_platform.kernel.event_bus import EventBus
from trading_platform.shared.events.base import Event

def test_publish():
    bus=EventBus()
    called=[]
    bus.subscribe("X", lambda e: called.append(e.name))
    bus.publish(Event("X"))
    assert called==["X"]
