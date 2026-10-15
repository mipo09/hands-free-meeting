
import cv2
import mediapipe as mp
import easyocr
import json
import time
import math
from pathlib import Path
from datetime import datetime


# =========================
# 基本設定
# =========================

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "hand_landmarker.task"
OUTPUT_PATH = BASE_DIR / "events.json"

POINTING_SECONDS = 1.0
STABLE_DISTANCE = 35
OCR_MARGIN = 100

WINDOW_NAME = "Meeting Camera"

# MediaPipe
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


# =========================
# カメラ選択
# =========================

def select_camera():
    available = []

    print("カメラを検索しています...")

    for camera_id in range(5):
        cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)

        if cap.isOpened():
            ret, frame = cap.read()

            if ret:
                available.append(camera_id)
                print(f"{camera_id}: 使用可能")

        cap.release()

    if not available:
        raise RuntimeError("カメラが見つかりません。")

    while True:
        try:
            selected = int(input("カメラ番号を入力: "))

            if selected in available:
                return selected

            print("一覧にある番号を入力してください。")

        except ValueError:
            print("数字を入力してください。")


# =========================
# 指さし判定
# =========================

def is_pointing(hand):

    def distance(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    def extended(tip, pip, mcp):
        return distance(hand[tip], hand[mcp]) > (
            distance(hand[pip], hand[mcp]) * 1.5
        )

    return (
        extended(8, 6, 5)
        and not extended(12, 10, 9)
        and not extended(16, 14, 13)
        and not extended(20, 18, 17)
    )


# =========================
# ボードの範囲設定
# =========================

def select_board(camera):

    print("ホワイトボードの範囲を選択してください。")
    print("マウスで囲んでEnter、キャンセルはCです。")

    while True:
        ret, frame = camera.read()

        if ret:
            break

    roi = cv2.selectROI(
        "Select Whiteboard",
        frame,
        fromCenter=False,
        showCrosshair=True
    )

    cv2.destroyWindow("Select Whiteboard")

    x, y, w, h = map(int, roi)

    if w == 0 or h == 0:
        raise RuntimeError("範囲が選択されませんでした。")

    return (x, y, w, h)



# =========================
# OCR（指先に近い文字を選択）
# =========================

def recognize_text(reader, frame, point, board_roi):

    px, py = point
    bx, by, bw, bh = board_roi

    # 指先周辺の範囲を取得
    x1 = max(bx, px - OCR_MARGIN)
    y1 = max(by, py - OCR_MARGIN)

    x2 = min(bx + bw, px + OCR_MARGIN)
    y2 = min(by + bh, py + OCR_MARGIN)

    if x1 >= x2 or y1 >= y2:
        return ""

    cropped = frame[y1:y2, x1:x2].copy()

    # グレースケール化
    gray = cv2.cvtColor(
        cropped,
        cv2.COLOR_BGR2GRAY
    )

    # コントラスト改善
    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # OCRを実行
    results = reader.readtext(
        enhanced,
        detail=1,
        paragraph=False
    )

    nearest_text = ""
    nearest_distance = float("inf")

    for bbox, text, confidence in results:

        # 信頼度の低い結果は除外
        if confidence < 0.3:
            continue

        # 文字領域の中心
        center_x = sum(p[0] for p in bbox) / 4 + x1
        center_y = sum(p[1] for p in bbox) / 4 + y1

        # 指先との距離
        distance = math.hypot(
            center_x - px,
            center_y - py
        )

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_text = text

    return nearest_text



# =========================
# JSON保存
# =========================

def save_events(events):

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            events,
            f,
            ensure_ascii=False,
            indent=4
        )


# =========================
# メイン処理
# =========================

def main(stop_event, meeting_dir, start_time):

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"モデルが見つかりません: {MODEL_PATH}"
        )

    camera_id = select_camera()

    camera = cv2.VideoCapture(
        camera_id,
        cv2.CAP_DSHOW
    )

    if not camera.isOpened():
        raise RuntimeError("カメラを起動できません。")

    events = []
    global OUTPUT_PATH
    OUTPUT_PATH = meeting_dir / "events.json"

    # OCRモデルの読み込み
    print("OCRを準備しています...")
    reader = easyocr.Reader(
        ["ja", "en"],
        gpu=False
    )

    options = HandLandmarkerOptions(
        base_options=BaseOptions(
            model_asset_path=str(MODEL_PATH)
        ),
        running_mode=VisionRunningMode.IMAGE,
        num_hands=2,
        min_hand_detection_confidence=0.5,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5
    )

    try:
        board_roi = select_board(camera)


        stable_point = None
        stable_start = None
        already_recorded = False

        cv2.namedWindow(WINDOW_NAME)

        with HandLandmarker.create_from_options(options) as landmarker:

            while True:

                ret, frame = camera.read()

                if not ret:
                    print("映像を取得できません。")
                    break

                # OCR用に描画前の画像を保持
                clean_frame = frame.copy()

                height, width = frame.shape[:2]

                rgb = cv2.cvtColor(
                    frame,
                    cv2.COLOR_BGR2RGB
                )

                mp_image = mp.Image(
                    image_format=mp.ImageFormat.SRGB,
                    data=rgb
                )

                result = landmarker.detect(mp_image)

                bx, by, bw, bh = board_roi

                # ボード領域を表示
                cv2.rectangle(
                    frame,
                    (bx, by),
                    (bx + bw, by + bh),
                    (255, 0, 0),
                    2
                )

                # 最初は1つの指さし候補を追跡する
                pointing_position = None

                if result.hand_landmarks:

                    for hand in result.hand_landmarks:

                        if not is_pointing(hand):
                            continue

                        tip = hand[8]

                        x = int(tip.x * width)
                        y = int(tip.y * height)

                        # 指先がボード内にあるか
                        inside = (
                            bx <= x <= bx + bw
                            and by <= y <= by + bh
                        )

                        if inside:
                            pointing_position = (x, y)
                            break

                if pointing_position is not None:

                    x, y = pointing_position
                    now = time.monotonic()

                    cv2.circle(
                        frame,
                        (x, y),
                        10,
                        (0, 255, 0),
                        -1
                    )

                    # 初めて指さしを検出
                    if stable_point is None:
                        stable_point = (x, y)
                        stable_start = now
                        already_recorded = False

                    # 指先の移動距離
                    movement = math.dist(
                        stable_point,
                        (x, y)
                    )

                    if movement > STABLE_DISTANCE:
                        stable_point = (x, y)
                        stable_start = now
                        already_recorded = False

                    elapsed = now - stable_start

                    cv2.putText(
                        frame,
                        f"POINTING {elapsed:.1f}s",
                        (20, 35),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (0, 255, 0),
                        2
                    )

                    # 一定時間安定したら記録
                    if (
                        elapsed >= POINTING_SECONDS
                        and not already_recorded
                    ):

                        print("指さしを検出しました。OCR実行中...")

                        recognized = recognize_text(
                            reader,
                            clean_frame,
                            (x, y),
                            board_roi
                        )

                        event = {
                            "type": "pointing",
                            "timestamp": round(
                                now - start_time, 2
                            ),
                            "datetime": datetime.now().isoformat(
                                timespec="seconds"
                            ),
                            "position": {
                                "x": x,
                                "y": y
                            },
                            "text": recognized
                        }

                        events.append(event)
                        save_events(events)

                        print("保存しました:", event)

                        already_recorded = True

                else:
                    stable_point = None
                    stable_start = None
                    already_recorded = False

                cv2.imshow(WINDOW_NAME, frame)

                key = cv2.waitKey(10) & 0xFF

                if key in (ord("q"), ord("Q"), 27):
                    print("カメラと録音を終了します。")
                    stop_event.set()
                    break

                if cv2.getWindowProperty(
                    WINDOW_NAME,
                    cv2.WND_PROP_VISIBLE
                ) < 1:
                    stop_event.set()
                    break

    finally:
        stop_event.set()
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    print("main.pyから起動してください。")
