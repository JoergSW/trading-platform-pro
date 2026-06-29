from collections.abc import Callable
class Scheduler:
    def __init__(self):
        self._jobs=[]
    def register(self,name:str,job:Callable)->None:
        self._jobs.append((name,job))
    def run_all(self):
        for _,job in self._jobs:
            job()
