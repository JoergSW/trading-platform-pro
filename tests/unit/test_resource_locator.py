from pathlib import Path
from trading_platform.infrastructure.resources.resource_locator import ResourceLocator

def test_locator():
    loc=ResourceLocator(Path('/tmp'))
    assert str(loc.get('a')).endswith('a')
