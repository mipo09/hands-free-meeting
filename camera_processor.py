import cv2
import mediapipe as mp


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

                # 人差し指の先端
                index_finger = hand_landmarks[8]

                height, width, _ = frame.shape

                x = int(index_finger.x * width)
                y = int(index_finger.y * height)

                # 指先に円を表示
                cv2.circle(
                    frame,
                    (x, y),
                    10,
                    (0, 0, 255),
                    -1
                )

                # 座標表示
                cv2.putText(
                    frame,
                    f"Index: ({x}, {y})",
                    (x + 10, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

        # カメラ映像表示
        cv2.imshow(
            "Meeting Camera",
            frame
        )

        # Qキーで終了
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


# =========================
# 終了処理
# =========================

camera.release()
cv2.destroyAllWindows()