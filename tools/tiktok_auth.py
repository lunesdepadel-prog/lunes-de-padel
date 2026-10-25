"""Obtén tu TIKTOK_REFRESH_TOKEN (solo hay que hacerlo una vez).

1. Ejecuta:  python tools/tiktok_auth.py
2. Abre el enlace que imprime, inicia sesión con la cuenta de Lunes de Pádel y acepta.
3. TikTok te redirige a tu web de GitHub Pages con ?code=... en la barra de direcciones.
   Copia la URL completa y pégala aquí.
4. Copia el refresh_token que aparece y guárdalo como secret TIKTOK_REFRESH_TOKEN.
"""
import secrets
import urllib.parse

import requests

client_key = input("Client key de tu app de TikTok: ").strip()
client_secret = input("Client secret: ").strip()
redirect_uri = input("Redirect URI registrada en la app (ej: https://tuusuario.github.io/lunes-de-padel/): ").strip()

params = {
    "client_key": client_key,
    "scope": "user.info.basic,video.publish",
    "response_type": "code",
    "redirect_uri": redirect_uri,
    "state": secrets.token_urlsafe(8),
}
print("\nAbre este enlace en el navegador:\n")
print("https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode(params))

pasted = input("\nPega aquí la URL completa a la que te ha redirigido: ").strip()
code = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query)["code"][0]

r = requests.post(
    "https://open.tiktokapis.com/v2/oauth/token/",
    data={
        "client_key": client_key,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri,
    },
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=30,
)
data = r.json()
if "refresh_token" not in data:
    raise SystemExit(f"Error: {data}")
print("\n✅ Guarda esto como secret TIKTOK_REFRESH_TOKEN:\n")
print(data["refresh_token"])
