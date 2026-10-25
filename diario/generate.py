"""Genera el borrador semanal y te lo envía por Telegram para que lo apruebes.

Uso: python -m diario.generate
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from . import config, state, telegram
from .news import fetch_weekly_news, previous_week
from .images import prepare_images
from .render import render_slides


def generate(feedback: str | None = None, week: tuple | None = None) -> None:
    st = state.load()
    start, end = week or previous_week()

    try:
        data = fetch_weekly_news(start, end, feedback)
    except Exception as exc:  # noqa: BLE001
        telegram.send_text(f"⚠️ No pude preparar el borrador de la semana {start} – {end}.\n\nError: {exc}\n\nPuedes reintentarlo con /generar")
        raise

    folder = _new_folder(end.isoformat())
    prepare_images(data["noticias"], config.POSTS_DIR / folder)
    _render_and_send(st, data, folder)


def _new_folder(prefix: str) -> str:
    # Carpeta única por versión para que la caché de GitHub Pages nunca sirva imágenes antiguas
    stamp = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}_{stamp}"


def _render_and_send(st: dict, data: dict, folder: str) -> None:
    images = render_slides(data, config.POSTS_DIR / folder)
    data.pop("published", None)
    st.update(status="pending", draft={**data, "folder": folder, "images": [p.name for p in images]})
    state.save(st)
    telegram.send_draft(data, images)
    print(f"✅ Borrador listo: {len(images)} imágenes en docs/posts/{folder}")


def rerender() -> None:
    """Vuelve a dibujar el borrador pendiente (tras cambiar una foto) sin volver a buscar noticias."""
    st = state.load()
    draft = dict(st["draft"])
    for key in ("folder", "images"):
        draft.pop(key, None)
    _render_and_send(st, draft, _new_folder(draft["hasta"]))


def main() -> None:
    # Renovar el token de Instagram una vez por semana para que no caduque (dura 60 días)
    if config.PUBLISH_INSTAGRAM:
        try:
            from .instagram import refresh_token

            refresh_token()
        except Exception as exc:  # noqa: BLE001
            print(f"⚠️ No se pudo renovar el token de Instagram: {exc}")
    generate()


if __name__ == "__main__":
    main()
