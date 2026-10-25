"""Configuración de Lunes de Pádel.

Todo lo sensible (tokens, claves) llega por variables de entorno, que en
GitHub Actions se cargan desde los Secrets del repositorio.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "state" / "state.json"
POSTS_DIR = ROOT / "docs" / "posts"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

TIMEZONE = "Europe/Madrid"


def env(name: str, default: str | None = None, required: bool = True) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        raise RuntimeError(f"Falta la variable de entorno {name}. Añádela en Settings > Secrets and variables > Actions.")
    return value or ""


# --- Claude ---
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_WEB_SEARCHES = int(os.environ.get("MAX_WEB_SEARCHES", "15"))
MAX_NEWS = 8  # portada + 8 noticias + cierre = 10 imágenes (límite cómodo para ambos carruseles)

# --- Web pública donde se alojan las imágenes (GitHub Pages) ---
# Ejemplo: https://tuusuario.github.io/lunes-de-padel
def pages_base_url() -> str:
    return env("PAGES_BASE_URL").rstrip("/")

# --- Instagram (API de Instagram con inicio de sesión de Instagram) ---
INSTAGRAM_API_VERSION = os.environ.get("INSTAGRAM_API_VERSION", "v23.0")

# --- TikTok ---
# Mientras la app de TikTok no esté auditada, solo se permite SELF_ONLY (privado).
# Cuando TikTok la apruebe, cambia la variable a PUBLIC_TO_EVERYONE.
TIKTOK_PRIVACY_LEVEL = os.environ.get("TIKTOK_PRIVACY_LEVEL", "SELF_ONLY")

# --- Plataformas activas (por si quieres empezar solo con una) ---
PUBLISH_INSTAGRAM = os.environ.get("PUBLISH_INSTAGRAM", "true").lower() == "true"
PUBLISH_TIKTOK = os.environ.get("PUBLISH_TIKTOK", "true").lower() == "true"
