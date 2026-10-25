# Lunes de Pádel 🎾

Cuenta automática de Instagram y TikTok que cada lunes publica un carrusel con las noticias de pádel de la semana anterior. Tú solo revisas el borrador en Telegram y respondes `/publicar`.

## Cómo funciona

1. **Lunes a las 8:00 (hora de España en verano, 7:00 en invierno)**, GitHub Actions lanza `diario.generate`.
2. Claude busca en la web las noticias de lunes a domingo (torneos Premier Padel y FIP, cambios de pareja del top 100, palas nuevas, retiradas, clubs, selecciones, ranking) y redacta los textos.
3. Para cada noticia busca una **imagen real** y le quita el fondo (ver más abajo).
4. Se generan 10 imágenes como máximo (portada, hasta 8 noticias y cierre) con la plantilla de `diario/templates/slides.html`. Las noticias con foto muestran el recorte "de pie" sobre la línea de saque.
5. Te llega por Telegram el carrusel, los textos de cada red, **la fuente de cada noticia** y de dónde sale cada foto, para que lo compruebes.
6. Respondes al bot y, en 10 minutos como mucho, se ejecuta tu orden:

| Orden | Qué hace |
|---|---|
| `/publicar` | Publica en Instagram y TikTok |
| `/foto 3` (como pie de una foto que envías) | Recorta tu foto y la pone en la diapositiva 3. Puedes añadir crédito: `/foto 3 Foto: @bullpadel` |
| `/sinfoto 3` | Deja la diapositiva 3 solo con texto |
| `/rehacer quita la noticia X y añade Y` | Claude prepara una nueva versión con tus cambios (se pierden las fotos que hayas puesto tú) |
| `/cancelar` | Esta semana no se publica |
| `/generar` | Crea un borrador ahora mismo (útil para probar) |
| `/estado` | Te dice en qué punto está |

## Identidad visual

La marca completa (logo, símbolo, colores, tipografías y reglas del carrusel) está en el sistema de diseño de Lunes de Pádel: https://claude.ai/artifact/JPjRmka2qPRbTGszyNfjBZ

En la carpeta `marca/` tienes el logo principal (la red con el nombre tejido), la foto de perfil (`lunes-de-padel-foto-perfil.png`, el símbolo LP) lista para subir a Instagram y TikTok, y las letras de la marca en blanco y negro. `marca/generar_logos.py` vuelve a dibujarlos si cambias algo.

## Imágenes de las noticias

Cada noticia puede llevar un recorte real, sin fondo, junto al titular:

- **Personas** (campeones, retiradas, entrenadores): se buscan en **Wikimedia Commons**, que solo tiene fotos con licencia libre. El autor y la licencia aparecen en pequeño en la diapositiva, como exigen esas licencias. Si es una pareja, salen los dos.
- **Material** (palas, zapatillas): se toma la imagen principal de la **web oficial de la marca**. Lo más seguro es escribir a las marcas para pedirles permiso o su kit de prensa; suelen agradecer la visibilidad.
- **Tus fotos**: si no aparece imagen o no te convence, envíala tú al bot con `/foto N`.
- Si no hay una imagen fiable, la diapositiva sale con el diseño de solo texto. Es preferible eso a una foto equivocada.

El fondo se quita con [rembg](https://github.com/danielgatis/rembg), gratis y dentro de GitHub Actions. La primera vez descarga el modelo (unos 170 MB) y luego queda en caché.

**Evita** usar fotos de agencias, de Premier Padel o de medios: tienen derechos de autor y son las que más denuncias generan. Revisa siempre que la foto corresponde a la persona correcta antes de publicar.

## Coste

Todo es gratis salvo la API de Claude, que se paga por uso: tokens más 10 $ por cada 1.000 búsquedas web. Con un post a la semana y hasta 15 búsquedas por borrador, son unos 1-2 € al mes. Pon un límite de gasto en la consola de Claude para estar tranquilo.

## Puesta en marcha (una sola vez, ~1 hora)

### 1. Repositorio y GitHub Pages
1. Crea un repositorio **público** en GitHub (por ejemplo `lunes-de-padel`) y sube todos estos archivos. Tiene que ser público para que GitHub Pages y Actions sean gratis sin límites. Las claves van en Secrets, que nunca son visibles.
2. Ve a *Settings → Pages* y elige *Deploy from a branch*, rama `main`, carpeta `/docs`.
3. Ve a *Settings → Secrets and variables → Actions → Variables* y crea `PAGES_BASE_URL` con tu URL, por ejemplo `https://tuusuario.github.io/lunes-de-padel`.

### 2. Clave de Claude
En [platform.claude.com](https://platform.claude.com) crea una cuenta, carga saldo (5 $ duran meses) y genera una API key. Guárdala como secret `ANTHROPIC_API_KEY`.

### 3. Bot de Telegram
1. En Telegram, habla con **@BotFather**, envía `/newbot` y sigue los pasos. Te dará el token, que va en el secret `TELEGRAM_BOT_TOKEN`.
2. Escríbele cualquier cosa a tu bot y abre `https://api.telegram.org/bot<TOKEN>/getUpdates`. El número en `"chat":{"id": ...}` es tu `TELEGRAM_CHAT_ID`. El bot solo obedece a ese chat.

### 4. Instagram
1. Pasa la cuenta de Instagram a **profesional** (Creador o Empresa).
2. En [developers.facebook.com](https://developers.facebook.com) crea una app y añade el producto **Instagram → API con inicio de sesión de Instagram**.
3. Añade tu cuenta de Instagram, genera un token con los permisos `instagram_business_basic` e `instagram_business_content_publish` y guárdalo como `INSTAGRAM_ACCESS_TOKEN`. El sistema lo renueva solo cada semana.
4. Abre `https://graph.instagram.com/me?fields=user_id,username&access_token=<TOKEN>` y guarda el `user_id` como `INSTAGRAM_USER_ID`.

Meta cambia sus menús a menudo. Si algo no coincide, busca su guía oficial de "Instagram API with Instagram Login".

### 5. TikTok
1. En [developers.tiktok.com](https://developers.tiktok.com) crea una app y añade **Login Kit** y **Content Posting API** con *Direct Post* activado. Los scopes son `user.info.basic` y `video.publish`.
2. Como Redirect URI pon tu web de Pages (`https://tuusuario.github.io/lunes-de-padel/`).
3. En la sección de verificación de dominio/URL, verifica el prefijo de tu web de Pages, porque TikTok solo descarga imágenes de URLs verificadas. Si te pide subir un archivo de verificación, colócalo en la carpeta `docs/`.
4. Guarda `TIKTOK_CLIENT_KEY` y `TIKTOK_CLIENT_SECRET` como secrets.
5. En tu ordenador ejecuta `pip install requests` y `python tools/tiktok_auth.py`, sigue los pasos y guarda el resultado como `TIKTOK_REFRESH_TOKEN`.
6. **Importante:** hasta que TikTok audite tu app, los posts se publican en privado. Cuando completes la auditoría (desde el panel de la app) y te la aprueben, crea la variable `TIKTOK_PRIVACY_LEVEL` con el valor `PUBLIC_TO_EVERYONE`. Mientras tanto puedes desactivar TikTok con la variable `PUBLISH_TIKTOK` = `false`.

### 6. Token para renovar claves solas
Crea en GitHub un *fine-grained personal access token* (*Settings → Developer settings*) solo para este repositorio, con el permiso **Secrets: Read and write**. Guárdalo como `GH_PAT`. Sirve para que los tokens de Instagram y TikTok se actualicen sin que hagas nada.

### Resumen de Secrets

| Secret | De dónde sale |
|---|---|
| `ANTHROPIC_API_KEY` | Consola de Claude |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | BotFather y getUpdates |
| `INSTAGRAM_ACCESS_TOKEN`, `INSTAGRAM_USER_ID` | App de Meta |
| `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET`, `TIKTOK_REFRESH_TOKEN` | App de TikTok y `tools/tiktok_auth.py` |
| `GH_PAT` | Token personal de GitHub |

Variables (no secretas): `PAGES_BASE_URL` (obligatoria), `TIKTOK_PRIVACY_LEVEL`, `PUBLISH_INSTAGRAM`, `PUBLISH_TIKTOK`.

### 7. Prueba
En la pestaña *Actions*, abre **Borrador semanal** y pulsa *Run workflow*. En unos minutos te llegará el borrador a Telegram. Te recomiendo la primera vez probar con `PUBLISH_INSTAGRAM` y `PUBLISH_TIKTOK` en `false` para ver solo el borrador.

## Personalizar

- **Diseño:** `diario/templates/slides.html` (colores en `:root`, tipografías de Google Fonts).
- **Qué noticias busca y cómo escribe:** `diario/news.py` (`SYSTEM_PROMPT` y `build_user_prompt`).
- **Día y hora:** el `cron` de `.github/workflows/generate.yml` (está en hora UTC).
- **Modelo de Claude y número de búsquedas:** variables `CLAUDE_MODEL` y `MAX_WEB_SEARCHES` en `diario/config.py`.

## Límites a tener en cuenta

- **Revisa siempre las fotos:** con nombres parecidos, Wikimedia puede devolver a otra persona. Usa `/sinfoto N` o `/foto N` si algo no cuadra.
- **Revisa siempre las fuentes.** Claude está instruido para no incluir nada sin verificar, pero puede equivocarse con un marcador o una pareja.
- GitHub puede retrasar las tareas programadas unos minutos, a veces más en horas punta.
- Las imágenes del carrusel quedan públicas en tu web de GitHub Pages, porque Instagram y TikTok necesitan descargarlas de una URL.
- La versión de la API de Instagram está en `INSTAGRAM_API_VERSION` (`diario/config.py`). Meta retira versiones antiguas cada ~2 años, así que actualízala si un día falla.
