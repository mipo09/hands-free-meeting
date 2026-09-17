import sounddevice as sd
import soundfile as sf
import numpy as np
import whisper
import os
import ollama


samplerate = 16000
channels = 1

recording = []

import ctypes

# Windowsがスリープしないようにする
def prevent_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(
        0x80000000 | 0x00000001 | 0x00000002
    )

# スリープ防止を解除する
def allow_sleep():
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)



def callback(indata, frames, time, status):
    if status:
        print(status)
    recording.append(indata.copy())

#＝＝＝会議フォルダーの作成＝＝＝
from datetime import datetime


meeting_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

meeting_dir = os.path.join("meeting_data", meeting_id)

os.makedirs(meeting_dir, exist_ok=True)


audio_dir = os.path.join(meeting_dir, "audio")
transcript_dir = os.path.join(meeting_dir, "transcript")
camera_dir = os.path.join(meeting_dir, "camera")
summary_dir = os.path.join(meeting_dir, "summary")
whiteboard_dir = os.path.join(meeting_dir, "whiteboard")

for d in [
    audio_dir,
    transcript_dir,
    camera_dir,
    summary_dir,
    whiteboard_dir
]:
    os.makedirs(d, exist_ok=True)

print("利用目的を選択してください")
print("1：会議")
print("2：授業")

while True:
    purpose = input("番号を入力してください：")

    if purpose == "1":
        purpose_name = "会議"
        break
    elif purpose == "2":
        purpose_name = "授業"
        break
    else:
        print("1 または 2 を入力してください。")

theme = input(f"{purpose_name}のテーマを入力してください：")

print("Enterキーを押すと録音を開始します。")
input()

print("録音中...")
print("もう一度Enterキーを押すと録音を終了します。")

# 録音中はスリープを防止
prevent_sleep()

try:
    with sd.InputStream(
        device=1,
        samplerate=samplerate,
        channels=channels,
        callback=callback
    ):
        input()

finally:
    # 録音終了後は通常の状態に戻す
    allow_sleep()

print("録音終了")

audio = np.concatenate(recording, axis=0)

audio_path = os.path.join(audio_dir, "record.wav")

sf.write(audio_path, audio, samplerate)

print("文字起こし中...")

model = whisper.load_model("base")

result = model.transcribe(audio_path, language="ja")

print("\n======================")
print("文字起こし結果")
print("======================")
print(result["text"])
print("======================")


#＝＝＝文字起こし結果の保存＝＝＝
transcript_path = os.path.join(
    transcript_dir,
    "transcript.txt"
)

with open(transcript_path, "w", encoding="utf-8") as f:
    f.write(result["text"])
    
print(f"文字起こし結果を {transcript_path} に保存しました。")

#＝＝＝要約＝＝＝
# 会議データ
meeting_data = {
    "purpose": purpose_name,
    "theme": theme,
    "transcript": result["text"],
    "events": [],      # 今は空、後でカメラの検知結果を追加
    "participants": [],
}

#要約プロンプト
prompt = f"""
あなたは音声から会議や授業の内容を整理するAIです。

以下の情報をもとに、内容を正確に整理してください。

【用途】
{meeting_data['purpose']}

【テーマ】
{meeting_data['theme']}

【重要イベント】
{meeting_data['events']}

【文字起こし】
{meeting_data['transcript']}

重要イベントがある場合は、そのイベント付近の発言を特に重視してください。

重要イベントとして検出された情報は、通常の要約で省略してはいけない。

ただし、文字起こしに存在しない情報を推測して追加してはいけません。

挙手イベントでは、その時刻付近の発言内容を重要情報として扱う。
指さしイベントでは、指さした場所の文字・内容を重要情報として扱う。


━━━━━━━━━━━━━━━━━━
【用途による整理方法】
━━━━━━━━━━━━━━━━━━

■ 会議の場合

以下を整理してください。

【要約】
会議全体の内容を簡潔にまとめる。

【決定事項】
会議で決定した内容。

【ToDo】
誰が何をするのか。

【保留事項】
まだ決まっていないこと。

【次回までの課題】
次回までに行うこと。

━━━━━━━━━━━━━━━━━━

■ 授業の場合

以下を整理してください。

【授業の要点】
授業で説明された重要な内容。

【重要な用語】
授業で登場した重要な用語と、その意味。

【重要な説明】
先生が詳しく説明した内容。

【覚えておきたいこと】
テストや今後の学習に役立つ重要事項。

【課題・提出物】
授業中に出された課題や提出物。

【次回までにやること】
次回の授業までに必要なこと。

━━━━━━━━━━━━━━━━━━

用途が「会議」の場合は会議用の形式、
「授業」の場合は授業用の形式を使用してください。

文章は短く、ホワイトボードに書くような
簡潔な表現にしてください。
"""

# ===== Gemma 3 4Bで要約 =====

print("Gemma 3 4Bで要約中...")

response = ollama.chat(
    model="gemma3:4b",
    messages=[
        {
            "role": "user",
            "content": prompt
        }
    ]
)

summary = response.message.content

print("\n======================")
print("AIによる要約")
print("======================")
print(summary)
print("======================")


# ===== 要約結果を保存 =====

summary_path = os.path.join(
    summary_dir,
    "summary.txt"
)

with open(summary_path, "w", encoding="utf-8") as f:
    f.write(summary)

print(f"要約結果を {summary_path} に保存しました。")