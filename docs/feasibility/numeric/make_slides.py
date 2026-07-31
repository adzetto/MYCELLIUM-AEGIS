# -*- coding: utf-8 -*-
"""Fizibilite slaytlarını sunuma yerleştirir.

- Seçilen pgfplots şekillerini SVG olarak sunumun figures/ klasörüne kopyalar
  (yazı tipleri yola çevrilmiş olduğu için sunumun çevrimdışı kuralı korunur),
- summary.json'daki gerçek sayılarla iki slayt üretir,
- slaytları sunumun içine FEAS-BEGIN / FEAS-END işaretleri arasına koyar;
  işaretler zaten varsa aralarındaki içeriği değiştirir, yoksa doğrulama
  slaytından hemen sonra ekler.

Betik yeniden çalıştırılabilir: sayısal çalışma güncellenince slayttaki
rakamlar da güncellenir.
"""
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECK = ROOT.parent / "pitch-decks" / "Mycellium-Aegis_Sunum.html"
DECKFIG = ROOT.parent / "pitch-decks" / "figures"
S = json.loads((ROOT / "summary.json").read_text(encoding="utf-8"))
G = json.loads((ROOT / "summary_geo.json").read_text(encoding="utf-8"))

# Çizgi grafikleri vektörel (SVG) kalır. Harita ve kesit, hücre başına bir
# dikdörtgen çizdiği için SVG olarak megabaytlarca yer tutuyor; bunlar 200 dpi
# PNG'ye rasterleştirilir — sunum 1920x1080 tuvalde bunun altında kalıyor.
WANT_SVG = {"depth": "feas_depth", "leadcdf": "feas_leadcdf"}
WANT_PNG = {"geomap": "feas_geomap", "geosection": "feas_section"}


def tr(v, nd=1):
    return f"{v:,.{nd}f}".replace(",", ".").replace(".", ",", 1) if nd else f"{v:,.0f}".replace(",", ".")


def num(v, nd=1):
    s = f"{v:.{nd}f}".replace(".", ",")
    return s


def copy_figs():
    import subprocess
    for src, dst in WANT_SVG.items():
        p = ROOT / "figures" / f"fig_{src}.svg"
        if not p.exists():
            raise SystemExit(f"eksik: {p} — once build_figures.py calistirin")
        shutil.copy(p, DECKFIG / f"{dst}.svg")
        print(f"  {p.name} -> figures/{dst}.svg ({p.stat().st_size // 1024} kB)")
    for src, dst in WANT_PNG.items():
        p = ROOT / "figures" / f"fig_{src}.pdf"
        if not p.exists():
            raise SystemExit(f"eksik: {p} — once build_figures.py calistirin")
        out = DECKFIG / dst
        subprocess.run(["pdftoppm", "-png", "-r", "200", "-singlefile",
                        str(p), str(out)], check=True)
        f = DECKFIG / f"{dst}.png"
        print(f"  {p.name} -> figures/{dst}.png ({f.stat().st_size // 1024} kB)")


def slides():
    mc, v, n, e = S["mc"], S["verification"], S["nominal"], S["econ"]
    cov, gr, lf = S["coverage"], G["grid"], G["lead_field"]
    lead_med = num(mc["lead_median"], 0)
    auc = num(mc["auc_fusion"], 2)
    gci = num(v["gci_grid_pct"], 1)
    p15 = num(100 * mc["p_lead_gt15"], 0)
    # tek yönlü kuralın alarm ürettiği en derin nokta (-999 = alarm yok)
    _ok = [(z, L) for z, L in zip(S["depth"]["z_cm"], S["depth"]["lead_one"]) if L > -900]
    z_one_max = num(max(z for z, _ in _ok), 0) if _ok else "--"
    land = f'{gr["land_km2"]:,.0f}'.replace(",", ".")
    high = f'{gr["risk_high_km2"]:,.0f}'.replace(",", ".")
    geo_med = num(lf["median"], 0)
    npv_pos = num(100 * e["p_npv_pos"], 0)
    capex = f'{cov["example"]["capex_ha"]:,.0f}'.replace(",", ".")
    _i18 = min(range(len(S["depth"]["z_cm"])), key=lambda k: abs(S["depth"]["z_cm"][k] - 18))
    lead_18 = num(S["depth"]["lead_two"][_i18], 0)

    a = f"""  <!-- FEAS-BEGIN · fizibilite slaytlari — numeric/make_slides.py uretir -->
  <!-- 10 FİZİBİLİTE I · FİZİK -->
  <section class="slide">
    <div class="inner">
      <div class="eyebrow reveal">04.1 · FİZİBİLİTE · FİZİKSEL DOĞRULAMA</div>
      <h1 class="title reveal">Öncü süre bir iddia değil, <span class="accent">çözülmüş bir denklem.</span></h1>
      <div class="grid reveal" style="grid-template-columns:1fr 1.12fr;gap:52px;margin-top:10px;flex:1;min-height:0">
        <div style="display:flex;flex-direction:column;gap:22px;min-height:0">
          <div class="block hi">
            <h3>Bağlaşık tensör–PDE modeli</h3>
            <p style="margin-bottom:16px;font-size:20px">Isı ve nem taşınımı ayrı ayrı değil,
              dört indisli tek bir yayınım nesnesiyle birlikte çözülür. Katmanlı toprağın
              yönbağımlılığı ikinci mertebe bir iletkenlik tensörüyle taşınır.</p>
            <p class="serif" style="font-size:21px;color:var(--ink);line-height:1.75;margin-bottom:6px">
              ∂<i>u<sub>a</sub></i>/∂<i>t</i> = ∂<i><sub>i</sub></i>
              ( 𝒟<i><sub>abij</sub></i> ∂<i><sub>j</sub>u<sub>b</sub></i> ) + <i>s<sub>a</sub></i>
            </p>
            <p class="serif" style="font-size:21px;color:var(--ink);line-height:1.75">
              <b>K</b>(<b>n</b>) = <i>k</i><sub>∥</sub>(<b>I</b> − <b>n</b>⊗<b>n</b>)
              + <i>k</i><sub>⊥</sub> <b>n</b>⊗<b>n</b>
            </p>
          </div>
          <div class="block">
            <h3 style="font-size:26px">Bulgu: kuralın işareti ters</h3>
            <p style="font-size:19px">Isınma ve buhar yoğuşması direnci <span class="warn">düşürür</span>.
              Belgedeki tek yönlü kural, prob {z_one_max} cm'den derinde <b>hiç tetiklenmiyor</b>;
              mutlak değere geçirildiğinde <b>{lead_med} dk önce</b> uyarıyor. Bedeli sıfır — tek satır gömülü yazılım.</p>
          </div>
          <div class="block">
            <h3 style="font-size:26px">Doğrulama, iddia değil ölçüm</h3>
            <p style="font-size:19px">Her iki uzaysal operatör de üretilmiş çözümle sınandı;
              gözlenen yakınsama mertebesi <b>2,0</b>. Öncü sürenin ızgara belirsizliği
              <b>%{gci}</b>, kaynama cephesinin sayısal düzenlileştirme parametrelerine
              duyarlılığı <b>ölçülemez düzeyde</b>.</p>
          </div>
        </div>
        <div class="fig-wrap" style="min-height:0;justify-content:center">
          <img src="figures/feas_depth.svg" alt="Öncü sürenin prob derinliğine bağımlılığı"
               style="width:100%;height:auto">
          <div class="figcap"><span class="caption-lbl">Şekil 12:</span> Öncü süre, prob derinliği
            ve iki farklı karar kuralı. Belgedeki tek yönlü kural yalnızca miselyumun
            yaşayamayacağı sığlıkta alarm üretebiliyor; iki yönlü kural miselyumun yaşadığı
            bantta bile {lead_18} dakika bırakıyor.</div>
        </div>
      </div>
      <div class="statline reveal" style="margin-top:20px">
        <div><div class="stat">{lead_med}<span class="u">dk</span></div>
          <div class="tile-lbl">Medyan öncü süre</div></div>
        <div><div class="stat">%{p15}<span class="u">olasılık</span></div>
          <div class="tile-lbl">Öncü süre &gt; 15 dk</div></div>
        <div><div class="stat">{auc}<span class="u">AUC</span></div>
          <div class="tile-lbl">Kanalların ayırt ediciliği</div></div>
        <div><div class="stat" style="color:var(--ember)">%{gci}<span class="u">GCI</span></div>
          <div class="tile-lbl">Sayısal belirsizlik</div></div>
      </div>
    </div>
    <div class="footnotes"><span>Philip &amp; de Vries (1957) · Côté &amp; Konrad (2005) · Geselowitz (1971) · {S["mc"]["n_pos"]} koşumluk Monte Carlo · üretilmiş çözümle doğrulanmış</span></div>
  </section>

  <!-- 11 FİZİBİLİTE II · SAHA -->
  <section class="slide">
    <div class="inner">
      <div class="eyebrow reveal">04.2 · FİZİBİLİTE · SAHA VE ÖLÇEK</div>
      <h1 class="title reveal">Model kâğıtta değil, <span class="accent">İzmir'in arazisinde.</span></h1>
      <div class="grid reveal" style="grid-template-columns:1.18fr 1fr;gap:44px;margin-top:6px;flex:1;min-height:0">
        <div class="fig-wrap" style="min-height:0;display:flex;flex-direction:column">
          <img src="figures/feas_geomap.png" alt="İzmir OBM kapsama alanı ve pilot saha adayları"
               style="flex:1;min-height:0;object-fit:contain;object-position:left top">
          <div class="figcap"><span class="caption-lbl">Şekil 14:</span> SRTM 30 m yükseklik modeli,
            UTM 35K. Eğim, bakı, akış birikimi ve potansiyel ışınımdan kurulan duyarlılık indisi;
            turuncu noktalar kısıtlı çok ölçütlü sıralamanın seçtiği pilot saha adayları.</div>
        </div>
        <div style="display:flex;flex-direction:column;gap:22px;min-height:0">
          <div class="fig-wrap" style="flex:1;min-height:0">
            <img src="figures/feas_section.png" alt="Arazi ve yeraltı kesiti"
                 style="flex:1;min-height:0;object-fit:contain">
            <div class="figcap"><span class="caption-lbl">Şekil 15:</span> Batı–doğu kesiti: üstte arazi
              profili, altta aynı hat boyunca modelin ürettiği yeraltı sıcaklık alanı.</div>
          </div>
          <div class="block hi">
            <h3 style="font-size:26px">Ölçek sorusu dürüstçe</h3>
            <p style="font-size:19px">Isıl kanalın yanal erimi metre mertebesinde. Hektarlar ölçeğinde
              kapsama, miselyum ağının elektrotonik uzunluk sabitine bağlı — ve bu büyüklük
              <b>WP-2'nin birincil ölçüm hedefi</b>.</p>
          </div>
        </div>
      </div>
      <div class="statline reveal" style="margin-top:22px">
        <div><div class="stat">{land}<span class="u">km²</span></div><div class="tile-lbl">Modellenen kapsama alanı</div></div>
        <div><div class="stat">{geo_med}<span class="u">dk</span></div><div class="tile-lbl">Arazi genelinde medyan öncü süre</div></div>
        <div><div class="stat">{capex}<span class="u">TL/ha</span></div><div class="tile-lbl">100 m aralıkta kurulum</div></div>
        <div><div class="stat" style="color:var(--accent-deep)">%{npv_pos}<span class="u">olasılık</span></div><div class="tile-lbl">NBD pozitif (7 yıl)</div></div>
      </div>
    </div>
    <div class="footnotes"><span>SRTM 1 yay-saniye · Natural Earth 1:10m · {G["lead_field"]["n"]} arazi hücresinde bağlaşık PDE koşumu · UTM 35K (EPSG:32635)</span></div>
  </section>
  <!-- FEAS-END -->
"""
    return a


def main():
    copy_figs()
    html = DECK.read_text(encoding="utf-8")
    block = slides()
    if "FEAS-BEGIN" in html:
        html = re.sub(r"  <!-- FEAS-BEGIN.*?<!-- FEAS-END -->\n",
                      block, html, flags=re.S)
        print("  mevcut slaytlar guncellendi")
    else:
        anchor = "\n  <!-- 10 MARKET -->"
        if anchor not in html:
            raise SystemExit("yerlestirme noktasi bulunamadi")
        html = html.replace(anchor, "\n" + block + anchor, 1)
        print("  slaytlar eklendi")
    DECK.write_text(html, encoding="utf-8")
    print(f"  toplam slayt: {html.count('<section class=\"slide')}")


if __name__ == "__main__":
    main()
