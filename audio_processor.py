
import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
import ollama


def list_microphones():
    """使用可能なマイクを表示する"""

    devices = sd.query_devices()
    available = []

    for i, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            print(f"{i}: {device['name']}")
            available.append(i)

    return available


def record_audio(output_path, device_id, stop_event):
    """終了指示が来るまで録音する"""

    samplerate = 16000
    channels = 1
    chunks = []

    def callback(indata, frames, time_info, status):
        if status:
            print("音声警告:", status)

        chunks.append(indata.copy())

    print("音声録音を開始します")

    with sd.InputStream(
        device=device_id,
        samplerate=samplerate,
        channels=channels,
        dtype="float32",
        callback=callback
    ):
        # カメラ側から終了指示が来るまで待つ
        stop_event.wait()

    if chunks:
        audio_data = np.concatenate(chunks, axis=0)

        sf.write(
            str(output_path),
            audio_data,
            samplerate
        )

        print("音声を保存しました:", output_path)
    else:
        print("録音データがありません")
