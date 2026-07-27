# Donanım — Rev B (Temmuz 2026)

**Kaynak belge:** [`MycelliumAegis_Donanim_Raporu.pdf`](./MycelliumAegis_Donanim_Raporu.pdf) · 7 sayfa · Temmuz 2026

Bu klasör, Mycellium-Aegis saha donanımının teknik raporunu ve raporun bağımsız
bir doğrulamasını içerir. Raporun canlı, etkileşimli karşılığı için
[`docs/digital-twin/`](../digital-twin/) klasörüne bakınız.

---

## 1. Raporun özeti

Sistem dört aşamalı bir veri yolu üzerine kuruludur:

| # | Katman | Bileşenler | Bağlantı |
|:--|:-------|:-----------|:---------|
| 1 | Toprak altı (18 cm) | Biyomimetik elektrot → OPA333 → ADS1115 → STM32L4 | analog → I²C |
| 2 | Yüzey / ağaç tepesi | 5 W güneş · BQ24650 MPPT · LiFePO₄ 32700 · TPS63020 · EBYTE E220 | RS485 (MAX3485 ×2) |
| 3 | Merkez kule | RAK2287 (SX1302) · Raspberry Pi 4 · SIM7600G-H | LoRa 868 MHz |
| 4 | Bulut | Karar ve alarm panosu | 4G / LTE |

Rapor üç şekil içerir: genel sistem mimarisi (Şekil 1), yeraltı algılama düğümü
blok diyagramı (Şekil 2) ve enerji yönetim sistemi blok diyagramı (Şekil 3).
Üçü de sayısal ikizde yeniden çizilmiş ve etkileşimli hâle getirilmiştir.

### Bileşen kararları

Raporun en değerli kısmı, her bileşen için **elenen alternatifin ve gerekçenin**
kayda geçirilmiş olmasıdır:

| Alt sistem | Seçilen | Elenen | Ana gerekçe |
|:-----------|:--------|:-------|:------------|
| Elektrot | Biyomimetik katmanlı (316L + grafit/PPy + aljinat) | İğne / Ag-AgCl disk | Düşük temas empedansı, korozyon direnci, **fikri mülkiyet unsuru** |
| Ön kuvvetlendirici | OPA333 | OPA2333 | Zero-drift; yüksek empedanslı biyolojik kaynağı yüklemez |
| ADC | ADS1115 | ADS131M0x | Mevcut kanal ihtiyacı için yeterli + maliyet |
| MCU | STM32L4 (L412/L452) | ESP32-S3, STM32U5 | Kullanılmayan radyo taşımıyor; Stop2'de ~1,3 µA |
| Ortam sensörü | BME280 | BME688 | Aktif üretimde, geniş tedarik |
| RS485 | MAX3485 ×2 | THVD1450/2450 | Kanıtlanmış, düşük maliyetli |
| LoRa | EBYTE E220-900T22D (LLCC68) | AI-Thinker RA-09H | Türkiye'de yerel stok, düşük RX akımı |
| Panel | 5 V / 5 W monokristal | Polikristal | Gölgede daha yüksek verim |
| MPPT | TI BQ24650 | Consonance CN3801 | Tedarik zinciri, dokümantasyon |
| Batarya | LiFePO₄ 32700 6000 mAh | Standart Li-ion | **Termal kararlılık** — yangın ortamında kritik |
| Regülatör | TPS63020 buck-boost | — | 3,65 V–2,0 V boyunca sabit 3,3 V |
| Gateway | RAK2287 + RPi 4 | RAK5146 + CM4 | Türkiye'de tedarik, topluluk desteği |

---

## 2. Bağımsız doğrulama

Raporun beyan ettiği sayılar, sayısal ikizde bileşen tablosundan yeniden
hesaplanmıştır. **Tüm kalemler eşleşmektedir:**

### Güç bütçesi (%50 görev döngüsü)

| Büyüklük | Rapor §5.1 | Yeniden hesap | Sapma |
|:---------|-----------:|--------------:|------:|
| Yeraltı düğümü ortalama akımı | 4,49 mA | 4,485 mA | −0,005 |
| Yüzey düğümü ortalama akımı | 0,28 mA | 0,282 mA | +0,002 |
| Toplam sistem ortalama akımı | 4,77 mA | 4,767 mA | −0,003 |
| Batarya ömrü — ideal | 7,5 hafta | 7,49 hafta | −0,01 |
| Batarya ömrü — muhafazakâr | 6,1 hafta | 6,07 hafta | −0,03 |
| %10 görev döngüsü bandı | 27–34 hafta | 27,3–33,7 hafta | ✓ |

Kullanılan model:

```
Ī = Σₖ [ D·Iₖ,aktif + (1−D)·Iₖ,uyku ]
ömür_ideal        = C / Ī
ömür_muhafazakâr  = C · DoD · η / Ī      (DoD = 0,90 · η = 0,90)
```

Yeraltı düğümünde **bir**, yüzey düğümünde **bir** MAX3485 bulunduğu varsayımı,
raporun 4,49 mA değerini tam olarak üretir (ikisi birden yeraltında olsaydı
4,64 mA çıkardı).

### Maliyet (§6)

| Büyüklük | Rapor | Yeniden toplam |
|:---------|------:|---------------:|
| Düğüm çifti | 103,8 USD ≈ 4.910 TL | 103,8 USD ≈ 4.910 TL |
| Gateway | 260,0 USD ≈ 12.300 TL | 260,0 USD ≈ 12.298 TL |

---

## 3. Belgede verilmeyen, ikizde varsayılan değerler

| Büyüklük | Durum | İkizdeki varsayım |
|:---------|:------|:------------------|
| LoRa görev döngüsü | Rapor vermiyor | TX %0,05 · RX %1,60 — yüzey düğümünün 0,28 mA'ini tam üretir; **başka kombinasyonlar da üretebilir**, bench ölçümü gerekir |
| γ eşiği (kuruma hızı) | Hiçbir belgede sayısal değer yok | 0,002 dk⁻¹ — WP-2 iklim odasının birincil çıktısı budur |
| BQ24650 sızıntı akımı | Raporda "tahmini" işaretli | ~2 µA — INA226 ile ölçülmeli |
| Hacim iskontosu | Rapor "önemli ölçüde düşer" diyor | 100+ adette %78, 1000+ adette %62 |

---

## 4. Tespit edilen tutarsızlıklar ve öneriler

### 4.1 · Rev A ile Rev B karıştırılmamalı

Depoda iki donanım kuşağı var ve README hâlâ Rev A'yı anlatıyor:

| | Rev A — laboratuvar (Mayıs 2026) | Rev B — saha (Temmuz 2026) |
|:--|:--|:--|
| MCU | ESP32 (Xtensa LX6) | STM32L4 (L412/L452) |
| Ön kuvvetlendirici | MCP6022 | OPA333 (zero-drift) |
| ADC | ADS1115 | ADS1115 |
| Haberleşme | USB / UART 115200 | RS485 + LoRa 868 MHz |
| Güç | Dizüstü USB | 5 W güneş + MPPT + LiFePO₄ |

Bu bir çelişki değil, bir **tasarım revizyonudur** — ancak kök `README.md`'nin
donanım tablosu Rev B ile güncellenmeli ve Rev A açıkça "laboratuvar tezgâhı"
olarak etiketlenmelidir.

### 4.2 · "24-bit ADC" ifadesi hatalıdır

Kök README, WP-2 ve haberleşme bölümlerinde "24-bit ADC" diyor; kullanılan parça
**16-bit ADS1115**'tir. Ya ifade düzeltilmeli, ya da 24-bit'e geçilecekse
ADS1220 / ADS131M0x seçilip güç bütçesi yeniden hesaplanmalıdır.

### 4.3 · Deney 1'in 20 Hz bulgusu takma-ad riski taşır

Deney 1'de örnekleme hızı 45 Hz (Nyquist 22,5 Hz) iken baskın bileşen 20 Hz'de
bulunmuştur — Nyquist'in %89'u. Anti-aliasing süzgeci yoktur. Deney 2'nin
100 Hz'e çıkması doğru hamledir; **20 Hz gözleminin 100 Hz'de tekrarlanması**
önerilir, aksi hâlde değerlendirme jürisi bu itirazı yapacaktır.

### 4.4 · Enerji marjı: adaptif görev döngüsü önerisi

Rapor açıkça belirtiyor: %10 görev döngüsünde 27–34 hafta, %50'de 6,1–7,5 hafta.
%50'ye geçiş tespit gecikmesini kısaltırken marjı daraltmıştır.

**Öneri:** olay-tetikli adaptif görev döngüsü — sakinken %10, anomali şüphesinde
%50 — her iki hedefi aynı anda karşılar ve WP-3 kapsamına yazılabilir. Raporun
kendi önerdiği iki donanım seçeneği (ikinci LiFePO₄ hücresi, 10 W panel) bu
yazılım çözümüne ek olarak kalır.

### 4.5 · Tespit derinliği ile hayatta kalma derinliği ayrıştırılmalı

Bu, sayısal ikizin ısı iletim çözücüsünden çıkan en önemli bulgudur.

Tüm belgeler sensörü 15–20 cm'e koyar. Ancak 1B geçici ısı iletimi çözüldüğünde,
ısıl cephe o derinliğe **yüzeydeki tutuşmadan sonra** varır. "Alev öncesi — için
için yanma" senaryosunda (yüzey 1,5 saatte 300 °C'ye çıkar), prob derinliğine
göre alarm zamanı:

| Prob derinliği | β ilk geçişi | Alarm | Tutuşma | Öncü süre |
|---------------:|-------------:|------:|--------:|----------:|
| 5 cm | 03:22 | 04:06 | 04:31 | **+25 dk** |
| 8 cm | 03:53 | 04:07 | 04:31 | **+24 dk** |
| 10 cm | 04:21 | 04:21 | 04:31 | +10 dk |
| 12 cm | 04:56 | 04:56 | 04:31 | −25 dk |
| 15 cm | 07:11 | 07:11 | 04:31 | −160 dk |
| **18 cm (belgedeki)** | **hiç** | **hiç** | 04:31 | **alarm yok** |
| 20 cm | hiç | hiç | 04:31 | alarm yok |

15–20 cm bandı miselyumun **hayatta kalma** koşuludur; ısının **tespit** koşulu
değildir. İkisi ayrıştırılmalıdır:

> **Öneri:** Biyoelektrot 18 cm'de kalsın (miselyum orada yaşar), sıcaklık ve
> direnç probu **aynı kablo üzerinde 5–8 cm'e** alınsın. ADS1115'in dört
> kanalından ikisi zaten boştur; ek maliyet bir termistör ve bir elektrot
> çiftidir (< 3 USD). Kuraklık senaryosunda bu yapılandırma hâlâ yanlış alarm
> üretmemektedir.

### 4.6 · AND kuralı eşzamanlılık gerektirmemelidir

Isıl cephe ile kuruma cephesi aynı derinliğe farklı zamanlarda varır. Koşullar
anlık olarak değil, kısa bir **kalıcılık penceresi** içinde birleştirilmelidir
(ikizde 45 dakika). Bu, ayrık cephe varışlarını tek bir olayda toplarken
kuraklık senaryosunun yanlış alarm üretmesini engeller ve firmware'de basit bir
zaman damgasıyla uygulanır.

---

## 5. Kapatılması önerilen kalemler

- [ ] Kök `README.md` donanım tablosu Rev B ile güncellensin
- [ ] "24-bit ADC" ifadesi düzeltilsin veya parça değiştirilsin
- [ ] 20 Hz bulgusu 100 Hz örneklemeyle, anti-aliasing süzgeci takılı tekrarlansın
- [ ] BQ24650 ve LoRa gerçek akımları INA219/INA226 ile ölçülsün
- [ ] Adaptif görev döngüsü WP-3 kapsamına yazılsın
- [ ] T/R probu 5–8 cm'e alınsın, biyoelektrot 18 cm'de kalsın
- [ ] Füzyon kuralına kalıcılık penceresi eklensin
- [ ] Yıldız dizilimli yön tespiti ürün vaadinde kalacaksa ADS131M0x geçişi fiyatlansın
