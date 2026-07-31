# Sayısal Fizibilite Analizi

Bu klasör, Mycellium-Aegis'in yapılabilirliğini niteliksel gerekçelerle değil
**çözülmüş bir fiziksel modelin sayısal sonuçlarıyla** değerlendiren raporu ve
onu üreten bütün kodu içerir. Rapordaki hiçbir sayı elle yazılmamıştır;
hepsi `summary.json` üzerinden LaTeX makrolarına akar, şekiller de aynı veri
dosyalarından pgfplots ile çizilir.

| Dosya | Ne |
|:--|:--|
| `Mycellium-Aegis_Fizibilite_Analizi.tex` / `.pdf` | Raporun kendisi |
| `numeric/aegis_physics.py` | Kurucu bağıntılar ve dört PDE çözücüsü |
| `numeric/run_all.py` | Bütün sayısal çalışma → `data/*.dat`, `summary.json` |
| `numeric/geo.py` | Coğrafi katman → `data/geo_*.dat`, `summary_geo.json` |
| `numeric/make_tikz.py` | pgfplots şekil kaynakları → `figures/*.tikz` |
| `numeric/make_numbers.py` | `summary*.json` → `numbers.tex` (LaTeX makroları) |
| `numeric/build_figures.py` | Şekilleri bağımsız derler → `figures/*.pdf`, `*.svg` |
| `numeric/make_slides.py` | Sunuma iki fizibilite slaydı yerleştirir |
| `numeric/build.py` | Yukarıdakilerin tamamını sırayla koşturur |

## Tam yeniden üretim

```bash
cd docs/feasibility
python numeric/build.py            # ~50 dk (Monte Carlo + Sobol + coğrafya)
python numeric/build.py --skip-run # veri hazırsa yalnızca şekil + PDF + slayt
```

Gereksinimler: numpy, scipy, pandas, geopandas, rasterio, pyogrio, requests
ve MiKTeX (pdflatex + dvisvgm). Coğrafi katman ilk koşumda SRTM ve Natural
Earth verisini indirir ve `numeric/.cache/` altında tutar (sürümlenmez,
≈40 MB). Bütün rastgelelik sabit tohumludur.

## Modelin özeti

Isı ve nem taşınımı, çapraz terimlerle bağlanmış tek bir sistem olarak
çözülür (Philip & de Vries). Uzaysal yönbağımlılık ikinci mertebe bir
iletkenlik tensörüyle, ölçülen elektriksel büyüklük ise eksenel simetrik bir
potansiyel probleminin Fréchet türeviyle (Geselowitz karşılıklılığı) tanımlanır.
Ayrıklaştırma üretilmiş çözümlerle doğrulanmıştır; ilgi büyüklüğünün ızgara ve
zaman adımı yakınsaması ile düzenlileştirme parametrelerine duyarsızlığı ayrıca
ölçülmüştür.

Coğrafi katman modeli gerçek araziye oturtur: SRTM 30 m yükseklik modelinden
türetilen eğim, akış birikimi ve potansiyel ışınım, bağlaşık PDE'nin girdileri
hâline gelir ve model binlerce arazi hücresinde yığın olarak koşturulur. Arazi
eğimi, tensörün yatak normalini döndüren açının ta kendisidir — coğrafya
doğrudan tensör matematiğine bağlanır.

## Rapordan çıkan üç tasarım kararı

1. **Füzyon kuralının ikinci koşulu mutlak değer üzerinden yazılmalıdır.**
   Isınma ve buhar yoğuşması, kuruma cephesi prob derinliğine varmadan önce
   direnci düşürür; yalnızca artışı arayan kural bu erken imzayı göremez.
   Gömülü yazılımda tek satırlık bir değişikliktir, donanım maliyeti yoktur.
2. **Sıcaklık/direnç probu ile elektrot açıklığı birlikte 5–8 cm bandına
   alınmalıdır**; biyoelektrot miselyumun yaşadığı derinlikte kalır. Duyarlılık
   çekirdeği, elektrot açıklığının araştırma derinliğini belirlediğini gösterir.
3. **Görev döngüsü olay-tetikli olmalıdır.** Panel gücü kısıtlayıcı değildir;
   kısıtlayıcı olan kanopi altında panele ulaşan ışık payıdır ve montaj
   yönergesi bunun için bir kabul eşiği içermelidir.

Açık kalan tek fizibilite kalemi mekânsal kapsamadır: alev öncesi tespit
yarıçapı, miselyum ağının elektrotonik uzunluk sabitine bağlıdır ve bu büyüklük
henüz ölçülmemiştir. Rapor bunu bir belirsizlik olarak değil, WP-2'de ek donanım
gerektirmeden yapılabilecek tanımlı bir ölçüm olarak bırakır.

## Sunumdaki karşılığı

`numeric/make_slides.py`, sunuma `FEAS-BEGIN` / `FEAS-END` işaretleri arasına
iki slayt yerleştirir (04.1 fiziksel doğrulama, 04.2 saha ve ölçek). Slayttaki
rakamlar da `summary.json`'dan gelir; betik yeniden çalıştırılabilir.
