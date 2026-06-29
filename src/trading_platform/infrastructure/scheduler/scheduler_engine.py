from trading_platform.infrastructure.scheduler.job import Job

class SchedulerEngine:
    def __init__(self) -> None:
        self._jobs: list[Job] = []

    def register(self, job: Job) -> None:
        self._jobs.append(job)

    def run_once(self) -> None:
        for job in list(self._jobs):
            job.run()

    def job_names(self) -> tuple[str, ...]:
        return tuple(job.name for job in self._jobs)
