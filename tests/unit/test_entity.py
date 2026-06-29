from trading_platform.domain.base.entity import Entity

def test_entity_equality():
    assert Entity("1")==Entity("1")
