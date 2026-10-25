"""Publica el borrador aprobado en Instagram y TikTok."""
from . import config, state, telegram


def publish() -> None:
    st = state.load()
    draft = st.get("draft")
    if not draft:
        telegram.send_text("No hay ningún borrador pendiente que publicar.")
        return

    base = config.pages_base_url()
    urls = [f"{base}/posts/{draft['folder']}/{name}" for name in draft["images"]]
    hashtags = " ".join(draft.get("hashtags", []))
    results = []
    done = set(draft.get("published", []))  # redes ya publicadas, para no duplicar si se reintenta

    if config.PUBLISH_INSTAGRAM and "instagram" not in done:
        try:
            from .instagram import publish_carousel

            media_id = publish_carousel(urls, f"{draft.get('caption_instagram', '')}\n\n{hashtags}")
            results.append(f"✅ Instagram publicado (id {media_id})")
            done.add("instagram")
        except Exception as exc:  # noqa: BLE001
            results.append(f"❌ Instagram falló: {exc}")

    if config.PUBLISH_TIKTOK and "tiktok" not in done:
        try:
            from .tiktok import publish_photos

            publish_id = publish_photos(
                urls,
                draft.get("titulo_tiktok") or f"Lunes de Pádel · {draft['semana']}",
                f"{draft.get('caption_tiktok', '')}\n\n{hashtags}",
            )
            privado = " en privado (app sin auditar)" if config.TIKTOK_PRIVACY_LEVEL == "SELF_ONLY" else ""
            results.append(f"✅ TikTok publicado{privado} (id {publish_id})")
            done.add("tiktok")
        except Exception as exc:  # noqa: BLE001
            results.append(f"❌ TikTok falló: {exc}")

    ok = all(r.startswith("✅") for r in results)
    draft["published"] = sorted(done)
    st["status"] = "published" if ok else "pending"
    state.save(st)
    resumen = "\n".join(results)
    if not ok:
        resumen += "\n\nEl borrador sigue pendiente. Cuando lo arregles, vuelve a enviar /publicar; solo se reintentará la red que falló."
    telegram.send_text(resumen)
