import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

CONFIG_DIR = Path.home() / ".vrt"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    api_key: str = ""
    source_lang: str = "vi"
    target_lang: str = "ko"


def load_config() -> Config:
    if not CONFIG_FILE.exists():
        return Config()
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})


def save_config(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
