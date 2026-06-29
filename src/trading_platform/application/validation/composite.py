class CompositeValidator:
    def __init__(self,*validators):
        self._validators=validators

    def validate(self,value):
        for validator in self._validators:
            validator.validate(value)
