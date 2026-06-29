class FakeHandler:
    def __init__(self, result=None):
        self.result=result
        self.calls=[]

    def __call__(self, message):
        self.calls.append(message)
        return self.result
