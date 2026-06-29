class HealthReport:
    def __init__(self):
        self.entries=[]
    def add(self,name,status):
        self.entries.append((name,status))
