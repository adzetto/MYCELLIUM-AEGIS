/* =============================================================================
   MYCELLIUM-AEGIS · SAYISAL İKİZ
   textures.js — Yordamsal (procedural) PBR doku üretimi
   -----------------------------------------------------------------------------
   Harici görsel dosyası kullanmadan, canvas üzerinde albedo / normal / pürüzlülük
   haritaları üretir. Tüm dokular MirroredRepeatWrapping ile dikişsiz döşenir.
   ============================================================================= */
(function (global) {
  'use strict';
  const T = global.THREE;

  /* ------------------------------------------------------------ gürültü --- */
  function mulberry(seed) {
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  function makeGrid(n, rnd) {
    const g = new Float32Array(n * n);
    for (let i = 0; i < n * n; i++) g[i] = rnd();
    return g;
  }
  const smooth = (t) => t * t * (3 - 2 * t);
  /* periyodik değer gürültüsü — kenarlarda dikiş yok */
  function pnoise(g, n, x, y) {
    const xi = Math.floor(x), yi = Math.floor(y);
    const xf = x - xi, yf = y - yi;
    const i0 = ((xi % n) + n) % n, j0 = ((yi % n) + n) % n;
    const i1 = (i0 + 1) % n, j1 = (j0 + 1) % n;
    const u = smooth(xf), v = smooth(yf);
    const a = g[j0 * n + i0], b = g[j0 * n + i1], c = g[j1 * n + i0], d = g[j1 * n + i1];
    return (a * (1 - u) + b * u) * (1 - v) + (c * (1 - u) + d * u) * v;
  }
  function fbmFactory(seed, base) {
    const grids = [], sizes = [];
    const rnd = mulberry(seed);
    for (let o = 0; o < 5; o++) { const n = base * (1 << o); sizes.push(n); grids.push(makeGrid(n, rnd)); }
    return function (u, v, oct) {
      let s = 0, a = 0.5, tot = 0;
      const O = oct || 5;
      for (let o = 0; o < O; o++) {
        s += a * pnoise(grids[o], sizes[o], u * sizes[o], v * sizes[o]);
        tot += a; a *= 0.5;
      }
      return s / tot;
    };
  }

  /* ---------------------------------------------- yükseklik → normal harita */
  function normalFromHeight(h, S, strength) {
    const c = document.createElement('canvas'); c.width = c.height = S;
    const ctx = c.getContext('2d'), img = ctx.createImageData(S, S), d = img.data;
    const at = (i, j) => h[((j % S) + S) % S * S + (((i % S) + S) % S)];
    for (let j = 0; j < S; j++) {
      for (let i = 0; i < S; i++) {
        const dx = (at(i + 1, j) - at(i - 1, j)) * strength;
        const dy = (at(i, j + 1) - at(i, j - 1)) * strength;
        let nx = -dx, ny = -dy, nz = 1;
        const l = Math.hypot(nx, ny, nz); nx /= l; ny /= l; nz /= l;
        const k = (j * S + i) * 4;
        d[k] = (nx * 0.5 + 0.5) * 255;
        d[k + 1] = (ny * 0.5 + 0.5) * 255;
        d[k + 2] = (nz * 0.5 + 0.5) * 255;
        d[k + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    return c;
  }

  function tex(canvas, repeat, srgb) {
    const t = new T.CanvasTexture(canvas);
    t.wrapS = t.wrapT = T.MirroredRepeatWrapping;
    if (repeat) t.repeat.set(repeat[0], repeat[1]);
    if (srgb) t.colorSpace = T.SRGBColorSpace;
    t.anisotropy = 8;
    t.needsUpdate = true;
    return t;
  }

  /* ================================================================ TOPRAK = */
  /* Her toprak horizonu için albedo + normal + pürüzlülük seti üretir.
     Parametreler horizona göre değişir: üst katmanlar organik ve koyu,
     alt katmanlar mineral, killi ve daha düzgün.                            */
  function soil(opts) {
    const S = 512;
    const o = Object.assign({
      base: [0x7a, 0x5f, 0x3c], seed: 7, grain: 0.42, organic: 0.25,
      pebbles: 46, pebbleR: [2.5, 9], roughBase: 0.94, dark: 0.35
    }, opts);

    const f1 = fbmFactory(o.seed, 4);
    const f2 = fbmFactory(o.seed + 101, 16);
    const f3 = fbmFactory(o.seed + 202, 48);

    const alb = document.createElement('canvas'); alb.width = alb.height = S;
    const ac = alb.getContext('2d');
    const img = ac.createImageData(S, S), d = img.data;
    const hgt = new Float32Array(S * S);
    const rgh = document.createElement('canvas'); rgh.width = rgh.height = S;
    const rc = rgh.getContext('2d');
    const rimg = rc.createImageData(S, S), rd = rimg.data;

    for (let j = 0; j < S; j++) {
      for (let i = 0; i < S; i++) {
        const u = i / S, v = j / S;
        const n1 = f1(u, v), n2 = f2(u, v), n3 = f3(u, v, 3);
        // katman katman renk kırılması
        const m = (n1 - 0.5) * o.grain + (n2 - 0.5) * o.grain * 0.65 + (n3 - 0.5) * 0.18;
        const org = Math.max(0, n2 - 0.62) * o.organic * 4;   // koyu organik lekeler
        const k = (j * S + i) * 4;
        const shade = 1 + m - org * o.dark;
        d[k]     = Math.max(0, Math.min(255, o.base[0] * shade));
        d[k + 1] = Math.max(0, Math.min(255, o.base[1] * shade * (1 - org * 0.12)));
        d[k + 2] = Math.max(0, Math.min(255, o.base[2] * shade * (1 - org * 0.2)));
        d[k + 3] = 255;
        hgt[j * S + i] = n1 * 0.55 + n2 * 0.3 + n3 * 0.15;
        const rv = Math.max(0, Math.min(1, o.roughBase + (n3 - 0.5) * 0.25 - org * 0.12));
        rd[k] = rd[k + 1] = rd[k + 2] = rv * 255; rd[k + 3] = 255;
      }
    }
    ac.putImageData(img, 0, 0);
    rc.putImageData(rimg, 0, 0);

    /* çakıl taşları — albedo ve yükseklik alanına birlikte işlenir */
    const rnd = mulberry(o.seed * 31 + 5);
    for (let p = 0; p < o.pebbles; p++) {
      const px = rnd() * S, py = rnd() * S;
      const pr = o.pebbleR[0] + rnd() * (o.pebbleR[1] - o.pebbleR[0]);
      const tone = 96 + rnd() * 52;
      const g = ac.createRadialGradient(px - pr * 0.3, py - pr * 0.35, pr * 0.1, px, py, pr);
      g.addColorStop(0, `rgba(${tone + 30},${tone + 24},${tone + 12},.72)`);
      g.addColorStop(0.65, `rgba(${tone},${tone - 6},${tone - 16},.66)`);
      g.addColorStop(1, `rgba(${tone * 0.5},${tone * 0.46},${tone * 0.4},0)`);
      ac.fillStyle = g;
      ac.beginPath(); ac.ellipse(px, py, pr, pr * (0.7 + rnd() * 0.4), rnd() * 6.28, 0, 6.28); ac.fill();
      for (let j = -pr | 0; j <= pr; j++) for (let i = -pr | 0; i <= pr; i++) {
        const dd = Math.hypot(i, j); if (dd > pr) continue;
        const ii = ((px + i) | 0) % S, jj = ((py + j) | 0) % S;
        const idx = ((jj % S) + S) % S * S + (((ii % S) + S) % S);
        hgt[idx] = Math.min(1, hgt[idx] + Math.cos(dd / pr * 1.57) * 0.55);
      }
    }

    return {
      map: tex(alb, [1, 1], true),
      normalMap: tex(normalFromHeight(hgt, S, 3.0), [1, 1], false),
      roughnessMap: tex(rgh, [1, 1], false)
    };
  }

  /* ============================================================== YAPRAK ÖRTÜSÜ */
  function litter(seed) {
    const S = 512;
    const c = document.createElement('canvas'); c.width = c.height = S;
    const x = c.getContext('2d');
    const f = fbmFactory(seed || 33, 8);
    const img = x.createImageData(S, S), d = img.data;
    const hgt = new Float32Array(S * S);
    for (let j = 0; j < S; j++) for (let i = 0; i < S; i++) {
      const n = f(i / S, j / S);
      const k = (j * S + i) * 4;
      d[k] = 74 + n * 62; d[k + 1] = 76 + n * 54; d[k + 2] = 44 + n * 34; d[k + 3] = 255;
      hgt[j * S + i] = n;
    }
    x.putImageData(img, 0, 0);
    /* iğne yapraklar ve kırık dallar */
    const rnd = mulberry((seed || 33) * 7 + 3);
    for (let n = 0; n < 900; n++) {
      const px = rnd() * S, py = rnd() * S, a = rnd() * 6.283, len = 5 + rnd() * 22;
      const t = rnd();
      x.strokeStyle = t < 0.45 ? `rgba(${96 + rnd() * 40},${74 + rnd() * 30},${40 + rnd() * 22},.72)`
                    : t < 0.8 ? `rgba(${64 + rnd() * 30},${78 + rnd() * 34},${38 + rnd() * 20},.6)`
                              : `rgba(${132 + rnd() * 40},${112 + rnd() * 30},${72 + rnd() * 24},.55)`;
      x.lineWidth = 0.8 + rnd() * 1.9;
      x.beginPath(); x.moveTo(px, py);
      x.quadraticCurveTo(px + Math.cos(a) * len * 0.5 + rnd() * 4 - 2, py + Math.sin(a) * len * 0.5,
                         px + Math.cos(a) * len, py + Math.sin(a) * len);
      x.stroke();
      const ix = px | 0, iy = py | 0;
      for (let s = 0; s < len; s++) {
        const jj = ((iy + (Math.sin(a) * s) | 0) % S + S) % S, ii = (((ix + (Math.cos(a) * s) | 0) % S) + S) % S;
        hgt[jj * S + ii] = Math.min(1, hgt[jj * S + ii] + 0.4);
      }
    }
    return { map: tex(c, [1, 1], true), normalMap: tex(normalFromHeight(hgt, S, 2.2), [1, 1], false) };
  }

  /* =================================================================== PCB = */
  function pcb() {
    const S = 512;
    const c = document.createElement('canvas'); c.width = c.height = S;
    const x = c.getContext('2d');
    x.fillStyle = '#0d4535'; x.fillRect(0, 0, S, S);
    // lehim maskesi dokusu
    const f = fbmFactory(5, 16);
    for (let j = 0; j < S; j += 2) for (let i = 0; i < S; i += 2) {
      const n = f(i / S, j / S, 3);
      x.fillStyle = `rgba(255,255,255,${(n - 0.5) * 0.055})`;
      x.fillRect(i, j, 2, 2);
    }
    // bakır izler
    const rnd = mulberry(91);
    x.lineCap = 'square'; x.lineJoin = 'miter';
    for (let n = 0; n < 60; n++) {
      x.strokeStyle = rnd() < 0.5 ? 'rgba(196,158,74,.55)' : 'rgba(168,134,60,.42)';
      x.lineWidth = 1.6 + rnd() * 3.4;
      let px = rnd() * S, py = rnd() * S;
      x.beginPath(); x.moveTo(px, py);
      for (let s = 0; s < 4 + (rnd() * 5 | 0); s++) {
        const horiz = rnd() < 0.5, d2 = (rnd() - 0.5) * 190;
        if (horiz) px += d2; else py += d2;
        x.lineTo(px, py);
      }
      x.stroke();
    }
    // via delikleri ve pedler
    for (let n = 0; n < 130; n++) {
      const px = rnd() * S, py = rnd() * S, r = 2.4 + rnd() * 3.6;
      x.fillStyle = '#c8a44e'; x.beginPath(); x.arc(px, py, r, 0, 6.283); x.fill();
      x.fillStyle = '#0a2c22'; x.beginPath(); x.arc(px, py, r * 0.42, 0, 6.283); x.fill();
    }
    // ipek baskı
    x.strokeStyle = 'rgba(232,240,236,.62)'; x.lineWidth = 1.4;
    for (let n = 0; n < 16; n++) {
      const px = rnd() * S, py = rnd() * S, w = 26 + rnd() * 60, h = 18 + rnd() * 40;
      x.strokeRect(px, py, w, h);
    }
    x.fillStyle = 'rgba(232,240,236,.72)';
    x.font = '16px monospace';
    ['MYCELLIUM-AEGIS', 'REV B', 'U1', 'U2', 'U3', 'J1', 'TP4'].forEach((t) => {
      x.fillText(t, rnd() * (S - 140), 24 + rnd() * (S - 40));
    });
    return { map: tex(c, [1, 1], true) };
  }

  /* ======================================================== GÜNEŞ PANELİ === */
  function solar() {
    const S = 512;
    const c = document.createElement('canvas'); c.width = c.height = S;
    const x = c.getContext('2d');
    const g = x.createLinearGradient(0, 0, S, S);
    g.addColorStop(0, '#12244a'); g.addColorStop(0.5, '#0b1730'); g.addColorStop(1, '#16305c');
    x.fillStyle = g; x.fillRect(0, 0, S, S);
    // monokristal hücre dokusu
    const f = fbmFactory(17, 32);
    for (let j = 0; j < S; j += 2) for (let i = 0; i < S; i += 2) {
      const n = f(i / S, j / S, 3);
      x.fillStyle = `rgba(120,170,255,${(n - 0.5) * 0.10})`;
      x.fillRect(i, j, 2, 2);
    }
    const cols = 4, rows = 6, pad = 10;
    const cw = (S - pad * (cols + 1)) / cols, chh = (S - pad * (rows + 1)) / rows;
    for (let r = 0; r < rows; r++) for (let q = 0; q < cols; q++) {
      const px = pad + q * (cw + pad), py = pad + r * (chh + pad);
      x.fillStyle = 'rgba(8,16,34,.55)';
      x.beginPath(); x.roundRect(px, py, cw, chh, 6); x.fill();
      // ince parmak iletkenler
      x.strokeStyle = 'rgba(206,214,226,.42)'; x.lineWidth = 1;
      for (let k = 6; k < chh; k += 7) { x.beginPath(); x.moveTo(px + 3, py + k); x.lineTo(px + cw - 3, py + k); x.stroke(); }
      // toplayıcı barlar
      x.strokeStyle = 'rgba(226,232,240,.78)'; x.lineWidth = 3.2;
      [0.33, 0.67].forEach(t => { x.beginPath(); x.moveTo(px + cw * t, py + 2); x.lineTo(px + cw * t, py + chh - 2); x.stroke(); });
    }
    return { map: tex(c, [1, 1], true) };
  }

  /* ================================================================= KABLO = */
  function cable() {
    const S = 256;
    const c = document.createElement('canvas'); c.width = c.height = S;
    const x = c.getContext('2d');
    x.fillStyle = '#1b1e20'; x.fillRect(0, 0, S, S);
    const h = new Float32Array(S * S);
    x.strokeStyle = 'rgba(58,64,68,.85)'; x.lineWidth = 5;
    for (let k = -S; k < S * 2; k += 13) {
      x.beginPath(); x.moveTo(k, 0); x.lineTo(k + S, S); x.stroke();
      x.beginPath(); x.moveTo(k + S, 0); x.lineTo(k, S); x.stroke();
    }
    for (let j = 0; j < S; j++) for (let i = 0; i < S; i++) {
      h[j * S + i] = (Math.sin((i + j) * 0.48) * 0.5 + Math.sin((i - j) * 0.48) * 0.5) * 0.5 + 0.5;
    }
    return { map: tex(c, [1, 4], true), normalMap: tex(normalFromHeight(h, S, 1.6), [1, 4], false) };
  }

  /* ====================================================== BİYOKOMPOZİT ===== */
  /* Pirinç kabuğu + silika takviyeli miselyum kompozit muhafaza yüzeyi       */
  function biocomposite() {
    const S = 512;
    const c = document.createElement('canvas'); c.width = c.height = S;
    const x = c.getContext('2d');
    const f = fbmFactory(43, 8);
    const img = x.createImageData(S, S), d = img.data;
    const h = new Float32Array(S * S);
    for (let j = 0; j < S; j++) for (let i = 0; i < S; i++) {
      const n = f(i / S, j / S);
      const k = (j * S + i) * 4;
      d[k] = 176 + n * 54; d[k + 1] = 158 + n * 48; d[k + 2] = 124 + n * 40; d[k + 3] = 255;
      h[j * S + i] = n * 0.6;
    }
    x.putImageData(img, 0, 0);
    // pirinç kabuğu parçacıkları
    const rnd = mulberry(61);
    for (let n = 0; n < 620; n++) {
      const px = rnd() * S, py = rnd() * S, a = rnd() * 6.283, len = 6 + rnd() * 16;
      x.save(); x.translate(px, py); x.rotate(a);
      x.fillStyle = `rgba(${140 + rnd() * 60},${120 + rnd() * 50},${76 + rnd() * 40},.62)`;
      x.beginPath(); x.ellipse(0, 0, len, len * 0.28, 0, 0, 6.283); x.fill();
      x.restore();
      for (let s = -len; s < len; s++) {
        const ii = (((px + Math.cos(a) * s) | 0) % S + S) % S, jj = (((py + Math.sin(a) * s) | 0) % S + S) % S;
        h[jj * S + ii] = Math.min(1, h[jj * S + ii] + 0.42);
      }
    }
    // miselyum hif ağı yüzeyde
    x.strokeStyle = 'rgba(238,234,222,.34)'; x.lineWidth = 0.9;
    for (let n = 0; n < 420; n++) {
      let px = rnd() * S, py = rnd() * S;
      x.beginPath(); x.moveTo(px, py);
      for (let s = 0; s < 6; s++) { px += (rnd() - 0.5) * 30; py += (rnd() - 0.5) * 30; x.lineTo(px, py); }
      x.stroke();
    }
    return { map: tex(c, [1, 1], true), normalMap: tex(normalFromHeight(h, S, 2.6), [1, 1], false) };
  }

  /* ============================================================== ARAZİ ==== */
  function terrain() {
    const S = 512;
    const c = document.createElement('canvas'); c.width = c.height = S;
    const x = c.getContext('2d');
    const f = fbmFactory(77, 8), f2 = fbmFactory(78, 32);
    const img = x.createImageData(S, S), d = img.data;
    const h = new Float32Array(S * S);
    for (let j = 0; j < S; j++) for (let i = 0; i < S; i++) {
      const n = f(i / S, j / S), n2 = f2(i / S, j / S, 3);
      const k = (j * S + i) * 4;
      const moss = Math.max(0, n - 0.52) * 1.1;
      d[k]     = 104 + n2 * 22 - moss * 20;
      d[k + 1] = 112 + n2 * 20 + moss * 8;
      d[k + 2] = 66 + n2 * 16 - moss * 8;
      d[k + 3] = 255;
      h[j * S + i] = n * 0.7 + n2 * 0.3;
    }
    x.putImageData(img, 0, 0);
    return { map: tex(c, [46, 46], true), normalMap: tex(normalFromHeight(h, S, 1.6), [46, 46], false) };
  }

  /* ------------------------------------------------ yumuşak nokta dokusu -- */
  function dot() {
    const c = document.createElement('canvas'); c.width = c.height = 64;
    const x = c.getContext('2d');
    const g = x.createRadialGradient(32, 32, 0, 32, 32, 32);
    g.addColorStop(0, 'rgba(255,255,255,1)');
    g.addColorStop(0.32, 'rgba(255,255,255,.5)');
    g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g; x.fillRect(0, 0, 64, 64);
    const t = new T.CanvasTexture(c); t.colorSpace = T.SRGBColorSpace; return t;
  }

  /* ---------------------------------------- gökyüzü (ortam haritası için) -- */
  function skyEquirect(sunEl, sunAz, haze) {
    const W = 1024, H = 512;
    const c = document.createElement('canvas'); c.width = W; c.height = H;
    const x = c.getContext('2d');
    const img = x.createImageData(W, H), d = img.data;
    const sx = Math.cos(sunEl) * Math.sin(sunAz), sy = Math.sin(sunEl), sz = Math.cos(sunEl) * Math.cos(sunAz);
    for (let j = 0; j < H; j++) {
      const theta = (j / H) * Math.PI;
      for (let i = 0; i < W; i++) {
        const phi = (i / W) * 2 * Math.PI - Math.PI;
        const vy = Math.cos(theta), r = Math.sin(theta);
        const vx = r * Math.sin(phi), vz = r * Math.cos(phi);
        const up = Math.max(0, vy);
        let R, G, B;
        if (vy >= 0) {                                  // gökyüzü
          R = 122 + (1 - up) * 96; G = 158 + (1 - up) * 68; B = 206 + (1 - up) * 40;
        } else {                                        // zemin yansıması
          const t = Math.min(1, -vy * 3);
          R = 128 - t * 42; G = 126 - t * 40; B = 104 - t * 36;
        }
        const dot = vx * sx + vy * sy + vz * sz;
        const sun = Math.pow(Math.max(0, dot), 900) * 900 + Math.pow(Math.max(0, dot), 12) * 46 * (haze || 1);
        R = Math.min(255, R + sun); G = Math.min(255, G + sun * 0.94); B = Math.min(255, B + sun * 0.8);
        const k = (j * W + i) * 4;
        d[k] = R; d[k + 1] = G; d[k + 2] = B; d[k + 3] = 255;
      }
    }
    x.putImageData(img, 0, 0);
    const t = new T.CanvasTexture(c);
    t.mapping = T.EquirectangularReflectionMapping;
    t.colorSpace = T.SRGBColorSpace;
    return t;
  }

  global.AEGIS_TEX = { soil, litter, pcb, solar, cable, biocomposite, terrain, dot, skyEquirect, fbmFactory, mulberry };
})(window);
