"""Publica un carrusel en Instagram con la API de Instagram (inicio de sesión de Instagram).

Requisitos: cuenta profesional (Business o Creator) y una app de Meta con el
permiso instagram_business_content_publish. Las imágenes deben ser JPEG en una
URL pública (GitHub Pages).
"""
import time

import requests

from . import config
from .secrets_store import update_secret

BASE = "https://graph.instagram.com"


def _token() -> str:
    return config.env("INSTAGRAM_ACCESS_TOKEN")


def _check(r: requests.Response) -> dict:
    data = r.json()
    if r.status_code != 200 or "error" in data:
        raise RuntimeError(f"Instagram API: {data}")
    return data


def refresh_token() -> None:
    """El token de larga duración dura 60 días; renovarlo cada semana lo mantiene vivo."""
    r = requests.get(
        f"{BASE}/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": _token()},
        timeout=30,
    )
    new_token = _check(r)["access_token"]
    if new_token != _token():
        update_secret("INSTAGRAM_ACCESS_TOKEN", new_token)


def _wait_ready(container_id: str, timeout_s: int = 300) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        r = requests.get(
            f"{BASE}/{config.INSTAGRAM_API_VERSION}/{container_id}",
            params={"fields": "status_code", "access_token": _token()},
            timeout=30,
        )
        status = _check(r).get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram rechazó el contenedor {container_id}: {status}")
        time.sleep(5)
    raise TimeoutError("Instagram tardó demasiado en procesar las imágenes.")


def publish_carousel(image_urls: list[str], caption: str) -> str:
    user_id = config.env("INSTAGRAM_USER_ID")
    url = f"{BASE}/{config.INSTAGRAM_API_VERSION}/{user_id}/media"

    children = []
    for image_url in image_urls[:10]:
        r = requests.post(url, data={"image_url": image_url, "is_carousel_item": "true", "access_token": _token()}, timeout=60)
        children.append(_check(r)["id"])
    for child in children:
        _wait_ready(child)

    r = requests.post(
        url,
        data={"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption[:2200], "access_token": _token()},
        timeout=60,
    )
    carousel_id = _check(r)["id"]
    _wait_ready(carousel_id)

    r = requests.post(
        f"{BASE}/{config.INSTAGRAM_API_VERSION}/{user_id}/media_publish",
        data={"creation_id": carousel_id, "access_token": _token()},
        timeout=60,
    )
    return _check(r)["id"]
