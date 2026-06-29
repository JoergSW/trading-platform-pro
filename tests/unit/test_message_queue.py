from trading_platform.infrastructure.messaging.in_memory_message_queue import InMemoryMessageQueue

def test_message_queue():
    q = InMemoryMessageQueue()
    q.enqueue("x")
    assert q.size() == 1
    assert q.dequeue() == "x"
    assert q.dequeue() is None
