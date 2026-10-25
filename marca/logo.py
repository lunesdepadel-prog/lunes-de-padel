"""Logotipo de Lunes de Pádel: letras trazadas como las líneas pintadas de una pista."""
S = 18  # grosor del trazo sobre una altura de letra de 100

# Cada letra: (ancho, path con coordenadas de la línea central, altura 0-100)
GLYPHS = {
    "L": (60, "M9,0 V91 H60"),
    "U": (66, "M9,0 V67 A24,24 0 0 0 57,67 V0"),
    "N": (66, "M9,100 V0 L57,100 V0"),
    "E": (56, "M56,9 H9 V91 H56 M9,50 H50"),
    "S": (60, "M60,9 H33 A20.5,20.5 0 0 0 33,50 H27 A20.5,20.5 0 0 1 27,91 H0"),
    "D": (64, "M9,9 H23 A32,41 0 0 1 23,91 H9 Z"),
    "P": (58, "M9,100 V9 H28 A21,21 0 0 1 28,51 H9"),
    "Á": (66, "M4,100 L33,0 L62,100 M17,66 H49 M27,-14 L41,-36"),
    " ": (26, ""),
}
GAP = 13


def word(text: str, x: float = 0, y: float = 0, scale: float = 1, color: str = "#F4F6F8") -> tuple[str, float]:
    parts, cx = [], 0.0
    for ch in text:
        w, d = GLYPHS[ch]
        if d:
            parts.append(f'<path transform="translate({cx:.1f} 0)" d="{d}"/>')
        cx += w + GAP
    width = cx - GAP
    g = (f'<g transform="translate({x:.1f} {y:.1f}) scale({scale})" fill="none" stroke="{color}" '
         f'stroke-width="{S}" stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="1.5" '
         f'clip-path="url(#corte)">{"".join(parts)}</g>')
    return g, width * scale


CLIP = '<defs><clipPath id="corte" clipPathUnits="userSpaceOnUse"><rect x="-20" y="-60" width="2000" height="160"/></clipPath></defs>'


_ball_n = [0]


def ball(cx, cy, r, color="#FF6B35", seam="#F4F6F8"):
    # bola con costura: dos arcos laterales recortados al contorno de la bola
    _ball_n[0] += 1
    cid = f"bola{_ball_n[0]}"
    return (f'<clipPath id="{cid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
            f'<path clip-path="url(#{cid})" d="M{cx - r * .62:.1f},{cy - r * .78:.1f} A{r * .95:.1f},{r * .95:.1f} 0 0 1 {cx - r * .62:.1f},{cy + r * .78:.1f} '
            f'M{cx + r * .62:.1f},{cy - r * .78:.1f} A{r * .95:.1f},{r * .95:.1f} 0 0 0 {cx + r * .62:.1f},{cy + r * .78:.1f}" '
            f'fill="none" stroke="{seam}" stroke-width="{r * .11:.1f}"/>')


def svg(w, h, body, bg=None):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{CLIP}{rect}{body}</svg>'


def stacked(ink, ball_color, bg=None, pad=40):
    # "LUNES" grande y "DE PÁDEL" debajo, ambos del mismo ancho
    top, wtop = word("LUNES", pad, pad + 0, 1, ink)
    sc = wtop / word("DE PÁDEL", 0, 0, 1, ink)[1]
    bottom, _ = word("DE PÁDEL", pad, pad + 100 + 26 + 36 * sc / 0.5 * 0, sc, ink)
    # recolocar la segunda línea: hueco fijo de 30 + espacio para la tilde
    y2 = pad + 100 + 30 + 36 * sc
    bottom, _ = word("DE PÁDEL", pad, y2, sc, ink)
    h = y2 + 100 * sc + pad
    w = wtop + 2 * pad
    return svg(round(w), round(h), top + bottom, bg)


def horizontal(ink, ball_color, bg=None, pad=40):
    a, wa = word("LUNES", pad, pad + 40, 1, ink)
    b, wb = word("DE PÁDEL", pad + wa + 44, pad + 40, 1, ink)
    w = pad + wa + 44 + wb + pad
    return svg(round(w), round(100 + 40 + 2 * pad), a + b, bg)


def mark(size=1080, bg="#000000", ink="#F4F6F8", ball_color="#FF6B35", circle=True):
    # La "L" como esquina de pista, con la bola apoyada en la línea
    k = size / 1080
    L = (f'<path d="M{350 * k:.1f},{230 * k:.1f} V{790 * k:.1f} H{830 * k:.1f}" fill="none" stroke="{ink}" '
         f'stroke-width="{104 * k:.1f}" stroke-linecap="butt" stroke-linejoin="miter"/>')
    # la bola descansa sobre la línea de fondo, junto a la esquina
    r = 128
    b = ball((402 + 34 + r) * k, (738 - r) * k, r * k, ball_color, ink)
    shape = (f'<circle cx="{size / 2}" cy="{size / 2}" r="{size / 2}" fill="{bg}"/>' if circle
             else f'<rect width="{size}" height="{size}" fill="{bg}"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">{shape}'
            f'<g transform="translate({-24 * k:.1f} 0)">{L}{b}</g></svg>')


if __name__ == "__main__":
    import pathlib
    out = pathlib.Path("out"); out.mkdir(exist_ok=True)
    INK, NIGHT, CAL, BALL = "#F4F6F8", "#000000", "#F4F6F8", "#FF6B35"
    (out / "lunes-de-padel-simbolo.svg").write_text(mark())
    (out / "lunes-de-padel-simbolo-cuadrado.svg").write_text(mark(circle=False))
    (out / "lunes-de-padel-logo-vertical-claro.svg").write_text(stacked(INK, BALL, NIGHT))
    (out / "lunes-de-padel-logo-vertical-oscuro.svg").write_text(stacked(NIGHT, BALL, CAL))
    (out / "lunes-de-padel-logo-horizontal-claro.svg").write_text(horizontal(INK, BALL, NIGHT))
    (out / "lunes-de-padel-logo-horizontal-oscuro.svg").write_text(horizontal(NIGHT, BALL, CAL))
    print("ok")
