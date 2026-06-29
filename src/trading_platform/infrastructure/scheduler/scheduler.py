class Scheduler:
    def __init__(self):
        self._jobs=[]
    def add(self,job):
        self._jobs.append(job)
    def run_pending(self):
        for job in list(self._jobs):
            job()
