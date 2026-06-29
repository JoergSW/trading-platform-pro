from trading_platform.infrastructure.events.event_store import InMemoryEventStore

def test_event_store():
    store = InMemoryEventStore()
    store.append("event")
    assert store.all() == ("event",)
