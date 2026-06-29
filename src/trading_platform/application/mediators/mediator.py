class Mediator:
    def __init__(self, dispatcher):
        self.dispatcher=dispatcher
    def send(self,key,message):
        return self.dispatcher.dispatch(key,message)
