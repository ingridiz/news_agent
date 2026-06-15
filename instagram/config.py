"""Persistência local da configuração do Zernio (profile/conta).

Grava em ``.zernio.json`` na raiz do projeto (ignorado pelo git) para que o
``post.py`` use a conta de Instagram conectada sem precisar informar o ID toda vez.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / ".zernio.json"


def load_dotenv() -> None:
    """Carrega variáveis do .env (sem dependência externa)."""
    env_path = CONFIG_PATH.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


def load_config() -> dict:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except ValueError:
            return {}
    return {}


def save_config(**values) -> dict:
    cfg = load_config()
    cfg.update({k: v for k, v in values.items() if v is not None})
    CONFIG_PATH.write_text(json.dumps(cfg, ensure_ascii=False, indent=2))
    return cfg
