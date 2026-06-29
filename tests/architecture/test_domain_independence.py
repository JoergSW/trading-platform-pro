from pathlib import Path


def test_domain_layer_does_not_import_infrastructure_or_presentation() -> None:
    domain_root = Path("src/trading_platform/domain")
    forbidden = ("trading_platform.infrastructure", "trading_platform.presentation")

    if not domain_root.exists():
        return

    for file in domain_root.rglob("*.py"):
        content = file.read_text(encoding="utf-8")
        assert not any(token in content for token in forbidden), file
