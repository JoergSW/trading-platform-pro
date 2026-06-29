from trading_platform.application.results.result import Result

def test_result():
    r=Result[int](True, value=5)
    assert r.success and r.value==5
