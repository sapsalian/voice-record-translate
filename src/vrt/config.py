import json
from dataclasses import asdict, dataclass
from pathlib import Path

CONFIG_DIR = Path.home() / ".vrt"
CONFIG_FILE = CONFIG_DIR / "config.json"


@dataclass
class Config:
    openai_api_key: str = ""
    soniox_api_key: str = ""
    ui_lang: str = "ko"


def load_config() -> Config:
    if not CONFIG_FILE.exists():
        return Config()
    data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    if "api_key" in data:
        data["openai_api_key"] = data.pop("api_key")
    if "target_lang" in data and "ui_lang" not in data:
        data["ui_lang"] = data.pop("target_lang")
    elif "target_lang" in data:
        data.pop("target_lang")
    return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})


def save_config(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
