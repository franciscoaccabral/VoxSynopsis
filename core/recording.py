"""Recording thread for continuous audio capture."""

import datetime
import os
from typing import TypedDict

import noisereduce as nr
import numpy as np
import sounddevice as sd
import soundfile as sf
from PyQt5.QtCore import QThread, pyqtSignal

from .config import SAMPLE_RATE, OUTPUT_DIR


class DeviceInfo(TypedDict):
    name: str
    index: int
    max_input_channels: int


class RecordingThread(QThread):
    status_update = pyqtSignal(dict)
    recording_error = pyqtSignal(str)

    def __init__(
        self,
        device_index: int,
        channels: int,
        output_path: str,
        apply_processing: bool,
        chunk_duration_seconds: int,
    ) -> None:
        super().__init__()
        self.device_index = device_index
        self.channels = channels
        self.output_path = output_path
        self.apply_processing = apply_processing
        self.chunk_duration_seconds = chunk_duration_seconds
        self._is_running = False
        self.total_recorded_time = 0

    def run(self):
        self._is_running = True
        try:
            while self._is_running:
                current_chunk_data = []
                chunk_start_time = self.total_recorded_time
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(self.output_path, f"gravacao_{timestamp}.wav")
                with sd.InputStream(
                    samplerate=SAMPLE_RATE,
                    device=self.device_index,
                    channels=self.channels,
                    dtype="float32",
                ) as stream:
                    print(f"Iniciando novo trecho. Salvando em: {filename}")
                    for _ in range(
                        int(SAMPLE_RATE * self.chunk_duration_seconds / 1024)
                    ):
                        if not self._is_running:
                            break
                        audio_chunk, overflowed = stream.read(1024)
                        if overflowed:
                            print("Aviso: Overflow de buffer de áudio detectado.")
                        current_chunk_data.append(audio_chunk)
                        volume_level = np.sqrt(np.mean(audio_chunk**2))
                        time_in_chunk = (len(current_chunk_data) * 1024) / SAMPLE_RATE
                        self.total_recorded_time = chunk_start_time + time_in_chunk
                        self.status_update.emit(
                            {
                                "total_time": self.total_recorded_time,
                                "chunk_time_remaining": (
                                    self.chunk_duration_seconds - time_in_chunk
                                ),
                                "volume": volume_level * 100,
                            }
                        )
                    if not self._is_running and len(current_chunk_data) > 0:
                        print("Gravação interrompida, salvando trecho parcial.")
                        sf.write(
                            filename, np.concatenate(current_chunk_data), SAMPLE_RATE
                        )
                        break
                if self._is_running:
                    print(
                        f"Trecho de {self.chunk_duration_seconds}s completo. "
                        "Salvando..."
                    )
                    full_audio_data = np.concatenate(current_chunk_data)
                    sf.write(filename, full_audio_data, SAMPLE_RATE)
                    if self.apply_processing:
                        self.process_audio(filename, full_audio_data)
        except Exception as e:
            error_message = f"Erro durante a gravação: {e}"
            print(error_message)
            self.recording_error.emit(error_message)

    def process_audio(self, original_filepath: str, audio_data: np.ndarray) -> None:
        try:
            print(f"Aplicando pós-processamento em {original_filepath}...")
            noise_sample_len = int(0.5 * SAMPLE_RATE)
            noise_clip = audio_data[:noise_sample_len]
            reduced_noise_audio = nr.reduce_noise(
                y=audio_data,
                sr=SAMPLE_RATE,
                y_noise=noise_clip,
                prop_decrease=1.0,
                stationary=True,
            )
            peak_level = np.max(np.abs(reduced_noise_audio))
            if peak_level > 0:
                target_peak_dbfs = -1.0
                target_peak_linear = 10 ** (target_peak_dbfs / 20.0)
                normalization_factor = target_peak_linear / peak_level
                normalized_audio = reduced_noise_audio * normalization_factor
            else:
                normalized_audio = reduced_noise_audio
            base, ext = os.path.splitext(original_filepath)
            processed_filepath = f"{base}_processed{ext}"
            sf.write(processed_filepath, normalized_audio, SAMPLE_RATE)
            print(f"Arquivo processado salvo em: {processed_filepath}")
        except Exception as e:
            print(f"Falha no pós-processamento de {original_filepath}: {e}")

    def stop(self):
        self._is_running = False
        print("Sinal de parada recebido.")