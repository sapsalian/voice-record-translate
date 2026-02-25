import json
from pathlib import Path

import pytest

from vrt.config import Config, load_config, save_config


def test_default_config():
    cfg = Config()
    assert cfg.openai_api_key == ""
    assert cfg.soniox_api_key == ""
    assert cfg.target_lang == "ko"


def test_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setattr("vrt.config.CONFIG_DIR", tmp_path)
    monkeypatch.setattr("vrt.config.CONFIG_FILE", tmp_path / "config.json")

    cfg = Config(openai_api_key="sk-test", soniox_api_key="so-test", target_lang="ja")
    save_config(cfg)

    assert (tmp_path / "config.json").exists()
    loaded = load_config()
    assert loaded.openai_api_key == "sk-test"
    assert loaded.soniox_api_key == "so-test"
    assert loaded.target_lang == "ja"


def test_load_missing_file_returns_default(tmp_path, monkeypatch):
    monkeypatch.setattr("vrt.config.CONFIG_FILE", tmp_path / "nonexistent.json")

    cfg = load_config()
    assert cfg == Config()


def test_load_migrates_legacy_api_key(tmp_path, monkeypatch):
    """구 config의 api_key 필드가 openai_api_key로 마이그레이션된다."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"api_key": "sk-x", "target_lang": "ko"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("vrt.config.CONFIG_FILE", config_file)

    cfg = load_config()
    assert cfg.openai_api_key == "sk-x"
    assert cfg.soniox_api_key == ""


def test_load_ignores_unknown_fields(tmp_path, monkeypatch):
    """구 config의 source_lang 및 알 수 없는 필드는 무시된다."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        json.dumps({"openai_api_key": "sk-x", "source_lang": "vi", "target_lang": "ko", "unknown_field": "ignored"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("vrt.config.CONFIG_FILE", config_file)

    cfg = load_config()
    assert cfg.openai_api_key == "sk-x"
    assert cfg.target_lang == "ko"
