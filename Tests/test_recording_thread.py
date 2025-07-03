from __future__ import annotations

import numpy as np

from vox_synopsis_fast_whisper import RecordingThread


def test_process_audio_creates_file(tmp_path, monkeypatch):
    audio_data = np.ones(48000, dtype=np.float32)
    thread = RecordingThread(0, 1, str(tmp_path), True)

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
    expected = tmp_path / "input_processed.wav"
    assert written["path"] == str(expected)
    assert np.array_equal(written["data"], audio_data)
    assert written["sr"] == 48000
