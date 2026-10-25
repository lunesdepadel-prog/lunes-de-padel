from logo import word, CLIP
AM = "#E3F23C"; NEG = "#000000"; AZ = "#1B4F9C"; CAL = "#F4F6F8"

def bola(cx, cy, r, uid, seam=NEG):
    return (f'<clipPath id="k{uid}"><circle cx="{cx}" cy="{cy}" r="{r}"/></clipPath>'
            f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{AM}"/>'
            f'<g clip-path="url(#k{uid})" fill="none" stroke="{seam}" stroke-width="{r*.1:.1f}">'
            f'<circle cx="{cx - r*1.55:.1f}" cy="{cy}" r="{r*1.05:.1f}"/><circle cx="{cx + r*1.55:.1f}" cy="{cy}" r="{r*1.05:.1f}"/></g>')

def svg(w, h, body, bg=NEG):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{CLIP}<rect width="{w}" height="{h}" fill="{bg}"/>{body}</svg>'

# D. Monograma LP: la L y el ojo de la P es la bola
def monograma(k=1, ox=0, oy=0, uid="d"):
    t = 92 * k
    x, top, bot = ox + 135*k, oy + 110*k, oy + 490*k
    r = 118 * k
    stem = f'<rect x="{x}" y="{top}" width="{t}" height="{bot-top}" fill="{CAL}"/>'
    foot = f'<rect x="{x}" y="{bot - t}" width="{330*k}" height="{t}" fill="{CAL}"/>'
    b = bola(x + t + r - 6*k, top + r, r, uid)
    return stem + foot + b

# E. Pala-calendario: los agujeros de la pala forman una semana; el lunes, en amarillo
def pala(k=1, ox=0, oy=0, uid="e"):
    cx = ox + 300*k
    head = (f'<path d="M{cx},{oy+60*k} C{cx+200*k},{oy+60*k} {cx+190*k},{oy+250*k} {cx+150*k},{oy+330*k} '
            f'C{cx+120*k},{oy+390*k} {cx+60*k},{oy+410*k} {cx+40*k},{oy+420*k} L{cx+40*k},{oy+540*k} '
            f'L{cx-40*k},{oy+540*k} L{cx-40*k},{oy+420*k} C{cx-60*k},{oy+410*k} {cx-120*k},{oy+390*k} {cx-150*k},{oy+330*k} '
            f'C{cx-190*k},{oy+250*k} {cx-200*k},{oy+60*k} {cx},{oy+60*k} Z" fill="{CAL}"/>')
    holes = []
    step, r = 38*k, 10*k
    x0 = cx - 3*step
    for row in range(5):
        for col in range(7):
            hx, hy = x0 + col*step, oy + 130*k + row*step
            if row == 0 and col in (0, 6) or row == 4 and col in (0, 1, 5, 6):
                continue
            fill = AM if (row == 1 and col == 0) else NEG
            rr = r*2.1 if fill == AM else r
            holes.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{rr:.1f}" fill="{fill}"/>')
    grip = f'<rect x="{cx-40*k}" y="{oy+470*k}" width="{80*k}" height="{70*k}" fill="{AZ}"/>'
    return head + grip + "".join(holes)

# F. La L como trayectoria: la bola baja pegada al cristal y sale rodando
def trayectoria(k=1, ox=0, oy=0, uid="f"):
    x, y0, y1, x1, rad = ox + 170*k, oy + 90*k, oy + 450*k, oy and 0, 90*k
    r = 70*k
    xb = ox + 460*k
    path = (f'<path d="M{x},{y0} V{y1 - rad} A{rad},{rad} 0 0 0 {x + rad},{y1} H{xb - r - 20*k}" fill="none" '
            f'stroke="{CAL}" stroke-width="{54*k}" stroke-linecap="round" stroke-dasharray="{1*k} {0*k}"/>')
    # estela: el trazo se adelgaza en tres tramos hacia el origen
    trail = (f'<path d="M{x},{y0} V{y0+90*k}" stroke="{NEG}" stroke-width="{58*k}" stroke-dasharray="{14*k} {22*k}" fill="none"/>')
    return path + trail + bola(xb, y1 - r + 27*k, r, uid)

def lockup(fn, uid, k, ox, oy):
    t1, w1 = word("LUNES", 0, 0, 1, CAL)
    sc = w1 / word("DE PÁDEL", 0, 0, 1, CAL)[1]
    x0 = 330
    t1, _ = word("LUNES", x0, 150, 1, CAL)
    t2, _ = word("DE PÁDEL", x0, 150 + 130 + 36 * sc, sc, CAL)
    return svg(int(x0 + w1 + 60), 470, fn(k, ox, oy, uid) + t1 + t2)

if __name__ == "__main__":
    import pathlib
    out = pathlib.Path("conceptos2"); out.mkdir(exist_ok=True)
    for n, fn, (k, ox, oy) in [("d", monograma, (.55, -20, 70)), ("e", pala, (.6, -30, 60)), ("f", trayectoria, (.55, -20, 85))]:
        (out / f"{n}_simbolo.svg").write_text(svg(600, 600, fn(1, 0, 0, n + "1")))
        (out / f"{n}_logo.svg").write_text(lockup(fn, n + "2", k, ox, oy))
    print("ok")
