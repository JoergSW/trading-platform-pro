from dataclasses import dataclass
from trading_platform.infrastructure.serialization.dataclass_serializer import DataclassSerializer

@dataclass
class Sample:
    value: int

def test_dataclass_serializer():
    assert DataclassSerializer().to_dict(Sample(5)) == {"value": 5}
