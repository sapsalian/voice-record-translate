import dataclasses
import os
import socket

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

from .config import load_config, save_config
from .pipeline import ProcessingWorker, start_processing
from .session import SESSIONS_DIR, create_session, delete_session, list_sessions, load_session, save_session

_static_dir = os.path.join(os.path.dirname(__file__), "static")
app = Flask(__name__, static_folder=_static_dir, static_url_path="")

if os.environ.get("VRT_DEV"):
    CORS(app, origins=["http://localhost:5173"])

_workers: dict[str, ProcessingWorker] = {}


def find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@app.get("/api/sessions")
def get_sessions():
    sessions = list_sessions()
    return jsonify([dataclasses.asdict(s) for s in sessions])


@app.get("/api/sessions/<session_id>")
def get_session(session_id: str):
    session = load_session(session_id)
    if session is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify(dataclasses.asdict(session))


@app.post("/api/sessions")
def post_session():
    data = request.get_json() or {}
    file_path = data.get("file_path")
    target_lang = data.get("target_lang", "ko")
    reset = data.get("reset", False)

    if not file_path:
        return jsonify({"error": "file_path is required"}), 400

    config = load_config()
    config.target_lang = target_lang
    title = os.path.basename(file_path)
    session = create_session(title=title, audio_src=file_path, target_lang=target_lang)

    worker = start_processing(session.id, file_path, config, reset=reset)
    _workers[session.id] = worker
    return jsonify({"id": session.id}), 201


@app.delete("/api/sessions/<session_id>")
def delete_session_route(session_id: str):
    if session_id in _workers:
        _workers[session_id].cancel()
        del _workers[session_id]
    delete_session(session_id)
    return "", 204


@app.patch("/api/sessions/<session_id>")
def patch_session(session_id: str):
    session = load_session(session_id)
    if session is None:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    if "title" in data:
        session.title = data["title"]
    save_session(session)
    return jsonify(dataclasses.asdict(session))


@app.get("/api/sessions/<session_id>/audio")
def get_audio(session_id: str):
    session = load_session(session_id)
    if session is None:
        return jsonify({"error": "Not found"}), 404
    audio_path = SESSIONS_DIR / session_id / session.audio_filename
    if not audio_path.exists():
        return jsonify({"error": "Audio not found"}), 404
    return send_file(str(audio_path), conditional=True)


@app.get("/api/config")
def get_config():
    config = load_config()
    return jsonify(dataclasses.asdict(config))


@app.patch("/api/config")
def patch_config():
    data = request.get_json() or {}
    config = load_config()
    if "openai_api_key" in data:
        config.openai_api_key = data["openai_api_key"]
    if "soniox_api_key" in data:
        config.soniox_api_key = data["soniox_api_key"]
    if "target_lang" in data:
        config.target_lang = data["target_lang"]
    save_config(config)
    return jsonify(dataclasses.asdict(config))


@app.errorhandler(404)
def not_found(e):
    if not request.path.startswith("/api/"):
        try:
            return app.send_static_file("index.html")
        except Exception:
            return "<h1>Frontend not built. Run: make build-frontend</h1>", 200
    return jsonify({"error": "Not found"}), 404
