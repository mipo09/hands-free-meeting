
/* =========================
   画面を取得する
========================= */

const homeScreen = document.getElementById("homeScreen");
const themeScreen = document.getElementById("themeScreen");
const confirmScreen = document.getElementById("confirmScreen");
const recordingScreen = document.getElementById("recordingScreen");
const transcriptScreen = document.getElementById("transcriptScreen");


/* =========================
   モード選択ボタン
========================= */

const classButton = document.getElementById("classButton");
const meetingButton = document.getElementById("meetingButton");


/* =========================
   テーマ入力画面の要素
========================= */

const themeHeading = document.getElementById("themeHeading");
const themeInput = document.getElementById("themeInput");
const topicInput = document.getElementById("topicInput");


/* =========================
   画面操作ボタン
========================= */

const backButton = document.getElementById("backButton");
const nextButton = document.getElementById("nextButton");

const backToThemeButton =
    document.getElementById("backToThemeButton");

const startRecordingButton =
    document.getElementById("startRecordingButton");

const stopRecordingButton =
    document.getElementById("stopRecordingButton");

const backToInputButton =
    document.getElementById("backToInputButton");

const homeButton =
    document.getElementById("homeButton");

const previewTranscriptButton =
    document.getElementById("previewTranscriptButton");


/* =========================
   表示内容
========================= */

const confirmMode = document.getElementById("confirmMode");
const confirmTitle = document.getElementById("confirmTitle");
const confirmTopic = document.getElementById("confirmTopic");

const recordingTitle = document.getElementById("recordingTitle");
const recordingTopic = document.getElementById("recordingTopic");
const recordingTimer = document.getElementById("recordingTimer");
const recordingStatus = document.getElementById("recordingStatus");

const transcriptTitle = document.getElementById("transcriptTitle");
const transcriptTopic = document.getElementById("transcriptTopic");
const transcriptText = document.getElementById("transcriptText");


/* =========================
   状態を保存する
========================= */

let selectedMode = "";

let sessionTitle = "";
let sessionTopic = "";

let recordingStarted = false;
let recordingStartTime = 0;
let timerInterval = null;


/* =========================
   画面を切り替える
========================= */

function showScreen(screenToShow) {
    homeScreen.classList.add("hidden");
    themeScreen.classList.add("hidden");
    confirmScreen.classList.add("hidden");
    recordingScreen.classList.add("hidden");
    transcriptScreen.classList.add("hidden");

    screenToShow.classList.remove("hidden");
}


/* =========================
   授業を選択する
========================= */

classButton.addEventListener("click", function () {
    selectedMode = "授業";

    themeHeading.textContent = "授業のテーマを設定する";

    themeInput.placeholder = "例：機械設計";
    topicInput.placeholder = "例：歯車の設計について";

    showScreen(themeScreen);
});


/* =========================
   会議を選択する
========================= */

meetingButton.addEventListener("click", function () {
    selectedMode = "会議";

    themeHeading.textContent = "会議のテーマを設定する";

    themeInput.placeholder = "例：新製品開発会議";
    topicInput.placeholder = "例：新製品の設計方針について";

    showScreen(themeScreen);
});


/* =========================
   モード選択画面に戻る
========================= */

backButton.addEventListener("click", function () {
    showScreen(homeScreen);
});


/* =========================
   テーマ入力画面から確認画面へ
========================= */

nextButton.addEventListener("click", function () {
    const title = themeInput.value.trim();
    const topic = topicInput.value.trim();

    if (title === "") {
        alert("授業名・会議名を入力してください。");
        themeInput.focus();
        return;
    }

    if (topic === "") {
        alert("今回のテーマ・議題を入力してください。");
        topicInput.focus();
        return;
    }

    /* 入力内容を保存する */
    sessionTitle = title;
    sessionTopic = topic;

    /* 確認画面に入力内容を表示する */
    confirmMode.textContent = selectedMode;
    confirmTitle.textContent = sessionTitle;
    confirmTopic.textContent = sessionTopic;

    /* 確認画面へ移動 */
    showScreen(confirmScreen);
});


/* =========================
   確認画面からテーマ入力へ戻る
========================= */

backToThemeButton.addEventListener("click", function () {
    showScreen(themeScreen);
});


/* =========================
   記録開始
========================= */

startRecordingButton.addEventListener("click", function () {

    /* 記録画面に内容を表示する */
    recordingTitle.textContent = sessionTitle;
    recordingTopic.textContent = sessionTopic;

    /* 記録状態を設定する */
    recordingStarted = true;
    recordingStartTime = Date.now();

    recordingStatus.textContent = "記録中";

    /* 記録画面へ移動 */
    showScreen(recordingScreen);

    /* 経過時間を更新する */
    updateRecordingTimer();

    /* 1秒ごとに更新する */
    timerInterval = setInterval(updateRecordingTimer, 1000);
});


/* =========================
   経過時間を更新する
========================= */

function updateRecordingTimer() {

    if (!recordingStarted) {
        return;
    }

    const elapsedSeconds = Math.floor(
        (Date.now() - recordingStartTime) / 1000
    );

    const hours = Math.floor(elapsedSeconds / 3600);
    const minutes = Math.floor((elapsedSeconds % 3600) / 60);
    const seconds = elapsedSeconds % 60;

    recordingTimer.textContent =
        String(hours).padStart(2, "0") + ":" +
        String(minutes).padStart(2, "0") + ":" +
        String(seconds).padStart(2, "0");
}


/* =========================
   記録終了
========================= */

stopRecordingButton.addEventListener("click", function () {

    /* 経過時間の更新を停止する */
    recordingStarted = false;

    if (timerInterval !== null) {
        clearInterval(timerInterval);
        timerInterval = null;
    }

    recordingStatus.textContent = "記録終了";

    /* 文字起こし結果画面に内容を表示する */
    transcriptTitle.textContent = sessionTitle;
    transcriptTopic.textContent = sessionTopic;

    /* 仮の文字起こし結果 */
    transcriptText.textContent =
        "記録が終了しました。\n\n" +
        "現在はGUIの動作確認用です。\n" +
        "実際の文字起こし結果は、Pythonとの接続後に表示されます。";

    /* 文字起こし結果画面へ移動 */
    showScreen(transcriptScreen);
});


/* =========================
   仮の文字起こし結果を表示
========================= */

previewTranscriptButton.addEventListener("click", function () {

    transcriptTitle.textContent =
        themeInput.value.trim() || "テスト記録";

    transcriptTopic.textContent =
        topicInput.value.trim() || "テストテーマ";

    transcriptText.textContent =
        "本日の授業では、人工知能について説明します。\n" +
        "人工知能は、データを利用して学習する技術です。\n" +
        "今後は、さまざまな分野で活用されると考えられます。";

    showScreen(transcriptScreen);
});


/* =========================
   テーマ入力画面へ戻る
========================= */

backToInputButton.addEventListener("click", function () {

    /* 記録画面から戻る場合はタイマーを停止する */
    recordingStarted = false;

    if (timerInterval !== null) {
        clearInterval(timerInterval);
        timerInterval = null;
    }

    showScreen(themeScreen);
});


/* =========================
   ホーム画面に戻る
========================= */

homeButton.addEventListener("click", function () {

    /* タイマーが動いていれば停止する */
    recordingStarted = false;

    if (timerInterval !== null) {
        clearInterval(timerInterval);
        timerInterval = null;
    }

    /* 入力内容を初期化する */
    themeInput.value = "";
    topicInput.value = "";

    sessionTitle = "";
    sessionTopic = "";
    selectedMode = "";

    /* ホーム画面へ移動 */
    showScreen(homeScreen);
});
