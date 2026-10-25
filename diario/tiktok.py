"""Publica un carrusel de fotos en TikTok con la Content Posting API.

Requisitos: app en developers.tiktok.com con el producto Content Posting API
y el scope video.publish, y el dominio/prefijo de GitHub Pages verificado
(TikTok solo descarga imágenes de URLs verificadas).
Mientras la app no pase la auditoría de TikTok, los posts salen en privado (SELF_ONLY).
"""
import time

import requests

from . import config
from .secrets_store import update_secret

BASE = "https://open.tiktokapis.com/v2"


def _check(r: requests.Response) -> dict:
    data = r.json()
    error = data.get("error", {})
    if r.status_code != 200 or (error and error.get("code") not in (None, "ok")):
        raise RuntimeError(f"TikTok API: {data}")
    return data


def get_access_token() -> str:
    """El access token dura 24 h, así que se pide uno nuevo cada vez a partir del refresh token."""
    r = requests.post(
        f"{BASE}/oauth/token/",
        data={
            "client_key": config.env("TIKTOK_CLIENT_KEY"),
            "client_secret": config.env("TIKTOK_CLIENT_SECRET"),
            "grant_type": "refresh_token",
            "refresh_token": config.env("TIKTOK_REFRESH_TOKEN"),
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=30,
    )
    data = r.json()
    if "access_token" not in data:
        raise RuntimeError(f"TikTok no renovó el token: {data}")
    if data.get("refresh_token") and data["refresh_token"] != config.env("TIKTOK_REFRESH_TOKEN"):
        update_secret("TIKTOK_REFRESH_TOKEN", data["refresh_token"])
    return data["access_token"]


def publish_photos(image_urls: list[str], title: str, description: str) -> str:
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=UTF-8"}

    # TikTok exige consultar la info del creador antes de publicar
    info = _check(requests.post(f"{BASE}/post/publish/creator_info/query/", headers=headers, timeout=30))["data"]
    privacy = config.TIKTOK_PRIVACY_LEVEL
    if privacy not in info.get("privacy_level_options", [privacy]):
        privacy = "SELF_ONLY"

    body = {
        "media_type": "PHOTO",
        "post_mode": "DIRECT_POST",
        "post_info": {
            "title": title[:90],
            "description": description[:4000],
            "privacy_level": privacy,
            "disable_comment": False,
            "auto_add_music": True,
        },
        "source_info": {"source": "PULL_FROM_URL", "photo_cover_index": 0, "photo_images": image_urls[:35]},
    }
    publish_id = _check(requests.post(f"{BASE}/post/publish/content/init/", headers=headers, json=body, timeout=60))["data"]["publish_id"]

    deadline = time.time() + 300
    while time.time() < deadline:
        time.sleep(6)
        status = _check(
            requests.post(f"{BASE}/post/publish/status/fetch/", headers=headers, json={"publish_id": publish_id}, timeout=30)
        )["data"]
        if status.get("status") == "PUBLISH_COMPLETE":
            return publish_id
        if status.get("status") == "FAILED":
            raise RuntimeError(f"TikTok no pudo publicar: {status.get('fail_reason')}")
    # Algunas publicaciones tardan más en confirmarse aunque acaben saliendo
    return publish_id
