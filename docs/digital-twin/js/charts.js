/* =============================================================================
   MYCELLIUM-AEGIS · DİJİTAL İKİZ
   charts.js — Bağımlılıksız 2B canvas çizim katmanı
   Retina-ölçekli, tema değişkenlerini okuyan minimal bir grafik kütüphanesi.
   ============================================================================= */
(function (global) {
  'use strict';

  const css = (n, f) => (getComputedStyle(document.documentElement).getPropertyValue(n) || f).trim();
  const PAL = () => ({
    ink:    css('--ink', '#14181c'),
    dim:    css('--ink-2', '#4a5359'),
    faint:  css('--rule-3', '#e3e7ea'),
    faint2: css('--ink-3', '#7b858c'),
    accent: css('--green', '#0f6b4a'),
    warn:   css('--amber', '#9a6410'),
    danger: css('--red', '#a8241a'),
    cool:   css('--blue', '#1b4f9c'),
    bg:     css('--paper', '#ffffff')
  });

  class Chart {
    constructor(canvas, opts) {
      this.c = canvas;
      this.ctx = canvas.getContext('2d');
      this.o = Object.assign({ pad: [10, 10, 20, 38], grid: true, font: '13px "CMU Serif", Georgia, serif' }, opts || {});
      this.resize();
    }
    resize() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      const r = this.c.getBoundingClientRect();
      const w = Math.max(1, Math.floor(r.width)), h = Math.max(1, Math.floor(r.height));
      if (this.c.width !== w * dpr || this.c.height !== h * dpr) {
        this.c.width = w * dpr; this.c.height = h * dpr;
      }
      this.w = w; this.h = h; this.dpr = dpr;
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    box() {
      const [pt, pr, pb, pl] = this.o.pad;
      return { x: pl, y: pt, w: this.w - pl - pr, h: this.h - pt - pb };
    }
    clear() { this.resize(); this.ctx.clearRect(0, 0, this.w, this.h); }

    frame(xd, yd, opts) {
      opts = opts || {};
      const p = PAL(), g = this.box(), ctx = this.ctx;
      ctx.font = this.o.font;
      ctx.strokeStyle = p.faint; ctx.lineWidth = 1;
      ctx.fillStyle = p.dim; ctx.textBaseline = 'middle';

      const ny = opts.ny || 4, nx = opts.nx || 5;
      for (let i = 0; i <= ny; i++) {
        const v = yd[0] + (yd[1] - yd[0]) * i / ny;
        const y = Math.round(g.y + g.h - g.h * i / ny) + 0.5;
        ctx.beginPath(); ctx.moveTo(g.x, y); ctx.lineTo(g.x + g.w, y); ctx.stroke();
        ctx.textAlign = 'right';
        ctx.fillText(opts.fy ? opts.fy(v) : v.toFixed(opts.dy != null ? opts.dy : 1), g.x - 6, y);
      }
      ctx.textAlign = 'center'; ctx.textBaseline = 'top';
      for (let i = 0; i <= nx; i++) {
        const v = xd[0] + (xd[1] - xd[0]) * i / nx;
        const x = Math.round(g.x + g.w * i / nx) + 0.5;
        if (i > 0 && i < nx && this.o.grid) {
          ctx.strokeStyle = p.faint; ctx.beginPath();
          ctx.moveTo(x, g.y); ctx.lineTo(x, g.y + g.h); ctx.stroke();
        }
        ctx.fillStyle = p.dim;
        ctx.fillText(opts.fx ? opts.fx(v) : v.toFixed(opts.dx != null ? opts.dx : 0), x, g.y + g.h + 6);
      }
      this.xd = xd; this.yd = yd;
      return g;
    }
    px(v) { const g = this.box(); return g.x + g.w * (v - this.xd[0]) / (this.xd[1] - this.xd[0]); }
    py(v) { const g = this.box(); return g.y + g.h - g.h * (v - this.yd[0]) / (this.yd[1] - this.yd[0]); }

    line(pts, color, width, fill) {
      const ctx = this.ctx, g = this.box();
      if (!pts.length) return;
      ctx.save(); ctx.beginPath(); ctx.rect(g.x, g.y, g.w, g.h); ctx.clip();
      ctx.beginPath();
      pts.forEach((p, i) => { const x = this.px(p[0]), y = this.py(p[1]); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      if (fill) {
        ctx.save(); ctx.lineTo(this.px(pts[pts.length - 1][0]), g.y + g.h);
        ctx.lineTo(this.px(pts[0][0]), g.y + g.h); ctx.closePath();
        ctx.fillStyle = fill; ctx.fill(); ctx.restore();
      }
      ctx.strokeStyle = color; ctx.lineWidth = width || 1.5;
      ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke();
      ctx.restore();
    }
    bars(pts, color, alphaFn) {
      const ctx = this.ctx, g = this.box();
      const bw = Math.max(1, g.w / pts.length - 0.5);
      ctx.save(); ctx.beginPath(); ctx.rect(g.x, g.y, g.w, g.h); ctx.clip();
      pts.forEach((p) => {
        const x = this.px(p[0]), y = this.py(p[1]);
        ctx.fillStyle = alphaFn ? alphaFn(p) : color;
        ctx.fillRect(x - bw / 2, y, bw, g.y + g.h - y);
      });
      ctx.restore();
    }
    vline(x, color, label, dash, opts) {
      opts = opts || {};
      const ctx = this.ctx, g = this.box(), X = this.px(x);
      if (X < g.x || X > g.x + g.w) return;
      ctx.save(); ctx.setLineDash(dash || [3, 3]);
      ctx.strokeStyle = color; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(X, g.y); ctx.lineTo(X, g.y + g.h); ctx.stroke();
      ctx.setLineDash([]);
      if (label) {
        const right = opts.align ? opts.align === 'right' : X > g.x + g.w * 0.75;
        ctx.fillStyle = color; ctx.font = '13px "CMU Serif", Georgia, serif';
        ctx.textAlign = right ? 'right' : 'left'; ctx.textBaseline = 'top';
        ctx.fillText(label, X + (right ? -4 : 4), g.y + 2 + (opts.dy || 0));
      }
      ctx.restore();
    }
    hline(y, color, label, dash, opts) {
      opts = opts || {};
      const ctx = this.ctx, g = this.box(), Y = this.py(y);
      if (Y < g.y - 1 || Y > g.y + g.h + 1) return;
      ctx.save(); ctx.setLineDash(dash || [4, 3]);
      ctx.strokeStyle = color; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(g.x, Y); ctx.lineTo(g.x + g.w, Y); ctx.stroke();
      ctx.setLineDash([]);
      if (label) {
        const right = opts.align !== 'left';
        ctx.fillStyle = color; ctx.font = '13px "CMU Serif", Georgia, serif';
        ctx.textAlign = right ? 'right' : 'left';
        ctx.textBaseline = 'bottom';
        ctx.fillText(label, right ? g.x + g.w - 3 : g.x + 4, Y - 2 + (opts.dy || 0));
      }
      ctx.restore();
    }
    label(text, color) {
      const ctx = this.ctx, g = this.box();
      ctx.save(); ctx.font = '13px "CMU Serif", Georgia, serif';
      ctx.fillStyle = color || PAL().dim; ctx.textAlign = 'left'; ctx.textBaseline = 'top';
      ctx.fillText(text, g.x + 4, g.y + 2); ctx.restore();
    }
    band(y0, y1, color) {
      const ctx = this.ctx, g = this.box();
      const a = this.py(y1), b = this.py(y0);
      ctx.save(); ctx.beginPath(); ctx.rect(g.x, g.y, g.w, g.h); ctx.clip();
      ctx.fillStyle = color; ctx.fillRect(g.x, a, g.w, b - a); ctx.restore();
    }
    vband(x0, x1, color) {
      const ctx = this.ctx, g = this.box();
      const a = this.px(x0), b = this.px(x1);
      ctx.save(); ctx.beginPath(); ctx.rect(g.x, g.y, g.w, g.h); ctx.clip();
      ctx.fillStyle = color; ctx.fillRect(a, g.y, b - a, g.h); ctx.restore();
    }
  }

  /* ------------------------------------------------ sıcaklık renk eşlemi -- */
  /* 20 °C (soğuk mavi) → 60 °C (kehribar) → 300 °C+ (kor kırmızısı)          */
  function heatColor(T) {
    const stops = [
      [15,  [ 96, 132, 168]],
      [25,  [126, 148, 118]],
      [40,  [186, 168,  78]],
      [70,  [230, 140,  50]],
      [150, [232,  86,  44]],
      [400, [255,  60,  40]],
      [900, [255, 226, 190]]
    ];
    if (T <= stops[0][0]) return stops[0][1];
    for (let i = 1; i < stops.length; i++) {
      if (T <= stops[i][0]) {
        const [a, ca] = stops[i - 1], [b, cb] = stops[i];
        const u = (T - a) / (b - a);
        return [0, 1, 2].map(k => Math.round(ca[k] + (cb[k] - ca[k]) * u));
      }
    }
    return stops[stops.length - 1][1];
  }
  const heatCss = (T, a) => { const c = heatColor(T); return `rgba(${c[0]},${c[1]},${c[2]},${a == null ? 1 : a})`; };

  global.AEGIS_CHART = { Chart, PAL, heatColor, heatCss };
})(window);
