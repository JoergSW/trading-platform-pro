from trading_platform.kernel.event_bus import EventBus
from trading_platform.domain.events.base import DomainEvent

class E(DomainEvent): pass

def test_publish():
    bus=EventBus()
    called=[]
    bus.subscribe(E, lambda e: called.append(e.event_id))
    e=E()
    bus.publish(e)
    assert called==[e.event_id]
