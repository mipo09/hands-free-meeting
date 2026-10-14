import cv2
import mediapipe as mp

# =========================
# 指さし判定
# =========================

def is_pointing(hand):

    # 人差し指
    index_tip = hand[8]
    index_pip = hand[6]
    index_mcp = hand[5]

    # 中指
    middle_tip = hand[12]
    middle_pip = hand[10]
    middle_mcp = hand[9]

    # 薬指
    ring_tip = hand[16]
    ring_pip = hand[14]
    ring_mcp = hand[13]

    # 小指
    pinky_tip = hand[20]
    pinky_pip = hand[18]
    pinky_mcp = hand[17]

    # 2点間の距離
    def distance(a, b):
        return (
            (a.x - b.x) ** 2 +
            (a.y - b.y) ** 2
        ) ** 0.5

    # 指が伸びているか
    def is_extended(tip, pip, mcp):
        return distance(tip, mcp) > distance(pip, mcp) * 1.5

    index_extended = is_extended(
        index_tip, index_pip, index_mcp
    )

    middle_extended = is_extended(
        middle_tip, middle_pip, middle_mcp
    )

    ring_extended = is_extended(
        ring_tip, ring_pip, ring_mcp
    )

    pinky_extended = is_extended(
        pinky_tip, pinky_pip, pinky_mcp
    )

    return (
        index_extended
        and not middle_extended
        and not ring_extended
        and not pinky_extended
    )

# =========================
# MediaPipeの設定
# =========================

BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode


# 手の検出モデルを指定
MODEL_PATH = "hand_landmarker.task"

options = HandLandmarkerOptions(
    base_options=BaseOptions(
        model_asset_path=MODEL_PATH
    ),
    running_mode=VisionRunningMode.IMAGE,
    num_hands=2,
    min_hand_detection_confidence=0.5,
    min_hand_presence_confidence=0.5,
    min_tracking_confidence=0.5
)


# =========================
# カメラ選択
# =========================

def select_camera():

    available_cameras = []

    print("使用可能なカメラを検索しています...")

    # カメラ番号0～9を確認
    for camera_id in range(10):

        cap = cv2.VideoCapture(
            camera_id,
            cv2.CAP_DSHOW
        )

        if cap.isOpened():

            ret, frame = cap.read()

            if ret:
                available_cameras.append(camera_id)
                print(f"{camera_id}：カメラ使用可能")

        cap.release()

    if not available_cameras:
        print("使用可能なカメラがありません。")
        return None

    # カメラを選択
    while True:

        try:
            camera_id = int(
                input("使用するカメラの番号を入力してください：")
            )

            if camera_id in available_cameras:
                return camera_id

            print("一覧にある番号を入力してください。")

        except ValueError:
            print("数字を入力してください。")


# =========================
# カメラ起動
# =========================

camera_id = select_camera()

if camera_id is None:
    raise SystemExit("カメラが見つかりませんでした。")

camera = cv2.VideoCapture(
    camera_id,
    cv2.CAP_DSHOW
)

if not camera.isOpened():
    raise SystemExit("カメラを開けませんでした。")

print(f"カメラ {camera_id} を使用します。")


# =========================
# MediaPipe開始
# =========================

with HandLandmarker.create_from_options(options) as landmarker:

    while True:

        ret, frame = camera.read()

        if not ret:
            print("カメラから画像を取得できませんでした。")
            break

        # OpenCVのBGR → RGB
        frame_rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        # MediaPipe用画像
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame_rgb
        )

        # 手を検出
        result = landmarker.detect(mp_image)

        # =========================
        # 検出結果を表示
        # =========================

        if result.hand_landmarks:

            for hand_landmarks in result.hand_landmarks:

                index_finger = hand_landmarks[8]

                height, width, _ = frame.shape

                x = int(index_finger.x * width)
                y = int(index_finger.y * height)

                # 指さし判定
                pointing = is_pointing(hand_landmarks)

                if pointing:

                    color = (0, 255, 0)
                    status = "POINTING"

                else:

                    color = (0, 0, 255)
                    status = "HAND DETECTED"

                # 指先に円を表示
                cv2.circle(
                    frame,
                    (x, y),
                    10,
                    color,
                    -1
                )

                # 判定結果を表示
                cv2.putText(
                    frame,
                    status,
                    (max(0, x - 50), max(25, y - 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    color,
                    2
                )

                # 座標表示
                cv2.putText(
                    frame,
                    f"({x}, {y})",
                    (x + 10, y + 25),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2
                )

        # カメラ映像表示
        cv2.imshow(
            "Meeting Camera",
            frame
        )

        key = cv2.waitKey(10) & 0xFF
        
        # Qキーで終了
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        # ウィンドウが閉じられた場合も終了
        if cv2.getWindowProperty(
            "Meeting Camera",
            cv2.WND_PROP_VISIBLE
        ) < 1:
            print("ウィンドウが閉じられました。")
            break


# =========================
# 終了処理
# =========================

camera.release()
cv2.destroyAllWindows()