from __future__ import annotations

import numpy as np

from vox_synopsis_fast_whisper import RecordingThread


def test_process_audio_creates_file(tmp_path, monkeypatch):
    audio_data = np.ones(48000, dtype=np.float32)
    thread = RecordingThread(0, 1, str(tmp_path), True, 60)

    def fake_reduce_noise(*args, **kwargs):
        return audio_data

    written = {}

    def fake_write(path: str, data: np.ndarray, sr: int) -> None:
        written["path"] = path
        written["data"] = data
        written["sr"] = sr

    monkeypatch.setattr(
        "vox_synopsis_fast_whisper.nr.reduce_noise",
        fake_reduce_noise,
        raising=False,
    )
    monkeypatch.setattr(
        "vox_synopsis_fast_whisper.sf.write",
        fake_write,
        raising=False,
    )
    thread.process_audio(str(tmp_path / "input.wav"), audio_data)

    # Calcula o áudio esperado após a normalização,
    # espelhando a lógica da função original.
    peak_level = np.max(np.abs(audio_data))
    if peak_level > 0:
        target_peak_dbfs = -1.0
        target_peak_linear = 10 ** (target_peak_dbfs / 20.0)
        normalization_factor = target_peak_linear / peak_level
        expected_audio = audio_data * normalization_factor
    else:
        expected_audio = audio_data

    expected_path = tmp_path / "input_processed.wav"
    assert written["path"] == str(expected_path)
    assert np.allclose(written["data"], expected_audio)
    assert written["sr"] == 48000
