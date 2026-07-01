from __future__ import annotations

from pathlib import Path

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".idea",
    ".vscode",
    ".tox",
}

EXCLUDE_FILES = {
    "PROJECT_TREE.txt",
}


def write_tree(path: Path, prefix: str, lines: list[str]) -> None:
    entries = sorted(
        (
            entry
            for entry in path.iterdir()
            if entry.name not in EXCLUDE_DIRS and entry.name not in EXCLUDE_FILES
        ),
        key=lambda p: (p.is_file(), p.name.lower()),
    )

    for index, entry in enumerate(entries):
        last = index == len(entries) - 1
        branch = "└── " if last else "├── "

        lines.append(f"{prefix}{branch}{entry.name}")

        if entry.is_dir():
            extension = "    " if last else "│   "
            write_tree(entry, prefix + extension, lines)


def main() -> None:
    root = Path(__file__).resolve().parent.parent

    lines = [root.name]

    write_tree(root, "", lines)

    output = root / "PROJECT_TREE.txt"
    output.write_text("\n".join(lines), encoding="utf-8")

    print(f"Created: {output}")


if __name__ == "__main__":
    main()
