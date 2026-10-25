"""Logo: red de pádel sobre negro, con LUNES DE PÁDEL tejido en blanco en la malla (como «SEVILLA P2»)."""
from logo import GLYPHS, GAP
from conceptos2 import bola
AM = "#E3F23C"; NEG = "#000000"; CAL = "#F4F6F8"; MALLA = "#3A414C"; POSTE = "#23272E"

def letras(texto, x, y, escala, sw=30):
    """Trazos de las letras (para usarlos como máscara). sw = grosor sobre altura 100."""
    parts, cx = [], 0.0
    for ch in texto:
        w, d = GLYPHS[ch]
        if d:
            parts.append(f'<path transform="translate({cx:.1f} 0)" d="{d}"/>')
        cx += w + GAP + (sw - 18) * .6
    ancho = (cx - GAP - (sw - 18) * .6) * escala
    g = (f'<g transform="translate({x:.1f} {y:.1f}) scale({escala})" fill="none" stroke="#fff" stroke-width="{sw}" '
         f'stroke-linecap="butt" stroke-linejoin="miter" stroke-miterlimit="1.5">{"".join(parts)}</g>')
    return g, ancho

def ancho_texto(texto, escala, sw=30):
    return letras(texto, 0, 0, escala, sw)[1]

def malla(x0, y0, x1, y1, paso, color, grosor, opacidad=1):
    ls = [f'<line x1="{x0}" y1="{yy}" x2="{x1}" y2="{yy}"/>' for yy in range(int(y0), int(y1) + 1, paso)]
    ls += [f'<line x1="{xx}" y1="{y0}" x2="{xx}" y2="{y1}"/>' for xx in range(int(x0), int(x1) + 1, paso)]
    return f'<g stroke="{color}" stroke-width="{grosor}" stroke-opacity="{opacidad}">{"".join(ls)}</g>'

def red(x, y, w, alto, texto, escala, uid, cinta=34, paso=14, bola_pos=.82, postes=True, r_bola=None, ocupa=.88, hilo=4.6, cx=None):
    yb = y + cinta
    out = [malla(x, yb, x + w, yb + alto, paso, MALLA, 2.4)]
    # letras tejidas: la misma malla, en blanco y más gruesa, solo dentro de las letras
    # el texto ocupa una fracción fija del ancho visible de la red
    visible = w if cx is None else cx[1]
    escala = min(escala, visible * ocupa / ancho_texto(texto, 1))
    tw = ancho_texto(texto, escala)
    th = 100 * escala
    centro = x + w / 2 if cx is None else cx[0]
    lx, ly = centro - tw / 2, yb + (alto - th) / 2 + 22 * escala / 1.55
    g, _ = letras(texto, lx, ly, escala)
    out.append(f'<mask id="t{uid}" maskUnits="userSpaceOnUse"><rect x="{x}" y="{yb}" width="{w}" height="{alto}" fill="#000"/>{g}</mask>')
    out.append(f'<g mask="url(#t{uid})">{malla(x, yb, x + w, yb + alto, paso, CAL, hilo)}</g>')
    # cinta superior blanca
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{cinta}" fill="{CAL}"/>')
    if postes:
        for px in (x - 26, x + w):
            out.append(f'<rect x="{px}" y="{y - 22}" width="26" height="{cinta + alto + 22}" rx="4" fill="{POSTE}"/>')
    r = r_bola or cinta * 1.25
    out.append(bola(x + w * bola_pos, y - r * .5, r, uid))
    return "".join(out)

def svg(w, h, body, bg=NEG):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}"><rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>'

def logo():
    return svg(1720, 520, red(90, 130, 1540, 300, "LUNES DE PÁDEL", 1.55, "lg", bola_pos=.86))

def simbolo(texto="LP", escala=3.2):
    return svg(1080, 1080, red(-20, 330, 1120, 500, texto, escala, "sb", cinta=56, paso=18, bola_pos=.70, postes=False, r_bola=82, ocupa=.72, hilo=7, cx=(540, 900)))

if __name__ == "__main__":
    import pathlib
    o = pathlib.Path("red2"); o.mkdir(exist_ok=True)
    (o / "logo.svg").write_text(logo())
    (o / "simbolo-lp.svg").write_text(simbolo())
    (o / "simbolo-lunes.svg").write_text(simbolo("LUNES", 1.75))
    print("ok")
