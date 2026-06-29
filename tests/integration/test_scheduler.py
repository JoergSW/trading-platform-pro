from trading_platform.infrastructure.scheduler.scheduler import Scheduler
def test_scheduler_runs_registered_jobs():
    s=Scheduler()
    state={"ok":False}
    s.register("job",lambda: state.__setitem__("ok",True))
    s.run_all()
    assert state["ok"]
