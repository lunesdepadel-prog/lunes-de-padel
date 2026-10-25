"""Convierte la plantilla HTML en imágenes JPEG de 1080x1350 (formato 4:5)."""
import subprocess
import sys
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.sync_api import sync_playwright

from . import config
from .config import TEMPLATES_DIR
from .news import MESES


def _fecha_bonita(iso: str | None) -> str:
    try:
        d = date.fromisoformat(iso or "")
    except ValueError:
        return ""
    return f"{d.day} {MESES[d.month - 1]}"


def render_slides(data: dict, out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=select_autoescape(["html"]))
    template = env.get_template("slides.html")

    docs = config.ROOT / "docs"
    noticias = [
        {
            **n,
            "fecha_bonita": _fecha_bonita(n.get("fecha")),
            "recortes_uri": [(docs / r).as_uri() for r in n.get("recortes", []) if (docs / r).exists()],
        }
        for n in data["noticias"]
    ]
    # Portada: "13–19" / "oct", o "27 oct –" / "2 nov" si la semana cruza de mes
    semana_corta = data["semana"].rsplit(" ", 1)[0]
    if "–" in semana_corta and " – " in semana_corta:
        ini, fin = semana_corta.split(" – ")
        portada_lineas, portada_larga = [f"{ini} –", fin], True
    else:
        dias, _, mes = semana_corta.partition(" ")
        portada_lineas, portada_larga = [dias, mes], False
    html = template.render(
        portada_lineas=portada_lineas,
        portada_larga=portada_larga,
        titular_portada=data.get("titular_portada", ""),
        noticias=noticias,
        logo_uri=(TEMPLATES_DIR / "logo-horizontal.svg").as_uri(),
        logo_red_uri=(TEMPLATES_DIR / "logo-red.svg").as_uri(),
    )

    html_path = out_dir / "slides.html"
    html_path.write_text(html, encoding="utf-8")

    paths: list[Path] = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:  # noqa: BLE001 - primera vez en el runner: falta el navegador
            subprocess.run([sys.executable, "-m", "playwright", "install", "--with-deps", "chromium"], check=True)
            browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.goto(html_path.as_uri(), wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        for i, slide in enumerate(page.locator(".slide").all(), start=1):
            path = out_dir / f"slide_{i:02d}.jpg"
            slide.screenshot(path=str(path), type="jpeg", quality=92)
            paths.append(path)
        browser.close()
    html_path.unlink()
    return paths
