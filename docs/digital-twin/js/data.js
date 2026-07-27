/* =============================================================================
   MYCELLIUM-AEGIS · DİJİTAL İKİZ
   data.js — Proje veri katmanı
   -----------------------------------------------------------------------------
   Buradaki her sayı, depodaki bir kaynak belgeden alınmıştır. `src` alanı
   kaynağı gösterir:
     HW   → docs/hardware/MycelliumAegis_Donanim_Raporu.pdf (Temmuz 2026)
     EXP  → docs/experiments/2260401_EK_Mantar_Deney_Raporu.pdf (Mayıs 2026)
     BP   → docs/business-plan/  (İş Planı / Maliyet Formu)
     RES  → docs/research/       (Bilimsel değerlendirme + yol haritası)
     RM   → README.md            (depo ana özeti)
   `assume` alanı taşıyan kayıtlar modelleme varsayımıdır, belgede yoktur.
   ============================================================================= */
(function (global) {
  'use strict';

  const D = {};

  /* ---------------------------------------------------------------- kimlik -- */
  D.project = {
    name: 'Mycellium-Aegis',
    tagline: 'Orman yangınını ilk alevden önce duyan canlı biyosensör ağı',
    taglineEn: 'Hearing the forest before it burns',
    program: 'TÜBİTAK 1812 BiGG · Yeşil Büyüme Çağrısı',
    institution: 'İzmir Yüksek Teknoloji Enstitüsü (İYTE)',
    trl: { now: 3.5, target: 7, label: 'TRL 3→4 (lab doğrulaması tamam) · hedef TRL 6–7' },
    hwRevision: 'Rev B · Temmuz 2026 (saha donanımı)',
    labRevision: 'Rev A · Mayıs 2026 (laboratuvar tezgâhı)',
    depth: { min: 0.15, max: 0.20, nominal: 0.18 },
    src: 'RM/HW'
  };

  D.team = [
    { name: 'Mehmet Çetin',       role: 'Kurucu · CEO', focus: 'Sistem mimarisi ve iş geliştirme' },
    { name: 'Muhammet Yağcıoğlu', role: 'Kurucu · CTO', focus: 'Yazılım ve YZ — LSTM / sensör füzyonu' },
    { name: 'Ömer Ünal',          role: 'Kurucu · COO', focus: 'Gömülü donanım ve IoT sistem mühendisliği' },
    { name: 'Mahmut Can Göçlü',   role: 'Kurucu · CRO', focus: 'Biyomalzeme ve elektrot Ar-Ge' }
  ];

  /* -------------------------------------------------- toprak ısı katmanları -- */
  /* RES/RM — yüzey alevi 900 °C iken derinliğe göre ulaşan sıcaklık            */
  D.soilLayers = [
    { z0: 0.00, z1: 0.02, name: 'O horizonu — ölü örtü',    tmax: '300–850 °C', effect: 'Neredeyse tam yıkım; hücreler kömürleşir',            hex: 0x3a2f24 },
    { z0: 0.02, z1: 0.05, name: 'A horizonu — humus',       tmax: '80–150 °C',  effect: 'Kısmi hasar; ısıya dayanıklı türler ve sporlar kalır', hex: 0x4a3a28 },
    { z0: 0.05, z1: 0.10, name: 'A/B geçiş',                tmax: '50–80 °C',   effect: 'Mezofillerin çoğu ölür; pirofilik mantarlar aktive olur', hex: 0x5b4630 },
    { z0: 0.10, z1: 0.15, name: 'B horizonu — üst',         tmax: '35–60 °C',   effect: 'Geçiş bölgesi',                                        hex: 0x6b5335 },
    { z0: 0.15, z1: 0.20, name: 'GÜVENLİ BÖLGE · sensör',   tmax: '25–50 °C',   effect: 'Miselyum yaşar ve sinyal üretmeye devam eder',          hex: 0x7a5f3c, safe: true },
    { z0: 0.20, z1: 0.40, name: 'B horizonu — alt',         tmax: '20–30 °C',   effect: 'Termal olarak neredeyse kararlı',                       hex: 0x6d5636 },
    { z0: 0.40, z1: 0.80, name: 'C horizonu — ana kaya üstü', tmax: '≈ ortam',  effect: 'Yıllık ortalama sıcaklık bandı',                        hex: 0x5c4b32 }
  ];
  D.soilLayers.src = 'RES/RM';

  /* ------------------------------------------------- donanım karar tablosu -- */
  /* HW §3 — seçilen bileşen / değerlendirilen alternatif / gerekçe             */
  D.components = [
    {
      id: 'electrode', block: 'sense', subsystem: 'Elektrot',
      selected: 'Biyomimetik katmanlı elektrot',
      detail: '316L çekirdek + grafit/PPy + aljinat-gliserol-nanokarbon',
      alt: 'Standart iğne veya Ag/AgCl disk elektrot',
      why: 'Düşük temas empedansı, korozyon direnci ve miselyum kolonizasyonunu teşvik eden yüzey; sistemin fikri mülkiyet unsuru.',
      ip: true, usd: 18.0, qty: 1, unit: 'set (4 adet)'
    },
    {
      id: 'opa333', block: 'sense', subsystem: 'Ön kuvvetlendirici (buffer)',
      selected: 'OPA333', detail: 'Zero-drift, V_OS ≈ 10 µV, I_Q ≈ 17 µA',
      alt: 'OPA2333 (çok kanallı genişleme için)',
      why: 'Sıfır kaymalı (zero-drift), çok düşük ofset voltajı; yüksek empedanslı biyolojik kaynağı yüklemeden izole eder.',
      usd: 1.8, qty: 1
    },
    {
      id: 'ads1115', block: 'sense', subsystem: 'ADC',
      selected: 'ADS1115', detail: '16-bit Σ-Δ, 4 kanal, PGA, I²C 0x48',
      alt: 'ADS131M0x (eş zamanlı çok kanallı)',
      why: 'Mevcut tek/çift kanal ölçüm ihtiyacı için yeterli çözünürlük ve maliyet avantajı; çok kanallı yön tespiti eklenirse revize edilmesi gerekir.',
      risk: 'Yıldız dizilim (yön tespiti) devreye girerse ADS131M0x’e geçiş gerekir.',
      usd: 3.5, qty: 1
    },
    {
      id: 'stm32l4', block: 'sense', subsystem: 'Mikrodenetleyici',
      selected: 'STM32L4 (L412 / L452)', detail: 'Cortex-M4F 80 MHz · Stop2 ≈ 1.3 µA',
      alt: 'ESP32-S3, STM32U5',
      why: 'Kullanılmayan bir radyo donanımı taşımıyor (haberleşme RS485+LoRa üzerinden); olgun ekosistem, düşük maliyet; mevcut güç bütçesini rahatça karşılıyor.',
      note: 'ESP32-S3 ilk turda değerlendirildi: yerinde ML çıkarımı için vektör komut seti var, ancak dahili WiFi/BT radyosu bu mimaride hiç kullanılmıyor. STM32U5 aktif modda belirgin daha verimli (≈16 µA/MHz vs ≈100 µA/MHz) ama güç bütçesi zaten karşılandığı için bu aşamada L4 seçildi.',
      usd: 3.0, qty: 1
    },
    {
      id: 'bme280', block: 'sense', subsystem: 'Ortam sensörü',
      selected: 'BME280', detail: 'Sıcaklık / bağıl nem / basınç · I²C',
      alt: 'BME688 (gaz/VOC sensörlü)',
      why: 'Halen aktif üretimde, geniş tedarik ağı; mevcut ihtiyaç (sıcaklık/nem/basınç) için yeterli.',
      usd: 3.5, qty: 1
    },
    {
      id: 'max3485', block: 'link', subsystem: 'RS485 arayüzü',
      selected: 'MAX3485 ×2', detail: 'Yeraltı ↔ yüzey kablolu diferansiyel hat, 3.3 V',
      alt: 'THVD1450 / THVD2450',
      why: 'Kanıtlanmış, düşük maliyetli, endüstri standardı diferansiyel haberleşme.',
      usd: 1.2, qty: 2
    },
    {
      id: 'lora', block: 'link', subsystem: 'Kablosuz haberleşme (LoRa)',
      selected: 'EBYTE E220-900T22D', detail: 'LLCC68 · 868 MHz · 22 dBm',
      alt: 'AI-Thinker RA-09H',
      why: 'Türkiye’de yerel stok mevcut; LLCC68 çekirdeği daha düşük alış (RX) akımı sunuyor; daha iyi dokümante edilmiş.',
      usd: 4.5, qty: 1
    },
    {
      id: 'panel', block: 'power', subsystem: 'Güneş paneli',
      selected: '5 V / 5 W monokristal', detail: 'Yüzey düğümü üstünde',
      alt: 'Polikristal panel',
      why: 'Gölgeli / düşük ışık koşullarında polikristale göre daha yüksek verim.',
      usd: 10.0, qty: 1
    },
    {
      id: 'bq24650', block: 'power', subsystem: 'MPPT şarj kontrolcüsü',
      selected: 'TI BQ24650', detail: 'MPPT girişli senkron anahtarlamalı şarj',
      alt: 'Consonance CN3801',
      why: 'Daha geniş ve istikrarlı global tedarik zinciri, daha iyi dokümante edilmiş MPPT algoritması.',
      usd: 3.2, qty: 1
    },
    {
      id: 'lifepo4', block: 'power', subsystem: 'Batarya',
      selected: 'LiFePO₄ 32700, 6000 mAh', detail: 'Nominal 3.2 V',
      alt: 'Standart Li-ion hücre',
      why: 'Termal kararlılık — yangın riski taşıyan bir ortamda kritik bir güvenlik faktörü; yurt içi tedarik mevcut.',
      usd: 11.0, qty: 1
    },
    {
      id: 's8261', block: 'power', subsystem: 'Batarya koruma IC',
      selected: 'S-8261 serisi', detail: 'LiFePO₄ eşiklerine göre yapılandırılmış',
      alt: 'Korumasız / genel amaçlı Li-ion IC',
      why: 'Aşırı şarj/deşarj koruması sağlar; LiFePO₄’ün farklı gerilim eşiklerine göre yapılandırılmış eşik gerekli.',
      usd: 0.4, qty: 1
    },
    {
      id: 'tps63020', block: 'power', subsystem: 'Voltaj regülatörü',
      selected: 'TPS63020', detail: 'Buck-boost · 3.65 V–2.0 V girişte sabit 3.3 V',
      alt: '—',
      why: 'Pilin deşarj eğrisi boyunca (3.65 V–2.0 V) sabit 3.3 V çıkışı garanti eder.',
      usd: 2.5, qty: 1
    },
    {
      id: 'rak2287', block: 'gw', subsystem: 'Gateway konsantratörü',
      selected: 'RAK2287 (SX1302)', detail: '8 kanallı LoRaWAN konsantratör',
      alt: 'RAK5146 (SX1303)',
      why: 'Türkiye’de tedarik mevcut (rfmarket.com.tr); kanıtlanmış kullanım geçmişi.',
      usd: 90.0, qty: 1, gateway: true
    },
    {
      id: 'rpi4', block: 'gw', subsystem: 'Gateway ana bilgisayarı',
      selected: 'Raspberry Pi 4 Model B (4 GB)', detail: 'Paket iletici + yerel tampon',
      alt: 'Compute Module 4 + taşıyıcı kart',
      why: 'Geniş topluluk desteği, hızlı prototipleme, kolay tedarik.',
      usd: 60.0, qty: 1, gateway: true
    }
  ];
  D.components.src = 'HW §3';

  /* ------------------------------------------------------- güç bütçesi ----- */
  /* HW §5 — datasheet düzeyinde akım tüketimleri                              */
  D.powerRows = [
    { part: 'STM32L4 (Run, 80 MHz)', active: 8.5,   sleep: 0.0013, node: 'under', note: 'ST datasheet, muhafazakâr varsayım' },
    { part: 'ADS1115',               active: 0.15,  sleep: 0.0005, node: 'under', note: 'TI datasheet' },
    { part: 'OPA333',                active: 0.017, sleep: 0,      node: 'under', note: 'TI datasheet, aktif pencerede açık' },
    { part: 'BME280',                active: 0,     sleep: 0,      node: 'under', note: 'Periyodik tekli ölçüm — ihmal edilebilir' },
    { part: 'MAX3485 (yeraltı)',     active: 0.30,  sleep: 0.001,  node: 'under', note: 'Maxim datasheet' },
    { part: 'MAX3485 (yüzey)',       active: 0.30,  sleep: 0.001,  node: 'surf',  note: 'Maxim datasheet' },
    { part: 'EBYTE E220-900T22D',    active: null,  sleep: 0.005,  node: 'surf',  note: 'TX 110 mA / RX 4.2 mA / uyku 5 µA', radio: true },
    { part: 'Hücre koruma IC',       active: null,  sleep: 0.002,  node: 'surf',  note: 'S-8261 serisi tipik değer', always: true },
    { part: 'BQ24650 (güneşsiz sızıntı)', active: null, sleep: 0.002, node: 'surf', note: 'Tahmini — bench ölçümüyle doğrulanmalı', always: true, estimate: true }
  ];
  D.powerRows.src = 'HW §5';

  /* HW §5.1 — raporun beyan ettiği sonuçlar; dijital ikiz bunları yeniden üretir */
  D.powerReference = {
    duty50: { under: 4.49, surf: 0.28, total: 4.77, weeksIdeal: 7.5, weeksCons: 6.1 },
    duty10: { weeksMin: 27, weeksMax: 34 },
    battery: { mAh: 6000, volt: 3.2, chem: 'LiFePO₄ 32700' },
    dod: 0.90, convEff: 0.90,
    src: 'HW §5.1'
  };

  /* Raporda LoRa görev döngüsü sayısal olarak verilmemiştir. Aşağıdaki iki değer,
     raporun yüzey düğümü için beyan ettiği 0.28 mA ortalamayı tam olarak üreten
     ters-çözüm sonucudur ve MODELLEME VARSAYIMIDIR.                            */
  D.loraDuty = { tx: 0.0005, rx: 0.0160, assume: true,
    note: 'Rapor LoRa görev döngüsünü vermiyor; bu değerler yüzey düğümünün beyan edilen 0.28 mA ortalamasından geri hesaplanmıştır.' };

  /* --------------------------------------------------------- maliyet ------- */
  /* HW §6 — tekli/küçük ölçekli tedarik fiyatları                             */
  D.bomNode = [
    { part: 'Biyomimetik elektrot seti (malzeme, 4 adet)', qty: 1, usd: 18.0, unit: 'set' },
    { part: 'OPA333',                                      qty: 1, usd: 1.8 },
    { part: 'ADS1115 (bare IC)',                           qty: 1, usd: 3.5 },
    { part: 'STM32L412/L452 (bare MCU)',                   qty: 1, usd: 3.0 },
    { part: 'BME280',                                      qty: 1, usd: 3.5 },
    { part: 'MAX3485',                                     qty: 2, usd: 1.2 },
    { part: 'EBYTE E220-900T22D',                          qty: 1, usd: 4.5 },
    { part: 'Güneş paneli 5V/5W',                          qty: 1, usd: 10.0 },
    { part: 'BQ24650',                                     qty: 1, usd: 3.2 },
    { part: 'LiFePO₄ 32700, 6000 mAh',                     qty: 1, usd: 11.0 },
    { part: 'Hücre koruma IC (S-8261 serisi)',             qty: 1, usd: 0.4 },
    { part: 'TPS63020',                                    qty: 1, usd: 2.5 },
    { part: 'PCB (yeraltı + yüzey, 2 kart)',               qty: 1, usd: 10.0, unit: 'set' },
    { part: 'Su geçirmez muhafaza (2 adet)',               qty: 1, usd: 18.0, unit: 'set' },
    { part: 'Kablo, konnektör, montaj malzemesi',          qty: 1, usd: 12.0, unit: 'set' }
  ];
  D.bomGateway = [
    { part: 'RAK2287 (SX1302 konsantratör)',    qty: 1, usd: 90.0 },
    { part: 'Raspberry Pi 4 Model B (4 GB)',    qty: 1, usd: 60.0 },
    { part: 'SIM7600G-H (4G/LTE modül)',        qty: 1, usd: 30.0 },
    { part: 'Muhafaza, anten, montaj malzemesi',qty: 1, usd: 50.0, unit: 'set' },
    { part: 'SD kart, kablo, güç kaynağı',      qty: 1, usd: 30.0, unit: 'set' }
  ];
  D.costMeta = {
    fxDefault: 47.3, fxDate: 'Temmuz 2026',
    nodeTotalUsd: 103.8, gatewayTotalUsd: 260.0,
    excludes: 'İşçilik, PCB üretim (NRE), sertifikasyon ve montaj maliyetleri dahil değildir.',
    src: 'HW §6'
  };

  /* --------------------------------------------------------- deneyler ------ */
  /* EXP — İYTE, Mayıs 2026                                                    */
  D.experiments = {
    e1: {
      title: 'Deney 1 — Tek Pleurotus ostreatus',
      subject: 'Tek mantar dokusu (istiridye mantarı)',
      mcu: 'ESP32 (Xtensa LX6, 240 MHz)', adc: 'ADS1115 · AIN0–AIN1 diferansiyel',
      amp: 'MCP6022', gain: 'GAIN_SIXTEEN (±0.256 V)', lsb: '7.8125 µV/bit',
      fs: 45, channels: 1, fir: 'Yok (ham sinyal)', offset: 'Yok',
      rest:   { vmin: -29.4, vmax: 0.1, vmean: -2.9,  fdom: 20.0, n: 1048 },
      stress: { vmin: -33.4, vmax: null, vmean: -2.94, fdom: 4.98, n: 1085 },
      goal: 'Biyoelektrik sinyalin varlığını kanıtlama (TRL 2–3)'
    },
    e2: {
      title: 'Deney 2 — Terraryumda miselyum ağı',
      subject: 'Toprak / kaya / organik materyal içinde aktif miselyum ağı',
      mcu: 'ESP32', adc: 'ADS1115 · 2 diferansiyel kanal (A: AIN0–1, B: AIN2–3)',
      amp: 'MCP6022', gain: 'GAIN_TWOTHIRDS (±6.144 V)', lsb: '187.5 µV/bit',
      fs: 100, channels: 2,
      fir: '5-tap doğrusal fazlı FIR [0.1, 0.2, 0.4, 0.2, 0.1] · Σh = 1.0',
      offset: 'Otomatik (50 örnek başlangıç ortalaması)',
      goal: 'Çok noktalı ağ ölçümü, sinyal iyileştirme (TRL 3–4)',
      gainWhy: 'GAIN_SIXTEEN toprak-elektrot arayüz direnci ve dağıtılmış empedans nedeniyle sık sık doyuma giriyordu; ±6.144 V ile aralık 24× genişletilerek DC ofset ve dalgalanmanın tamamı temsil edilebilir hale getirildi. Çözünürlük kaybı (7.8 → 187.5 µV/bit) mV mertebesindeki sinyal için kabul edilebilir.'
    },
    src: 'EXP'
  };

  /* Deney 1 FFT gözlemi — dijital ikizin biyosinyal modeli bu iki noktayı hedefler */
  D.bioTargets = {
    fRest: 20.0, fStress: 4.98,
    vminRest: -29.4, vminStress: -33.4,
    vmeanRest: -2.9, vmeanStress: -2.94,
    src: 'EXP §3.5'
  };

  /* ------------------------------------------------------- füzyon eşikleri -- */
  D.fusion = {
    beta:  { value: 1.5,   unit: '°C / 10 dk', label: 'β — ısı akısı hızı eşiği',
             natural: '20 cm’de doğal hız ≈ 0.05 °C/sa', src: 'RM' },
    gamma: { value: 0.002, unit: 'dk⁻¹', label: 'γ — kuruma hızı eşiği d(ln R)/dt',
             assume: true, note: 'Sayısal değer belgede verilmemiştir; WP-2 iklim odası kalibrasyonunda sabitlenecek (98 % güven).' },
    spike: { value: 3, unit: 'σ', label: 'f_spike > taban + 3σ', src: 'RM' },
    rule: 'Alarm = (dT/dt > β) AND (d(ln R)/dt > γ) AND (spike_active = TRUE)',
    fpTarget: 0.01
  };

  /* ------------------------------------------------------ yol haritası ----- */
  D.roadmap = [
    { id: 'WP-1', title: 'Biyokompozit ve kültür',      m0: 1,  m1: 3,
      focus: 'Pirinç kabuğu/silika matris; Pyronema domesticum inokülasyonu; biyobozunur muhafaza kalıplama',
      out: '100 adet entegre elektrotlu muhafaza', trl: '3→4' },
    { id: 'WP-2', title: 'İklim odası ve eşikler',      m0: 4,  m1: 7,
      focus: '15–20 cm toprak simülasyonu; ışınımsal ısı şoku; dT/dt ve dR/dt kaydı',
      out: 'β, γ katsayıları %98 güvenle sabitlenir', trl: '4→5' },
    { id: 'WP-3', title: 'Sinyal işleme ve LoRa',       m0: 6,  m1: 9,
      focus: 'Spike gürültü giderme; olay tetikli MCU kodu; P2P LoRaWAN; enerji hasadı; PCB',
      out: 'Düşük gecikmeli anomali aktarımı; PCB tamam', trl: '5→6' },
    { id: 'WP-4', title: 'Saha prototipi',              m0: 9,  m1: 11,
      focus: 'Yetkili orman parselinde gömülü sensörler; eşzamanlı kayıtla küçük kontrollü yakma',
      out: 'Alev öncesi tespitin sunucuya ulaşması; dayanıklılık', trl: '6→7' },
    { id: 'WP-5', title: 'YZ ve patent',                m0: 11, m1: 15,
      focus: 'LSTM sınıflandırıcı (FP < %1); TÜRKPATENT başvurusu; yatırım görüşmeleri',
      out: 'Patent başvurusu; ihale uyum dosyası', trl: '—' },
    { id: 'WP-6', title: 'Ticari MVP',                  m0: 15, m1: 18,
      focus: 'İlk B2B/B2G MVP sahası ve referans verisi',
      out: 'Referans kurulum', trl: '6→7' }
  ];
  D.roadmap.src = 'RM/BP';

  /* ---------------------------------------------------------- ticari ------- */
  D.budget = [
    { cat: 'Personel',                                  tl: 720000 },
    { cat: 'Ekipman / yazılım',                         tl: 350000 },
    { cat: 'Malzeme',                                   tl: 119000 },
    { cat: 'Hizmet alımı (CE/RoHS, BTK, patent)',       tl:  85000 },
    { cat: 'Diğer (kira, saha lojistiği, kuruluş)',     tl:  76000 }
  ];
  D.budgetTotal = 1350000;
  D.commercial = {
    seed: '1.350.000 TL · %3 pay · Aşama-2 “Mükemmeliyet Mührü” (TRL 6–7 hedefi)',
    follow: 'Takip yatırımı +1.350.000 TL’ye kadar; GCIP üzerinden %5 pay ile 2.250.000 TL’ye kadar',
    vehicle: 'Mycellium-Aegis A.Ş. (kurulacak) · İYTE Teknopark kuluçkası',
    pilots: 'Ege Orman Vakfı & OGM parselleri, İYTE — Orman Bölge Müdürlüğü ve İYTE niyet mektupları mevcut',
    compliance: 'CE, RoHS, BTK 868 MHz RF sertifikasyonu, biyomimetik elektrot için TÜRKPATENT başvurusu',
    src: 'RM/BP'
  };

  D.risks = [
    { r: 'Yanlış alarm (yaz kuraklığı / yer altı ısı birikimi)',
      m: 'Üç sinyalli AND füzyonu; kuraklık–yangın sınıflandırması; komşu düğüm çapraz kontrolü' },
    { r: 'Biyotik/abiyotik hasar (böcek, kemirgen, rakip mikroorganizma)',
      m: 'Miselyumun kendini onarması; silika dış katman fiziksel bariyer' },
    { r: 'Elektrot korozyonu (iyonik toprak)',
      m: 'Platin kaplı karbon veya diferansiyel Ag/AgCl elektrot ile SNR korunur' },
    { r: 'Güneşsiz dönemde enerji marjı (%50 duty-cycle’da 6.1 hafta)',
      m: 'İkinci LiFePO₄ hücresi paralel (6000→12000 mAh) veya panelin 5W→10W büyütülmesi', src: 'HW §5.1' }
  ];

  /* --------------------------------------------------- tasarım revizyonu --- */
  /* Depoda iki farklı donanım kuşağı var; dijital ikiz ikisini de gösterir.    */
  D.revisions = [
    { stage: 'Rev A — Laboratuvar tezgâhı (Mayıs 2026)', src: 'EXP',
      rows: [['MCU','ESP32 (Xtensa LX6, 240 MHz)'],['Ön kuv.','MCP6022'],['ADC','ADS1115 (16-bit)'],
             ['Haberleşme','USB / UART 115200 baud'],['Güç','Dizüstü USB'],['Amaç','Hipotez doğrulama, TRL 2→4']] },
    { stage: 'Rev B — Saha donanımı (Temmuz 2026)', src: 'HW',
      rows: [['MCU','STM32L4 (L412/L452), Stop2 1.3 µA'],['Ön kuv.','OPA333 (zero-drift)'],['ADC','ADS1115 (16-bit)'],
             ['Haberleşme','RS485 (MAX3485) + LoRa 868 MHz'],['Güç','5 W güneş + MPPT + LiFePO₄'],['Amaç','Saha prototipi, TRL 5→7']] }
  ];

  /* Depoda tespit edilen tutarsızlıklar — dürüst mühendislik notu             */
  D.discrepancies = [
    { t: 'MCU ailesi',
      a: 'README ve sunum ESP32 diyor', b: 'Donanım raporu STM32L4 diyor',
      v: 'Tutarsızlık değil, tasarım revizyonu: ESP32 lab tezgâhıdır (Rev A), STM32L4 saha donanımıdır (Rev B). README’nin donanım tablosu Rev B ile güncellenmelidir.' },
    { t: 'Ön kuvvetlendirici',
      a: 'MCP6022 (deney raporu)', b: 'OPA333 (donanım raporu)',
      v: 'Aynı revizyon farkı. OPA333’ün zero-drift yapısı, aylarca gömülü kalacak bir elektrotta DC ofset kaymasını bastırmak için doğru tercih.' },
    { t: 'ADC bit derinliği',
      a: 'README WP-2/haberleşme bölümünde “24-bit ADC” geçiyor', b: 'Kullanılan parça ADS1115 = 16-bit',
      v: 'README’de düzeltilmesi gereken gerçek bir hata. 24-bit’e geçilecekse ADS1220/ADS131M0x gibi bir parça seçilip güç bütçesi yeniden hesaplanmalıdır.' },
    { t: 'Örnekleme hızı vs 20 Hz bulgusu',
      a: 'Deney 1: fs = 45 Hz, baskın frekans ≈20 Hz', b: 'Nyquist sınırı 22.5 Hz',
      v: '20 Hz bileşeni Nyquist’in %89’unda ölçülmüştür — anti-aliasing filtresi olmadan takma-ad (aliasing) riski yüksektir. Deney 2’nin 100 Hz’e çıkması doğru hamledir; 20 Hz bulgusunun 100 Hz’de tekrarlanması önerilir.' },
    { t: 'Enerji marjı',
      a: '%10 duty-cycle → 27–34 hafta', b: '%50 duty-cycle → 6.1–7.5 hafta',
      v: 'Rapor bunu açıkça belirtiyor: daha kısa tespit gecikmesi için marj daraltılmıştır. Olay-tetikli (adaptif) duty-cycle — sakinken %10, anomali şüphesinde %50 — her iki hedefi de karşılar.' },
    { t: 'Tespit derinliği ile hayatta kalma derinliği aynı varsayılmış',
      a: 'Tüm belgeler: sensör 15–20 cm’de', b: 'Bu ikizin ısı iletim çözümü: ısıl cephe 18 cm’e tutuşmadan SONRA varıyor',
      v: '15–20 cm miselyumun hayatta kalma koşuludur; ısıl cephenin tespit koşulu değildir. Biyoelektrot 18 cm’de kalmalı, ancak sıcaklık/direnç probu aynı kablo üzerinde 5–8 cm’e alınmalıdır. ADS1115’in dört kanalından ikisi boş; ek maliyet bir termistör ve bir elektrot çifti (< $3). İkizde bu değişiklik alarmı tutuşmadan ~25 dk önceye çekiyor ve kuraklık senaryosunda yanlış alarm üretmiyor.' },
    { t: 'AND kuralının eşzamanlılık gereksinimi',
      a: 'Alarm = (β) AND (γ) AND (spike) — anlık', b: 'Isıl cephe ile kuruma cephesi aynı derinliğe farklı zamanlarda varır',
      v: 'Koşullar anlık olarak değil, kısa bir kalıcılık penceresi içinde birleştirilmelidir. İkizde 45 dakikalık pencere kullanıldı; bu, ayrık cephe varışlarını tek bir olayda toplarken kuraklık senaryosunun yanlış alarm üretmesini engelliyor. Firmware’de basit bir zaman damgası ile uygulanabilir.' },
    { t: 'γ eşiğinin sayısal değeri',
      a: 'Kural tanımlı: d(ln R)/dt > γ', b: 'γ için sayısal değer hiçbir belgede yok',
      v: 'WP-2’nin (iklim odası) birincil çıktısı zaten budur. Bu ikizde γ = 0.002 dk⁻¹ varsayılmıştır ve varsayım olarak işaretlenmiştir.' }
  ];

  /* ---------------------------------------------------------- kaynaklar ---- */
  D.references = [
    'S. H. Doerr ve diğ., “Soil heating during wildfires and prescribed burns: A global evaluation,” Int. J. Wildland Fire, 34(12), WF25103, 2025.',
    'N. Phillips, A. Gandia, A. Adamatzky, “Electrical response of fungi to changing moisture content,” Fungal Biol. Biotechnol., 10(1):8, 2023.',
    'A. Adamatzky, “Towards fungal computer,” Interface Focus, 8(6):20180029, 2018.',
    'A. Adamatzky, “Fungal systems for security and resilience,” arXiv:2602.10543, 2026.',
    'A. Adamatzky, “Directional electrical spiking… star-shaped electrode array,” arXiv:2601.08099, 2026.',
    'X. Zhang ve diğ., “Novelly grown fire-resistant fungal fibers,” Sci. Rep., 12:10836, 2022.',
    'S. Makdee ve diğ., “Wildfire early warning system using LoRa technology,” Computers, 15(2):105, 2026.',
    'T. A. Duong ve diğ., “Thermotolerance and post-fire growth in Rhizina undulata,” BMC Genomics, 26(1):1041, 2025.',
    'M. S. Fischer ve diğ., “Pyrolyzed substrates… post-fire fungus Pyronema domesticum,” Front. Microbiol., 12:729289, 2021.'
  ];

  /* -------------------------------------------------------- depo haritası -- */
  D.dossier = [
    { path: 'docs/hardware/',       what: 'Donanım teknik raporu (Rev B) — bu ikizin ana kaynağı', n: 1, hot: true },
    { path: 'docs/research/',       what: 'Bilimsel değerlendirme, Wood Wide Web, elektrofizyoloji yol haritası', n: 7 },
    { path: 'docs/experiments/',    what: 'Deney 1 & 2 raporları — firmware, FFT, sonuçlar', n: 2 },
    { path: 'docs/pitch-decks/',    what: 'BiGG sunumu (HTML + Beamer), yedek slaytlar, YZ soru-cevap', n: 22 },
    { path: 'docs/business-plan/',  what: 'İş planı, AGY112, maliyet formu', n: 11 },
    { path: 'docs/letters-of-intent/', what: 'OGM Bölge Müdürlüğü, İYTE niyet mektupları, taahhütname', n: 6 },
    { path: 'docs/bigg-training/',  what: 'BiGG modül eğitimleri ve çağrı dokümanı', n: 10 },
    { path: 'docs/team-cvs/',       what: 'Ekip özgeçmişleri', n: 12 },
    { path: 'docs/media/',          what: 'Deney fotoğrafları, teraryum, referans sensör görselleri', n: 22 },
    { path: 'docs/digital-twin/',   what: 'Bu interaktif dijital ikiz', n: 1, hot: true }
  ];

  global.AEGIS_DATA = D;
})(window);
