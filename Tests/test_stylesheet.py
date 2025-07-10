from vox_synopsis_fast_whisper import load_stylesheet


class DummyApp:
    def __init__(self) -> None:
        self.style = ""

    def setStyleSheet(self, style: str) -> None:  # noqa: N802 - Qt style
        self.style = style


def test_load_stylesheet_success(tmp_path, monkeypatch):
    style_path = tmp_path / "style.qss"
    style_content = "QWidget { color: red; }"
    style_path.write_text(style_content)
    monkeypatch.chdir(tmp_path)
    app = DummyApp()
    load_stylesheet(app)
    assert app.style == style_content


def test_load_stylesheet_missing(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    app = DummyApp()
    load_stylesheet(app)
    captured = capsys.readouterr()
    assert "style.qss" in captured.out
