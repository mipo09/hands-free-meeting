
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return "AIハンズフリーホワイトボード API 起動成功"


@app.route("/api/test", methods=["GET"])
def test_api():
    return jsonify({
        "status": "success",
        "message": "GUIとPythonの通信に成功しました。",
        "transcript": "これはテスト用の文字起こしです。",
        "summary": "これはテスト用のAI要約です。"
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
