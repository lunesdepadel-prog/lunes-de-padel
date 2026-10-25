"""Revisa cada pocos minutos si has respondido al bot de Telegram.

Órdenes:
  /publicar            publica el borrador pendiente
  /foto N [crédito]    (como pie de una foto) pone esa foto recortada en la diapositiva N
  /sinfoto N           deja la diapositiva N solo con texto
  /rehacer <cambios>   Claude vuelve a preparar el borrador con tus indicaciones
  /cancelar            descarta el borrador de esta semana
  /generar             prepara ahora un borrador de la semana anterior
  /estado              te dice en qué punto está

Uso: python -m diario.check_approval
"""
from datetime import date

from . import config, state, telegram
from .generate import generate, rerender
from .images import from_user_photo
from .publish import publish


def _slide_to_news(arg: str, total: int) -> int | None:
    """'/foto 3' se refiere a la diapositiva 3, que es la noticia 2 (la 1 es la portada)."""
    try:
        slide = int(arg.strip().split()[0])
    except (ValueError, IndexError):
        return None
    index = slide - 2
    return index if 0 <= index < total else None


def handle_photos(cmds: list[tuple[str, dict]]) -> None:
    st = state.load()
    if st.get("status") != "pending":
        telegram.send_text("No hay borrador pendiente al que cambiar fotos.")
        return
    draft = st["draft"]
    noticias = draft["noticias"]
    changed = False

    for text, msg in cmds:
        cmd, _, arg = text.partition(" ")
        cmd = cmd.split("@")[0].lower()
        index = _slide_to_news(arg, len(noticias))
        if index is None:
            telegram.send_text(f"Indica el número de diapositiva de una noticia (de 2 a {len(noticias) + 1}). Ej: /foto 3")
            continue
        n = noticias[index]

        if cmd == "/sinfoto":
            n.update(recortes=[], credito="", foto_entera=False)
            changed = True
            continue

        # /foto N: la imagen puede venir como foto o como archivo
        file_id = None
        if msg.get("photo"):
            file_id = msg["photo"][-1]["file_id"]  # la última es la de mayor resolución
        elif (msg.get("document") or {}).get("mime_type", "").startswith("image/"):
            file_id = msg["document"]["file_id"]
        if not file_id:
            telegram.send_text("Para /foto envía la imagen con el texto «/foto N» como pie de foto.")
            continue

        telegram.send_text(f"⏳ Recortando la foto para la diapositiva {index + 2}…")
        raw = telegram.download_file(file_id)
        path = config.POSTS_DIR / "fotos-propias" / f"{draft['hasta']}_{msg.get('message_id', 0)}.png"
        rel, recortada = from_user_photo(raw, path)
        credito = (arg.strip().split(maxsplit=1)[1:] or [""])[0]  # texto opcional tras el número: crédito
        n.update(recortes=[rel], credito=credito, foto_entera=not recortada)
        if not recortada:
            telegram.send_text("No pude quitarle el fondo, así que la pongo entera con marco.")
        changed = True

    if changed:
        state.save(st)
        rerender()


def main() -> None:
    st = state.load()
    updates = telegram.get_updates(st.get("telegram_offset", 0))
    if not updates:
        return

    # Solo se hace caso a mensajes de tu chat; el resto se ignora
    commands = []
    for u in updates:
        msg = u.get("message") or {}
        text = (msg.get("text") or msg.get("caption") or "").strip()
        if str(msg.get("chat", {}).get("id")) == config.env("TELEGRAM_CHAT_ID") and text.startswith("/"):
            commands.append((text, msg))
    st["telegram_offset"] = updates[-1]["update_id"] + 1
    state.save(st)

    # Las órdenes de foto se aplican todas, en orden; del resto vale la última
    photo_cmds = [c for c in commands if c[0].split()[0].split("@")[0].lower() in ("/foto", "/sinfoto")]
    other_cmds = [c for c in commands if c not in photo_cmds]
    if photo_cmds:
        handle_photos(photo_cmds)
        st = state.load()
    if not other_cmds:
        return
    text, _msg = other_cmds[-1]
    cmd, _, arg = text.partition(" ")
    cmd = cmd.split("@")[0].lower()
    pending = st.get("status") == "pending"

    if cmd == "/publicar":
        if pending:
            telegram.send_text("⏳ Publicando…")
            publish()
        else:
            telegram.send_text("No hay borrador pendiente. Usa /generar para crear uno.")
    elif cmd == "/rehacer":
        if pending:
            telegram.send_text("⏳ Rehaciendo el borrador, tardará unos minutos…")
            draft = st["draft"]
            week = (date.fromisoformat(draft["desde"]), date.fromisoformat(draft["hasta"]))
            generate(feedback=arg.strip() or "Revisa de nuevo las noticias y mejora la selección.", week=week)
        else:
            telegram.send_text("No hay borrador pendiente que rehacer. Usa /generar.")
    elif cmd == "/cancelar":
        if pending:
            st["status"] = "cancelled"
            state.save(st)
            telegram.send_text("🗑️ Borrador descartado. Esta semana no se publica nada.")
        else:
            telegram.send_text("No había borrador pendiente.")
    elif cmd == "/generar":
        telegram.send_text("⏳ Preparando el borrador de la semana anterior, tardará unos minutos…")
        generate()
    elif cmd == "/estado":
        draft = st.get("draft") or {}
        telegram.send_text(f"Estado: {st.get('status')}\nÚltimo borrador: semana {draft.get('semana', '—')}")
    else:
        telegram.send_text("No conozco esa orden. Usa /publicar, /rehacer <cambios>, /cancelar, /generar o /estado.")


if __name__ == "__main__":
    main()
