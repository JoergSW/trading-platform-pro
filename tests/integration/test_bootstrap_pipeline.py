from trading_platform.kernel.bootstrap_pipeline import BootstrapPipeline

def test_pipeline():
    state=[]
    p=BootstrapPipeline()
    p.add_step(lambda: state.append(1))
    p.add_step(lambda: state.append(2))
    p.execute()
    assert state==[1,2]
