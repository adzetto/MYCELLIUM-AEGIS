# -*- coding: utf-8 -*-
"""Her figures/fig_*.tikz dosyasını bağımsız (standalone) derler ve
dvisvgm ile SVG'ye çevirir. SVG'ler sunumda kullanılır; yazı tipleri yola
(path) dönüştürüldüğü için dosyalar kendi kendine yeterlidir ve sunumun
"sıfır ağ isteği" kuralını bozmaz.

Kullanım:  python build_figures.py [ad ...]
Ad verilmezse bütün şekiller derlenir.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figures"
BUILD = ROOT / ".build"
BUILD.mkdir(exist_ok=True)

# Yoğun matris çizimleri: yalnızca PDF üretilir (SVG'leri 1--6 MB olurdu)
NO_SVG = {"fig_geomap", "fig_georisk", "fig_geosection", "fig_energy"}

WRAPPER = r"""\documentclass[border=3pt]{standalone}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[shorthands=off,turkish]{babel}
\usepackage{lmodern}
\usepackage{amsmath,amssymb,bm}
\input{preamble}
\begin{document}
\input{figures/%s.tikz}
\end{document}
"""


def build(stem):
    tex = ROOT / f"__standalone_{stem}.tex"
    tex.write_text(WRAPPER % stem, encoding="utf-8")
    cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
           f"-output-directory={BUILD}", tex.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    tex.unlink(missing_ok=True)
    pdf = BUILD / f"__standalone_{stem}.pdf"
    if r.returncode != 0 or not pdf.exists():
        log = (BUILD / f"__standalone_{stem}.log")
        tail = ""
        if log.exists():
            lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
            tail = "\n".join(l for l in lines if l.startswith("!") or "Error" in l)[:1200]
        print(f"  HATA {stem}\n{tail}")
        return False
    shutil.copy(pdf, FIG / f"{stem}.pdf")
    svg = FIG / f"{stem}.svg"
    if stem in NO_SVG:
        # Matris çizimleri hücre başına bir dikdörtgen ürettiği için SVG
        # olarak megabaytlarca yer tutuyor; bunların sunum kopyası
        # make_slides.py tarafından PDF'ten PNG olarak alınır.
        svg.unlink(missing_ok=True)
        print(f"  {stem}: {pdf.stat().st_size // 1024} kB pdf (svg atlandi)")
        return True
    # pdftocairo kullanılıyor, dvisvgm değil: dvisvgm'in PDF yolu şeffaflık
    # durumunu sızdırıp bütün yolları stroke-opacity='0' ile yazıyor, yani
    # SVG tarayıcıda görünmez oluyor (PDF'te sorun yok). pdftocairo glifleri
    # yol olarak gömer, dolayısıyla çıktı yine çevrimdışı çalışır.
    r2 = subprocess.run(["pdftocairo", "-svg", str(pdf), str(svg)],
                        capture_output=True, text=True, encoding="utf-8",
                        errors="replace")
    if r2.returncode != 0:
        print(f"  pdftocairo HATA {stem}: {r2.stderr[:400]}")
        return False
    print(f"  {stem}: {pdf.stat().st_size // 1024} kB pdf · "
          f"{svg.stat().st_size // 1024} kB svg")
    return True


def main():
    names = sys.argv[1:]
    stems = ([f"fig_{n}" if not n.startswith("fig_") else n for n in names]
             if names else sorted(p.stem for p in FIG.glob("fig_*.tikz")))
    ok = sum(build(s) for s in stems)
    print(f"{ok}/{len(stems)} sekil derlendi")


if __name__ == "__main__":
    main()
