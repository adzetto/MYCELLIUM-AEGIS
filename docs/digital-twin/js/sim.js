/* =============================================================================
   MYCELLIUM-AEGIS · DİJİTAL İKİZ
   sim.js — Fiziksel simülasyon çekirdeği
   -----------------------------------------------------------------------------
   Dört bağlı model:
     1. 1B geçici ısı iletimi        — açık sonlu fark, α(θ) nem bağımlı
     2. Toprak nemi / kuruma cephesi — buharlaşma + ısıl sürüklenme (öncü cephe)
     3. Elektriksel direnç           — Archie yasası, R ∝ θ^(-n)
     4. Biyoelektrik sinyal          — osilasyon + AP spike + pembe gürültü
   Ardından füzyon kuralı ve güç bütçesi.

   DÜRÜSTLÜK NOTU: (1) ve (3) literatür modelleridir. (2) ve (4) davranışsal
   (fenomenolojik) modellerdir; katsayıları WP-2 iklim odası ölçümleriyle
   kalibre edilecektir. Modelin amacı sistemin ne ölçtüğünü ve neden AND
   füzyonunun ayırt edici olduğunu gösteren, sayısal olarak tutarlı bir
   tezgâh sunmaktır — saha tahmini üretmek değildir.
   ============================================================================= */
(function (global) {
  'use strict';

  /* ----------------------------------------------------------- yardımcılar - */
  const clamp = (x, a, b) => (x < a ? a : x > b ? b : x);
  const lerp  = (a, b, t) => a + (b - a) * t;

  // Abramowitz & Stegun 7.1.26 — hata fonksiyonu yaklaşımı (|ε| < 1.5e-7)
  function erf(x) {
    const s = x < 0 ? -1 : 1; x = Math.abs(x);
    const t = 1 / (1 + 0.3275911 * x);
    const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
    return s * y;
  }
  const erfc = (x) => 1 - erf(x);

  /* ============================================================ SABİTLER === */
  const GRID = { N: 61, dz: 0.01 };            // 0 … 0.60 m, 1 cm adım
  const ALPHA_DRY = 1.8e-7;                    // m²/s  kuru mineral toprak
  const ALPHA_WET = 5.5e-7;                    // m²/s  doygun toprak
  const THETA_SAT = 0.35;                      // hacimsel doygunluk referansı
  const ARCHIE_N  = 2.0;                       // doygunluk üssü (Archie)
  const THETA_REF = 0.25;                      // R_ref'in ölçüldüğü nem
  const R_REF     = 12000;                     // Ω  elektrot çifti referans direnci
  const THETA_RES = 0.030;                     // higroskopik artık su — buradan aşağısı ısıl olarak kopmaz
  const E0_SURF   = 2.2e-8;                    // s⁻¹ yüzeyde taban evapotranspirasyon
  const E_DEPTH   = 0.10;                      // m   buharlaşmanın sönüm derinliği
  const C_THERMAL = 2.2e-5;                    // s⁻¹ ısıl kaynaklı kuruma ölçek katsayısı
  const T_SCALE   = 9.0;                       // K   buharlaşmanın sıcaklık duyarlılığı (Arrhenius benzeri)
  const Z_LEAD    = 0.04;                      // m   buhar taşınımının kuruma cephesini öne taşıması
  const LEAD_MIX  = 0.45;                      // öncü (sığ) sıcaklığın kuruma sürücüsündeki ağırlığı
  const FS        = 100;                       // Hz  biyosinyal örnekleme (Deney 2)
  const FFT_N     = 512;                       // FFT pencere uzunluğu

  /* ============================================== SENARYO YÜZEY SICAKLIĞI == */
  /* Hepsi t [s] alır, yüzey (z=0) sıcaklığını [°C] döndürür.                  */
  const SCENARIOS = {
    normal: {
      id: 'normal', label: 'Normal gün', tag: 'Referans',
      desc: 'Bulutsuz bir yaz günü. Yüzeyde ±12 °C günlük salınım, nem yavaşça düşer. Alarm beklenmiyor.',
      ignite: null,
      surfT: (t, p) => p.tAmb + 12 * Math.sin(2 * Math.PI * (t - 32400) / 86400)
    },
    drought: {
      id: 'drought', label: 'Kuraklık / sıcak hava dalgası', tag: 'Yanlış alarm testi',
      desc: 'Haftalarca yağış yok, yüzey 55 °C’ye kadar ısınıyor. γ koşulu tetiklenir, β tetiklenmez → sistem KURAKLIK der, alarm vermez.',
      ignite: null,
      surfT: (t, p) => p.tAmb + 8 + 22 * Math.max(0, Math.sin(2 * Math.PI * (t - 32400) / 86400))
    },
    preignition: {
      id: 'preignition', label: 'Alev öncesi — için için yanma', tag: 'Hedef senaryo',
      desc: 'Ölü örtüde alevsiz pirolizle ilerleyen sıcaklık. Yüzey 2 saatte 240 °C’ye çıkar. Tutuşma 300 °C kabul edilir; ikiz alarm ile tutuşma arasındaki öncü süreyi ölçer.',
      ignite: 300,
      surfT: (t, p) => {
        const t0 = p.tStart, ramp = 5400;
        if (t < t0) return p.tAmb + 10 * Math.sin(2 * Math.PI * (t - 32400) / 86400);
        const u = clamp((t - t0) / ramp, 0, 1);
        // pirolitik ısınma: yavaş başlar, hızlanır, sonra korlaşmış örtüde platoya oturur
        const rise = p.tAmb + (300 - p.tAmb) * (u * u * (3 - 2 * u));
        const plateau = 140 * clamp((t - t0 - ramp) / 9000, 0, 1);   // için için yanma sürer
        return rise + plateau;
      }
    },
    surfaceFire: {
      id: 'surfaceFire', label: 'Yüzey yangını — alev cephesi', tag: 'Geç tespit',
      desc: 'Alev cephesi dakikalar içinde 900 °C’ye çıkıp geçer, ardından kor kalır. Alev zaten görünürdür; bu senaryo iletim gecikmesinin neden erken uyarı için tek başına yeterli olmadığını gösterir.',
      ignite: 300,
      surfT: (t, p) => {
        const t0 = p.tStart;
        if (t < t0) return p.tAmb + 10 * Math.sin(2 * Math.PI * (t - 32400) / 86400);
        const dt = t - t0;
        if (dt < 300) return p.tAmb + (900 - p.tAmb) * (dt / 300);          // cephe gelişi 5 dk
        if (dt < 1200) return 900;                                          // alev 15 dk
        // cephe geçtikten sonra ölü örtü kor halinde için için yanmaya devam eder
        return Math.max(p.tAmb + 20, 260 + 640 * Math.exp(-(dt - 1200) / 2400));
      }
    }
  };

  /* ==================================================== BİYOSİNYAL ÜRETECİ = */
  /* Deney 1 ölçümlerini hedefler:
       dinlenim  → baskın ≈20 Hz, V_min ≈ -29.4 mV, ortalama ≈ -2.9 mV
       ateş str. → baskın ≈5 Hz,  V_min ≈ -33.4 mV, ortalama ≈ -2.94 mV      */
  class BioSignal {
    constructor() {
      this.buf = new Float32Array(FFT_N);
      this.idx = 0;
      this.t = 0;
      this.phase = 0; this.phase2 = 0;
      this.spikes = [];             // {t0, amp}
      this.spikeTimes = [];         // alarm penceresi için zaman damgaları
      this.pink = 0;
      this.lastSpikeRate = 0;
    }
    reset() { this.buf.fill(0); this.idx = 0; this.spikes.length = 0; this.spikeTimes.length = 0; }

    /* stres s ∈ [0,1] için bir örnek üretir; dt = 1/FS */
    step(s, dt) {
      this.t += dt;
      const fDom  = lerp(AEGIS_DATA.bioTargets.fRest, AEGIS_DATA.bioTargets.fStress, s); // 20 → 5 Hz
      const aOsc  = 0.55 + 1.85 * s;                       // mV, taban osilasyon genliği
      this.phase  += 2 * Math.PI * fDom * dt;
      this.phase2 += 2 * Math.PI * fDom * 2 * dt;

      // 1/f benzeri gürültü (tek kutuplu AR(1) süzgeç)
      this.pink = 0.985 * this.pink + 0.15 * (Math.random() * 2 - 1);
      const noise = this.pink * 0.9 + (Math.random() * 2 - 1) * 0.25;

      // aksiyon potansiyeli spike'ları — Poisson, strese göre hızlanır
      const rate = 0.35 + 2.5 * s;                          // Hz
      this.lastSpikeRate = rate;
      if (Math.random() < rate * dt) {
        this.spikes.push({ t0: this.t, amp: -(23 + 9 * s) * (0.75 + 0.5 * Math.random()) });
        this.spikeTimes.push(this.t);
      }
      while (this.spikeTimes.length && this.t - this.spikeTimes[0] > 60) this.spikeTimes.shift();

      let sp = 0;
      for (let i = this.spikes.length - 1; i >= 0; i--) {
        const a = this.spikes[i], age = this.t - a.t0;
        if (age > 0.6) { this.spikes.splice(i, 1); continue; }
        // hızlı depolarizasyon + üstel repolarizasyon
        sp += a.amp * (1 - Math.exp(-age / 0.012)) * Math.exp(-age / 0.085);
      }

      const v = AEGIS_DATA.bioTargets.vmeanRest
              + aOsc * Math.sin(this.phase)
              + 0.35 * aOsc * Math.sin(this.phase2 + 1.1)
              + noise + sp;

      this.buf[this.idx] = v;
      this.idx = (this.idx + 1) % FFT_N;
      return v;
    }

    /* son 60 s içindeki spike frekansı [Hz] */
    spikeFreq() { return this.spikeTimes.length / 60; }

    /* pencereyi kronolojik sırayla döndürür */
    window() {
      const out = new Float32Array(FFT_N);
      for (let i = 0; i < FFT_N; i++) out[i] = this.buf[(this.idx + i) % FFT_N];
      return out;
    }
  }

  /* ------------------------------------------------ radix-2 in-place FFT --- */
  function fftMag(x) {
    const n = x.length;
    const re = new Float64Array(n), im = new Float64Array(n);
    // Hann penceresi + DC giderme
    let mean = 0; for (let i = 0; i < n; i++) mean += x[i]; mean /= n;
    for (let i = 0; i < n; i++) re[i] = (x[i] - mean) * (0.5 - 0.5 * Math.cos(2 * Math.PI * i / (n - 1)));

    for (let i = 1, j = 0; i < n; i++) {                 // bit-reversal
      let bit = n >> 1;
      for (; j & bit; bit >>= 1) j ^= bit;
      j ^= bit;
      if (i < j) { let t = re[i]; re[i] = re[j]; re[j] = t; t = im[i]; im[i] = im[j]; im[j] = t; }
    }
    for (let len = 2; len <= n; len <<= 1) {
      const ang = -2 * Math.PI / len, wr = Math.cos(ang), wi = Math.sin(ang);
      for (let i = 0; i < n; i += len) {
        let cr = 1, ci = 0;
        for (let k = 0; k < len / 2; k++) {
          const ur = re[i + k],           ui = im[i + k];
          const vr = re[i + k + len / 2] * cr - im[i + k + len / 2] * ci;
          const vi = re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
          re[i + k] = ur + vr;            im[i + k] = ui + vi;
          re[i + k + len / 2] = ur - vr;  im[i + k + len / 2] = ui - vi;
          const ncr = cr * wr - ci * wi;  ci = cr * wi + ci * wr; cr = ncr;
        }
      }
    }
    const half = n >> 1, mag = new Float32Array(half);
    for (let i = 0; i < half; i++) mag[i] = Math.sqrt(re[i] * re[i] + im[i] * im[i]) * 2 / n;
    return mag;
  }

  /* ============================================================== DÜNYA ==== */
  class World {
    constructor() {
      this.p = {
        tAmb: 22,            // °C  yıllık ortalama toprak sıcaklığı
        theta0: 0.22,        // hacimsel su içeriği başlangıcı
        depth: 0.18,         // m   BİYOELEKTROT derinliği (miselyumun yaşadığı yer)
        probe: 0.18,         // m   T/R PROBU derinliği — belgede elektrotla aynı
        tStart: 3 * 3600,    // s   olayın başlangıcı (sim saati)
        beta: AEGIS_DATA.fusion.beta.value,     // °C / 10 dk
        gamma: AEGIS_DATA.fusion.gamma.value,   // dk⁻¹
        kSigma: 3,
        hold: 45 * 60        // s   koşul tutma penceresi (kalıcılık)
      };
      this.scenario = 'preignition';
      this.reset();
    }

    reset() {
      const N = GRID.N;
      this.T = new Float64Array(N).fill(this.p.tAmb);
      this.TH = new Float64Array(N).fill(this.p.theta0);
      // nem yüzeye doğru biraz daha düşük başlar (kurumuş ölü örtü)
      for (let i = 0; i < N; i++) this.TH[i] = this.p.theta0 * (0.55 + 0.45 * clamp(i * GRID.dz / 0.12, 0, 1));
      this.t = 0;
      this._dth = new Float64Array(N);          // düğüm başına dθ/dt (son adım)
      this.prevT = this.p.tAmb;
      this.prevLnR = Math.log(this.resistance());
      this.dTdt = 0; this.dlnRdt = 0;
      this.held = { c1: -1e9, c2: -1e9, c3: -1e9 };   // son tetiklenme zamanları
      this.first = { c1: null, c2: null, c3: null };  // ilk eşik geçişleri
      this.hist = [];               // {t, Tz, theta, R, dTdt, dlnRdt, fs, alarm}
      this.bio = new BioSignal();
      this.baseF = { mean: 0.4, sd: 0.12, n: 0 };
      this.alarmAt = null; this.igniteAt = null;
      this.state = 'NORMAL';
      this.latched = false;
      this.scope = [];
      this.mag = new Float32Array(FFT_N >> 1);
      this.fDom = 20;
      this.packets = 0;
      this.samplePhase = 0;
    }

    setScenario(id) { this.scenario = id; this.reset(); }

    /* Prob derinliği değişince türev referansları yeni derinliğe taşınmalı,
       aksi halde ilk adımda sahte bir dT/dt ve d(lnR)/dt sıçraması oluşur.  */
    setProbe(z) {
      this.p.probe = z;
      this.prevT = this.Tz();
      this.prevLnR = Math.log(this.resistance());
      this.dTdt = 0; this.dlnRdt = 0;
    }

    /* ---- yardımcı okumalar --------------------------------------------- */
    idxOf(z) { return clamp(Math.round(z / GRID.dz), 0, GRID.N - 1); }
    Tz(z)     { return this.T[this.idxOf(z === undefined ? this.p.probe : z)]; }
    thetaZ(z) { return this.TH[this.idxOf(z === undefined ? this.p.probe : z)]; }

    /* Archie yasası: R = R_ref · (θ/θ_ref)^(−n) */
    resistance(z) {
      const th = Math.max(0.02, this.thetaZ(z));
      return R_REF * Math.pow(th / THETA_REF, -ARCHIE_N);
    }

    /* Miselyum ağı 10–30 cm bandına yayılır ve elektriksel olarak bağlıdır;
       ağın herhangi bir noktasındaki stres, mesafeyle zayıflayarak elektrota
       ulaşır (Adamatzky: ağ boyunca sinyal yayılımı). Bu yüzden biyoelektrik
       stres tek bir derinlikten değil, ağ genelinden okunur.                */
    networkStress() {
      let best = 0;
      for (let z = 0.08; z <= 0.30001; z += 0.02) {
        const dT = Math.max(0, this.T[this.idxOf(z)] - this.p.tAmb);
        const sT = clamp(dT / 12, 0, 1);
        const sD = clamp(this.dryRateAt(z) * 60 / 0.02, 0, 1);
        const local = clamp(0.65 * sT + 0.65 * sD, 0, 1);
        const atten = Math.exp(-Math.abs(z - this.p.depth) / 0.15);
        best = Math.max(best, local * atten);
      }
      return best;
    }

    /* z derinliğinde anlık d(lnR)/dt — nem türevinden Archie ile             */
    dryRateAt(z) {
      const i = this.idxOf(z);
      return -ARCHIE_N * (this._dth ? this._dth[i] : 0) / Math.max(0.02, this.TH[i]);
    }

    alpha(i) {                       // nem bağımlı ısıl yayınım
      return lerp(ALPHA_DRY, ALPHA_WET, clamp(this.TH[i] / THETA_SAT, 0, 1));
    }

    /* ---- bir makro adım: dt saniye ilerlet ------------------------------ */
    advance(dt) {
      const N = GRID.N, dz2 = GRID.dz * GRID.dz;
      const sc = SCENARIOS[this.scenario];

      // kararlılık için alt adımlama: r = α·dt/dz² ≤ 0.4
      const aMax = ALPHA_WET;
      const dtMax = 0.4 * dz2 / aMax;
      const nSub = Math.max(1, Math.ceil(dt / dtMax));
      const h = dt / nSub;

      for (let s = 0; s < nSub; s++) {
        const t = this.t + s * h;
        const Ts = sc.surfT(t, this.p);
        const Tn = new Float64Array(N);
        Tn[0] = Ts;                                   // Dirichlet yüzey
        for (let i = 1; i < N - 1; i++) {
          const a = this.alpha(i);
          Tn[i] = this.T[i] + a * h / dz2 * (this.T[i + 1] - 2 * this.T[i] + this.T[i - 1]);
        }
        Tn[N - 1] = this.p.tAmb;                      // derin sabit sıcaklık
        this.T = Tn;

        /* --- nem: taban evapotranspirasyon + ısıl kuruma cephesi ---
           Sürücü, yerel sıcaklık fazlası ile bir miktar daha sığ (öncü) noktanın
           fazlasının karışımıdır: buhar taşınımı kuruma cephesini iletim
           cephesinin biraz önüne taşır. Kuruma hızı (θ − θ_res) ile orantılıdır,
           yani higroskopik artık su ısıl olarak kopmaz; sıcaklık bağımlılığı
           buharlaşmanın enerji bariyerini yansıtacak şekilde üsteldir.        */
        for (let i = 0; i < N; i++) {
          const z = i * GRID.dz;
          const avail = Math.max(0, this.TH[i] - THETA_RES);
          const evap = E0_SURF * Math.exp(-z / E_DEPTH) * (avail / THETA_REF);
          const zLead = clamp(z - Z_LEAD, 0, (N - 1) * GRID.dz);
          const dTloc  = Math.max(0, this.T[i] - this.p.tAmb);
          const dTlead = Math.max(0, this.T[this.idxOf(zLead)] - this.p.tAmb);
          const dTeff = (1 - LEAD_MIX) * dTloc + LEAD_MIX * dTlead;
          const g = Math.expm1(Math.min(dTeff / T_SCALE, 9));      // exp(ΔT/9) − 1, taşma korumalı
          const dry = C_THERMAL * avail * g;
          const next = Math.max(THETA_RES * 0.5, this.TH[i] - (evap + dry) * h);
          this._dth[i] = (next - this.TH[i]) / h;
          this.TH[i] = next;
        }
      }
      this.t += dt;

      // --- türevler (ölçüm noktasında) ---
      const Tz = this.Tz();
      this.dTdt = (Tz - this.prevT) / dt;                       // °C/s
      this.prevT = Tz;
      const lnR = Math.log(this.resistance());
      this.dlnRdt = (lnR - this.prevLnR) / dt;                  // s⁻¹
      this.prevLnR = lnR;

      // --- stres → biyosinyal (ağ genelinden, elektrot derinliğine zayıflayarak) ---
      const stress = this.networkStress();
      this.stress = stress;

      // biyosinyali gerçek zamanlı örnekle (sim hızından bağımsız, sabit 100 Hz)
      const nSamp = Math.min(400, Math.round(FS * Math.min(dt, 4)));
      for (let k = 0; k < nSamp; k++) {
        const v = this.bio.step(stress, 1 / FS);
        this.scope.push(v);
      }
      while (this.scope.length > 900) this.scope.shift();

      // --- taban istatistiği: yalnızca sakin dönemde güncellenir ---
      const f = this.bio.spikeFreq();
      if (stress < 0.08) {
        const b = this.baseF; b.n++;
        const d = f - b.mean;
        b.mean += d / Math.min(b.n, 400);
        b.sd = Math.sqrt(clamp(b.sd * b.sd + (d * (f - b.mean) - b.sd * b.sd) / Math.min(b.n, 400), 1e-4, 100));
      }

      /* --- füzyon kuralı ---
         Ham eşik geçişleri anlıktır; ancak ısıl cephe ile kuruma cephesi aynı
         derinliğe farklı zamanlarda ulaşır. Bu yüzden her koşul, tetiklendikten
         sonra `hold` süresi boyunca DOĞRU kalır (kalıcılık penceresi) ve AND
         bu tutulmuş değerler üzerinde değerlendirilir. hold = 0 yapıldığında
         kural belgedeki eşzamanlı AND'e indirgenir.                          */
      const fThr = this.baseF.mean + this.p.kSigma * this.baseF.sd;
      const raw1 = (this.dTdt * 600) > this.p.beta;                  // °C / 10 dk
      const raw2 = (this.dlnRdt * 60) > this.p.gamma;                // dk⁻¹
      const raw3 = f > fThr;
      if (raw1) { this.held.c1 = this.t; if (this.first.c1 === null) this.first.c1 = this.t; }
      if (raw2) { this.held.c2 = this.t; if (this.first.c2 === null) this.first.c2 = this.t; }
      if (raw3) { this.held.c3 = this.t; if (this.first.c3 === null) this.first.c3 = this.t; }
      const c1 = (this.t - this.held.c1) <= this.p.hold;
      const c2 = (this.t - this.held.c2) <= this.p.hold;
      const c3 = (this.t - this.held.c3) <= this.p.hold;
      this.cond = { c1, c2, c3, raw1, raw2, raw3, f, fThr };

      const alarm = c1 && c2 && c3;
      this.state = alarm ? 'YANGIN BAŞLANGICI'
                 : (c2 && !c1) ? 'KURAKLIK'
                 : (c1 && !c2) ? 'ISIL ANOMALİ'
                 : 'NORMAL';
      if (alarm && this.alarmAt === null) { this.alarmAt = this.t; this.packets++; }
      if (alarm) this.latched = true;

      // tutuşma anı (yüzeyde eşik)
      if (sc.ignite !== null && this.igniteAt === null && this.T[0] >= sc.ignite) this.igniteAt = this.t;

      // FFT
      /* Baskın frekans: Deney 1'in raporladığı salınım bandında (≥2 Hz) aranır.
         Spike dizisinin çok düşük frekanslı enerjisi aksi halde tepeyi ~0.4 Hz'e
         çeker ve 20 Hz → 5 Hz kaymasını gizlerdi.                              */
      this.mag = fftMag(this.bio.window());
      const iMin = Math.max(2, Math.round(2.0 * FFT_N / FS));
      let bi = iMin, bm = 0;
      for (let i = iMin; i < this.mag.length; i++) if (this.mag[i] > bm) { bm = this.mag[i]; bi = i; }
      this.fDom = bi * FS / FFT_N;

      this.hist.push({ t: this.t, Tz, theta: this.thetaZ(), R: this.resistance(),
                       dTdt: this.dTdt, dlnRdt: this.dlnRdt, f, state: this.state });
      if (this.hist.length > 4000) this.hist.shift();
      return this;
    }

    /* alarmın tutuşmadan kaç saniye önce geldiği (+ = erken) */
    leadTime() {
      if (this.alarmAt === null || this.igniteAt === null) return null;
      return this.igniteAt - this.alarmAt;
    }

    profile() {                       // z, T, θ dizileri (grafik için)
      const z = [], T = [], th = [];
      for (let i = 0; i < GRID.N; i++) { z.push(i * GRID.dz); T.push(this.T[i]); th.push(this.TH[i]); }
      return { z, T, th };
    }
  }

  /* ========================================================= GÜÇ BÜTÇESİ == */
  /* HW §5 tablosundan doğrudan; varsayılan parametrelerle rapor değerlerini
     birebir üretir: yeraltı 4.49 mA · yüzey 0.28 mA · toplam 4.77 mA         */
  function powerBudget(o) {
    const d  = o.duty;                     // 0…1
    const tx = o.txDuty, rx = o.rxDuty;
    const idle = Math.max(0, 1 - tx - rx);

    const under =
        d * 8.5   + (1 - d) * 0.0013 +     // STM32L4  Run / Stop2
        d * 0.15  + (1 - d) * 0.0005 +     // ADS1115
        d * 0.017 +                        // OPA333
        d * 0.30  + (1 - d) * 0.001;       // MAX3485 ×1
    const lora = tx * 110 + rx * 4.2 + idle * 0.005;
    const surf =
        d * 0.30 + (1 - d) * 0.001 +       // MAX3485 ×1
        lora + 0.002 + 0.002;              // + koruma IC + BQ24650 sızıntı
    const total = under + surf;

    const cap = 6000 * o.cells;                       // mAh
    const hIdeal = cap / total;
    const hCons  = cap * o.dod * o.eff / total;

    // güneş: 5 W panel, MPPT verimi, etkin tepe güneş saati (kanopi gölgesi dahil)
    const wh   = o.panelW * o.psh * o.mpptEff * o.canopy;
    const mAhIn = wh * 1000 / 3.2;
    const mAhOut = total * 24;

    return {
      under, surf, lora, total,
      capacity: cap,
      hoursIdeal: hIdeal, hoursCons: hCons,
      weeksIdeal: hIdeal / 168, weeksCons: hCons / 168,
      daysIdeal: hIdeal / 24, daysCons: hCons / 24,
      mAhIn, mAhOut, netDaily: mAhIn - mAhOut,
      autonomyDays: hCons / 24
    };
  }

  /* 60 günlük şarj durumu simülasyonu — rastgele bulutluluk ile */
  function socSeries(o, days) {
    const pb = powerBudget(o);
    const cap = pb.capacity * o.dod;
    let soc = cap;
    const out = [];
    let seed = 1337;
    const rnd = () => (seed = (seed * 1664525 + 1013904223) % 4294967296) / 4294967296;
    for (let d = 0; d < days; d++) {
      const cloud = o.cloudy && d >= o.cloudStart && d < o.cloudStart + o.cloudLen ? 0.12 : (0.55 + 0.45 * rnd());
      const gain = pb.mAhIn * cloud;
      soc = clamp(soc + gain - pb.mAhOut, 0, cap);
      out.push({ day: d, soc, pct: soc / cap, gain, cloud });
    }
    return out;
  }

  /* ============================================================ MALİYET === */
  function costModel(o) {
    const nodeUsd = AEGIS_DATA.bomNode.reduce((a, r) => a + r.usd * r.qty, 0);
    const gwUsd   = AEGIS_DATA.bomGateway.reduce((a, r) => a + r.usd * r.qty, 0);
    // hacim iskontosu: 100+ adette birim fiyatların düşmesi beklenir (HW §6)
    const disc = o.volume >= 1000 ? 0.62 : o.volume >= 100 ? 0.78 : 1.0;
    const nodes = o.nodes, gws = Math.max(1, Math.ceil(o.nodes / o.nodesPerGw));
    const capexUsd = nodes * nodeUsd * disc + gws * gwUsd;
    return {
      nodeUsd, gwUsd, disc, nodes, gws,
      capexUsd, capexTl: capexUsd * o.fx,
      perNodeUsd: nodeUsd * disc,
      perHaTl: o.hectares > 0 ? capexUsd * o.fx / o.hectares : 0
    };
  }

  global.AEGIS_SIM = {
    World, SCENARIOS, powerBudget, socSeries, costModel,
    fftMag, erfc, clamp, lerp, FS, FFT_N, GRID,
    consts: { ALPHA_DRY, ALPHA_WET, ARCHIE_N, THETA_REF, R_REF, E0_SURF, E_DEPTH, C_THERMAL, Z_LEAD }
  };
})(window);
