#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mycellium-Aegis — publication-quality figures for the pitch deck.
scienceplots + matplotlib + LaTeX (Computer Modern). Transparent PDF + PNG.
Axis text kept in English/math so usetex (CM) renders cleanly; Turkish captions
live in the Beamer slides.
"""
import os
import numpy as np
import matplotlib as mpl
mpl.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from cycler import cycler

import scienceplots  # noqa: F401  (registers the 'science' style)

# ---- house style -----------------------------------------------------------
INK   = "#14201A"
GREEN = "#1B7A54"   # normal / primary data
EMBER = "#B4531B"   # fire / warning data
INDIGO= "#3B5BA5"   # tertiary data
GRID  = "#C9CCC4"
MUT   = "#5C6B62"

plt.style.use(["science"])
mpl.rcParams.update({
    "text.usetex": True,
    "text.latex.preamble": r"\usepackage{amsmath}\usepackage{bm}",
    "font.family": "serif",
    "font.size": 9.5,
    "axes.prop_cycle": cycler(color=[GREEN, EMBER, INDIGO]),
    "figure.dpi": 220,
    "savefig.dpi": 220,
    "savefig.transparent": True,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.02,
    "axes.edgecolor": "#41514A",
    "axes.linewidth": 0.7,
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": INK, "ytick.color": INK,
    "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "grid.alpha": 0.9,
    "legend.frameon": True, "legend.framealpha": 0.9, "legend.edgecolor": GRID,
    "legend.fontsize": 8,
})

HERE = os.path.dirname(os.path.abspath(__file__))
def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(HERE, f"{name}.{ext}"))
    plt.close(fig)
    print("wrote", name)

# erfc (prefer scipy; fall back to vectorised math.erfc)
try:
    from scipy.special import erfc
except Exception:  # pragma: no cover
    import math
    erfc = np.vectorize(math.erfc)

# ---- signal models (faithful to the measured Deney 1/2 characteristics) -----
def sig_normal(t):
    # baseline -2.9 mV, ~20 Hz dominant ripple, periodic 5 Hz negative pips to ~-29 mV
    rng = np.random.default_rng(7)
    return (-3.0 + 3.4*np.sin(2*np.pi*20*t)
            - 22.0*np.clip(np.sin(2*np.pi*5*t), 0, None)**12
            + 0.5*rng.standard_normal(t.shape))

def sig_fire(t):
    # dominant ~5 Hz, deep spikes clamped at the measured -33.4 mV minimum
    rng = np.random.default_rng(11)
    s = (-5.0 + 4.0*np.sin(2*np.pi*20*t)
         - 30.0*np.clip(np.sin(2*np.pi*5*t), 0, None)**4
         + 0.6*rng.standard_normal(t.shape))
    return np.clip(s, -33.4, None)

# =============================================================================
# 1 — time-domain bioelectric signal (two stacked panels)
# =============================================================================
def fig_signal_time():
    t = np.linspace(0, 5, 5*220)
    n, f = sig_normal(t), sig_fire(t)
    fig, ax = plt.subplots(2, 1, figsize=(5.6, 3.5), sharex=True)
    ax[0].plot(t, n, color=GREEN, lw=0.9)
    ax[0].axhline(-2.9, color=MUT, lw=0.7, ls=(0, (4, 3)))
    ax[0].text(4.98, -2.9, r"\,$\bar V=-2.9$", ha="right", va="bottom", color=MUT, fontsize=7)
    ax[0].set_ylabel(r"$V\;[\mathrm{mV}]$")
    ax[0].set_title(r"\textbf{Normal (dinlenim)}\quad$f_{\mathrm{dom}}\!\approx\!20$ Hz",
                    color=GREEN, fontsize=9, loc="left")
    ax[1].plot(t, f, color=EMBER, lw=0.9)
    ax[1].axhline(-33.4, color=EMBER, lw=0.7, ls=":")
    ax[1].text(4.98, -33.4, r"\,$V_{\min}=-33.4$", ha="right", va="bottom", color=EMBER, fontsize=7)
    ax[1].set_ylabel(r"$V\;[\mathrm{mV}]$")
    ax[1].set_xlabel(r"$t\;[\mathrm{s}]$")
    ax[1].set_title(r"\textbf{Ate\c{s} stresi}\quad$f_{\mathrm{dom}}\!\approx\!5$ Hz",
                    color=EMBER, fontsize=9, loc="left")
    for a in ax:
        a.set_xlim(0, 5); a.set_ylim(-36, 4)
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
    fig, ax = plt.subplots(figsize=(5.6, 3.0))
    ax.plot(fn, Xn, color=GREEN, lw=1.0, label=r"Normal")
    ax.plot(ff, Xf, color=EMBER, lw=1.0, ls=(0, (5, 2)), label=r"Ate\c{s} stresi")
    ax.set_xlim(0, 26); ax.set_ylim(bottom=0)
    ax.set_xlabel(r"Frekans $f\;[\mathrm{Hz}]$")
    ax.set_ylabel(r"Genlik $|\hat V(f)|\;[\mathrm{mV}]$")
    # annotate dominant peaks
    kn = np.argmax(Xn[(fn>1)])+np.searchsorted(fn,1)
    kf = np.argmax(Xf[(ff>1)])+np.searchsorted(ff,1)
    ax.annotate(r"$20\,$Hz", xy=(fn[kn], Xn[kn]), xytext=(fn[kn]+2.5, Xn[kn]),
                color=GREEN, fontsize=8, va="center",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.7))
    ax.annotate(r"$5\,$Hz", xy=(ff[kf], Xf[kf]), xytext=(ff[kf]+2.5, Xf[kf]*0.98),
                color=EMBER, fontsize=8, va="center",
                arrowprops=dict(arrowstyle="->", color=EMBER, lw=0.7))
    ax.legend(loc="upper right")
    save(fig, "fft_spectrum")

# =============================================================================
# 3 — 1-D transient heat conduction in soil  (analytic erfc solution)
#     T(z,t) = T0 + (Ts-T0) erfc( z / (2 sqrt(alpha t)) )
# =============================================================================
def fig_heat():
    T0, Ts = 20.0, 300.0
    alpha = 2.5e-7                      # effective diffusivity of moist forest soil [m^2/s]
    z = np.linspace(0, 0.30, 260)       # 0..30 cm
    tmin = np.linspace(0.5, 90, 320)    # minutes
    tt = tmin*60.0
    Z, T = np.meshgrid(z, tt)
    field = T0 + (Ts-T0)*erfc(Z/(2*np.sqrt(alpha*T)))

    fig = plt.figure(figsize=(5.7, 4.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.35, 1.0], hspace=0.42)
    axm = fig.add_subplot(gs[0])
    pm = axm.pcolormesh(tmin, z*100, field.T, cmap="afmhot_r", shading="auto",
                        vmin=20, vmax=180, rasterized=True)
    axm.axhline(17.5, color=INK, lw=1.0, ls=(0, (5, 2)))
    axm.text(1.5, 15.0, r"sens\"or yata\u{g}\i\;($z=17.5$ cm)", color=INK, fontsize=7.5, va="top")
    axm.set_ylabel(r"Derinlik $z\;[\mathrm{cm}]$")
    axm.set_xlabel(r"Zaman $t\;[\mathrm{dk}]$")
    axm.set_title(r"\textbf{Toprakta \i s\i\ yay\i n\i m\i}\;\;$\partial_t T=\alpha\,\partial_z^2 T$",
                  loc="left", fontsize=9)
    cb = fig.colorbar(pm, ax=axm, pad=0.02); cb.set_label(r"$T\;[^{\circ}\mathrm{C}]$", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    # depth curves + derivative at sensor bed
    axc = fig.add_subplot(gs[1])
    for zi, c, ls in [(0.05, INDIGO, "-"), (0.10, GREEN, "-"), (0.175, EMBER, "-")]:
        Tz = T0 + (Ts-T0)*erfc(zi/(2*np.sqrt(alpha*tt)))
        axc.plot(tmin, Tz, color=c, ls=ls, lw=1.1, label=fr"$z={int(zi*100)}$ cm")
    axc.set_xlabel(r"Zaman $t\;[\mathrm{dk}]$")
    axc.set_ylabel(r"$T\;[^{\circ}\mathrm{C}]$")
    axc.set_xlim(0, 90)
    axc.legend(loc="upper left", ncol=3, fontsize=7)
    axc.set_title(r"Derinli\u{g}e g\"ore s\i cakl\i k \& t\"urev tabanl\i\ e\c{s}ik $dT/dt>\beta$",
                  loc="left", fontsize=8)
    save(fig, "heat_diffusion")

# =============================================================================
# 4 — sensor-fusion feature space & decision region (AND-gate + LSTM boundary)
# =============================================================================
def fig_fusion():
    rng = np.random.default_rng(3)
    # normal: low dT/dt, shallow spike depth ; fire: high both
    nrm = np.column_stack([rng.normal(0.4, 0.35, 260), rng.normal(6, 3.0, 260)])
    fire = np.column_stack([rng.normal(3.6, 0.7, 150), rng.normal(28, 4.0, 150)])
    nrm[:, 0] = np.clip(nrm[:, 0], 0, None); fire[:, 1] = np.clip(fire[:, 1], 0, None)
    bx, by = 1.8, 15.0                          # beta thresholds
    fig, ax = plt.subplots(figsize=(4.7, 3.7))
    ax.axvspan(bx, 6, ymin=(by)/40, color=EMBER, alpha=0.10)
    ax.scatter(nrm[:, 0], nrm[:, 1], s=9, color=GREEN, alpha=0.8, label=r"Normal", edgecolor="none")
    ax.scatter(fire[:, 0], fire[:, 1], s=12, color=EMBER, alpha=0.85, marker="^",
               label=r"Ate\c{s}", edgecolor="none")
    ax.axvline(bx, color=MUT, lw=0.8, ls=(0, (4, 3)))
    ax.axhline(by, color=MUT, lw=0.8, ls=(0, (4, 3)))
    # smooth LSTM-style boundary
    xx = np.linspace(0, 6, 200)
    yy = 15 + 9*np.tanh((xx-2.0)*1.4)
    ax.plot(xx, yy, color=INDIGO, lw=1.4, label=r"LSTM s\i n\i r\i")
    ax.text(3.9, 36, r"\textbf{ALARM}", color=EMBER, fontsize=8, ha="center")
    ax.text(0.15, 37, r"$\beta_{T}$", color=MUT, fontsize=8)
    ax.set_xlim(0, 6); ax.set_ylim(0, 40)
    ax.set_xlabel(r"Is\i\ ivmesi $\dfrac{dT}{dt}\;[^{\circ}\mathrm{C}/\mathrm{dk}]$")
    ax.set_ylabel(r"Spike derinli\u{g}i $|\Delta V|\;[\mathrm{mV}]$")
    ax.legend(loc="lower right", fontsize=7)
    ax.set_title(r"\textbf{Sens\"or f\"uzyonu — ay\i rt edilebilirlik}", loc="left", fontsize=9)
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
    fig, ax = plt.subplots(figsize=(4.5, 3.6))
    ax.plot([0, 1], [0, 1], color=MUT, lw=0.8, ls=":")
    ax.plot(f1, t1, color=INDIGO, lw=1.3, label=fr"Tek e\c{{s}}ik  (AUC$=${a1:.2f})")
    ax.plot(f2, t2, color=GREEN, lw=1.6, label=fr"Sens\"or f\"uzyonu  (AUC$=${a2:.2f})")
    # operating point at FPR < 1%
    i = np.argmin(np.abs(f2-0.01))
    ax.scatter([f2[i]], [t2[i]], s=28, color=EMBER, zorder=5)
    ax.annotate(r"\%1 yanl\i\c{s} alarm", xy=(f2[i], t2[i]), xytext=(0.28, 0.55),
                color=EMBER, fontsize=8,
                arrowprops=dict(arrowstyle="->", color=EMBER, lw=0.7))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
    ax.set_xlabel(r"Yanl\i\c{s} alarm oran\i\ (FPR)")
    ax.set_ylabel(r"Do\u{g}ru tespit oran\i\ (TPR)")
    ax.legend(loc="lower right", fontsize=7.5)
    ax.set_title(r"\textbf{ROC — f\"uzyon vs. tek e\c{s}ik}", loc="left", fontsize=9)
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
    # weighted circular mean -> estimated AoA
    est = np.angle(np.sum(resp*np.exp(1j*ang)))
    fig = plt.figure(figsize=(4.3, 3.9))
    ax = fig.add_subplot(projection="polar")
    ax.set_theta_zero_location("N"); ax.set_theta_direction(-1)
    ax.bar(ang, resp, width=np.deg2rad(30), color=GREEN, alpha=0.55, edgecolor=GREEN, lw=0.8)
    ax.plot([est, est], [0, 1.05], color=EMBER, lw=1.8)
    ax.plot([src, src], [0, 1.05], color=INDIGO, lw=1.0, ls=(0, (4, 2)))
    ax.scatter(ang, resp, s=14, color=GREEN, zorder=6)
    ax.set_rmax(1.15); ax.set_rticks([0.5, 1.0]); ax.set_yticklabels([])
    ax.set_xticks(np.deg2rad([0, 45, 90, 135, 180, 225, 270, 315]))
    ax.set_xticklabels([r"K", r"KD", r"D", r"GD", r"G", r"GB", r"B", r"KB"], fontsize=8)
    ax.set_title(r"\textbf{Y\"onsel alg\i lama}\;\; $\hat\theta=\arg\!\sum_k r_k e^{i\theta_k}$",
                 fontsize=8.5, pad=14)
    ax.text(est, 1.28, fr"$\hat\theta={np.rad2deg(est):.0f}^{{\circ}}$", color=EMBER,
            ha="center", fontsize=8)
    save(fig, "directional")

# =============================================================================
# 7 — break-even analysis
# =============================================================================
def fig_breakeven():
    x = np.linspace(0, 8, 200)
    rev = 360*x
    cost = 880 + 160*x
    be = 880/200.0
    fig, ax = plt.subplots(figsize=(5.2, 3.3))
    ax.fill_between(x, rev, cost, where=(rev >= cost), color=GREEN, alpha=0.10)
    ax.plot(x, rev, color=GREEN, lw=1.6, label=r"Gelir $=360k\cdot n$")
    ax.plot(x, cost, color=EMBER, lw=1.6, label=r"Toplam maliyet $=880k+160k\cdot n$")
    ax.axhline(880, color=MUT, lw=0.7, ls=(0, (4, 3)))
    ax.axvline(be, color=INK, lw=0.8, ls=":")
    ax.scatter([be], [360*be], s=34, color=INK, zorder=6)
    ax.annotate(r"Ba\c{s}a ba\c{s}: $n=4.4\!\to\!5$ paket", xy=(be, 360*be),
                xytext=(be+0.4, 360*be-620), fontsize=8,
                arrowprops=dict(arrowstyle="->", color=INK, lw=0.7))
    ax.set_xlim(0, 8); ax.set_ylim(0, 3000)
    ax.set_xlabel(r"Sat\i lan paket say\i s\i\ $n$")
    ax.set_ylabel(r"Tutar $[\times 10^{3}\;\mathrm{TL}]$")
    ax.legend(loc="upper left", fontsize=7.5)
    ax.set_title(r"\textbf{Ba\c{s}a ba\c{s} analizi}", loc="left", fontsize=9)
    save(fig, "breakeven")

# =============================================================================
# 8 — electrode cross-section (3-layer concentric)
# =============================================================================
def fig_electrode():
    from matplotlib.patches import Circle, FancyArrowPatch, Wedge
    fig, ax = plt.subplots(figsize=(4.8, 4.8))
    ax.set_aspect('equal')
    ax.set_xlim(-1.7, 1.7); ax.set_ylim(-1.7, 1.7)
    ax.axis('off')
    # layers (outside-in)
    layers = [
        (1.4, GREEN, 0.18, r"\textbf{D\i\c{s}}: Sodyum Aljinat Hidrojel"),
        (0.95, MUT,  0.15, r"\textbf{Orta}: \.Iletken Grafit Matris"),
        (0.52, "#888890", 0.12, r"\textbf{\c{C}ekirdek}: 316L \c{C}elik"),
    ]
    for r, c, a, lbl in layers:
        circ = Circle((0, 0), r, fill=True, facecolor=c, alpha=a,
                       edgecolor=c, lw=1.8, ls='-')
        ax.add_patch(circ)
    # mycelium tendrils on outer layer
    rng = np.random.default_rng(42)
    for _ in range(18):
        th = rng.uniform(0, 2*np.pi)
        r0 = 1.38
        dr = rng.uniform(0.15, 0.35)
        x0, y0 = r0*np.cos(th), r0*np.sin(th)
        x1, y1 = (r0+dr)*np.cos(th+rng.uniform(-.15,.15)), (r0+dr)*np.sin(th+rng.uniform(-.15,.15))
        ax.plot([x0, x1], [y0, y1], color=GREEN, lw=0.8, alpha=0.6)
        ax.plot(x1, y1, 'o', color=GREEN, ms=2.5, alpha=0.5)
    # labels with lines
    ax.annotate(layers[0][3], xy=(0.99, 0.99), xytext=(1.35, 1.55),
                fontsize=7.5, color=GREEN, ha='center',
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=0.7))
    ax.annotate(layers[1][3], xy=(0.67, -0.67), xytext=(1.3, -1.45),
                fontsize=7.5, color=MUT, ha='center',
                arrowprops=dict(arrowstyle='->', color=MUT, lw=0.7))
    ax.annotate(layers[2][3], xy=(0, 0), xytext=(-1.35, -1.45),
                fontsize=7.5, color='#888890', ha='center',
                arrowprops=dict(arrowstyle='->', color='#888890', lw=0.7))
    # 8 electrode arms
    for i in range(8):
        th = i * np.pi/4
        ax.plot([0.52*np.cos(th), 1.38*np.cos(th)],
                [0.52*np.sin(th), 1.38*np.sin(th)],
                color=GREEN, lw=1.2, alpha=0.4, ls=(0,(5,3)))
        ax.plot(1.38*np.cos(th), 1.38*np.sin(th), 'o', color=GREEN, ms=4, zorder=5)
    dirs = ['K','KD','D','GD','G','GB','B','KB']
    for i, d in enumerate(dirs):
        th = i * np.pi/4
        ax.text(1.58*np.cos(th), 1.58*np.sin(th), d,
                ha='center', va='center', fontsize=7, color=INK)
    ax.set_title(r"\textbf{\"U\c{c} katmanl\i\\ biyomimetik k\"ok-elektrot}", fontsize=10, pad=12)
    save(fig, "electrode_cross_section")

# =============================================================================
# 9 — system architecture (terrarium → gateway → cloud → alert)
# =============================================================================
def fig_architecture():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(7.2, 2.8))
    ax.set_xlim(-0.2, 7.5); ax.set_ylim(-0.5, 2.5)
    ax.axis('off')
    boxes = [
        (0.0, 0.3, 1.3, 1.4, GREEN, r"Sens\"or"+"\n"+r"Teraryum", r"Biyoelektrot"+"\n"+r"ESP32 + ADC"),
        (2.0, 0.3, 1.3, 1.4, INDIGO, r"A\u{g} Ge\c{c}idi", r"LoRaWAN 868"+"\n"+r"Mesh gateway"),
        (4.0, 0.3, 1.3, 1.4, EMBER, r"Bulut / U\c{c}", r"LSTM f\"uzyon"+"\n"+r"AND-gate karar"),
        (6.0, 0.3, 1.3, 1.4, "#cc3333", r"Alarm", r"SaaS pano"+"\n"+r"SMS / API"),
    ]
    for x, y, w, h, c, title, sub in boxes:
        bb = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                            facecolor=c, alpha=0.15, edgecolor=c, lw=1.5)
        ax.add_patch(bb)
        ax.text(x+w/2, y+h*0.68, title, ha='center', va='center',
                fontsize=8.5, fontweight='bold', color=c)
        ax.text(x+w/2, y+h*0.28, sub, ha='center', va='center',
                fontsize=6.5, color=MUT, linespacing=1.4)
    # arrows
    for i in range(3):
        x0 = boxes[i][0] + boxes[i][2]
        x1 = boxes[i+1][0]
        ymid = 1.0
        ax.annotate('', xy=(x1, ymid), xytext=(x0, ymid),
                    arrowprops=dict(arrowstyle='->', color=INK, lw=1.3))
        labels = [r"LoRa 868\,MHz", r"TLS 1.3 / MQTT", r"WebSocket"]
        ax.text((x0+x1)/2, ymid+0.18, labels[i], ha='center', fontsize=6, color=MUT)
    # top label
    ax.text(3.65, 2.25, r"\textbf{Mycellium-Aegis --- Sistem Mimarisi}", ha='center', fontsize=10, color=INK)
    save(fig, "system_architecture")

# =============================================================================
# 10 — AI signal processing pipeline
# =============================================================================
def fig_ai_pipeline():
    from matplotlib.patches import FancyBboxPatch
    fig, ax = plt.subplots(figsize=(7.5, 3.6))
    ax.set_xlim(-0.3, 7.8); ax.set_ylim(-1.0, 3.2)
    ax.axis('off')
    steps = [
        (r"\textbf{01}", r"Ofset"+"\n"+r"Kalibrasyon",
         r"$\bar{x}_{50}$ DC "+r"\"o"+r"teleme", GREEN),
        (r"\textbf{02}", r"5-tap FIR"+"\n"+r"Filtre",
         r"$y[n]=\sum h_k\,x[n\!-\!k]$", GREEN),
        (r"\textbf{03}", r"\"Oznitelik"+"\n"+r"\c{C}\i kar\i m",
         r"FFT $\cdot$ $dT\!/\!dt$ $\cdot$ $f_{\mathrm{spike}}$", INDIGO),
        (r"\textbf{04}", r"LSTM"+"\n"+r"S\i n\i fland\i rma",
         r"Zaman serisi $\to$ skor", INDIGO),
        (r"\textbf{05}", r"AND-Gate"+"\n"+r"Karar",
         r"3 ko\c{s}ul $\Rightarrow$ alarm", EMBER),
    ]
    w, h = 1.2, 1.5
    gap = 0.35
    for i, (num, title, eq, c) in enumerate(steps):
        x = i * (w + gap)
        bb = FancyBboxPatch((x, 0), w, h, boxstyle="round,pad=0.08",
                            facecolor=c, alpha=0.12, edgecolor=c, lw=1.5)
        ax.add_patch(bb)
        ax.text(x+w/2, h-0.2, num, ha='center', va='center',
                fontsize=7, color=c)
        ax.text(x+w/2, h*0.55, title, ha='center', va='center',
                fontsize=7.5, fontweight='bold', color=INK, linespacing=1.3)
        ax.text(x+w/2, 0.18, eq, ha='center', va='center',
                fontsize=6.5, color=MUT)
        if i < len(steps)-1:
            ax.annotate('', xy=(x+w+gap-0.05, h/2), xytext=(x+w+0.05, h/2),
                        arrowprops=dict(arrowstyle='->', color=INK, lw=1.2))
    # AND gate detail below
    ax.text(3.5, -0.55, r"$\left(\frac{dT}{dt}>\beta\right) \;\wedge\; "
            r"\left(\frac{dR}{dt}>\gamma\right) \;\wedge\; "
            r"\left(f_{\mathrm{spike}} \in [0.5,5]\,\mathrm{Hz},\;"
            r"V_{\min}\!<\!-33\,\mathrm{mV}\right)$",
            ha='center', va='center', fontsize=8, color=EMBER,
            bbox=dict(boxstyle='round,pad=0.3', facecolor=EMBER, alpha=0.08, edgecolor=EMBER, lw=0.8))
    ax.set_title(r"\textbf{Sinyal i\c{s}leme hatt\i\\ --- ham gerilimden karara}", fontsize=10, pad=10)
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
