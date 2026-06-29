from trading_platform.infrastructure.serialization.json_serializer import JsonSerializer

def test_json():
    s=JsonSerializer()
    assert s.loads(s.dumps({"a":1}))["a"]==1
