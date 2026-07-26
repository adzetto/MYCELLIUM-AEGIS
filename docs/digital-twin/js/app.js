/* =============================================================================
   MYCELLIUM-AEGIS · SAYISAL İKİZ
   app.js — Tek ekran denetleyicisi
   Tipografi: Computer Modern · matematik: KaTeX · tema: beyaz
   ============================================================================= */
(function () {
  'use strict';

  const D = window.AEGIS_DATA, SIM = window.AEGIS_SIM, CH = window.AEGIS_CHART, SC = window.AEGIS_SCENE;
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const clamp = SIM.clamp;

  /* ---------------------------------------------------------- biçimleme --- */
  const nf = (n, d) => (n == null || !isFinite(n)) ? '—'
    : n.toLocaleString('tr-TR', { minimumFractionDigits: d || 0, maximumFractionDigits: d || 0 });
  const hms = (s) => String(Math.floor(s / 3600)).padStart(2, '0') + ':' + String(Math.floor(s % 3600 / 60)).padStart(2, '0');
  const dur = (s) => s == null ? '—' : s < 90 ? Math.round(s) + ' sn' : s < 5400 ? (s / 60).toFixed(0) + ' dk' : (s / 3600).toFixed(2) + ' sa';

  /* ------------------------------------------------------------- KaTeX ---- */
  function K(tex, display) {
    try {
      return katex.renderToString(tex, { displayMode: !!display, throwOnError: false, output: 'html' });
    } catch (e) { return '<code>' + tex + '</code>'; }
  }
  const Ki = (t) => '<span class="inl">' + K(t, false) + '</span>';

  /* ================================================================ DURUM = */
  const A = {
    world: new SIM.World(),
    playing: true,
    speed: 120,
    charts: {},
    view: 'sub',
    power: {
      duty: 0.50, txDuty: D.loraDuty.tx, rxDuty: D.loraDuty.rx, cells: 1,
      dod: D.powerReference.dod, eff: D.powerReference.convEff,
      panelW: 5, psh: 4.2, mpptEff: 0.90, canopy: 0.55, cloudy: false, cloudStart: 22, cloudLen: 12
    },
    cost: { fx: D.costMeta.fxDefault, nodes: 40, nodesPerGw: 25, volume: 100, hectares: 1200 }
  };

  const VIEWCAP = {
    sub:   '<b>Şekil 1.</b> Orman tabanı toprak profili kesiti — biyomimetik elektrotlar 18 cm derinlikte miselyum ağı içine yerleştirilmiş; yeraltı düğümü RS485 ile yüzey düğümüne bağlı. Katman renkleri anlık ' + '' + 'sıcaklık alanını taşır.',
    node:  '<b>Şekil 1.</b> Yeraltı algılama düğümü — biyokompozit muhafaza (yarı saydam gösterildi), kart üzerinde OPA333 · ADS1115 · STM32L4 · MAX3485 · BME280. Bileşene tıklayınca seçim gerekçesi açılır.',
    strata:'<b>Şekil 1.</b> Toprak horizonları ve güvenli bölge — yüzeydeki ısı derinlikle sönümlenir; 15–20 cm bandı miselyumun hayatta kaldığı bölgedir.',
    site:  '<b>Şekil 1.</b> Orman parseli — dört ölçüm noktası, merkez kule (RAK2287 + Raspberry Pi 4) ve LoRa 868 MHz bağlantıları. Yangın senaryosunda paket trafiği hızlanır.',
    tower: '<b>Şekil 1.</b> Aegis-Nexus kulesi — LoRa konsantratörü ve 4G/LTE geri bağlantısı.'
  };

  /* ============================================== ÖLÇÜM SÜTUNU (sol panel) */
  function renderMeas() {
    const w = A.world;
    $('#meas').innerHTML = `
      <h2 class="sec">Karar kuralı</h2>
      <div class="eq">${K('\\mathrm{Alarm}=\\Big(\\tfrac{dT}{dt}>\\beta\\Big)\\wedge\\Big(\\tfrac{d\\ln R}{dt}>\\gamma\\Big)\\wedge\\big(f_{\\mathrm{spike}}>\\mu+3\\sigma\\big)', true)}</div>
      <div id="gate"></div>

      <h2 class="sec">Yerleşim ve eşikler</h2>
      <div class="ctl"><span class="l">${Ki('z_p')} — sıcaklık/direnç probu derinliği</span><span class="v" id="l-probe"></span>
        <input type="range" id="i-probe" min="0.03" max="0.30" step="0.01" value="${w.p.probe}"></div>
      <div class="ctl"><span class="l">${Ki('z_e')} — biyoelektrot derinliği</span><span class="v" id="l-depth"></span>
        <input type="range" id="i-depth" min="0.10" max="0.30" step="0.01" value="${w.p.depth}"></div>
      <div class="ctl"><span class="l">${Ki('\\beta')} — ısı akısı eşiği</span><span class="v" id="l-beta"></span>
        <input type="range" id="i-beta" min="0.05" max="6" step="0.05" value="${w.p.beta}"></div>
      <div class="ctl"><span class="l">${Ki('\\gamma')} — kuruma eşiği <i>(varsayım)</i></span><span class="v" id="l-gamma"></span>
        <input type="range" id="i-gamma" min="0.0002" max="0.02" step="0.0002" value="${w.p.gamma}"></div>
      <div class="ctl"><span class="l">${Ki('\\theta_0')} — başlangıç toprak nemi</span><span class="v" id="l-th"></span>
        <input type="range" id="i-th" min="0.06" max="0.34" step="0.01" value="${w.p.theta0}"></div>

      <div class="box" id="finding"></div>

      <h2 class="sec">Anlık durum</h2>
      <table class="t"><tbody id="live"></tbody></table>

      <h2 class="sec">Çözücü</h2>
      <div class="eq">${K('\\frac{\\partial T}{\\partial t}=\\frac{\\partial}{\\partial z}\\!\\left[\\alpha(\\theta)\\frac{\\partial T}{\\partial z}\\right],\\qquad \\alpha\\in[1{,}8;5{,}5]\\times10^{-7}\\ \\mathrm{m^2/s}', true)}</div>
      <div class="eq">${K('\\frac{\\partial\\theta}{\\partial t}=-\\,E_0e^{-z/d_e}\\frac{\\theta-\\theta_r}{\\theta_{\\mathrm{ref}}}\\;-\\;c_T(\\theta-\\theta_r)\\!\\left(e^{\\Delta T_{\\mathrm{eff}}/T_s}-1\\right)', true)}</div>
      <div class="eq">${K('R=R_{\\mathrm{ref}}\\left(\\frac{\\theta}{\\theta_{\\mathrm{ref}}}\\right)^{-n},\\quad n=2 \\quad\\text{(Archie)}', true)}</div>
      <p class="note">1B açık sonlu fark, 61 düğüm, ${Ki('\\Delta z=1\\,\\mathrm{cm}')},
      kararlılık ${Ki('r=\\alpha\\Delta t/\\Delta z^2\\le0{,}4')}. Isı ve Archie modelleri literatürdendir;
      kuruma modeli fenomenolojiktir ve WP-2 iklim odası ölçümleriyle kalibre edilecektir.</p>

      <h2 class="sec">Laboratuvar doğrulaması</h2>
      <table class="t">
        <caption>Tablo 1. Deney 1 — <i>Pleurotus ostreatus</i>, İYTE, Mayıs 2026</caption>
        <thead><tr><th>Büyüklük</th><th class="n">Dinlenim</th><th class="n">Ateş stresi</th></tr></thead>
        <tbody>
          <tr><td class="k">Baskın frekans</td><td class="n">20,0 Hz</td><td class="n">4,98 Hz</td></tr>
          <tr><td class="k">En düşük gerilim</td><td class="n">−29,4 mV</td><td class="n">−33,4 mV</td></tr>
          <tr><td class="k">Ortalama gerilim</td><td class="n">−2,90 mV</td><td class="n">−2,94 mV</td></tr>
          <tr><td class="k">Örnek sayısı ${Ki('N')}</td><td class="n">1048</td><td class="n">1085</td></tr>
        </tbody>
      </table>
      <p class="note">Deney 2 toprak/miselyum ağına geçti: iki diferansiyel kanal,
      ${Ki('f_s=100\\,\\mathrm{Hz}')}, 5-katsayılı FIR ${Ki('[0{,}1\\ 0{,}2\\ 0{,}4\\ 0{,}2\\ 0{,}1]')},
      otomatik ofset kalibrasyonu, PGA ${Ki('\\pm6{,}144\\,\\mathrm{V}')}.</p>
      <div class="box"><b>Yöntem uyarısı.</b> Deney 1’de ${Ki('f_s=45\\,\\mathrm{Hz}')} iken
      baskın bileşen 20 Hz’de bulunmuştur — Nyquist sınırının (22,5 Hz) %89’u.
      Anti-aliasing süzgeci olmadan takma-ad riski vardır; bulgunun 100 Hz’de tekrarlanması önerilir.</div>`;
    bindMeas();
  }

  /* ========================================= DONANIM / EKONOMİ (sağ panel) */
  function renderEcon() {
    const p = SIM.powerBudget(A.power);
    $('#econ').innerHTML = `
      <h2 class="sec">Ölçüm zinciri</h2>
      <div id="chain"></div>

      <h2 class="sec">Bileşen seçimi</h2>
      <table class="t cmp">
        <caption>Tablo 2. Seçilen bileşen — elenen alternatif <span class="faint">(donanım raporu §3)</span></caption>
        <thead><tr><th>Alt sistem</th><th>Seçilen</th><th>Alternatif</th></tr></thead>
        <tbody>${D.components.map(c => `<tr data-cid="${c.id}" style="cursor:pointer">
          <td class="k">${c.subsystem}</td><td class="g">${c.selected}</td>
          <td class="faint">${c.alt}</td></tr>`).join('')}</tbody>
      </table>
      <p class="note">Satıra veya üç boyutlu modeldeki bileşene tıklayınca seçim gerekçesi açılır.</p>

      <h2 class="sec">Güç bütçesi</h2>
      <div class="eq">${K('\\bar I=\\sum_k\\big[D\\,I_k^{\\mathrm{akt}}+(1-D)\\,I_k^{\\mathrm{uyku}}\\big]', true)}</div>
      <div class="ctl"><span class="l">${Ki('D')} — görev döngüsü</span><span class="v" id="l-duty"></span>
        <input type="range" id="i-duty" min="0.02" max="1" step="0.01" value="${A.power.duty}"></div>
      <div class="ctl"><span class="l">Paralel LiFePO₄ hücre</span><span class="v" id="l-cells"></span>
        <input type="range" id="i-cells" min="1" max="4" step="1" value="${A.power.cells}"></div>
      <table class="t"><tbody id="pwr"></tbody></table>
      <div class="box ok" id="pverify"></div>

      <h2 class="sec">Maliyet</h2>
      <div class="ctl"><span class="l">Ölçüm noktası sayısı</span><span class="v" id="l-nodes"></span>
        <input type="range" id="i-nodes" min="4" max="600" step="4" value="${A.cost.nodes}"></div>
      <div class="ctl"><span class="l">USD/TL kuru</span><span class="v" id="l-fx"></span>
        <input type="range" id="i-fx" min="30" max="90" step="0.5" value="${A.cost.fx}"></div>
      <table class="t"><tbody id="cst"></tbody></table>
      <p class="note">Fiyatlar tekli/küçük ölçekli tedarik esaslıdır; işçilik, PCB üretim (NRE),
      sertifikasyon ve montaj dahil değildir. 100+ adette %78, 1000+ adette %62 birim fiyat
      varsayılmıştır <i>(varsayım)</i>.</p>

      <h2 class="sec">Program</h2>
      <table class="t wp">
        <caption>Tablo 4. 18 aylık iş paketleri ve bütçe</caption>
        <thead><tr><th>İP</th><th>Konu</th><th class="n">Ay</th><th class="n">TRL</th></tr></thead>
        <tbody>${D.roadmap.map(r => `<tr><td>${r.id}</td><td class="k">${r.title}</td>
          <td class="n">${r.m0}–${r.m1}</td><td class="n">${r.trl}</td></tr>`).join('')}</tbody>
      </table>
      <table class="t"><tbody>
        ${D.budget.map(b => `<tr><td class="k">${b.cat}</td><td class="n">${nf(b.tl)} TL</td></tr>`).join('')}
        <tr><td class="k"><b>Toplam</b></td><td class="n"><b>${nf(D.budgetTotal)} TL</b></td></tr>
      </tbody></table>

      <h2 class="sec">Belge tutarlılığı</h2>
      <table class="t disc">
        <caption>Tablo 5. Kaynak belgeler arasında tespit edilen farklar</caption>
        <tbody>${D.discrepancies.map((d, i) => `<tr><td class="k">${i + 1}. ${d.t}</td>
          <td class="faint" style="font-size:12px">${d.v}</td></tr>`).join('')}</tbody>
      </table>

      <h2 class="sec">Ekip ve kaynak</h2>
      <table class="t"><tbody>
        ${D.team.map(t => `<tr><td class="k">${t.name}</td><td class="faint">${t.role.replace('Kurucu · ', '')}</td></tr>`).join('')}
      </tbody></table>
      <p class="note">${D.project.institution} · ${D.commercial.vehicle}.
      Kaynak belgeler: <a href="../hardware/MycelliumAegis_Donanim_Raporu.pdf">donanım raporu</a>,
      <a href="../experiments/">deney raporları</a>, <a href="../research/">bilimsel değerlendirme</a>,
      <a href="../business-plan/">iş planı</a>.</p>`;
    renderChain();
    bindEcon();
    refreshPower();
    refreshCost();
  }

  /* ---------------------------------------- ölçüm zinciri (SVG, Şekil 2') */
  function renderChain() {
    const nodes = [
      ['electrode', 'elektrot', '316L+grafit'],
      ['opa333', 'OPA333', 'buffer'],
      ['ads1115', 'ADS1115', '16-bit'],
      ['stm32l4', 'STM32L4', 'MCU'],
      ['max3485', 'MAX3485', 'RS485'],
      ['lora', 'E220', 'LoRa']
    ];
    const W = 300, bw = 42, gap = (W - 12 - nodes.length * bw) / (nodes.length - 1), y = 16, h = 32;
    $('#chain').innerHTML = `<svg viewBox="0 0 ${W} 62" style="width:100%;height:auto">
      <defs><marker id="ar" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto">
        <path d="M0 0L8 4L0 8z" fill="#4a5359"/></marker></defs>
      ${nodes.map((n, i) => {
        const x = 6 + i * (bw + gap);
        return `<g class="cb" data-cid="${n[0]}" style="cursor:pointer">
          <rect x="${x}" y="${y}" width="${bw}" height="${h}" fill="#f7f8f9" stroke="#4a5359" stroke-width=".8"/>
          <text x="${x + bw / 2}" y="${y + 13}" text-anchor="middle" font-family="CMU Serif,serif" font-size="9" fill="#14181c">${n[1]}</text>
          <text x="${x + bw / 2}" y="${y + 24}" text-anchor="middle" font-family="CMU Serif,serif" font-size="7.5" fill="#7b858c">${n[2]}</text>
        </g>` + (i < nodes.length - 1
          ? `<line x1="${x + bw}" y1="${y + h / 2}" x2="${x + bw + gap - 2}" y2="${y + h / 2}" stroke="#4a5359" stroke-width=".8" marker-end="url(#ar)"/>` : '');
      }).join('')}
      <text x="6" y="10" font-family="CMU Serif,serif" font-size="8" fill="#7b858c">mV analog</text>
      <text x="${W - 6}" y="10" text-anchor="end" font-family="CMU Serif,serif" font-size="8" fill="#7b858c">868 MHz</text>
      <text x="${W / 2}" y="58" text-anchor="middle" font-family="CMU Serif,serif" font-size="8" fill="#7b858c" font-style="italic">3,3 V ortak besleme — TPS63020 buck-boost</text>
    </svg>`;
    $$('#chain .cb').forEach(g => g.addEventListener('click', () => inspect(g.dataset.cid)));
  }

  /* ================================================================ HUD == */
  function renderGate() {
    const w = A.world, c = w.cond || { c1: 0, c2: 0, c3: 0, f: 0, fThr: 0 };
    const alarm = w.state === 'YANGIN BAŞLANGICI';
    const al = alarm ? ' al' : '';
    const lt = w.leadTime();
    $('#gate').innerHTML = `<div class="gate">
      <div class="row">
        <span class="st" style="color:${alarm ? 'var(--red)' : w.state === 'KURAKLIK' ? 'var(--amber)' : 'var(--green)'}">${w.state.toLowerCase()}</span>
        <span class="lt">${lt != null
          ? 'öncü süre ' + (lt > 0 ? '+' : '−') + dur(Math.abs(lt))
          : SIM.SCENARIOS[w.scenario].tag}</span>
      </div>
      <div class="conds">
        <div class="cond${c.c1 ? ' on' + al : ''}">
          <div class="lbl">${Ki('dT/dt')}</div>
          <div class="v">${(w.dTdt * 600).toFixed(2)}</div>
          <div class="th">${Ki('\\beta=' + w.p.beta.toFixed(2))} °C/10dk</div></div>
        <div class="cond${c.c2 ? ' on' + al : ''}">
          <div class="lbl">${Ki('d\\ln R/dt')}</div>
          <div class="v">${(w.dlnRdt * 60).toFixed(4)}</div>
          <div class="th">${Ki('\\gamma=' + w.p.gamma.toFixed(4))} dk⁻¹</div></div>
        <div class="cond${c.c3 ? ' on' + al : ''}">
          <div class="lbl">${Ki('f_{\\mathrm{spike}}')}</div>
          <div class="v">${c.f.toFixed(2)}</div>
          <div class="th">eşik ${c.fThr.toFixed(2)} Hz</div></div>
      </div>
    </div>`;
  }

  function renderLive() {
    const w = A.world, sc = SIM.SCENARIOS[w.scenario];
    const rows = [
      ['Senaryo', sc.label],
      ['Yüzey sıcaklığı ' + Ki('T_s'), sc.surfT(w.t, w.p).toFixed(1) + ' °C'],
      ['Prob sıcaklığı ' + Ki('T(z_p)'), w.Tz().toFixed(2) + ' °C'],
      ['Elektrot sıcaklığı ' + Ki('T(z_e)'), w.Tz(w.p.depth).toFixed(2) + ' °C'],
      ['Su içeriği ' + Ki('\\theta'), w.thetaZ().toFixed(4) + ' m³/m³'],
      ['Elektrot direnci ' + Ki('R'), nf(w.resistance() / 1000, 2) + ' kΩ'],
      ['Ağ stresi ' + Ki('s'), (w.stress * 100).toFixed(0) + ' %'],
      ['Baskın frekans ' + Ki('f_{\\mathrm{dom}}'), w.fDom.toFixed(2) + ' Hz'],
      [Ki('\\beta') + ' ilk geçişi', w.first.c1 != null ? hms(w.first.c1) : 'hiç'],
      [Ki('\\gamma') + ' ilk geçişi', w.first.c2 != null ? hms(w.first.c2) : 'hiç'],
      ['Spike ilk geçişi', w.first.c3 != null ? hms(w.first.c3) : 'hiç'],
      ['Alarm', w.alarmAt != null ? hms(w.alarmAt) : '—'],
      ['Tutuşma', w.igniteAt != null ? hms(w.igniteAt) : '—']
    ];
    $('#live').innerHTML = rows.map((r, i) =>
      `<tr${i >= 11 && w.alarmAt != null ? ' class="hi"' : ''}><td class="k">${r[0]}</td><td class="n">${r[1]}</td></tr>`).join('');
  }

  /* ============================================================ GRAFİKLER */
  function chart(id) {
    const c = document.getElementById(id);
    if (!c) return null;
    if (!A.charts[id]) A.charts[id] = new CH.Chart(c, { pad: [10, 10, 20, 38], font: '10px "CMU Serif", serif' });
    return A.charts[id];
  }
  const setRd = (id, t) => { const e = $('#rd-' + id); if (e) e.innerHTML = t; };
  const setFl = (id, t) => { const e = $('#fl-' + id); if (e) e.innerHTML = t; };

  function drawScope() {
    const ch = chart('scope'); if (!ch) return;
    const d = A.world.scope; ch.clear();
    if (!d.length) return;
    let lo = 1e9, hi = -1e9;
    for (const v of d) { if (v < lo) lo = v; if (v > hi) hi = v; }
    lo = Math.min(-36, Math.floor(lo / 5) * 5); hi = Math.max(6, Math.ceil(hi / 5) * 5);
    ch.frame([0, d.length / SIM.FS], [lo, hi], { ny: 4, nx: 4, dy: 0, fx: v => v.toFixed(1) });
    ch.hline(-29.4, CH.PAL().faint2, 'Deney 1 dinlenim −29,4', [3, 3], { align: 'right', dy: -1 });
    ch.hline(-33.4, CH.PAL().warn, 'Deney 1 stres −33,4', [3, 3], { align: 'left', dy: 11 });
    ch.line(d.map((v, i) => [i / SIM.FS, v]), A.world.stress > 0.35 ? CH.PAL().warn : CH.PAL().accent, 1.1);
    setRd('scope', 'V<sub>min</sub> ' + Math.min.apply(null, d).toFixed(1) + ' mV');
    setFl('scope', 'Gerilim (mV) — zaman (s) · f<sub>s</sub> = 100 Hz · yatay çizgiler Deney 1 uçları');
  }

  function drawFFT() {
    const ch = chart('fft'); if (!ch) return;
    const m = A.world.mag; ch.clear();
    const nB = Math.min(m.length, Math.floor(40 / (SIM.FS / SIM.FFT_N)));
    let mx = 1e-6; for (let i = 2; i < nB; i++) mx = Math.max(mx, m[i]);
    ch.frame([0, 40], [0, mx * 1.12], { ny: 3, nx: 8, dy: 1, fy: v => v.toFixed(1) });
    ch.vband(3.5, 6.5, 'rgba(154,100,16,.10)');
    ch.vband(17, 23, 'rgba(27,79,156,.09)');
    const pts = [];
    for (let i = 1; i < nB; i++) pts.push([i * SIM.FS / SIM.FFT_N, m[i]]);
    ch.bars(pts, CH.PAL().accent, (p) => p[0] > 3.5 && p[0] < 6.5 ? CH.PAL().warn
      : p[0] > 17 && p[0] < 23 ? CH.PAL().cool : 'rgba(15,107,74,.55)');
    ch.vline(20, CH.PAL().cool, '20 Hz');
    ch.vline(4.98, CH.PAL().warn, '4,98 Hz');
    setRd('fft', 'f<sub>dom</sub> ' + A.world.fDom.toFixed(2) + ' Hz');
    setFl('fft', '|X(f)| (mV) — frekans (Hz) · Hann, N = 512 · <span class="b">mavi</span> dinlenim bandı, <span class="a">turuncu</span> stres bandı');
  }

  function drawProfile() {
    const ch = chart('prof'); if (!ch) return;
    const w = A.world, p = w.profile(); ch.clear();
    const tMax = Math.max(45, Math.ceil(Math.max.apply(null, p.T) / 50) * 50);
    ch.frame([0, tMax], [0.6, 0], { ny: 6, nx: 4, fy: v => (v * 100).toFixed(0), fx: v => v.toFixed(0) });
    ch.band(0.15, 0.20, 'rgba(26,127,90,.10)');
    ch.line(p.z.map((z, i) => [p.T[i], z]), CH.PAL().danger, 1.7);
    ch.line(p.z.map((z, i) => [p.th[i] / 0.35 * tMax, z]), CH.PAL().cool, 1.3);
    ch.hline(w.p.depth, CH.PAL().accent, 'z_e', [2, 3], { align: 'right', dy: -2 });
    ch.hline(w.p.probe, CH.PAL().warn, 'z_p', [2, 3], { align: 'left', dy: 11 });
    setRd('prof', 'T(z<sub>p</sub>) ' + w.Tz().toFixed(1) + ' °C');
    setFl('prof', 'Derinlik (cm) — <span class="r">T(z) °C</span> ve <span class="b">θ(z)</span> · yeşil bant 15–20 cm güvenli bölge');
  }

  function drawTimeline() {
    const ch = chart('tline'); if (!ch) return;
    const w = A.world, h = w.hist; ch.clear();
    if (h.length < 2) return;
    const t0 = h[0].t / 3600, t1 = Math.max(h[h.length - 1].t / 3600, t0 + 0.5);
    const bMax = Math.max(w.p.beta * 2.2, ...h.map(r => r.dTdt * 600));
    const gMax = Math.max(w.p.gamma * 2.2, ...h.map(r => r.dlnRdt * 60));
    ch.frame([t0, t1], [-0.15, 1.35], { ny: 3, nx: 5, dy: 1, fy: v => v.toFixed(1), fx: v => v.toFixed(1) });
    ch.line(h.map(r => [r.t / 3600, clamp(r.dTdt * 600 / bMax, -0.1, 1.3)]), CH.PAL().danger, 1.4);
    ch.line(h.map(r => [r.t / 3600, clamp(r.dlnRdt * 60 / gMax, -0.1, 1.3)]), CH.PAL().cool, 1.4);
    ch.hline(w.p.beta / bMax, CH.PAL().danger, 'β', [3, 3]);
    ch.hline(w.p.gamma / gMax, CH.PAL().cool, 'γ', [3, 3], { align: 'left', dy: 11 });
    if (w.igniteAt != null) ch.vline(w.igniteAt / 3600, CH.PAL().warn, 'tutuşma', [3, 3], { align: 'right', dy: 0 });
    if (w.alarmAt != null) ch.vline(w.alarmAt / 3600, CH.PAL().accent, 'alarm', [3, 3], { align: 'left', dy: 12 });
    const lt = w.leadTime();
    setRd('tline', lt != null ? (lt > 0 ? '+' : '−') + dur(Math.abs(lt)) : '');
    setFl('tline', 'Eşiğe göre normalize — <span class="r">dT/dt ÷ β</span>, <span class="b">d ln R/dt ÷ γ</span> · zaman (sa)');
  }

  /* ============================================================= TAZELEME */
  function refreshLabels() {
    const w = A.world;
    $('#l-probe').textContent = (w.p.probe * 100).toFixed(0) + ' cm';
    $('#l-depth').textContent = (w.p.depth * 100).toFixed(0) + ' cm';
    $('#l-beta').textContent = w.p.beta.toFixed(2) + ' °C/10dk';
    $('#l-gamma').textContent = w.p.gamma.toFixed(4) + ' dk⁻¹';
    $('#l-th').textContent = w.p.theta0.toFixed(2) + ' m³/m³';
    const deep = w.p.probe >= 0.14;
    $('#finding').className = 'box' + (deep ? '' : ' ok');
    $('#finding').innerHTML = deep
      ? `<b>Bu ikizin bulgusu.</b> Prob belgede olduğu gibi biyoelektrotla aynı derinlikte
         (${(w.p.probe * 100).toFixed(0)} cm) iken ısıl cephe oraya tutuşmadan sonra varır;
         ${Ki('\\beta')} koşulu erken uyarı üretemez. 15–20 cm miselyumun <i>hayatta kalma</i>
         derinliğidir, ısının <i>tespit</i> derinliği değil. Probu 5–8 cm’e çekin.`
      : `<b>Önerilen yapılandırma.</b> Biyoelektrot 18 cm’de (miselyum orada yaşar), T/R probu
         aynı kablo üzerinde ${(w.p.probe * 100).toFixed(0)} cm’de. ADS1115’in dört kanalından
         ikisi zaten boş; ek maliyet bir termistör ve bir elektrot çifti (&lt; 3 USD).`;
  }

  function refreshPower() {
    const p = SIM.powerBudget(A.power), ref = D.powerReference.duty50;
    $('#l-duty').textContent = '%' + (A.power.duty * 100).toFixed(0);
    $('#l-cells').textContent = A.power.cells + ' × 6000 mAh';
    $('#pwr').innerHTML = `
      <tr><td class="k">Yeraltı düğümü ${Ki('\\bar I_u')}</td><td class="n">${p.under.toFixed(2)} mA</td></tr>
      <tr><td class="k">Yüzey düğümü ${Ki('\\bar I_s')}</td><td class="n">${p.surf.toFixed(2)} mA</td></tr>
      <tr class="hi"><td class="k">Toplam ${Ki('\\bar I')}</td><td class="n">${p.total.toFixed(2)} mA</td></tr>
      <tr><td class="k">Batarya ömrü — ideal</td><td class="n">${p.weeksIdeal.toFixed(1)} hafta</td></tr>
      <tr><td class="k">Batarya ömrü — muhafazakâr</td><td class="n">${p.weeksCons.toFixed(1)} hafta</td></tr>
      <tr><td class="k">Günlük hasat / tüketim</td><td class="n">${nf(p.mAhIn, 0)} / ${nf(p.mAhOut, 0)} mAh</td></tr>`;
    const at50 = Math.abs(A.power.duty - 0.5) < 0.005 && A.power.cells === 1;
    const v = $('#pverify');
    v.className = at50 ? 'box ok' : 'box';
    v.innerHTML = at50
      ? `<b>Rapor doğrulandı.</b> ${p.under.toFixed(2)} / ${p.surf.toFixed(2)} / ${p.total.toFixed(2)} mA
         ve ${p.weeksIdeal.toFixed(1)} / ${p.weeksCons.toFixed(1)} hafta — donanım raporu §5.1’de beyan
         edilen ${ref.under} / ${ref.surf} / ${ref.total} mA ve ${ref.weeksIdeal} / ${ref.weeksCons} hafta ile aynı.`
      : `<b>Rapor dışı çalışma noktası.</b> ${Ki('D=' + A.power.duty.toFixed(2))} ·
         ${A.power.cells} hücre → ${p.total.toFixed(2)} mA, ${p.weeksCons.toFixed(1)} hafta (muhafazakâr).
         %10 görev döngüsü 27–34 hafta verir; olay-tetikli adaptif duty-cycle her iki hedefi karşılar.`;
  }

  function refreshCost() {
    const c = SIM.costModel(A.cost), fx = A.cost.fx;
    $('#l-nodes').textContent = A.cost.nodes + ' düğüm';
    $('#l-fx').textContent = fx.toFixed(1) + ' TL/USD';
    $('#cst').innerHTML = `
      <tr><td class="k">Düğüm çifti (yeraltı + yüzey)</td><td class="n">${c.perNodeUsd.toFixed(1)} USD · ${nf(c.perNodeUsd * fx, 0)} TL</td></tr>
      <tr><td class="k">Merkez kule / gateway</td><td class="n">${c.gwUsd.toFixed(0)} USD · ${nf(c.gwUsd * fx, 0)} TL</td></tr>
      <tr><td class="k">Gateway sayısı</td><td class="n">${c.gws}</td></tr>
      <tr class="hi"><td class="k">Toplam yatırım</td><td class="n">${nf(c.capexUsd, 0)} USD · ${nf(c.capexTl, 0)} TL</td></tr>
      <tr><td class="k">Malzeme bütçesiyle (119.000 TL)</td><td class="n">${Math.floor(119000 / (c.perNodeUsd * fx))} düğüm çifti</td></tr>`;
  }

  /* --------------------------------------------------------- bileşen kartı */
  function inspect(cid) {
    const c = D.components.find(x => x.id === cid);
    const el = $('#insp');
    if (!c) { el.style.display = 'none'; return; }
    el.innerHTML = `<h4>${c.subsystem}<button id="ix">kapat ✕</button></h4>
      <p><b>${c.selected}</b> — <i>${c.detail}</i></p>
      <p class="dim">Elenen alternatif: ${c.alt}</p>
      <p>${c.why}</p>
      ${c.note ? `<p class="dim" style="border-left:2px solid var(--rule-2);padding-left:7px">${c.note}</p>` : ''}
      ${c.risk ? `<p class="a">⚠ ${c.risk}</p>` : ''}
      ${c.usd ? `<dl class="kv"><dt>Birim fiyat</dt><dd>${c.usd.toFixed(1)} USD${c.qty > 1 ? ' × ' + c.qty : ''}</dd>
        <dt>TL karşılığı</dt><dd>${nf(c.usd * c.qty * A.cost.fx, 0)} TL</dd></dl>` : ''}`;
    el.style.display = 'block';
    $('#ix').addEventListener('click', () => { el.style.display = 'none'; });
  }

  /* =============================================================== BAĞLA = */
  function bindMeas() {
    const w = A.world;
    const bind = (sel, fn) => { const e = $(sel); if (e) e.addEventListener('input', () => { fn(parseFloat(e.value)); refreshLabels(); }); };
    bind('#i-probe', v => w.setProbe(v));
    bind('#i-depth', v => w.p.depth = v);
    bind('#i-beta', v => w.p.beta = v);
    bind('#i-gamma', v => w.p.gamma = v);
    bind('#i-th', v => { w.p.theta0 = v; w.reset(); });
    refreshLabels();
  }

  function bindEcon() {
    $$('#econ tr[data-cid]').forEach(tr => tr.addEventListener('click', () => inspect(tr.dataset.cid)));
    const b = (sel, key, fn) => { const e = $(sel); if (e) e.addEventListener('input', () => { A[key][e.dataset.k] = parseFloat(e.value); fn(); }); };
    $('#i-duty').dataset.k = 'duty'; $('#i-cells').dataset.k = 'cells';
    $('#i-nodes').dataset.k = 'nodes'; $('#i-fx').dataset.k = 'fx';
    b('#i-duty', 'power', refreshPower);
    b('#i-cells', 'power', refreshPower);
    b('#i-nodes', 'cost', refreshCost);
    b('#i-fx', 'cost', () => { refreshCost(); });
  }

  function setView(v) {
    A.view = v;
    SC.setView(v, SC.VIEWS[v].mode !== SC.mode);
    $$('#bar [data-v]').forEach(b => b.classList.toggle('on', b.dataset.v === v));
    $('#viewcap').innerHTML = VIEWCAP[v] || '';
  }

  /* =============================================================== DÖNGÜ = */
  let last = performance.now(), acc = 0;
  function loop(now) {
    /* Çizim adımı (kamera yumuşatma) ile benzetim adımı ayrıdır: ağır bir
       karede benzetim yavaşlamasın diye benzetim duvar saatini kullanır.     */
    const real = (now - last) / 1000; last = now;
    const dt = Math.min(0.05, real);
    if (A.playing) {
      let s = Math.min(0.3, real) * A.speed;
      while (s > 0) { const step = Math.min(120, s); A.world.advance(step); s -= step; }
    }
    const w = A.world, sc = SIM.SCENARIOS[w.scenario];
    const surf = sc.surfT(w.t, w.p);
    const alarm = w.state === 'YANGIN BAŞLANGICI';
    SC.update(dt, { world: w, fireIntensity: clamp((surf - 60) / 500, 0, 1), alarm });

    acc += dt;
    if (acc > 0.1) {
      acc = 0;
      renderGate(); renderLive();
      drawScope(); drawFFT(); drawProfile(); drawTimeline();
      $('#clk').textContent = hms(w.t);
      const st = $('#state');
      st.textContent = w.state.toLowerCase();
      st.className = 'badge ' + (alarm ? 'al' : w.state === 'KURAKLIK' ? 'dr' : 'on');
      $('#env').innerHTML = `T<sub>s</sub> ${surf.toFixed(0)} °C · T(z<sub>p</sub>) ${w.Tz().toFixed(1)} °C · θ ${w.thetaZ().toFixed(3)} · R ${(w.resistance() / 1000).toFixed(1)} kΩ`;
    }
    requestAnimationFrame(loop);
  }

  /* =============================================================== BAŞLAT */
  function boot() {
    const steps = [['veri katmanı', 14], ['yordamsal dokular', 42], ['miselyum ağı', 66],
                   ['ortam aydınlatması', 86], ['hazır', 100]];
    let i = 0;
    (function tick() {
      if (i >= steps.length) return;
      $('#boot .bar i').style.transform = `scaleX(${steps[i][1] / 100})`;
      $('#boot .st').textContent = steps[i][0];
      i++; setTimeout(tick, 220);
    })();

    renderMeas();
    renderEcon();
    SC.init($('#gl'));
    SC.bindInput($('#gl'), inspect);
    SC.setGrowth(0);
    setView('sub');

    const t0 = performance.now();
    (function grow() {
      const u = clamp((performance.now() - t0) / 3200, 0, 1);
      SC.setGrowth(u * u * (3 - 2 * u));
      if (u < 1) requestAnimationFrame(grow);
    })();

    requestAnimationFrame(loop);
    setTimeout(() => $('#boot').classList.add('gone'), 1300);

    $$('#bar [data-v]').forEach(b => b.addEventListener('click', () => setView(b.dataset.v)));
    $$('#bar [data-sc]').forEach(b => b.addEventListener('click', () => {
      A.world.setScenario(b.dataset.sc);
      $$('#bar [data-sc]').forEach(x => x.classList.toggle('on', x === b));
      refreshLabels();
    }));
    $('#play').addEventListener('click', (e) => {
      A.playing = !A.playing;
      e.currentTarget.textContent = A.playing ? 'durdur' : 'devam';
      e.currentTarget.classList.toggle('on', !A.playing);
    });
    $('#rst').addEventListener('click', () => A.world.reset());
    $('#spd').addEventListener('click', (e) => {
      const arr = [30, 60, 120, 300, 600, 1200];
      A.speed = arr[(arr.indexOf(A.speed) + 1) % arr.length];
      e.currentTarget.textContent = A.speed + '×';
    });

    window.addEventListener('keydown', (e) => {
      if (e.target.tagName === 'INPUT') return;
      if (e.key === ' ') { e.preventDefault(); $('#play').click(); }
      else if (e.key.toLowerCase() === 'r') A.world.reset();
      else if (['1', '2', '3', '4'].includes(e.key)) {
        const b = $$('#bar [data-sc]')[+e.key - 1]; if (b) b.click();
      } else if (e.key === 'Escape') $('#insp').style.display = 'none';
    });

    let rt;
    window.addEventListener('resize', () => {
      clearTimeout(rt);
      rt = setTimeout(() => { SC.resize(); Object.values(A.charts).forEach(c => c.resize()); }, 120);
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();
})();
