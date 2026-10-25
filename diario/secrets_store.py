"""Guarda tokens renovados como Secrets del repositorio usando la CLI de GitHub (gh).

Los tokens de Instagram (60 días) y TikTok (refresh token) se renuevan solos;
para no tener que copiarlos a mano, el script los reescribe en los Secrets.
Necesita el secret GH_PAT: un token personal de GitHub con permiso
"Secrets: Read and write" sobre este repositorio.
"""
import os
import subprocess


def update_secret(name: str, value: str) -> bool:
    pat, repo = os.environ.get("GH_PAT"), os.environ.get("GITHUB_REPOSITORY")
    if not pat or not repo:
        print(f"⚠️  No se pudo guardar {name}: falta GH_PAT. Actualízalo a mano en los Secrets.")
        return False
    result = subprocess.run(
        ["gh", "secret", "set", name, "--repo", repo, "--body", value],
        env={**os.environ, "GH_TOKEN": pat},
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"⚠️  Error guardando {name}: {result.stderr.strip()}")
        return False
    print(f"🔐 Secret {name} actualizado.")
    return True
