"""Revisa cada pocos minutos si has respondido al bot de Telegram.

Órdenes:
  /publicar            publica el borrador pendiente
  /foto N [crédito]    (como pie de una foto) pone esa foto recortada en la diapositiva N
  /sinfoto N           deja la diapositiva N solo con texto
  /añadir [N] <qué>    Claude busca y añade UNA noticia (en la diapositiva N, o al final)
  /quitar N            quita la noticia de la diapositiva N
  /rehacer <cambios>   Claude vuelve a preparar el borrador con tus indicaciones
  /cancelar            descarta el borrador de esta semana
  /generar             prepara ahora un borrador de la semana anterior
  /estado              te dice en qué punto está

Uso: python -m diario.check_approval
"""
from datetime import date

from . import config, state, telegram
from .generate import generate, rerender
from .images import from_user_photo, prepare_images
from .news import fetch_single_news, rewrite_texts

EDIT_CMDS = ("/foto", "/sinfoto", "/añadir", "/anadir", "/quitar")
from .publish import publish


def _slide_to_news(arg: str, total: int) -> int | None:
    """'/foto 3' se refiere a la diapositiva 3, que es la noticia 2 (la 1 es la portada)."""
    try:
        slide = int(arg.strip().split()[0])
    except (ValueError, IndexError):
        return None
    index = slide - 2
    return index if 0 <= index < total else None


def _add_news(draft: dict, arg: str, msg_id: int) -> bool:
    """/añadir [N] <qué>: busca una noticia y la mete en la diapositiva N (o al final)."""
    noticias = draft["noticias"]
    if len(noticias) >= config.MAX_NEWS:
        telegram.send_text(f"Ya hay {config.MAX_NEWS} noticias, que es el máximo. Quita una antes con /quitar N.")
        return False
    first, _, rest = arg.strip().partition(" ")
    if first.isdigit():
        slide, peticion = int(first), rest.strip()
        index = min(max(slide - 2, 0), len(noticias))
    else:
        index, peticion = len(noticias), arg.strip()
    if not peticion:
        telegram.send_text("Dime qué noticia añadir. Ej: /añadir 4 las parejas que han superado la previa del Kuwait Major")
        return False

    telegram.send_text(f"⏳ Buscando la noticia para la diapositiva {index + 2}…")
    try:
        nueva = fetch_single_news(date.fromisoformat(draft["desde"]), date.fromisoformat(draft["hasta"]), peticion)
    except Exception as exc:  # noqa: BLE001
        telegram.send_text(f"⚠️ No la he añadido: {exc}")
        return False
    # La foto se busca solo para la noticia nueva, en una carpeta propia
    prepare_images([nueva], config.POSTS_DIR / "anadidas" / f"{draft['hasta']}_{msg_id}")
    noticias.insert(index, nueva)
    telegram.send_text(f"✅ Añadida en la diapositiva {index + 2}: {nueva['titulo']}\nFuente: {nueva.get('fuente', 'sin fuente')}")
    return True


def handle_edits(cmds: list[tuple[str, dict]]) -> None:
    """Fotos, noticias añadidas y quitadas: se aplican todas en orden y se redibuja una sola vez."""
    st = state.load()
    if st.get("status") != "pending":
        telegram.send_text("No hay borrador pendiente que cambiar. Usa /generar para crear uno.")
        return
    draft = st["draft"]
    noticias = draft["noticias"]
    changed = False
    lista_cambiada = False

    for text, msg in cmds:
        cmd, _, arg = text.partition(" ")
        cmd = cmd.split("@")[0].lower()

        if cmd in ("/añadir", "/anadir"):
            if _add_news(draft, arg, msg.get("message_id", 0)):
                changed = lista_cambiada = True
            continue

        index = _slide_to_news(arg, len(noticias))
        if index is None:
            telegram.send_text(f"Indica el número de diapositiva de una noticia (de 2 a {len(noticias) + 1}). Ej: {cmd} 3")
            continue

        if cmd == "/quitar":
            if len(noticias) == 1:
                telegram.send_text("No puedo quitar la única noticia del post. Usa /cancelar si no quieres publicar.")
                continue
            quitada = noticias.pop(index)
            telegram.send_text(f"🗑️ Quitada la diapositiva {index + 2}: {quitada['titulo']}")
            changed = lista_cambiada = True
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
        if lista_cambiada:
            # la portada y los textos de redes tienen que cuadrar con la nueva lista
            try:
                draft.update(rewrite_texts(draft))
            except Exception as exc:  # noqa: BLE001
                telegram.send_text(f"⚠️ No pude actualizar los textos de redes ({exc}); revísalos antes de publicar.")
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

    # Las órdenes de edición se aplican todas, en orden; del resto vale la última
    edit_cmds = [c for c in commands if c[0].split()[0].split("@")[0].lower() in EDIT_CMDS]
    other_cmds = [c for c in commands if c not in edit_cmds]
    if edit_cmds:
        handle_edits(edit_cmds)
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
        telegram.send_text("No conozco esa orden. Usa /publicar, /foto N, /sinfoto N, /añadir [N] <qué>, /quitar N, /rehacer <cambios>, /cancelar, /generar o /estado.")


if __name__ == "__main__":
    main()
