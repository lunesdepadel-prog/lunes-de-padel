"""Imágenes reales para cada noticia, recortadas sin fondo.

Fuentes (por orden de seguridad legal):
  - Personas: Wikimedia Commons (licencias libres; se muestra autor y licencia en la diapositiva).
  - Productos: la imagen principal (og:image) de la web oficial de la marca.
  - Tus propias fotos, enviadas al bot de Telegram con /foto N.
El fondo se quita con rembg, que funciona en local, gratis.
"""
import html
import io
import os
import re
import unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from PIL import Image

from . import config

USER_AGENT = "LunesDePadelBot/1.0 (cuenta automatica de noticias de padel; " + os.environ.get("PAGES_BASE_URL", "github.com") + ")"
HEADERS = {"User-Agent": USER_AGENT}
MAX_BYTES = 15 * 1024 * 1024

_session = None


# ---------------------------------------------------------------- recorte

def cutout(raw: bytes) -> Image.Image:
    """Quita el fondo y recorta al contorno. Lanza ValueError si el recorte sale mal."""
    global _session
    from rembg import new_session, remove  # import aquí: el modelo pesa y solo se carga si hace falta

    if _session is None:
        _session = new_session("isnet-general-use")
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail((1600, 1600))
    out = remove(img, session=_session).convert("RGBA")

    alpha = out.getchannel("A")
    coverage = sum(alpha.histogram()[129:]) / (out.width * out.height)
    if not 0.03 < coverage < 0.97:
        raise ValueError("el recorte no ha detectado bien la figura")
    bbox = alpha.point(lambda a: 255 if a > 20 else 0).getbbox()
    out = out.crop(bbox)
    out.thumbnail((1100, 1100))
    return out


def save_cutout(img: Image.Image, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)
    return path.relative_to(config.ROOT / "docs").as_posix()


# ---------------------------------------------------------------- descargas

def _download(url: str) -> bytes:
    r = requests.get(url, headers=HEADERS, timeout=30, stream=True)
    r.raise_for_status()
    if not r.headers.get("Content-Type", "").startswith("image/"):
        raise ValueError(f"{url} no es una imagen")
    data = r.raw.read(MAX_BYTES + 1, decode_content=True)
    if len(data) > MAX_BYTES:
        raise ValueError("imagen demasiado grande")
    with Image.open(io.BytesIO(data)) as im:
        if min(im.size) < 350:
            raise ValueError("imagen demasiado pequeña")
    return data


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9 ]", " ", text.lower())


def _strip_html(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text or "")).strip()


def commons_person(name: str) -> tuple[bytes, str] | None:
    """Busca en Wikimedia Commons una foto cuyo título contenga nombre y apellido."""
    r = requests.get(
        "https://commons.wikimedia.org/w/api.php",
        params={
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": f'"{name}" filetype:bitmap', "gsrnamespace": 6, "gsrlimit": 15,
            "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1400,
        },
        headers=HEADERS, timeout=30,
    )
    pages = (r.json().get("query") or {}).get("pages", {}).values()

    tokens = [t for t in _norm(name).split() if len(t) > 2]
    if not tokens:
        return None
    candidates = []
    for page in pages:
        title = _norm(page.get("title", ""))
        info = (page.get("imageinfo") or [{}])[0]
        # el nombre y el primer apellido tienen que aparecer en el título del archivo
        if not (tokens[0] in title and tokens[1 if len(tokens) > 1 else 0] in title):
            continue
        w, h = info.get("width", 0), info.get("height", 0)
        if min(w, h) < 500:
            continue
        meta = info.get("extmetadata", {})
        artist = _strip_html(meta.get("Artist", {}).get("value", "")) or "Wikimedia Commons"
        license_ = _strip_html(meta.get("LicenseShortName", {}).get("value", ""))
        score = (2 if h >= w else 0) + (1 if "padel" in title else 0) + min(w * h, 8_000_000) / 8_000_000
        candidates.append((score, info.get("thumburl") or info.get("url"), f"Foto: {artist[:40]} ({license_}, Wikimedia)"))

    for _, url, credit in sorted(candidates, reverse=True)[:3]:
        try:
            return _download(url), credit
        except Exception:  # noqa: BLE001
            continue
    return None


def official_product(page_url: str) -> tuple[bytes, str] | None:
    """Toma la imagen principal (og:image) de la página oficial de la marca."""
    r = requests.get(page_url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    for prop in ("og:image", "twitter:image"):
        m = re.search(
            rf'<meta[^>]+(?:property|name)=["\']{prop}["\'][^>]+content=["\']([^"\']+)'
            rf'|<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{prop}["\']',
            r.text, re.I,
        )
        if m:
            image_url = urljoin(page_url, html.unescape(m.group(1) or m.group(2)))
            return _download(image_url), f"Imagen: {urlparse(page_url).netloc.removeprefix('www.')}"
    return None


# ---------------------------------------------------------------- por noticia

def prepare_images(noticias: list[dict], folder: Path) -> None:
    """Rellena en cada noticia 'recortes' (rutas dentro de docs/), 'credito' e 'imagen_estado'."""
    for i, n in enumerate(noticias, start=1):
        n.setdefault("recortes", [])
        if n["recortes"]:  # ya tiene imagen (p. ej. una foto tuya de una versión anterior)
            continue
        info = n.get("imagen") or {}
        tipo = info.get("tipo", "ninguna")
        try:
            if tipo == "persona":
                credits = []
                for j, name in enumerate((info.get("personas") or [])[:2]):
                    found = commons_person(name)
                    if not found:
                        continue
                    raw, credit = found
                    n["recortes"].append(save_cutout(cutout(raw), folder / "recortes" / f"n{i:02d}_{j}.png"))
                    credits.append(credit)
                n["credito"] = " / ".join(dict.fromkeys(credits))
            elif tipo == "producto" and info.get("pagina"):
                found = official_product(info["pagina"])
                if found:
                    raw, n["credito"] = found
                    n["recortes"].append(save_cutout(cutout(raw), folder / "recortes" / f"n{i:02d}_0.png"))
        except Exception as exc:  # noqa: BLE001 - una imagen fallida nunca debe parar el post
            print(f"⚠️ Imagen de la noticia {i} descartada: {exc}")
            n["recortes"] = []
        n["imagen_estado"] = "con foto" if n["recortes"] else "solo texto"


def from_user_photo(raw: bytes, path: Path) -> tuple[str, bool]:
    """Foto enviada por ti a Telegram. Devuelve (ruta, recortada). Si el recorte falla, se usa la foto entera."""
    try:
        return save_cutout(cutout(raw), path), True
    except Exception:  # noqa: BLE001
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        img.thumbnail((1100, 1100))
        return save_cutout(img, path), False
