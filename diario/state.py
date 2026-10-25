"""Estado persistente guardado en state/state.json (se commitea al repo).

Campos:
  status: "idle" | "pending" | "published" | "cancelled"
  telegram_offset: último update_id procesado + 1
  draft: datos del borrador pendiente (fecha, noticias, captions, imágenes)
"""
import json

from .config import STATE_FILE


def load() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"status": "idle", "telegram_offset": 0}


def save(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
