from trading_platform.kernel.application import Application
def test_start_stop():
    app=Application()
    app.start()
    assert app.running
    app.stop()
    assert not app.running
