"""Bot de Telegram: envía el borrador y lee tus órdenes (/publicar, /rehacer, /cancelar)."""
import json
from pathlib import Path

import requests

from . import config

API = "https://api.telegram.org/bot{token}/{method}"


def _call(method: str, **kwargs) -> dict:
    url = API.format(token=config.env("TELEGRAM_BOT_TOKEN"), method=method)
    r = requests.post(url, timeout=60, **kwargs)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram {method} falló: {data}")
    return data["result"]


def chat_id() -> str:
    return config.env("TELEGRAM_CHAT_ID")


def send_text(text: str) -> None:
    # Telegram limita cada mensaje a 4096 caracteres
    for i in range(0, len(text), 4000):
        _call("sendMessage", data={"chat_id": chat_id(), "text": text[i : i + 4000], "disable_web_page_preview": True})


def send_album(images: list[Path]) -> None:
    files, media = {}, []
    for i, path in enumerate(images[:10]):
        key = f"img{i}"
        files[key] = (path.name, path.read_bytes(), "image/jpeg")
        media.append({"type": "photo", "media": f"attach://{key}"})
    _call("sendMediaGroup", data={"chat_id": chat_id(), "media": json.dumps(media)}, files=files)


def get_updates(offset: int) -> list[dict]:
    return _call("getUpdates", data={"offset": offset, "timeout": 0, "allowed_updates": json.dumps(["message"])})


def download_file(file_id: str) -> bytes:
    info = _call("getFile", data={"file_id": file_id})
    url = f"https://api.telegram.org/file/bot{config.env('TELEGRAM_BOT_TOKEN')}/{info['file_path']}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def _linea_noticia(slide: int, n: dict) -> str:
    if n.get("recortes"):
        foto = f"📸 con foto ({n.get('credito') or 'sin crédito'})"
    else:
        foto = "🔤 solo texto"
    return f"Diapositiva {slide}: {n['titulo']}\n  {foto}\n  Fuente: {n.get('fuente', 'sin fuente')}"


def send_draft(data: dict, images: list[Path]) -> None:
    send_album(images)
    fuentes = "\n\n".join(_linea_noticia(i, n) for i, n in enumerate(data["noticias"], start=2))
    hashtags = " ".join(data.get("hashtags", []))
    send_text(
        f"📰 Borrador de Lunes de Pádel · semana {data['semana']}\n\n"
        f"— INSTAGRAM —\n{data.get('caption_instagram', '')}\n\n{hashtags}\n\n"
        f"— TIKTOK —\n{data.get('titulo_tiktok', '')}\n\n{data.get('caption_tiktok', '')}\n\n{hashtags}"
    )
    send_text(
        "🔎 Revisa cada noticia y su foto:\n\n" + fuentes + "\n\n"
        "Responde con:\n"
        "/publicar → se publica en Instagram y TikTok\n"
        "/foto 3 → envía una foto con este texto como pie y la pongo (recortada) en la diapositiva 3. Puedes añadir el crédito: /foto 3 Foto: @bullpadel\n"
        "/sinfoto 3 → quito la foto de la diapositiva 3\n"
        "/rehacer <qué cambiar> → Claude vuelve a buscar y redactar (ej: /rehacer quita la noticia de la pala y añade el FIP de Egipto). Ojo: se pierden las fotos que hayas puesto tú\n"
        "/cancelar → esta semana no se publica"
    )
