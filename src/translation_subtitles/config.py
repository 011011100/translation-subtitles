from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


APP_NAME = "TranslationSubtitles"
DEFAULT_MODEL = "qwen-plus"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass
class AppConfig:
    api_key: str = ""
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    whisper_model: str = "small"
    device: str = "auto"
    compute_type: str = "auto"
    burn_subtitles: bool = True


def user_config_path() -> Path:
    appdata = os.getenv("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / "config.json"
    return Path.home() / f".{APP_NAME.lower()}" / "config.json"


def load_config() -> AppConfig:
    config = AppConfig(
        api_key=os.getenv("DASHSCOPE_API_KEY", ""),
        model=os.getenv("BAILIAN_MODEL", DEFAULT_MODEL),
    )
    path = user_config_path()
    if not path.exists():
        return config

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return config

    for field_name in asdict(config):
        value = data.get(field_name)
        if isinstance(value, bool) or isinstance(value, str):
            setattr(config, field_name, value)
    if os.getenv("DASHSCOPE_API_KEY"):
        config.api_key = os.environ["DASHSCOPE_API_KEY"]
    return config


def save_config(config: AppConfig) -> None:
    path = user_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(asdict(config), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
