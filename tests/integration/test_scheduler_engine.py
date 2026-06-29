from trading_platform.infrastructure.scheduler.job import Job
from trading_platform.infrastructure.scheduler.scheduler_engine import SchedulerEngine

def test_scheduler_engine_runs_registered_jobs():
    state = {"value": 0}
    scheduler = SchedulerEngine()
    scheduler.register(Job("increment", lambda: state.__setitem__("value", 1)))
    scheduler.run_once()
    assert state["value"] == 1
    assert scheduler.job_names() == ("increment",)
