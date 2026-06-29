from trading_platform.infrastructure.files.file_writer import FileWriter

def test_file_writer(tmp_path):
    path = tmp_path / "out" / "file.txt"
    FileWriter().write_text(path, "ok")
    assert path.read_text(encoding="utf-8") == "ok"
