#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mycellium-Aegis — publication-quality figures for the pitch deck (White Theme).
scienceplots + matplotlib + LaTeX (Computer Modern). Transparent SVG + PDF.

SVG, HTML sunuma gömülmek içindir: her ölçekte keskin kalır ve yazı tipi
gömülüdür (usetex glifleri yol olarak yazılır). PDF, LaTeX yedek slaytları
içindir.
"""
import os
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from cycler import cycler

import scienceplots  # noqa: F401  (registers the 'science' style)

# ---- house style (Corporate White Theme) -----------------------------------
INK   = "#1A1D20"   # Deep Charcoal
GREEN = "#00A389"   # Emerald/Teal (Mycelium Accent)
EMBER = "#D95D39"   # Terracotta/Rust (Warning/Fire)
INDIGO= "#0F2537"   # Deep Navy/Midnight
GRID  = "#E5E7EB"   # Very Light Gray
MUT   = "#6B7280"   # Muted Gray

plt.style.use(["science"])
# Şekiller projeksiyonda, salonun arkasından okunuyor. Yazı boyutları ve
# çizgi kalınlıkları buna göre seçildi: bir şekil slaytta yaklaşık kendi
# inç genişliğinin 1.5-3 katı ölçekle çizildiğinden, 13-15 pt taban ölçü
# ekranda 25-40 px'e karşılık geliyor.
mpl.rcParams.update({
    "text.usetex": True,
    "text.latex.preamble": r"\usepackage{amsmath}\usepackage{amssymb}\usepackage{bm}",
    "font.family": "serif",
    "font.size": 14,
    "axes.prop_cycle": cycler(color=[GREEN, EMBER, INDIGO]),
    "figure.dpi": 220,
    "savefig.dpi": 220,
    "savefig.transparent": True,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    # SVG: glifleri yola çevir -> dosya kendi kendine yeter, tarayıcıda
    # Computer Modern kurulu olmasa da aynı görünür.
    "svg.fonttype": "path",
    # Sabit tuz -> aynı girdi aynı SVG'yi üretir, gereksiz git diff olmaz.
    "svg.hashsalt": "mycellium-aegis",
    "axes.edgecolor": "#C3C8CE",
    "axes.linewidth": 1.1,
    "axes.labelcolor": INK,
    "axes.labelsize": 14,
    "axes.titlesize": 15,
    "text.color": INK,
    "xtick.color": INK, "ytick.color": INK,
    "xtick.labelsize": 12.5, "ytick.labelsize": 12.5,
    "xtick.major.width": 1.0, "ytick.major.width": 1.0,
    "xtick.major.size": 4.0, "ytick.major.size": 4.0,
    "lines.linewidth": 2.0,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "grid.alpha": 1.0,
    "legend.frameon": True, "legend.framealpha": 0.95, "legend.edgecolor": GRID,
    "legend.fontsize": 12.5, "legend.borderpad": 0.5,
})

HERE = os.path.dirname(os.path.abspath(__file__))
def save(fig, name):
    for ext in ("svg", "pdf"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"))
    plt.close(fig)
    print("wrote", name)

try:
    from scipy.special import erfc
except Exception:
    import math
    erfc = np.vectorize(math.erfc)

# ---- signal models ---------------------------------------------------------
def sig_normal(t):
    rng = np.random.default_rng(7)
    return (-3.0 + 3.4*np.sin(2*np.pi*20*t)
            - 22.0*np.clip(np.sin(2*np.pi*5*t), 0, None)**12
            + 0.5*rng.standard_normal(t.shape))

def sig_fire(t):
    rng = np.random.default_rng(11)
    s = (-5.0 + 4.0*np.sin(2*np.pi*20*t)
         - 30.0*np.clip(np.sin(2*np.pi*5*t), 0, None)**4
         + 0.6*rng.standard_normal(t.shape))
    return np.clip(s, -33.4, None)

# =============================================================================
# 1 — time-domain bioelectric signal (Wider Aspect Ratio)
# =============================================================================
def fig_signal_time():
    t = np.linspace(0, 5, 5*220)
    n, f = sig_normal(t), sig_fire(t)
    # Etiketler yoğun dalga biçiminin üstüne düşüyor; okunabilmesi için
    # yarı saydam beyaz zemin veriyoruz.
    lblbox = dict(facecolor="white", alpha=0.78, edgecolor="none",
                  boxstyle="round,pad=0.18")
    # Made wider and slightly shorter: 6.5 x 3.0
    fig, ax = plt.subplots(2, 1, figsize=(6.5, 3.0), sharex=True)
    ax[0].plot(t, n, color=GREEN, lw=1.5)
    ax[0].axhline(-2.9, color=MUT, lw=1.2, ls=(0, (4, 3)))
    # Etiketler eksen kenarında kırpılıyordu; dalga biçiminin üstünde
    # açılan boş şeride, çerçeveden içeri alındı (bkz. ylim üst payı).
    ax[0].text(4.84, 3.6, r"$\bar V=-2.9$", ha="right", va="center",
               color=MUT, fontsize=11.5, bbox=lblbox, zorder=5)
    ax[0].set_ylabel(r"$V\;[\mathrm{mV}]$")
    ax[0].set_title(r"\textbf{Normal (dinlenim)}\quad$f_{\mathrm{dom}}\!\approx\!20$ Hz",
                    color=INDIGO, fontsize=14, loc="left")
    ax[1].plot(t, f, color=EMBER, lw=1.5)
    ax[1].axhline(-33.4, color=EMBER, lw=1.2, ls=":")
    ax[1].text(4.84, 3.6, r"$V_{\min}=-33.4$", ha="right", va="center",
               color=EMBER, fontsize=11.5, bbox=lblbox, zorder=5)
    ax[1].set_ylabel(r"$V\;[\mathrm{mV}]$")
    ax[1].set_xlabel(r"$t\;[\mathrm{s}]$")
    ax[1].set_title(r"\textbf{Ate\c{s} stresi}\quad$f_{\mathrm{dom}}\!\approx\!5$ Hz",
                    color=EMBER, fontsize=14, loc="left")
    for a in ax:
        # üst pay, referans etiketlerinin dalga biçimine binmemesi için
        a.set_xlim(0, 5); a.set_ylim(-36, 7)
    fig.align_ylabels(ax)
    save(fig, "signal_time")

# =============================================================================
# 2 — single-sided amplitude spectrum (FFT)
# =============================================================================
def fig_fft():
    fs, N = 200.0, 4096
    t = np.arange(N)/fs
    def spec(x):
        x = x - x.mean()
        X = np.abs(np.fft.rfft(x*np.hanning(N)))/N*2
        fr = np.fft.rfftfreq(N, 1/fs)
        return fr, X
    fn, Xn = spec(sig_normal(t))
    ff, Xf = spec(sig_fire(t))
    fig, ax = plt.subplots(figsize=(5.8, 3.0))
    ax.plot(fn, Xn, color=INDIGO, lw=1.5, label=r"Normal")
    ax.plot(ff, Xf, color=EMBER, lw=1.5, ls=(0, (5, 2)), label=r"Ate\c{s} stresi")
    ax.set_xlim(0, 26); ax.set_ylim(bottom=0)
    ax.set_xlabel(r"Frekans $f\;[\mathrm{Hz}]$")
    ax.set_ylabel(r"Genlik $|\hat V(f)|\;[\mathrm{mV}]$")
    # annotate dominant peaks
    kn = np.argmax(Xn[(fn>1)])+np.searchsorted(fn,1)
    kf = np.argmax(Xf[(ff>1)])+np.searchsorted(ff,1)
    ax.annotate(r"$20\,$Hz", xy=(fn[kn], Xn[kn]), xytext=(fn[kn]+2.5, Xn[kn]),
                color=INDIGO, fontsize=12.6, va="center",
                arrowprops=dict(arrowstyle="->", color=INDIGO, lw=1.2))
    ax.annotate(r"$5\,$Hz", xy=(ff[kf], Xf[kf]), xytext=(ff[kf]+2.5, Xf[kf]*0.98),
                color=EMBER, fontsize=12.6, va="center",
                arrowprops=dict(arrowstyle="->", color=EMBER, lw=1.2))
    ax.legend(loc="upper right")
    save(fig, "fft_spectrum")

# =============================================================================
# 3 — 1-D transient heat conduction in soil  (Side by side to reduce height)
# =============================================================================
def fig_heat():
    T0, Ts = 20.0, 300.0
    alpha = 2.5e-7                      # effective diffusivity of moist forest soil [m^2/s]
    z = np.linspace(0, 0.30, 260)       # 0..30 cm
    tmin = np.linspace(0.5, 90, 320)    # minutes
    tt = tmin*60.0
    Z, T = np.meshgrid(z, tt)
    field = T0 + (Ts-T0)*erfc(Z/(2*np.sqrt(alpha*T)))

    # Use side-by-side layout to make it fit 16:9 nicely
    fig = plt.figure(figsize=(7.8, 3.2))
    # wspace: renk çubuğunun etiketi ile sağ eksenin ylabel'i büyük puntoda
    # yan yana geliyordu; aralığı açtık.
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.0], wspace=0.42)

    # Left: Colormap
    axm = fig.add_subplot(gs[0])
    pm = axm.pcolormesh(tmin, z*100, field.T, cmap="YlOrRd", shading="auto",
                        vmin=20, vmax=180, rasterized=True)
    axm.axhline(17.5, color=INDIGO, lw=1.6, ls=(0, (5, 2)))
    # Etiket açık sarı bölgede kalsın diye çizginin üstüne, beyaz zeminle.
    axm.text(2.5, 18.8, r"sens\"or yata\u{g}\i\;($17.5$ cm)", color=INDIGO,
             fontsize=11.5, va="bottom", ha="left", zorder=6,
             bbox=dict(facecolor="white", alpha=0.82, edgecolor="none",
                       boxstyle="round,pad=0.2"))
    axm.set_ylabel(r"Derinlik $z\;[\mathrm{cm}]$")
    axm.set_xlabel(r"Zaman $t\;[\mathrm{dk}]$")
    axm.set_title(r"\textbf{Is\i\ yay\i n\i m\i}\;\;$\partial_t T=\alpha\,\partial_z^2 T$",
                  loc="left", fontsize=14)
    cb = fig.colorbar(pm, ax=axm, pad=0.04)
    # Birim renk çubuğunun ALTINDA: yanda olunca sağ eksenin ylabel'iyle,
    # üstte olunca sol eksenin başlığıyla çakışıyordu. Altta ikisinden de uzak.
    cb.ax.set_xlabel(r"$T\;[^{\circ}\mathrm{C}]$", fontsize=12, labelpad=9)
    cb.ax.tick_params(labelsize=11)

    # Right: Depth curves
    axc = fig.add_subplot(gs[1])
    for zi, c, ls in [(0.05, INDIGO, "-"), (0.10, GREEN, "-"), (0.175, EMBER, "-")]:
        Tz = T0 + (Ts-T0)*erfc(zi/(2*np.sqrt(alpha*tt)))
        axc.plot(tmin, Tz, color=c, ls=ls, lw=1.75, label=fr"$z={int(zi*100)}$ cm")
    axc.set_xlabel(r"Zaman $t\;[\mathrm{dk}]$")
    axc.set_ylabel(r"$T\;[^{\circ}\mathrm{C}]$")
    axc.set_xlim(0, 90)
    axc.legend(loc="upper left", ncol=1, fontsize=11.2)
    axc.set_title(r"\textbf{Is\i\ ivmesi $dT/dt>\beta$}", loc="left", fontsize=14)
    save(fig, "heat_diffusion")

# =============================================================================
# 4 — sensor-fusion feature space & decision region (AND-gate + LSTM boundary)
# =============================================================================
def fig_fusion():
    rng = np.random.default_rng(3)
    nrm = np.column_stack([rng.normal(0.4, 0.35, 260), rng.normal(6, 3.0, 260)])
    fire = np.column_stack([rng.normal(3.6, 0.7, 150), rng.normal(28, 4.0, 150)])
    nrm[:, 0] = np.clip(nrm[:, 0], 0, None); fire[:, 1] = np.clip(fire[:, 1], 0, None)
    bx, by = 1.8, 15.0                          # beta thresholds
    
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    ax.axvspan(bx, 6, ymin=(by)/40, color=EMBER, alpha=0.05)
    ax.scatter(nrm[:, 0], nrm[:, 1], s=24, color=GREEN, alpha=0.8, label=r"Normal", edgecolor="none")
    ax.scatter(fire[:, 0], fire[:, 1], s=32, color=EMBER, alpha=0.85, marker="^",
               label=r"Ate\c{s}", edgecolor="none")
    ax.axvline(bx, color=MUT, lw=1.25, ls=(0, (4, 3)))
    ax.axhline(by, color=MUT, lw=1.25, ls=(0, (4, 3)))
    xx = np.linspace(0, 6, 200)
    yy = 15 + 9*np.tanh((xx-2.0)*1.4)
    ax.plot(xx, yy, color=INDIGO, lw=2, label=r"LSTM s\i n\i r\i")
    ax.text(3.9, 36, r"\textbf{ALARM}", color=EMBER, fontsize=14, ha="center")
    ax.text(0.15, 37, r"$\beta_{T}$", color=MUT, fontsize=14)
    ax.set_xlim(0, 6); ax.set_ylim(0, 40)
    ax.set_xlabel(r"Is\i\ ivmesi $\dfrac{dT}{dt}\;[^{\circ}\mathrm{C}/\mathrm{dk}]$")
    ax.set_ylabel(r"Spike derinli\u{g}i $|\Delta V|\;[\mathrm{mV}]$")
    ax.legend(loc="lower right", fontsize=12.6)
    ax.set_title(r"\textbf{Sens\"or f\"uzyonu — ay\i rt edilebilirlik}", loc="left", fontsize=15.4)
    save(fig, "fusion_separability")

# =============================================================================
# 5 — ROC: single threshold vs. sensor fusion
# =============================================================================
def fig_roc():
    def roc_from_gauss(d, n=4000, seed=0):
        rng = np.random.default_rng(seed)
        pos = rng.normal(d, 1, n); neg = rng.normal(0, 1, n)
        thr = np.linspace(-4, d+5, 400)
        tpr = np.array([(pos > t).mean() for t in thr])
        fpr = np.array([(neg > t).mean() for t in thr])
        auc = np.trapezoid(tpr[::-1], fpr[::-1])
        return fpr, tpr, auc
    f1, t1, a1 = roc_from_gauss(1.7, seed=1)   # single threshold
    f2, t2, a2 = roc_from_gauss(4.2, seed=2)   # fusion
    fig, ax = plt.subplots(figsize=(5.0, 3.6))
    ax.plot([0, 1], [0, 1], color=MUT, lw=1.25, ls=":")
    ax.plot(f1, t1, color=INDIGO, lw=1.88, label=fr"Tek e\c{{s}}ik  (AUC$=${a1:.2f})")
    ax.plot(f2, t2, color=GREEN, lw=2.5, label=fr"Sens\"or f\"uzyonu  (AUC$=${a2:.2f})")
    i = np.argmin(np.abs(f2-0.01))
    ax.scatter([f2[i]], [t2[i]], s=72, color=EMBER, zorder=5)
    ax.annotate(r"\%1 yanl\i\c{s} alarm", xy=(f2[i], t2[i]), xytext=(0.28, 0.55),
                color=EMBER, fontsize=12.6,
                arrowprops=dict(arrowstyle="->", color=EMBER, lw=1.25))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel(r"Yanl\i\c{s} alarm oran\i\ (FPR)")
    ax.set_ylabel(r"Do\u{g}ru tespit oran\i\ (TPR)")
    ax.legend(loc="lower right", fontsize=12.6)
    ax.set_title(r"\textbf{ROC — f\"uzyon vs. tek e\c{s}ik}", loc="left", fontsize=15.4)
    save(fig, "roc")

# =============================================================================
# 6 — 8-channel directional response & angle-of-arrival (circular statistics)
# =============================================================================
def fig_directional():
    ang = np.deg2rad(np.arange(0, 360, 45))       # 8 electrodes
    src = np.deg2rad(112.5)                        # fire azimuth (ESE)
    rng = np.random.default_rng(5)
    resp = np.clip(np.cos(ang-src), 0, None) + 0.06*rng.standard_normal(8)
    resp = np.clip(resp, 0, None)
    est = np.angle(np.sum(resp*np.exp(1j*ang)))
    
    fig = plt.figure(figsize=(4.8, 4.3))
    ax = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.bar(ang, resp, width=np.deg2rad(30), color=INDIGO, alpha=0.35, edgecolor=INDIGO, lw=1.5)
    ax.plot([est, est], [0, 1.05], color=EMBER, lw=2.75)
    ax.plot([src, src], [0, 1.05], color=GREEN, lw=1.88, ls=(0, (4, 2)))
    ax.scatter(ang, resp, s=40, color=INDIGO, zorder=6)
    ax.set_rmax(1.15); ax.set_rticks([0.5, 1.0]); ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels([r"K", r"KD", r"D", r"GD", r"G", r"GB", r"B", r"KB"], fontsize=12.6)
    ax.set_title(r"\textbf{Y\"onsel alg\i lama}\;\; $\hat\theta=\arg\!\sum_k r_k e^{i\theta_k}$",
                 fontsize=14.7, pad=16)
    ax.text(est, 1.30, fr"$\hat\theta={np.rad2deg(est):.0f}^{{\circ}}$", color=EMBER,
            ha="center", fontsize=12.6, fontweight='bold')
    save(fig, "directional")

# =============================================================================
# 7 — break-even analysis
# =============================================================================
def fig_breakeven():
    x = np.linspace(0, 8, 200)
    rev = 360*x
    cost = 880 + 160*x
    be = 880/200.0
    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.fill_between(x, rev, cost, where=(rev >= cost), color=GREEN, alpha=0.15)
    ax.plot(x, rev, color=GREEN, lw=2.5, label=r"Gelir $=360k\cdot n$")
    ax.plot(x, cost, color=EMBER, lw=2.5, label=r"Maliyet $=880k+160k\cdot n$")
    ax.axhline(880, color=MUT, lw=1.25, ls=(0, (4, 3)))
    ax.axvline(be, color=INDIGO, lw=1.5, ls=":")
    ax.scatter([be], [360*be], s=80, color=INDIGO, zorder=6)
    ax.annotate(r"Ba\c{s}a ba\c{s}: $n=4.4\!\to\!5$ paket", xy=(be, 360*be),
                xytext=(be+0.4, 360*be-620), fontsize=12.6,
                arrowprops=dict(arrowstyle="->", color=INDIGO, lw=1.25))
    ax.set_xlim(0, 8); ax.set_ylim(0, 3000)
    ax.set_xlabel(r"Sat\i lan paket say\i s\i\ $n$")
    ax.set_ylabel(r"Tutar $[\times 10^{3}\;\mathrm{TL}]$")
    ax.legend(loc="upper left", fontsize=12.6)
    ax.set_title(r"\textbf{Ba\c{s}a ba\c{s} analizi}", loc="left", fontsize=15.4)
    save(fig, "breakeven")

# =============================================================================
# 8 — electrode cross-section
# =============================================================================
def fig_electrode():
    from matplotlib.patches import Circle, FancyArrowPatch, Wedge
    fig, ax = plt.subplots(figsize=(5.2, 5.2))
    ax.set_aspect('equal')
    ax.set_xlim(-1.75, 1.75); ax.set_ylim(-1.75, 1.75)
    ax.axis('off')
    layers = [
        (1.4, GREEN, 0.15, r"\textbf{D\i\c{s}}: Sodyum Aljinat Hidrojel"),
        (0.95, INDIGO,  0.15, r"\textbf{Orta}: \.Iletken Grafit Matris"),
        (0.52, "#9CA3AF", 0.20, r"\textbf{\c{C}ekirdek}: 316L \c{C}elik"),
    ]
    for r, c, a, lbl in layers:
        circ = Circle((0, 0), r, fill=True, facecolor=c, alpha=a,
                       edgecolor=c, lw=2.5, ls='-')
        ax.add_patch(circ)
    rng = np.random.default_rng(42)
    for _ in range(24):
        th = rng.uniform(0, 2*np.pi)
        r0 = 1.38
        dr = rng.uniform(0.15, 0.38)
        x0, y0 = r0*np.cos(th), r0*np.sin(th)
        x1, y1 = (r0+dr)*np.cos(th+rng.uniform(-.15,.15)), (r0+dr)*np.sin(th+rng.uniform(-.15,.15))
        ax.plot([x0, x1], [y0, y1], color=GREEN, lw=1.5, alpha=0.7)
        ax.plot(x1, y1, 'o', color=GREEN, ms=4.5, alpha=0.6)
    
    # annotations
    ax.annotate(layers[0][3], xy=(0.99, 0.99), xytext=(1.35, 1.55),
                fontsize=11.9, color=GREEN, ha='center',
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.25))
    ax.annotate(layers[1][3], xy=(0.67, -0.67), xytext=(1.3, -1.45),
                fontsize=11.9, color=INDIGO, ha='center',
                arrowprops=dict(arrowstyle='->', color=INDIGO, lw=1.25))
    ax.annotate(layers[2][3], xy=(0, 0), xytext=(-1.35, -1.45),
                fontsize=11.9, color=MUT, ha='center',
                arrowprops=dict(arrowstyle='->', color=MUT, lw=1.25))
    
    for i in range(8):
        th = i * np.pi/4
        ax.plot([0.52*np.cos(th), 1.38*np.cos(th)],
                [0.52*np.sin(th), 1.38*np.sin(th)],
                color=INDIGO, lw=1.88, alpha=0.5, ls=(0,(5,3)))
        ax.plot(1.38*np.cos(th), 1.38*np.sin(th), 'o', color=INDIGO, ms=7.5, zorder=5)
    dirs = ['K','KD','D','GD','G','GB','B','KB']
    for i, d in enumerate(dirs):
        th = i * np.pi/4
        ax.text(1.62*np.cos(th), 1.62*np.sin(th), d,
                ha='center', va='center', fontsize=11.2, color=INK)
    ax.set_title(r"\textbf{\"U\c{c} katmanl\i\ biyomimetik k\"ok-elektrot}", fontsize=16.1, pad=14)
    save(fig, "electrode_cross_section")

# =============================================================================
# 9 — system architecture (Wider spacing for text legibility)
# =============================================================================
def fig_architecture():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(8.0, 2.6))
    ax.set_xlim(-0.2, 8.5); ax.set_ylim(-0.2, 2.5)
    ax.axis('off')
    boxes = [
        (0.0, 0.3, 1.4, 1.4, GREEN, r"Sens\"or"+"\n"+r"Teraryum", r"Biyoelektrot"+"\n"+r"ESP32 + ADC"),
        (2.3, 0.3, 1.4, 1.4, INDIGO, r"A\u{g} Ge\c{c}idi", r"LoRaWAN 868"+"\n"+r"Mesh gateway"),
        (4.6, 0.3, 1.4, 1.4, EMBER, r"Bulut / U\c{c}", r"LSTM f\"uzyon"+"\n"+r"AND-gate karar"),
        (6.9, 0.3, 1.4, 1.4, "#B91C1C", r"Alarm", r"SaaS pano"+"\n"+r"SMS / API"),
    ]
    for x, y, w, h, c, title, sub in boxes:
        bb = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                            facecolor=c, alpha=0.08, edgecolor=c, lw=2.25)
        ax.add_patch(bb)
        ax.text(x+w/2, y+h*0.68, title, ha='center', va='center',
                fontsize=13.3, fontweight='bold', color=c)
        ax.text(x+w/2, y+h*0.28, sub, ha='center', va='center',
                fontsize=11, color=INK, linespacing=1.4)
    for i in range(3):
        x0 = boxes[i][0] + boxes[i][2]
        x1 = boxes[i+1][0]
        ymid = 1.0
        ax.annotate('', xy=(x1, ymid), xytext=(x0, ymid),
                    arrowprops=dict(arrowstyle='->', color=MUT, lw=1.88))
        labels = [r"LoRa 868\,MHz", r"TLS 1.3 / MQTT", r"WebSocket"]
        ax.text((x0+x1)/2, ymid+0.2, labels[i], ha='center', fontsize=11, color=MUT)
    ax.text(4.15, 2.25, r"\textbf{Mycellium-Aegis --- Sistem Mimarisi}", ha='center', fontsize=16.1, color=INK)
    save(fig, "system_architecture")

# =============================================================================
# 10 — AI signal processing pipeline
# =============================================================================
def fig_ai_pipeline():
    from matplotlib.patches import FancyBboxPatch
    # Eski hâlde ylim üst sınırı 3.2 idi ama kutular y=1.6'da bitiyordu:
    # şeklin üst %38'i boştu. Sınırı içeriğe oturtup figür yüksekliğini de
    # aynı oranda kısıyoruz — böylece kutu en-boy oranı korunuyor, yalnızca
    # boşluk gidiyor (birim başına inç sabit: 4.2/3.8 ~ 2.8/2.53).
    # Kutu genişliği 1.3 iken alttaki denklemler kutuya sığmıyor, komşu
    # kutunun üstüne taşıyordu. Kutuları genişletip aralığı kısıyoruz ve
    # denklem puntosunu düşürüyoruz; artık her ifade kendi kutusunda.
    W, H, GAP = 1.62, 1.6, 0.22
    N = 5
    span = N*W + (N-1)*GAP                      # = 8.98
    fig, ax = plt.subplots(figsize=(8.9, 2.53))
    ax.set_xlim(-0.22, span + 0.22); ax.set_ylim(-1.0, 1.8)
    ax.axis('off')
    steps = [
        (r"\textbf{01}", r"Ofset"+"\n"+r"Kalibrasyon", r"$\bar{x}_{50}$ DC "+r"\"o"+r"teleme", GREEN),
        (r"\textbf{02}", r"5-tap FIR"+"\n"+r"Filtre", r"$y[n]=\sum h_k\,x[n\!-\!k]$", GREEN),
        (r"\textbf{03}", r"\"Oznitelik"+"\n"+r"\c{C}\i kar\i m", r"FFT $\cdot\;dT\!/\!dt\;\cdot\;f_{\mathrm{spike}}$", INDIGO),
        (r"\textbf{04}", r"LSTM"+"\n"+r"S\i n\i fland\i rma", r"zaman serisi $\to$ skor", INDIGO),
        (r"\textbf{05}", r"AND-Gate"+"\n"+r"Karar", r"3 ko\c{s}ul $\Rightarrow$ alarm", EMBER),
    ]
    for i, (num, title, eq, c) in enumerate(steps):
        x = i * (W + GAP)
        bb = FancyBboxPatch((x, 0), W, H, boxstyle="round,pad=0.08",
                            facecolor=c, alpha=0.06, edgecolor=c, lw=2.25)
        ax.add_patch(bb)
        ax.text(x+W/2, H-0.2, num, ha='center', va='center', fontsize=11.2, color=c)
        ax.text(x+W/2, H*0.56, title, ha='center', va='center',
                fontsize=12.4, fontweight='bold', color=INK, linespacing=1.4)
        ax.text(x+W/2, 0.19, eq, ha='center', va='center', fontsize=10.2, color=MUT)
        if i < len(steps)-1:
            ax.annotate('', xy=(x+W+GAP-0.03, H/2), xytext=(x+W+0.03, H/2),
                        arrowprops=dict(arrowstyle='->', color=MUT, lw=1.88))
    # Alarm koşulu tam olarak kutu dizisinin ortasına hizalanıyor.
    ax.text(span/2, -0.55, r"$\left(\frac{dT}{dt}>\beta\right) \;\wedge\; "
            r"\left(\frac{dR}{dt}>\gamma\right) \;\wedge\; "
            r"\left(f_{\mathrm{spike}} \in [0.5,5]\,\mathrm{Hz},\;"
            r"V_{\min}\!<\!-33\,\mathrm{mV}\right)$",
            ha='center', va='center', fontsize=12.6, color=EMBER,
            bbox=dict(boxstyle='round,pad=0.42', facecolor=EMBER, alpha=0.06, edgecolor=EMBER, lw=1.25))
    ax.set_title(r"\textbf{Sinyal i\c{s}leme hatt\i\\ --- ham gerilimden karara}", fontsize=16.1, pad=12)
    save(fig, "ai_pipeline")

# =============================================================================
# 11 — elektrot malzemesi: katman yapısı, korozyon dayanımı, arayüz empedansı
# -----------------------------------------------------------------------------
# Belgelenmiş yığın: 316L çekirdek + grafit/PPy (polipirol) ara katman +
# aljinat–gliserol–nanokarbon hidrojel (bkz. donanım raporu §3).
# (b) ve (c) panelleri ÖLÇÜM DEĞİL, literatür dayanaklı model eğrileridir;
# şekil üzerinde de böyle etiketlenir. TiN kaplama, elenen alternatif olarak
# kıyas için konuldu — tasarımda titanyum kullanılmıyor.
# =============================================================================
def fig_electrode_material():
    from matplotlib.patches import Rectangle, FancyBboxPatch
    fig = plt.figure(figsize=(11.4, 3.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.02, 1.0, 1.0], wspace=0.34)

    # ---- (a) katman yığını ----------------------------------------------
    # Eş oranlı eksen şart: aksi hâlde eşmerkezli daireler elips çıkıyor.
    axa = fig.add_subplot(gs[0])
    # Eş oranlı eksen şart, yoksa eşmerkezli daireler elips çıkıyor.
    # Sınır oranı panel kutusunun oranına (~1.32) yakın tutuluyor ki kutu
    # küçülüp (a) başlığı diğer iki başlığın altına düşmesin.
    axa.set_aspect("equal", adjustable="box")
    axa.set_xlim(-4.7, 12.6); axa.set_ylim(-7.4, 5.7); axa.axis("off")
    layers = [                       # (yarıçap mm, renk, ad, işlev, açı)
        (1.50, "#8A9099", r"316L \c{c}ekirdek",      r"mekanik dayan\i m",      -38),
        (2.35, INDIGO,    r"grafit\,/\,PPy",          r"elektron ilet\i m\i",     8),
        (3.40, GREEN,     r"aljinat--nanokarbon",     r"iyonik e\c{s}le\c{s}me", 52),
    ]
    for r, c, *_ in reversed(layers):
        axa.add_patch(plt.Circle((0, 0), r, facecolor=c, alpha=0.18,
                                 edgecolor=c, lw=2.2, zorder=2))
    # Her katman kendi açısından dışarı çıkan tek kırıklı bir kılavuzla
    # etiketlenir; açılar ayrı olduğu için çizgiler birbirini kesmiyor.
    for r, c, name, fn, ang in layers:
        th = np.deg2rad(ang)
        # halkanın ortasından başlat (çekirdek için merkeze yakın)
        r0 = r - 0.42 if r > 1.6 else r*0.55
        x0, y0 = r0*np.cos(th), r0*np.sin(th)
        xk = 4.15
        yk = {-38: -3.05, 8: 0.30, 52: 3.75}[ang]
        axa.plot([x0, xk-1.15, xk], [y0, yk, yk], color=c, lw=1.35,
                 solid_capstyle="round", zorder=4)
        axa.plot([x0], [y0], "o", color=c, ms=4.5, zorder=5)
        axa.text(xk+0.32, yk+0.40, name, color=c, fontsize=11.5, va="center", ha="left")
        axa.text(xk+0.32, yk-0.58, fn, color=MUT, fontsize=10, va="center", ha="left")
    # Çap ölçüsü. Çemberlere fazla yakınken en alttaki katman etiketiyle
    # aynı bantta kalıyor ve sıkışık görünüyordu; ölçü çizgisini ve yazıyı
    # daha aşağı indirip nefes payı bıraktık.
    # Ölçü yazısı okun ÜSTÜNDE (teknik resimdeki alışılmış gösterim).
    # Metni okun ortasına koyup iki yandan ok çizmeyi denedik ama yazı
    # bırakılan boşluktan geniş kalıp okun üstüne biniyordu.
    ydim = -5.30
    axa.annotate("", xy=(-3.40, ydim), xytext=(3.40, ydim),
                 arrowprops=dict(arrowstyle="<->", color=INK, lw=1.2))
    for xe in (-3.40, 3.40):
        axa.plot([xe, xe], [-3.55, -5.72], color=MUT, lw=0.8, ls=(0, (3, 3)))
    axa.text(0, ydim + 0.34, r"$\varnothing\,6.8$ mm", ha="center", va="bottom",
             fontsize=11.5, color=INK)
    axa.text(0, ydim - 0.46, r"ger\c{c}ek \"ol\c{c}ek", ha="center", va="top",
             fontsize=10, color=MUT)
    axa.set_title(r"\textbf{(a)} Katman yap\i s\i", loc="left", fontsize=14)

    # ---- (b) korozyon: 24 ay toprak gömülü kütle kaybı --------------------
    axb = fig.add_subplot(gs[1])
    t = np.linspace(0, 24, 200)
    # doygunluğa giden basit pasifleşme modeli: m(t) = m_inf (1 - e^{-t/tau})
    for m_inf, tau, c, ls, lbl in [
            (4.20, 7.0, EMBER,  (0, (5, 2)), r"\c{C}\i plak karbon \c{c}elik"),
            (0.95, 9.0, "#9CA3AF", "-",      r"TiN kaplama (elenen)"),
            (0.34, 11.0, GREEN,   "-",       r"316L + grafit/PPy")]:
        axb.plot(t, m_inf*(1-np.exp(-t/tau)), color=c, ls=ls, lw=2.1, label=lbl)
    axb.axvline(18, color=INDIGO, lw=1.2, ls=":")
    # Gösterge kutusunun altında kalıyordu; sağdaki boş alana alındı.
    axb.text(18.5, 1.95, r"proje sonu" + "\n" + r"($18$ ay)", color=INDIGO,
             fontsize=10.5, va="center", ha="left", linespacing=1.35)
    axb.set_xlim(0, 24); axb.set_ylim(0, 5.55)
    axb.set_xlabel(r"Topra\u{g}a g\"om\"ul\"u s\"ure $[\mathrm{ay}]$")
    axb.set_ylabel(r"K\"utle kayb\i\;$[\mathrm{mg/cm^2}]$")
    axb.legend(loc="upper left", fontsize=10.5)
    axb.set_title(r"\textbf{(b)} Korozyon dayan\i m\i", loc="left", fontsize=14)

    # ---- (c) arayüz empedansı |Z| ----------------------------------------
    axc = fig.add_subplot(gs[2])
    f = np.logspace(-1, 3, 300)
    # sabit faz elemanı + çözelti direnci:  |Z| = Rs + 1/(Q (2 pi f)^n)
    for Rs, Q, n, c, ls, lbl in [
            (1.8e3, 4.0e-5, 0.80, EMBER,  (0, (5, 2)), r"\c{C}\i plak 316L i\u{g}ne"),
            (0.9e3, 2.6e-4, 0.86, INDIGO, "-",          r"+ grafit/PPy"),
            (0.4e3, 1.5e-3, 0.92, GREEN,  "-",          r"+ aljinat hidrojel")]:
        axc.loglog(f, Rs + 1.0/(Q*(2*np.pi*f)**n), color=c, ls=ls, lw=2.1, label=lbl)
    axc.axvspan(0.5, 5, color=GREEN, alpha=0.12)
    # Etiket eksenin içinde kalsın: üstte olunca başlıkla çakışıyordu.
    axc.text(1.6, 1.9e2, r"sinyal band\i" + "\n" + r"$0.5$--$5$ Hz",
             color=GREEN, fontsize=10.5, ha="center", va="bottom",
             linespacing=1.35)
    axc.set_xlim(0.1, 1e3); axc.set_ylim(1.4e2, 9e4)
    axc.set_xlabel(r"Frekans $f\;[\mathrm{Hz}]$")
    axc.set_ylabel(r"$|Z|\;[\Omega]$")
    axc.legend(loc="upper right", fontsize=10.5)
    axc.set_title(r"\textbf{(c)} Arayüz empedans\i", loc="left", fontsize=14)
    axc.grid(True, which="both", color=GRID, lw=0.6)

    fig.text(0.5, -0.055,
             r"(b) ve (c) literat\"ur dayanakl\i\ \emph{model} e\u{g}rileridir; "
             r"WP-1 kapsam\i nda \"ol\c{c}\"umle do\u{g}rulanacakt\i r.",
             ha="center", fontsize=10, color=MUT)
    save(fig, "electrode_material")

# =============================================================================
# 12 — pazar büyümesi ve birim ekonomisi
# -----------------------------------------------------------------------------
# Tüm eğriler iş planındaki açık varsayımlardan türetilmiştir (TAM 2.4 milyar
# USD, %8.5 CAGR; paket 360k TL fiyat / 160k TL maliyet; 18 ay 880k TL sabit
# gider). Ölçülmüş veri değil, projeksiyondur.
# =============================================================================
def fig_market():
    fig = plt.figure(figsize=(11.4, 3.4))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.0, 1.0, 1.05], wspace=0.36)

    # ---- (a) TAM büyümesi -------------------------------------------------
    axa = fig.add_subplot(gs[0])
    yr = np.arange(2024, 2031)
    tam = 2.4*(1.085**(yr-2024))
    axa.fill_between(yr, tam, color=GREEN, alpha=0.13)
    axa.plot(yr, tam, color=GREEN, lw=2.4, marker="o", ms=5)
    # "\$" LaTeX'te tuhaf küçük bir işaret bırakıyordu; birimi yazıyla veriyoruz.
    axa.annotate(fr"{tam[-1]:.1f} milyar USD", xy=(yr[-1], tam[-1]),
                 xytext=(yr[-1]-3.4, tam[-1]+0.42), fontsize=11.5, color=GREEN)
    axa.text(2024.15, 1.15, r"\%8.5 CAGR", fontsize=11.5, color=MUT)
    axa.set_xlim(2024, 2030.4); axa.set_ylim(0, 5.15)
    axa.set_xlabel(r"Y\i l"); axa.set_ylabel(r"TAM $[\mathrm{milyar\;USD}]$")
    axa.set_title(r"\textbf{(a)} Pazar b\"uy\"umesi", loc="left", fontsize=14)

    # ---- (b) birim ekonomisi: şelale --------------------------------------
    axb = fig.add_subplot(gs[1])
    bars = [(r"Sat\i\c{s}", 360, GREEN), (r"\"Uretim", -110, EMBER),
            (r"Kurulum", -50, EMBER), (r"Br\"ut k\^ar", 200, INDIGO)]
    run = 0
    for i, (lbl, v, c) in enumerate(bars):
        if lbl == r"Br\"ut k\^ar":
            axb.bar(i, v, bottom=0, color=c, alpha=0.85, width=0.62)
            axb.text(i, v+13, r"$200$k", ha="center", fontsize=11.5, color=c)
        else:
            base = run if v < 0 else 0
            axb.bar(i, abs(v), bottom=min(base, base+v), color=c,
                    alpha=0.85 if v > 0 else 0.55, width=0.62)
            axb.text(i, max(base, base+v)+13, fr"${abs(v)}$k", ha="center",
                     fontsize=11.5, color=c)
            run = base + v if v < 0 else v
    axb.set_xticks(range(len(bars)))
    axb.set_xticklabels([b[0] for b in bars], fontsize=11)
    axb.set_ylim(0, 452)
    axb.set_ylabel(r"Paket ba\c{s}\i\ $[\mathrm{bin\;TL}]$")
    axb.text(0.97, 0.93, r"br\"ut marj \%56", transform=axb.transAxes,
             fontsize=11.5, color=INDIGO, ha="right")
    axb.set_title(r"\textbf{(b)} Birim ekonomisi", loc="left", fontsize=14)
    axb.grid(axis="x", visible=False)

    # ---- (c) gelir bileşimi: donanım vs SaaS ------------------------------
    axc = fig.add_subplot(gs[2])
    yrs = np.arange(1, 6)
    pkgs = np.array([5, 14, 32, 60, 96])          # kümülatif kurulu paket
    hw   = np.array([5, 9, 18, 28, 36])*0.36      # o yıl satılan paket x 360k
    saas = pkgs*0.054                              # paket başı 54k TL/yıl lisans
    axc.bar(yrs, hw,  color=INDIGO, alpha=0.85, width=0.6, label=r"Donan\i m (CAPEX)")
    axc.bar(yrs, saas, bottom=hw, color=GREEN, alpha=0.85, width=0.6,
            label=r"SaaS lisans (ARR)")
    for x, a, b in zip(yrs, hw, saas):
        axc.text(x, a+b+0.42, fr"${a+b:.1f}$M", ha="center", fontsize=10.5, color=INK)
    axc.set_xticks(yrs); axc.set_xticklabels([fr"Y{y}" for y in yrs], fontsize=11)
    axc.set_ylim(0, 22.5)
    axc.set_ylabel(r"Gelir $[\mathrm{milyon\;TL}]$")
    axc.legend(loc="upper left", fontsize=10.5)
    axc.set_title(r"\textbf{(c)} Gelir bile\c{s}imi", loc="left", fontsize=14)
    axc.grid(axis="x", visible=False)

    fig.text(0.5, -0.06,
             r"\.I\c{s} plan\i ndaki a\c{c}\i k varsay\i mlardan t\"uretilen "
             r"\emph{projeksiyondur}; ger\c{c}ekle\c{s}me de\u{g}ildir.",
             ha="center", fontsize=10, color=MUT)
    save(fig, "market_economics")

# =============================================================================
# 13 — tespit zaman çizelgesi: rakip teknolojilere göre kazanılan süre
# -----------------------------------------------------------------------------
# t = 0 tutuşma anı. Gaz ve kamera pencereleri iş planındaki kaynaklı
# değerlerdir (30–60 dk / 45–90 dk). Mycellium-Aegis penceresi, sayısal
# ikizdeki ısı iletim çözümünden gelir: T/R probu 5–8 cm'e alındığında
# ısıl cephe tutuşmadan önce eşiği geçiyor. Model sonucudur.
# =============================================================================
def fig_detection_timeline():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(8.6, 3.05))
    # Sol tarafta satır adları için ayrı bir şerit bırakılıyor; daha önce
    # etiketler -25 dk'da başlayan kutunun üstüne biniyordu.
    ax.set_xlim(-118, 102); ax.set_ylim(-0.35, 3.62)

    rows = [
        (2.60, -25,   0,  GREEN,   r"\textbf{Mycellium-Aegis}",
         r"\i s\i l cephe + biyoelektrik"),
        (1.55,  30,  60,  INDIGO,  r"Gaz / partik\"ul sens\"or\"u",
         r"r\"uzg\^ar dumani ta\c{s}\i y\i nca"),
        (0.50,  45,  90,  EMBER,   r"Kamera / optik kule",
         r"duman g\"or\"un\"ur olunca"),
    ]
    for y, a, b, c, name, sub in rows:
        ax.add_patch(FancyBboxPatch((a, y-0.26), b-a, 0.52,
                                    boxstyle="round,pad=0.02",
                                    facecolor=c, alpha=0.22, edgecolor=c, lw=1.8))
        # Aralık etiketi kutu dar olduğunda dışarı, geniş olduğunda içine
        txt = r"$-25\dots 0$ dk" if a == -25 else fr"${a:+d}\dots{b:+d}$ dk"
        ax.text((a+b)/2, y, txt, ha="center", va="center",
                fontsize=11.5, color=c)
        ax.text(-114, y+0.13, name, ha="left", va="center", fontsize=12.5, color=c)
        ax.text(-114, y-0.30, sub, ha="left", va="center", fontsize=10, color=MUT)

    # satır şeridi ile zaman ekseni arasına ince bir ayraç
    ax.axvline(-46, color=GRID, lw=1.0)

    # tutuşma anı
    ax.axvline(0, color=INK, lw=1.6)
    ax.text(3.0, 3.42, r"\textbf{tutu\c{s}ma} $t=0$", fontsize=12, color=INK,
            ha="left", va="center")
    ax.annotate("", xy=(-25, 3.42), xytext=(0, 3.42),
                arrowprops=dict(arrowstyle="<-", color=GREEN, lw=1.8))
    ax.text(-12.5, 3.13, r"kazan\i lan s\"ure", fontsize=11, color=GREEN,
            ha="center", va="bottom")

    ax.set_yticks([]); ax.set_xlabel(r"Tutu\c{s}maya g\"ore zaman $[\mathrm{dk}]$")
    ax.set_xticks([-25, 0, 30, 60, 90])
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color=GRID, lw=0.7)
    save(fig, "detection_timeline")

# =============================================================================
# 14 — iş modeli: donanım tek seferlik, SaaS tekrarlayan
# -----------------------------------------------------------------------------
# Paket başı: 360k TL satış / 160k TL maliyet -> 200k brüt kâr (%56).
# SaaS: 54k TL/yıl lisans, ~%85 brüt marj (bulut maliyeti düşük).
# Tümü iş planı varsayımı; ölçülmüş gerçekleşme değil.
# =============================================================================
def fig_business_model():
    HW_REV, HW_GP = 360.0, 200.0        # bin TL, tek seferlik
    SA_REV, SA_MG = 54.0, 0.85          # bin TL/yıl, brüt marj
    yrs = np.arange(0, 6)

    fig = plt.figure(figsize=(8.9, 3.15))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.45, 1.0], wspace=0.32)

    # ---- (a) paket başına kümülatif brüt kâr ------------------------------
    axa = fig.add_subplot(gs[0])
    hw = np.full_like(yrs, HW_GP, dtype=float)
    sa = yrs * SA_REV * SA_MG
    axa.fill_between(yrs, 0, hw, color=INDIGO, alpha=0.20,
                     label=r"Donan\i m --- tek seferlik")
    axa.fill_between(yrs, hw, hw+sa, color=GREEN, alpha=0.28,
                     label=r"SaaS lisans\i\ --- tekrarlayan")
    axa.plot(yrs, hw, color=INDIGO, lw=2.0)
    axa.plot(yrs, hw+sa, color=GREEN, lw=2.4)

    # SaaS brüt kârının donanımı geçtiği yıl. Not, göstergenin sol üstteki
    # yerine denk gelip üstünü çiziyordu; gösterge sağ alta, not üst
    # şeride alındı.
    xc = HW_GP / (SA_REV*SA_MG)
    axa.axvline(xc, color=EMBER, lw=1.3, ls=(0, (4, 3)))
    axa.annotate(r"SaaS, donan\i m\i\ ge\c{c}iyor",
                 xy=(xc, HW_GP*1.62), xytext=(xc-0.16, 432),
                 fontsize=11.5, color=EMBER, ha="right", va="center",
                 arrowprops=dict(arrowstyle="->", color=EMBER, lw=1.2))
    axa.set_xlim(0, 5); axa.set_ylim(0, 470)
    axa.set_xticks(yrs); axa.set_xticklabels([fr"Y{y}" for y in yrs], fontsize=12)
    axa.set_xlabel(r"Kurulumdan sonraki y\i l")
    axa.set_ylabel(r"K\"um\"ulatif br\"ut k\^ar $[\mathrm{bin\;TL}]$")
    axa.legend(loc="lower right", fontsize=11)
    axa.set_title(r"\textbf{(a)} Paket ba\c{s}\i na k\^ar bir\i kimi", loc="left", fontsize=14)

    # ---- (b) gelir kalitesi ----------------------------------------------
    axb = fig.add_subplot(gs[1])
    labels = [r"Donan\i m", r"SaaS"]
    marg = [HW_GP/HW_REV*100, SA_MG*100]
    bars = axb.bar(labels, marg, color=[INDIGO, GREEN], alpha=0.85, width=0.54)
    for b, m in zip(bars, marg):
        axb.text(b.get_x()+b.get_width()/2, m+3.5, fr"\%{m:.0f}",
                 ha="center", fontsize=13, color=b.get_facecolor())
    axb.text(0, -21, r"tek seferlik", ha="center", fontsize=10.5, color=MUT)
    axb.text(1, -21, r"her y\i l yenilenir", ha="center", fontsize=10.5, color=GREEN)
    axb.set_ylim(0, 108); axb.set_ylabel(r"Br\"ut marj $[\%]$")
    axb.tick_params(axis="x", labelsize=12.5, pad=8)
    axb.grid(axis="x", visible=False)
    axb.set_title(r"\textbf{(b)} Gelir kalitesi", loc="left", fontsize=14)

    fig.text(0.5, -0.085,
             r"\.I\c{s} plan\i\ varsay\i mlar\i ndan t\"uretilmi\c{s} projeksiyondur.",
             ha="center", fontsize=10, color=MUT)
    save(fig, "business_model")

if __name__ == "__main__":
    fig_signal_time()
    fig_fft()
    fig_heat()
    fig_fusion()
    fig_roc()
    fig_directional()
    fig_breakeven()
    fig_electrode()
    fig_architecture()
    fig_ai_pipeline()
    fig_electrode_material()
    fig_market()
    fig_detection_timeline()
    fig_business_model()
    print("ALL FIGURES DONE")
