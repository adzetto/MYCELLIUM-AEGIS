# -*- coding: utf-8 -*-
"""Fizibilite analizinin tamamını sırayla üretir.

    python numeric/build.py              # her şeyi baştan
    python numeric/build.py --skip-run   # veri hazırsa yalnızca çıktılar
    python numeric/build.py --skip-geo   # coğrafi katmanı atla

Adımlar: sayısal çalışma → coğrafi katman → şekil kaynakları → LaTeX makroları
→ bağımsız şekil derlemesi → rapor PDF'i (iki geçiş) → sunum slaytları.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NUM = ROOT / "numeric"
PY = sys.executable
ARGS = set(sys.argv[1:])


def run(cmd, cwd=ROOT, label=""):
    t0 = time.time()
    print(f"\n>>> {label or ' '.join(map(str, cmd))}", flush=True)
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        sys.exit(f"HATA: {label} (kod {r.returncode})")
    print(f"    tamam ({time.time() - t0:.0f} s)", flush=True)


def main():
    if "--skip-run" not in ARGS:
        run([PY, str(NUM / "run_all.py")], label="sayisal calisma")
    if "--skip-run" not in ARGS and "--skip-geo" not in ARGS:
        run([PY, str(NUM / "geo.py")], label="cografi katman")
    run([PY, str(NUM / "make_tikz.py")], label="sekil kaynaklari")
    run([PY, str(NUM / "make_numbers.py")], label="LaTeX makrolari")
    run([PY, str(NUM / "build_figures.py")], label="bagimsiz sekil derlemesi")
    for i in (1, 2):
        run(["pdflatex", "-interaction=nonstopmode",
             "Mycellium-Aegis_Fizibilite_Analizi.tex"],
            label=f"rapor derlemesi {i}/2")
    run([PY, str(NUM / "make_slides.py")], label="sunum slaytlari")
    print("\nbitti.")


if __name__ == "__main__":
    main()
