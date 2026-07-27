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
    "text.latex.preamble": r"\usepackage{amsmath}\usepackage{bm}",
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
    fig, ax = plt.subplots(figsize=(8.2, 2.53))
    ax.set_xlim(-0.25, 8.15); ax.set_ylim(-1.0, 1.8)
    ax.axis('off')
    steps = [
        (r"\textbf{01}", r"Ofset"+"\n"+r"Kalibrasyon", r"$\bar{x}_{50}$ DC "+r"\"o"+r"teleme", GREEN),
        (r"\textbf{02}", r"5-tap FIR"+"\n"+r"Filtre", r"$y[n]=\sum h_k\,x[n\!-\!k]$", GREEN),
        (r"\textbf{03}", r"\"Oznitelik"+"\n"+r"\c{C}\i kar\i m", r"FFT $\cdot$ $dT\!/\!dt$ $\cdot$ $f_{\mathrm{spike}}$", INDIGO),
        (r"\textbf{04}", r"LSTM"+"\n"+r"S\i n\i fland\i rma", r"Zaman serisi $\to$ skor", INDIGO),
        (r"\textbf{05}", r"AND-Gate"+"\n"+r"Karar", r"3 ko\c{s}ul $\Rightarrow$ alarm", EMBER),
    ]
    w, h = 1.3, 1.6
    gap = 0.35
    for i, (num, title, eq, c) in enumerate(steps):
        x = i * (w + gap)
        bb = FancyBboxPatch((x, 0), w, h, boxstyle="round,pad=0.08",
                            facecolor=c, alpha=0.06, edgecolor=c, lw=2.25)
        ax.add_patch(bb)
        ax.text(x+w/2, h-0.2, num, ha='center', va='center', fontsize=11.2, color=c)
        ax.text(x+w/2, h*0.55, title, ha='center', va='center',
                fontsize=11.9, fontweight='bold', color=INK, linespacing=1.4)
        ax.text(x+w/2, 0.18, eq, ha='center', va='center', fontsize=11, color=MUT)
        if i < len(steps)-1:
            ax.annotate('', xy=(x+w+gap-0.05, h/2), xytext=(x+w+0.05, h/2),
                        arrowprops=dict(arrowstyle='->', color=MUT, lw=1.88))
    ax.text(3.9, -0.55, r"$\left(\frac{dT}{dt}>\beta\right) \;\wedge\; "
            r"\left(\frac{dR}{dt}>\gamma\right) \;\wedge\; "
            r"\left(f_{\mathrm{spike}} \in [0.5,5]\,\mathrm{Hz},\;"
            r"V_{\min}\!<\!-33\,\mathrm{mV}\right)$",
            ha='center', va='center', fontsize=12.6, color=EMBER,
            bbox=dict(boxstyle='round,pad=0.4', facecolor=EMBER, alpha=0.06, edgecolor=EMBER, lw=1.25))
    ax.set_title(r"\textbf{Sinyal i\c{s}leme hatt\i\\ --- ham gerilimden karara}", fontsize=16.1, pad=12)
    save(fig, "ai_pipeline")

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
    print("ALL FIGURES DONE")
