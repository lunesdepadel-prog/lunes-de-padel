"""Pide a Claude (con búsqueda web) las noticias de pádel de la semana anterior."""
import json
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import anthropic

from . import config

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]

CATEGORIAS = ["Torneos", "Parejas", "Material", "Retiradas", "Clubs", "Selecciones", "Ranking", "Otros"]


def previous_week(today: date | None = None) -> tuple[date, date]:
    """Devuelve (lunes, domingo) de la semana anterior a 'today'."""
    today = today or datetime.now(ZoneInfo(config.TIMEZONE)).date()
    this_monday = today - timedelta(days=today.weekday())
    start = this_monday - timedelta(days=7)
    return start, start + timedelta(days=6)


def week_label(start: date, end: date) -> str:
    if start.month == end.month:
        return f"{start.day}–{end.day} {MESES[end.month - 1]} {end.year}"
    return f"{start.day} {MESES[start.month - 1]} – {end.day} {MESES[end.month - 1]} {end.year}"


SYSTEM_PROMPT = """Eres el redactor jefe de "Lunes de Pádel", una cuenta de Instagram y TikTok que resume cada lunes la actualidad del pádel profesional y su industria. Escribes en español de España, con tono cercano y aficionado pero riguroso.

Tu prioridad absoluta es la exactitud. Una noticia falsa destruye la credibilidad de la cuenta, así que:
- Solo incluyes hechos que hayas confirmado en los resultados de búsqueda y que hayan ocurrido dentro del rango de fechas indicado.
- Nunca inventas resultados, marcadores, parejas, nombres ni fechas. Si no encuentras confirmación, no lo incluyes.
- Para resultados de torneos, prioriza las webs oficiales (premierpadel.com, padelfip.com) y contrasta con medios especializados.
- Cada noticia lleva la URL de la fuente donde la verificaste."""


def build_user_prompt(start: date, end: date, feedback: str | None) -> str:
    prompt = f"""Busca en la web las noticias del mundo del pádel publicadas u ocurridas entre el lunes {start.isoformat()} y el domingo {end.isoformat()} (ambos incluidos).

Cubre, en este orden de prioridad:
1. Torneos: campeones y finalistas (masculino y femenino) de Premier Padel y de los torneos del FIP Tour (FIP Platinum, Gold, Silver, Bronze...) disputados esa semana.
2. Parejas: cambios o separaciones de pareja de jugadores del top 100 del ranking FIP.
3. Material: lanzamientos de palas, zapatillas o colecciones de marcas como Bullpadel, Siux, Nox, Adidas, Head, Babolat, Star Vie, Wilson, Black Crown, etc.
4. Retiradas: jugadores profesionales que anuncien su retirada.
5. Clubs: aperturas de clubs con repercusión internacional (nuevos países, clubs muy grandes, sedes de torneos).
6. Selecciones: Mundial de selecciones, clasificatorios, campeonatos continentales.
7. Ranking: cambios relevantes en los primeros puestos del ranking FIP.
8. Otros: lesiones importantes, calendario, normativa, acuerdos o fichajes de patrocinio con repercusión.

Haz varias búsquedas, en español y en inglés, y verifica las fechas. Selecciona como máximo las {config.MAX_NEWS} noticias más relevantes. Si una categoría no tiene novedades, simplemente omítela.

Cuando termines de buscar, responde ÚNICAMENTE con un objeto JSON válido (sin texto antes ni después, sin bloques de código) con esta estructura:
{{
  "titular_portada": "frase corta y llamativa para la portada (máx. 60 caracteres)",
  "noticias": [
    {{
      "categoria": "una de: {', '.join(CATEGORIAS)}",
      "titulo": "titular de la noticia (máx. 70 caracteres)",
      "resumen": "explicación clara en 1-3 frases (máx. 260 caracteres)",
      "fecha": "AAAA-MM-DD",
      "fuente": "URL donde lo verificaste",
      "imagen": {{
        "tipo": "producto | persona | ninguna",
        "personas": ["si tipo=persona: nombre completo de las personas protagonistas (máx. 2, p. ej. la pareja campeona), tal y como aparecen en Wikipedia"],
        "pagina": "si tipo=producto: URL de la web OFICIAL de la marca (ficha del producto o nota de prensa de la propia marca) donde aparece el producto"
      }}
    }}
  ],
  "caption_instagram": "texto del post de Instagram: gancho inicial, resumen en viñetas con emojis de cada noticia, pregunta final para fomentar comentarios. Máx. 1800 caracteres. Sin hashtags.",
  "caption_tiktok": "versión más corta y directa del texto para TikTok (máx. 900 caracteres). Sin hashtags.",
  "titulo_tiktok": "título corto para TikTok (máx. 80 caracteres)",
  "hashtags": ["#padel", "...entre 8 y 15 hashtags relevantes"]
}}

Ordena "noticias" de más a menos relevante.

Sobre "imagen" (cada diapositiva lleva un recorte real relacionado con la noticia):
- "producto": lanzamientos de palas, zapatillas o material. Solo si encuentras la página oficial de la marca (su web, no un medio ni una tienda). Si no la encuentras, usa "ninguna".
- "persona": noticias protagonizadas claramente por una persona (retirada, cambio de entrenador, lesión) o por una pareja (campeones de un torneo, nueva pareja). Máximo 2 nombres completos, sin ambigüedad.
- "ninguna": noticias de clubs, calendario, normativa o cuando dudes. Es preferible "ninguna" a una imagen equivocada."""
    if feedback:
        prompt += f"\n\nIMPORTANTE: es una segunda versión. El editor ha pedido estos cambios sobre la anterior: {feedback}"
    return prompt


def _extract_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"Claude no devolvió JSON. Respuesta:\n{text[:1000]}")
    return json.loads(text[start : end + 1])


def fetch_weekly_news(start: date, end: date, feedback: str | None = None) -> dict:
    client = anthropic.Anthropic(api_key=config.env("ANTHROPIC_API_KEY"))
    messages = [{"role": "user", "content": build_user_prompt(start, end, feedback)}]
    tools = [{"type": "web_search_20250305", "name": "web_search", "max_uses": config.MAX_WEB_SEARCHES}]

    # Las búsquedas largas pueden devolver stop_reason="pause_turn": se continúa la misma petición.
    for _ in range(5):
        response = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=8000,
            system=SYSTEM_PROMPT,
            messages=messages,
            tools=tools,
        )
        if response.stop_reason != "pause_turn":
            break
        messages = messages + [{"role": "assistant", "content": response.content}]

    text = "".join(block.text for block in response.content if block.type == "text")
    data = _extract_json(text)

    noticias = [n for n in data.get("noticias", []) if n.get("titulo") and n.get("resumen")]
    data["noticias"] = noticias[: config.MAX_NEWS]
    if not data["noticias"]:
        raise ValueError("Claude no encontró noticias verificadas para esa semana.")
    data["semana"] = week_label(start, end)
    data["desde"], data["hasta"] = start.isoformat(), end.isoformat()
    return data
