from pathlib import Path

def test_application_layer_does_not_import_presentation():
    root=Path("src/trading_platform/application")
    if not root.exists():
        return

    for file in root.rglob("*.py"):
        content=file.read_text(encoding="utf-8")
        assert "trading_platform.presentation" not in content, file
