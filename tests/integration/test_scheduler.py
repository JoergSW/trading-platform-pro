from trading_platform.infrastructure.scheduler.scheduler import Scheduler
def test_scheduler():
    s=Scheduler()
    x={"v":0}
    s.add(lambda:x.__setitem__("v",1))
    s.run_pending()
    assert x["v"]==1
