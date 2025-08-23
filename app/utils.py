import os
from typing import Optional


def get_env_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.lower() in {"1", "true", "yes", "on"}


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def project_path(*parts: str) -> str:
    return os.path.join(os.getcwd(), *parts)
