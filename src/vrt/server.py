import dataclasses
import os
import socket
import tempfile

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
    content_type = request.content_type or ""
    if "multipart" in content_type:
        audio = request.files.get("audio")
        target_lang = request.form.get("target_lang", "ko")
        if not audio:
            return jsonify({"error": "audio is required"}), 400
        suffix = os.path.splitext(audio.filename or "")[1] or ".audio"
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=suffix)
        try:
            os.close(tmp_fd)
            audio.save(tmp_path)
            title = audio.filename or "upload"
            config = load_config()
            session = create_session(title=title, audio_src=tmp_path, target_lang=target_lang)
        finally:
            os.unlink(tmp_path)
        audio_path = str(SESSIONS_DIR / session.id / session.audio_filename)
        worker = start_processing(session.id, audio_path, config)
        _workers[session.id] = worker
        return jsonify({"id": session.id}), 201

    data = request.get_json() or {}
    file_path = data.get("file_path")
    target_lang = data.get("target_lang", "ko")
    reset = data.get("reset", False)

    if not file_path:
        return jsonify({"error": "file_path is required"}), 400

    config = load_config()
    title = os.path.basename(file_path)
    session = create_session(title=title, audio_src=file_path, target_lang=target_lang)

    worker = start_processing(session.id, file_path, config, reset=reset)
    _workers[session.id] = worker
    return jsonify({"id": session.id}), 201


@app.post("/api/sessions/<session_id>/cancel")
def cancel_session_route(session_id: str):
    worker = _workers.pop(session_id, None)
    if worker:
        worker.cancel()
        session = load_session(session_id)
        if session and session.status == "processing":
            session.progress_message = "취소 중..."
            save_session(session)
    return jsonify({"ok": True})


@app.post("/api/sessions/<session_id>/retry")
def retry_session_route(session_id: str):
    session = load_session(session_id)
    if session is None:
        return jsonify({"error": "Not found"}), 404
    config = load_config()
    session.status = "processing"
    session.error_message = None
    session.progress = 0
    session.progress_message = ""
    save_session(session)
    audio_path = str(SESSIONS_DIR / session_id / session.audio_filename)
    worker = start_processing(session_id, audio_path, config, reset=False)
    _workers[session_id] = worker
    return jsonify({"ok": True})


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
    if "speaker_names" in data:
        session.speaker_names = data["speaker_names"]
    if "segments" in data:
        session.segments = data["segments"]
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
    if "ui_lang" in data:
        config.ui_lang = data["ui_lang"]
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
