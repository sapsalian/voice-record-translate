import json
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .config import CONFIG_DIR

SESSIONS_DIR = CONFIG_DIR / "sessions"


@dataclass
class Session:
    id: str
    title: str
    created_at: str          # ISO 8601 UTC
    audio_filename: str
    source_lang: str
    target_lang: str
    status: str = "processing"   # processing | completed | failed
    duration: float | None = None
    error_message: str | None = None
    progress: int = 0
    progress_message: str = ""
    speaker_names: dict = field(default_factory=dict)
    segments: list = field(default_factory=list)


def create_session(title: str, audio_src: str, source_lang: str, target_lang: str) -> Session:
    sid = str(uuid.uuid4())
    sdir = SESSIONS_DIR / sid
    sdir.mkdir(parents=True, exist_ok=True)

    suffix = Path(audio_src).suffix
    audio_filename = "audio" + suffix
    shutil.copy2(audio_src, sdir / audio_filename)

    session = Session(
        id=sid,
        title=title,
        created_at=datetime.now(timezone.utc).isoformat(),
        audio_filename=audio_filename,
        source_lang=source_lang,
        target_lang=target_lang,
    )
    save_session(session)
    return session


def save_session(session: Session) -> None:
    sdir = SESSIONS_DIR / session.id
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / "session.json").write_text(
        json.dumps(asdict(session), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def load_session(session_id: str) -> Session | None:
    path = SESSIONS_DIR / session_id / "session.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Session(**{k: v for k, v in data.items() if k in Session.__dataclass_fields__})


def list_sessions() -> list[Session]:
    if not SESSIONS_DIR.exists():
        return []
    sessions = []
    for path in SESSIONS_DIR.iterdir():
        if path.is_dir():
            s = load_session(path.name)
            if s is not None:
                sessions.append(s)
    sessions.sort(key=lambda s: s.created_at, reverse=True)
    return sessions


def delete_session(session_id: str) -> None:
    sdir = SESSIONS_DIR / session_id
    if sdir.exists():
        shutil.rmtree(sdir)
