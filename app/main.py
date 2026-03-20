from flask import Flask, request, jsonify

app = Flask(__name__)


@app.get("/health")
def health_check() -> tuple[dict[str, str], int]:
    return {"status": "ok", "project": "Expedition-0"}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
