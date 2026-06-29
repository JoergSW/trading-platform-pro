from trading_platform.application.results.factory import ResultFactory

def test_result_factory():
    ok = ResultFactory.ok(5)
    assert ok.success and ok.value == 5
    fail = ResultFactory.fail("x")
    assert not fail.success and fail.error == "x"
