#!/usr/bin/env python3
"""
MYCELLIUM-AEGIS · SAYISAL İKİZ
build_single_file.py — Tüm kaynakları tek bir bağımsız HTML dosyasına gömer.

Gömülenler: Computer Modern yazı tipleri (WOFF2, data: URI), KaTeX (CSS + JS +
20 yazı tipi), three.js ve projenin kendi CSS/JS dosyaları. Çıktı dosyası
hiçbir ağ isteği yapmaz ve file:// üzerinden çalışır.

Kullanım:  python3 docs/digital-twin/build_single_file.py
Çıktı:     docs/digital-twin/Mycellium-Aegis_Sayisal_Ikiz.html
"""
import base64
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "Mycellium-Aegis_Sayisal_Ikiz.html"


def b64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode("ascii")


def font_uri(path: pathlib.Path) -> str:
    return f"data:font/woff2;base64,{b64(path)}"


def guard(js: str) -> str:
    """Gömülü betikte </script> dizisi HTML ayrıştırıcısını erken kapatmasın."""
    return js.replace("</script", "<\\/script")


def main() -> int:
    html = (ROOT / "index.html").read_text(encoding="utf-8")

    # ---------------------------------------------------- proje yazı tipleri --
    css = (ROOT / "css" / "twin.css").read_text(encoding="utf-8")
    for otf in ("CMUSerif-Roman", "CMUSerif-Bold", "CMUSerif-Italic", "CMUSansSerif-Regular"):
        woff2 = ROOT / "fonts" / f"{otf}.woff2"
        if not woff2.exists():
            print(f"HATA: {woff2} yok — önce OTF→WOFF2 dönüşümünü çalıştırın.", file=sys.stderr)
            return 1
        css = css.replace(f"url('../fonts/{otf}.otf') format('opentype')",
                          f"url({font_uri(woff2)}) format('woff2')")

    # ------------------------------------------------------------- KaTeX CSS --
    kcss = (ROOT / "vendor" / "katex" / "katex.min.css").read_text(encoding="utf-8")
    kfonts = ROOT / "vendor" / "katex" / "fonts"
    missing = []

    def sub_font(m):
        name = m.group(1)
        f = kfonts / name
        if not f.exists():
            missing.append(name)
            return m.group(0)
        return f"url({font_uri(f)})"

    kcss = re.sub(r"url\(fonts/([^)]+\.woff2)\)", sub_font, kcss)
    if missing:
        print(f"HATA: eksik KaTeX yazı tipleri: {missing}", file=sys.stderr)
        return 1

    # ------------------------------------------------------------- betikler ---
    scripts = [
        ROOT / "vendor" / "three.min.js",
        ROOT / "vendor" / "katex" / "katex.min.js",
        ROOT / "js" / "data.js",
        ROOT / "js" / "textures.js",
        ROOT / "js" / "charts.js",
        ROOT / "js" / "sim.js",
        ROOT / "js" / "scene.js",
        ROOT / "js" / "app.js",
    ]
    js_blocks = []
    for p in scripts:
        js_blocks.append(
            f"<script>/* ==== {p.name} ==== */\n{guard(p.read_text(encoding='utf-8'))}\n</script>"
        )

    # ------------------------------------------------------- HTML'i yeniden --
    html = html.replace(
        '<link rel="stylesheet" href="vendor/katex/katex.min.css">\n'
        '<link rel="stylesheet" href="css/twin.css">',
        f"<style>/* ==== katex.min.css ==== */\n{kcss}\n</style>\n"
        f"<style>/* ==== twin.css ==== */\n{css}\n</style>",
    )
    joined = "\n".join(js_blocks)
    html = re.sub(
        r'<script src="vendor/three\.min\.js"></script>.*?<script src="js/app\.js"></script>',
        lambda _m: joined,          # ters bölü kaçışları yorumlanmasın
        html,
        flags=re.S,
    )
    # PDF bağlantısı tek dosya taşındığında kırılmasın — mutlak depo yoluna çevir
    html = html.replace('href="../hardware/MycelliumAegis_Donanim_Raporu.pdf"',
                        'href="https://github.com/adzetto/MYCELLIUM-AEGIS/blob/main/docs/hardware/MycelliumAegis_Donanim_Raporu.pdf"')
    html = html.replace(
        "<title>Mycellium-Aegis — Sayısal İkiz</title>",
        "<title>Mycellium-Aegis — Sayısal İkiz</title>\n"
        "<!-- Bağımsız tek dosya. Kaynaklardan üretilir: build_single_file.py -->",
    )

    if "vendor/" in html or "js/app.js" in html or "css/twin.css" in html:
        print("HATA: dış kaynak referansı kaldı.", file=sys.stderr)
        return 1

    OUT.write_text(html, encoding="utf-8")
    kb = OUT.stat().st_size / 1024
    print(f"✓ {OUT.relative_to(ROOT.parent.parent)}  —  {kb:,.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
