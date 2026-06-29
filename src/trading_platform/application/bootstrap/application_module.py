class ApplicationModule:
    def __init__(self):
        self.registrations=[]

    def register(self, name, service):
        self.registrations.append((name, service))
