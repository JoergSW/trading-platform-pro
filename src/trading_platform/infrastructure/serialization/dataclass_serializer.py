from dataclasses import asdict, is_dataclass

class DataclassSerializer:
    def to_dict(self, value):
        if not is_dataclass(value):
            raise TypeError("Value must be a dataclass instance.")
        return asdict(value)
