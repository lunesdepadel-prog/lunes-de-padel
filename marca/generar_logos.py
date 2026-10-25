"""Vuelve a generar los logos de Lunes de Pádel en esta carpeta.

Uso: cd marca && python generar_logos.py
(logo.py = letras de línea de pista, red2.py = red con el nombre tejido, conceptos2.py = la bola)
"""
from logo import horizontal
from red2 import logo, simbolo

open("lunes-de-padel-logo-red.svg", "w").write(logo())
open("lunes-de-padel-simbolo-lp.svg", "w").write(simbolo())
open("lunes-de-padel-letras-blanco.svg", "w").write(horizontal("#F4F6F8", "#E3F23C", None, pad=0))
open("lunes-de-padel-letras-negro.svg", "w").write(horizontal("#000000", "#E3F23C", None, pad=0))
print("Logos generados. Para los PNG, abre los SVG en el navegador y expórtalos, o usa Playwright.")
