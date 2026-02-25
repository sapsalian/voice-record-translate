from dataclasses import asdict, dataclass, field
from pathlib import Path
import json


@dataclass
class Checkpoint:
    file_path: str
    source_lang: str
    target_lang: str
    segments: list[dict] | None = None
    corrected_segments: list[dict] = field(default_factory=list)
    last_chunk_done: int = -1
    ctx_summary: str = ""
    ctx_recent_pairs: list[list[str]] = field(default_factory=list)


def checkpoint_path(file_path: str) -> Path:
    return Path(file_path).with_suffix(".vrt_checkpoint.json")


def load_checkpoint(file_path: str) -> Checkpoint | None:
    p = checkpoint_path(file_path)
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    return Checkpoint(**data)


def save_checkpoint(cp: Checkpoint) -> None:
    p = checkpoint_path(cp.file_path)
    p.write_text(json.dumps(asdict(cp), ensure_ascii=False, indent=2), encoding="utf-8")


def delete_checkpoint(file_path: str) -> None:
    p = checkpoint_path(file_path)
    if p.exists():
        p.unlink()
