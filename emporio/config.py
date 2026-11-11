from __future__ import annotations

import os
from importlib.resources import files
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def default_data_dir() -> Path:
    source = ROOT / "data"
    return source if source.is_dir() else Path(str(files("konaet_music_data")))


def default_state_dir() -> Path:
    base = Path(os.getenv("LOCALAPPDATA", str(Path.home() / ".local" / "state")))
    return base / "Konaet" / "Music"


@dataclass(frozen=True)
class Settings:
    data_dir: Path = default_data_dir()
    state_dir: Path = default_state_dir()
    provider: str = "local"
    model_url: str = ""
    model: str = ""
    model_key: str = ""
    model_timeout: float = 15.0
    public_url: str = "http://127.0.0.1:8000"

    @classmethod
    def from_env(cls) -> "Settings":
        provider = os.getenv("EMPORIO_PROVIDER", "local")
        if provider not in {"local", "openai_compatible"}:
            raise ValueError("EMPORIO_PROVIDER must be local or openai_compatible")
        timeout = float(os.getenv("EMPORIO_MODEL_TIMEOUT", "15"))
        if not 1 <= timeout <= 60:
            raise ValueError("EMPORIO_MODEL_TIMEOUT must be between 1 and 60 seconds")
        return cls(
            data_dir=Path(os.getenv("EMPORIO_DATA_DIR", str(default_data_dir()))),
            state_dir=Path(os.getenv("EMPORIO_STATE_DIR", str(default_state_dir()))),
            provider=provider,
            model_url=os.getenv("EMPORIO_MODEL_URL", ""),
            model=os.getenv("EMPORIO_MODEL", ""),
            model_key=os.getenv("EMPORIO_MODEL_KEY", ""),
            model_timeout=timeout,
            public_url=os.getenv("KONAET_PUBLIC_URL", "http://127.0.0.1:8000").rstrip("/"),
        )
