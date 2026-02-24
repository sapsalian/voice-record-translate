import json
from pathlib import Path

import pytest

from vrt.config import Config, load_config, save_config


def test_default_config():
    cfg = Config()
    assert cfg.api_key == ""
    assert cfg.source_lang == "vi"
    assert cfg.target_lang == "ko"


def test_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr("vrt.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("vrt.config.CONFIG_FILE", tmp_path / "config.json")

    cfg = Config(api_key="sk-test", source_lang="en", target_lang="ja")
    save_config(cfg)

    assert (tmp_path / "config.json").exists()
    loaded = load_config()
    assert loaded.api_key == "sk-test"
    assert loaded.source_lang == "en"
    assert loaded.target_lang == "ja"


def test_load_missing_file_returns_default(tmp_path, monkeypatch):
    monkeypatch.setattr("vrt.config.CONFIG_FILE", tmp_path / "nonexistent.json")

    cfg = load_config()
    assert cfg == Config()


def test_load_ignores_unknown_fields(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"api_key": "sk-x", "source_lang": "vi", "target_lang": "ko", "unknown_field": "ignored"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("vrt.config.CONFIG_FILE", config_file)

    cfg = load_config()
    assert cfg.api_key == "sk-x"
