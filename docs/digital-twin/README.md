# Sayısal İkiz (Digital Twin)

Mycellium-Aegis'in tek ekranlık, etkileşimli ve fiziksel olarak tutarlı sayısal
ikizi. Depodaki bütün teknik belgeleri tek bir çalışan modelde birleştirir.

**Açmak için:** [`index.html`](./index.html) dosyasını tarayıcıda açın.
İnternet bağlantısı gerekmez — three.js, KaTeX ve Computer Modern yazı tipleri
depoya dahildir.

```bash
# yerel sunucu (dosya:// üzerinden de çalışır)
python3 -m http.server 8000
# → http://localhost:8000/docs/digital-twin/
```

---

## Ekranda ne var

| Bölge | İçerik |
|:------|:-------|
| **Şekil 1** (sol) | PBR üç boyutlu sahne: toprak profili kesiti, miselyum ağı, gömülü donanım — ya da orman parseli görünümü |
| **Orta sütun** | Karar kuralı (LaTeX), üç koşullu füzyon kapısı, yerleşim/eşik kaydırıcıları, anlık durum, çözücü denklemleri, laboratuvar doğrulaması |
| **Sağ sütun** | Ölçüm zinciri, bileşen karar tablosu, güç bütçesi, maliyet, program, belge tutarlılığı |
| **Şekil 2–5** (alt) | Biyoelektrik iz · güç spektrumu · derinlik profili · karar değişkenleri |

Denetimler: dört senaryo düğmesi, dört kamera görünümü, durdur/sıfırla/hız.
Klavye: `Boşluk` duraklat · `R` sıfırla · `1`–`4` senaryo · `Esc` kartı kapat.
Üç boyutlu modeldeki bir bileşene (veya sağdaki tablo satırına) tıklamak, o
bileşenin seçim gerekçesini ve elenen alternatifini açar.

---

## Fizik çekirdeği

`js/sim.js` dört bağlı modeli çözer:

**1 · Geçici ısı iletimi** — 1B açık sonlu fark, 61 düğüm, Δz = 1 cm,
kararlılık koşulu `r = αΔt/Δz² ≤ 0,4`. Isıl yayınım neme bağlıdır:
`α(θ) ∈ [1,8 · 5,5] × 10⁻⁷ m²/s`. Üst sınır Dirichlet (senaryonun yüzey
sıcaklığı), alt sınır 60 cm'de sabit ortam sıcaklığı.

**2 · Toprak nemi** — taban evapotranspirasyon artı ısıl kuruma cephesi:

```
∂θ/∂t = −E₀·e^(−z/d_e)·(θ−θ_r)/θ_ref  −  c_T·(θ−θ_r)·(e^(ΔT_eff/T_s) − 1)
ΔT_eff = 0,55·ΔT(z) + 0,45·ΔT(z − 4 cm)
```

Üstel sıcaklık bağımlılığı buharlaşmanın enerji bariyerini, öncü terim ise buhar
taşınımının kuruma cephesini iletim cephesinin önüne taşımasını temsil eder.
`θ_r = 0,03` higroskopik artık sudur — ısıl olarak kopmaz.

**3 · Elektriksel direnç** — Archie yasası `R = R_ref·(θ/θ_ref)^(−n)`, `n = 2`.

**4 · Biyoelektrik sinyal** — 100 Hz'de sentezlenir: stresle 20 Hz'den 5 Hz'e
kayan taşıyıcı salınım, Poisson dağılımlı aksiyon potansiyeli spike'ları
(hızlı depolarizasyon + üstel repolarizasyon), 1/f benzeri gürültü. Genlik ve
frekans hedefleri **Deney 1'in ölçülen değerleridir** (dinlenim 20 Hz / −29,4 mV,
ateş stresi 4,98 Hz / −33,4 mV). 512 noktalı Hann pencereli radix-2 FFT ile
spektrum canlı hesaplanır.

**Füzyon** — üç koşul bir kalıcılık penceresi (öntanımlı 45 dk) içinde AND'lenir.
Yalnız γ tetiklenirse sınıflandırma `KURAKLIK` olur ve alarm üretilmez.

### Modelin sınırları

Isı iletimi ve Archie yasası literatür modelleridir. Kuruma ve biyoelektrik
modelleri **fenomenolojiktir**: gözlenen davranışı niteliksel olarak doğru
temsil ederler, ancak katsayıları WP-2 iklim odası ölçümleriyle kalibre
edilmeden saha tahmini üretmezler. Bu ikiz bir *tahminci* değil, sistemin ne
ölçtüğünü ve AND füzyonunun neden ayırt edici olduğunu gösteren sayısal olarak
tutarlı bir *tezgâhtır*.

---

## Doğrulanan değerler

Güç ve maliyet modelleri, öntanımlı çalışma noktasında donanım raporunun beyan
ettiği değerleri **birebir** yeniden üretir:

| | Rapor §5.1 / §6 | İkiz |
|:--|--:|--:|
| Yeraltı / yüzey / toplam akım | 4,49 / 0,28 / 4,77 mA | 4,49 / 0,28 / 4,77 mA |
| Batarya ömrü (ideal / muhafazakâr) | 7,5 / 6,1 hafta | 7,49 / 6,07 hafta |
| %10 görev döngüsü | 27–34 hafta | 27,3–33,7 hafta |
| Düğüm çifti / gateway | 103,8 / 260,0 USD | 103,8 / 260,0 USD |

---

## İkizin ürettiği bulgu

Prob 18 cm'de (belgedeki gibi) iken, "alev öncesi" senaryosunda ısıl cephe o
derinliğe tutuşmadan sonra varır ve **β koşulu hiç tetiklenmez**. Probu 5–8 cm'e
almak alarmı tutuşmadan ~25 dk önceye çeker ve kuraklık senaryosunda hâlâ yanlış
alarm üretmez. Ayrıntı ve tam tablo: [`../hardware/README.md §4.5`](../hardware/README.md).

Kaydırıcıyı hareket ettirip sonucu kendiniz görebilirsiniz.

---

## Dosya düzeni

```
index.html            tek ekran yerleşimi
css/twin.css          beyaz tema · Computer Modern tipografi
js/data.js            proje veri katmanı (her sayı kaynak belgeye bağlı)
js/sim.js             fizik çekirdeği (ısı · nem · direnç · biyosinyal · füzyon · güç · maliyet)
js/textures.js        yordamsal PBR doku üretimi (albedo · normal · pürüzlülük)
js/scene.js           three.js sahnesi — PMREM ortam aydınlatması, PCF gölgeler, ACES
js/charts.js          bağımlılıksız 2B canvas çizim katmanı
js/app.js             tek ekran denetleyicisi
fonts/                Computer Modern (CMU Serif · CMU Sans)
vendor/three.min.js   three.js r160
vendor/katex/         KaTeX 0.16.11 (yalnızca woff2)
```

Hiçbir yapı adımı, paket yöneticisi veya ağ isteği yoktur.

## Tarayıcı gereksinimi

WebGL 2 destekleyen güncel bir tarayıcı. Sahne yordamsal doku üretimi nedeniyle
ilk açılışta ~1 saniye hazırlanır. Gölgeler ve ortam aydınlatması açıktır;
yazıcı çıktısında (`Ctrl+P`) araç çubuğu gizlenir.
