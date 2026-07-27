#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sunumu tek, bağımsız bir HTML dosyasına derler.

Gömülenler:
  - yazı tipleri (woff2 / otf)            -> CSS içinde data URI
  - şekiller (svg) ve fotoğraflar         -> img src içinde data URI
  - anime.js                              -> satır içi script
  - sayısal ikizin tek dosyalık sürümü    -> iframe srcdoc (base64)

Sonuç dosyası hiçbir ağ isteği yapmaz ve hiçbir yerel dosyaya bağlı
değildir; çift tıklayıp açmak yeterlidir.

Kullanım:  python build_single_file.py
"""
import base64
import mimetypes
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "Mycellium-Aegis_Sunum.html")
OUT = os.path.join(HERE, "Mycellium-Aegis_Sunum_Tek_Dosya.html")
TWIN = os.path.normpath(os.path.join(
    HERE, "..", "digital-twin", "Mycellium-Aegis_Sayisal_Ikiz.html"))

MIME = {".woff2": "font/woff2", ".otf": "font/otf", ".ttf": "font/ttf",
        ".svg": "image/svg+xml", ".webp": "image/webp",
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png"}

missing = []


def data_uri(rel):
    """Göreli yolu data URI'ye çevir; bulunamazsa listeye yaz."""
    path = os.path.normpath(os.path.join(HERE, rel))
    if not os.path.isfile(path):
        missing.append(rel)
        return None
    ext = os.path.splitext(path)[1].lower()
    mime = MIME.get(ext) or mimetypes.guess_type(path)[0] or "application/octet-stream"
    with open(path, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def inline_css_urls(html):
    """CSS içindeki url('...') referanslarını göm."""
    def rep(m):
        rel = m.group(2)
        if rel.startswith(("data:", "http:", "https:")):
            return m.group(0)
        uri = data_uri(rel)
        return m.group(0) if uri is None else f"url({m.group(1)}{uri}{m.group(3)})"
    return re.sub(r"url\((['\"]?)([^'\")]+)\1(\))", rep, html)


def inline_img_src(html):
    """<img src="..."> ve benzeri özniteliklerdeki dosyaları göm."""
    def rep(m):
        attr, quote, rel = m.group(1), m.group(2), m.group(3)
        if rel.startswith(("data:", "http:", "https:", "#")):
            return m.group(0)
        uri = data_uri(rel)
        return m.group(0) if uri is None else f'{attr}={quote}{uri}{quote}'
    return re.sub(r'\b(src|href)=(["\'])([^"\']+\.(?:svg|png|jpe?g|webp))\2',
                  rep, html, flags=re.I)


def inline_scripts(html):
    """<script src="..."></script> etiketlerini satır içine al."""
    def rep(m):
        rel = m.group(1)
        path = os.path.normpath(os.path.join(HERE, rel))
        if not os.path.isfile(path):
            missing.append(rel)
            return m.group(0)
        with open(path, "r", encoding="utf-8") as fh:
            code = fh.read()
        # </script> dizisi betiğin içinde geçerse etiketi erken kapatır
        code = code.replace("</script>", "<\\/script>")
        return f"<script>\n/* {os.path.basename(rel)} */\n{code}\n</script>"
    return re.sub(r'<script[^>]+src=["\']([^"\']+)["\'][^>]*>\s*</script>',
                  rep, html, flags=re.I)


def embed_twin(html):
    """Sayısal ikizi iframe'e srcdoc olarak göm.

    Dosya yolu yerine base64 taşıyoruz: içerik tırnak, betik ve HTML
    etiketi dolu olduğu için öznitelik kaçışlarıyla uğraşmak yerine
    çalışma anında çözülüyor. Böylece ikiz de aynı dosyanın içinde.
    """
    if not os.path.isfile(TWIN):
        missing.append(os.path.relpath(TWIN, HERE))
        return html
    with open(TWIN, "rb") as fh:
        b64 = base64.b64encode(fh.read()).decode("ascii")

    # data-src'yi kaldır; yerine base64 gövdeyi koyan bir betik ekle
    html = re.sub(r'\sdata-src=["\'][^"\']*Sayisal_Ikiz\.html["\']', "", html)
    loader = (
        "\n<script>\n"
        "/* Sayısal ikiz bu dosyanın içine gömülü. iframe'e srcdoc olarak\n"
        "   veriliyor; dış dosya veya ağ gerekmiyor. */\n"
        "window.__AEGIS_TWIN_B64 = \"%s\";\n"
        "</script>\n" % b64
    )
    return html.replace("</body>", loader + "</body>")


def patch_twin_loader(html):
    """primeTwin'i gömülü gövdeyi kullanacak şekilde değiştir."""
    old = "    f.src = f.dataset.src;"
    new = ("    // Tek dosya sürümü: kaynak dışarıda değil, gömülü base64'te.\n"
           "    if(window.__AEGIS_TWIN_B64){\n"
           "      var bin = atob(window.__AEGIS_TWIN_B64);\n"
           "      var bytes = new Uint8Array(bin.length);\n"
           "      for(var i=0;i<bin.length;i++) bytes[i] = bin.charCodeAt(i);\n"
           "      f.srcdoc = new TextDecoder('utf-8').decode(bytes);\n"
           "    } else if(f.dataset.src){ f.src = f.dataset.src; }")
    if old not in html:
        print("  !! primeTwin yaması uygulanamadı (kaynak değişmiş olabilir)")
        return html
    return html.replace(old, new)


def main():
    with open(SRC, "r", encoding="utf-8") as fh:
        html = fh.read()

    html = inline_scripts(html)
    html = inline_css_urls(html)
    html = inline_img_src(html)
    html = patch_twin_loader(html)
    html = embed_twin(html)

    html = html.replace(
        "<title>",
        "<!-- Bağımsız tek dosya sürümü — build_single_file.py ile üretildi.\n"
        "     Yazı tipleri, şekiller, fotoğraflar, anime.js ve sayısal ikiz\n"
        "     gömülüdür; hiçbir ağ isteği yapılmaz. -->\n<title>", 1)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(html)

    left = re.findall(r'\b(?:src|href)=["\'](?!data:|#|https?:)([^"\']+)["\']', html)
    left = [u for u in left if not u.startswith("mailto:")]

    print(f"\n  {os.path.basename(OUT)}  —  {os.path.getsize(OUT)/1024/1024:.2f} MB")
    if missing:
        print("  !! bulunamayan dosyalar:", ", ".join(sorted(set(missing))))
    if left:
        print("  !! hâlâ dışarıya bakan referanslar:", ", ".join(sorted(set(left))))
    if not missing and not left:
        print("  tüm varlıklar gömüldü, dış referans yok")
    return 1 if (missing or left) else 0


if __name__ == "__main__":
    sys.exit(main())
