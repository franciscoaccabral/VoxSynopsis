from __future__ import annotations

from PyQt5.QtWidgets import QApplication

from vox_synopsis_fast_whisper import FastWhisperSettingsDialog


def test_get_settings_returns_updated_values(monkeypatch):
    _ = QApplication.instance() or QApplication([])
    dialog = FastWhisperSettingsDialog({"model": "medium"})
    dialog.model_combo.setCurrentText("small")
    dialog.language_combo.setCurrentText("en")
    dialog.device_combo.setCurrentText("cpu")
    dialog.compute_type_combo.setCurrentText(dialog.compute_type_combo.itemText(0))
    dialog.vad_filter_checkbox.setChecked(False)
    dialog.temperature_slider.setValue(5)
    dialog.best_of_slider.setValue(3)
    dialog.beam_size_slider.setValue(3)
    dialog.condition_checkbox.setChecked(False)
    dialog.initial_prompt_edit.setText("hello")
    dialog.acceleration_spinbox.setValue(2.0)
    settings = dialog.get_settings()

    assert settings["model"] == "small"
    assert settings["language"] == "en"
    assert settings["device"] == "cpu"
    assert settings["vad_filter"] is False
    assert settings["temperature"] == 0.5
    assert settings["best_of"] == 3
    assert settings["beam_size"] == 3
    assert settings["condition_on_previous_text"] is False
    assert settings["initial_prompt"] == "hello"
    assert settings["acceleration_factor"] == 2.0
