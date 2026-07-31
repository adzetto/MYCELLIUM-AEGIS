"""
=============================================================================
MYCELLIUM-AEGIS · FİZİBİLİTE ANALİZİ
run_all.py — bütün sayısal çalışmayı yürütür ve pgfplots tablolarını üretir
-----------------------------------------------------------------------------
Çıktılar `docs/feasibility/data/*.dat` altına yazılır (boşlukla ayrılmış,
ilk satır sütun adları — pgfplots `table` ile doğrudan okunur) ve başlık
sayıları `summary.json` dosyasına düşer.

Çalıştırma:  python run_all.py [--quick]
`--quick` Monte Carlo örneklem sayılarını düşürür (geliştirme için).

Bütün rastgelelik sabit tohumludur; betik yeniden çalıştırıldığında aynı
sayılar üretilir.
=============================================================================
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.special import k0 as bessel_k0
from scipy.stats import qmc

sys.path.insert(0, str(Path(__file__).parent))
from aegis_physics import (Soil, CoupledColumn, AnisotropicSlab, AxisymmetricERT,
                           fusion_alarm, surface_temperature, mms_fields, ert_mms,
                           observed_order, richardson_gci, von_neumann_bound,
                           damped_thermal_wave, L_VAP, RHO_W)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
QUICK = "--quick" in sys.argv
S = {}                                   # summary.json içeriği
T0 = time.time()


def log(msg):
    print(f"[{time.time() - T0:7.1f}s] {msg}", flush=True)


def table(name, header, *cols):
    """pgfplots tablosu yaz. header: boşlukla ayrılmış sütun adları (ASCII)."""
    arr = np.column_stack([np.asarray(c, float).ravel() for c in cols])
    path = DATA / f"{name}.dat"
    with path.open("w", encoding="ascii") as fh:
        fh.write(header + "\n")
        for row in arr:
            fh.write(" ".join(f"{v:.8g}" for v in row) + "\n")
    log(f"  -> {path.name}  ({arr.shape[0]} satir)")


# =============================================================================
# A · TENSÖR CEBİRİ — anizotropi ve akı yönelim sapması
# =============================================================================
def part_A():
    log("A · tensor cebiri: anizotropi, akinin gradyanla acisi")
    k_par, k_perp = 1.60, 0.85              # W/(m K) katman içi / katmana dik
    dips = np.linspace(0.0, 45.0, 91)
    Kxx, Kxz, Kzz, misalign = [], [], [], []
    # Düşey sıcaklık gradyanı (ısıl cephe aşağı doğru) için akı yönelimi
    gradT = np.array([0.0, 1.0])            # ∇T = (0,1) — düşey
    for psi in dips:
        K = AnisotropicSlab.tensor(k_par, k_perp, psi)
        q = -K @ gradT
        ang = np.degrees(np.arccos(np.clip(
            (q @ -gradT) / (np.linalg.norm(q) * np.linalg.norm(gradT)), -1, 1)))
        Kxx.append(K[0, 0]); Kxz.append(K[0, 1]); Kzz.append(K[1, 1])
        misalign.append(ang)
    table("tensor_dip", "dip Kxx Kxz Kzz misalign", dips, Kxx, Kxz, Kzz, misalign)

    # tensörün özdeğerleri dip'ten bağımsızdır (dönme değişmezliği) — kontrol
    K25 = AnisotropicSlab.tensor(k_par, k_perp, 25.0)
    ev = np.linalg.eigvalsh(K25)
    S["tensor"] = dict(k_par=k_par, k_perp=k_perp, anisotropy=k_par / k_perp,
                       eig=[float(ev[0]), float(ev[1])],
                       misalign_max=float(np.max(misalign)),
                       dip_at_max=float(dips[int(np.argmax(misalign))]),
                       Kxz_at_25=float(K25[0, 1]))


# =============================================================================
# B · DOĞRULAMA — üretilmiş çözümler, yakınsama mertebeleri, kararlılık
# =============================================================================
def part_B():
    log("B · dogrulama: MMS, yakinsama, kararlilik")
    # ---- B1: 2B tam tensörlü ısı operatörü, üretilmiş çözüm ----------------
    Lx, Lz, rho_c = 1.0, 0.6, 2.0e6
    ns, l2s, linfs = [], [], []
    for n in [16, 32, 64, 128, 256]:
        sl = AnisotropicSlab(Lx, Lz, n, int(n * 0.6))
        T0f, Kxx, Kxz, Kzz, f0 = mms_fields(sl.X, sl.Z, 0.0, Lx, Lz, rho_c=rho_c)
        div_num = sl.divergence(T0f, Kxx, Kxz, Kzz)
        div_exact = rho_c * (-T0f / 4000.0) - f0
        e = np.abs(div_num - div_exact)[2:-2, 2:-2]
        ns.append(n); l2s.append(np.sqrt(np.mean(e ** 2))); linfs.append(e.max())
    p_th = observed_order(l2s)
    table("conv_mms_thermal", "n h l2 linf", ns, [Lx / n for n in ns], l2s, linfs)

    # ---- B2: eksenel simetrik elektriksel operatör, üretilmiş çözüm --------
    sh, sv = 0.020, 0.010
    ns2, e2 = [], []
    for n in [40, 80, 160, 320]:
        ert = AxisymmetricERT(rmax=1.0, zmax=1.0, nr=n, nz=n)
        R, Z = np.meshgrid(ert.r, ert.z, indexing="ij")
        ana, src = ert_mms(R, Z, 1.0, 1.0, sh, sv)
        phi = ert.solve(sh, sv, [], phi_bc=lambda r, z: ert_mms(r, z, 1.0, 1.0, sh, sv)[0],
                        source_density=src)
        ns2.append(n)
        e2.append(np.sqrt(np.mean((phi - ana) ** 2)) / np.sqrt(np.mean(ana ** 2)))
    p_ert = observed_order(e2)

    # ---- B3: nokta kaynak — anizotropik yarı-uzayın analitik çözümü -------
    ns3, e3 = [], []
    for n in [60, 120, 240]:
        ert = AxisymmetricERT(rmax=1.2, zmax=1.2, nr=n, nz=n)
        R, Z = np.meshgrid(ert.r, ert.z, indexing="ij")
        bc = lambda r, z: AxisymmetricERT.analytic_halfspace(r, z, 0.10, sh, sv)
        ana = AxisymmetricERT.analytic_halfspace(R, Z, 0.10, sh, sv)
        phi = ert.solve(sh, sv, [(0.10, 1.0)], phi_bc=bc)
        mask = np.sqrt(R ** 2 + (Z - 0.10) ** 2) > 0.15
        ns3.append(n)
        e3.append(np.sqrt(np.mean(((phi - ana)[mask] / ana[mask]) ** 2)))
    p_pt = observed_order(e3)
    table("conv_mms_ert", "n h smooth point",
          ns2, [1.0 / n for n in ns2], e2, e3 + [np.nan] * (len(ns2) - len(e3)))

    # ---- B4: bağlaşık sütunun ızgara ve zaman adımı yakınsaması -----------
    soil = Soil()
    nzs, lead_nz = [60, 120, 240, 480], []
    for nz in nzs:
        c = CoupledColumn(soil, depth=0.60, nz=nz)
        r = c.run(theta0=0.22, t_amb=22.0, scenario="preignition",
                  t_end=8 * 3600, dt=5.0, probe_depth=0.06, spin_dt=300.0)
        lead_nz.append(fusion_alarm(r)["lead"][0] / 60.0)
    d = np.abs(np.diff(lead_nz))
    p_grid = float(np.log(d[-2] / d[-1]) / np.log(2))
    gci_grid = float(richardson_gci(lead_nz[-2], lead_nz[-1], max(p_grid, 0.5)))
    table("conv_grid", "nz dz_mm lead", nzs, [600.0 / n for n in nzs], lead_nz)

    dts, lead_dt = [40.0, 20.0, 10.0, 5.0], []
    col = CoupledColumn(soil, depth=0.60, nz=240)
    for dt in dts:
        r = col.run(theta0=0.22, t_amb=22.0, scenario="preignition",
                    t_end=8 * 3600, dt=dt, probe_depth=0.06, spin_dt=300.0)
        lead_dt.append(fusion_alarm(r)["lead"][0] / 60.0)
    dd = np.abs(np.diff(lead_dt))
    p_time = float(np.log(dd[-2] / dd[-1]) / np.log(2))
    table("conv_dt", "dt lead", dts, lead_dt)

    # ---- B5: von Neumann — bağlaşık sistemin açık şema sınırı --------------
    # 2×2 blok yayınım matrisi, tipik çalışma noktasında (θ=0.15, T=60 °C)
    th_, T_ = 0.15, 60.0
    Cv = soil.heat_capacity(th_)
    Dblk = np.array([
        [soil.lam_eff(th_, T_) / Cv,        L_VAP * RHO_W * soil.D_thv(th_, T_) / Cv],
        [soil.D_Tv(th_, T_),                soil.D_liquid(th_) + soil.D_thv(th_, T_)]
    ])
    dz = 0.0025
    dt_max, ev = von_neumann_bound(Dblk, dz)
    sym = 0.5 * (Dblk + Dblk.T)
    coerc = float(np.min(np.linalg.eigvalsh(sym)))

    # ---- B6: düzenlileştirme parametrelerine duyarsızlık -------------------
    # k₀ ve ΔT, kaynama cephesini çözmeye yarayan sayısal gevşeme
    # parametreleridir; sonucun bunlara duyarsız olması gerekir.
    reg = []
    for kb in (5e-4, 1e-3, 5e-3):
        for dTb in (4.0, 8.0, 16.0):
            c = CoupledColumn(soil, depth=0.60, nz=240, k_boil=kb, dT_boil=dTb)
            r = c.run(theta0=0.22, t_amb=22.0, scenario="preignition",
                      t_end=8 * 3600, dt=10.0, probe_depth=0.06, spin_dt=300.0)
            reg.append((kb, dTb, fusion_alarm(r)["lead"][0] / 60.0))
    table("conv_reg", "kboil dTboil lead", [r[0] for r in reg],
          [r[1] for r in reg], [r[2] for r in reg])
    lv = np.array([r[2] for r in reg])

    # ---- B7: izotermal gizli ısı teriminin katkısı ------------------------
    # Terim kararlı bir zaman adımında (Δt = 2 s) açık ve kapalı koşularak
    # ihmalin öncü süreye etkisi ölçülür.
    lat = {}
    for flag in (False, True):
        c = CoupledColumn(soil, depth=0.60, nz=240, latent_iso=flag)
        r = c.run(theta0=0.22, t_amb=22.0, scenario="preignition",
                  t_end=8 * 3600, dt=2.0, probe_depth=0.06, spin_dt=60.0)
        lat[flag] = fusion_alarm(r)["lead"][0] / 60.0

    S["verification"] = dict(
        reg_lead_min=float(lv.min()), reg_lead_max=float(lv.max()),
        latent_off=float(lat[False]), latent_on=float(lat[True]),
        latent_delta_pct=float(100 * abs(lat[True] - lat[False]) / lat[False]),
        reg_spread_pct=float(100 * (lv.max() - lv.min()) / lv.mean()),
        p_mms_thermal=[float(x) for x in p_th],
        p_mms_ert=[float(x) for x in p_ert],
        p_point_source=[float(x) for x in p_pt],
        p_grid=p_grid, gci_grid_pct=100 * gci_grid,
        p_time=p_time, lead_grid=lead_nz, lead_dt=lead_dt,
        dt_explicit_max=float(dt_max),
        D_block=[[float(v) for v in row] for row in Dblk],
        D_eigs=[float(np.real(v)) for v in ev],
        coercivity=coerc,
        lead_reference=float(lead_nz[-1]),
        num_uncertainty_min=float(abs(lead_nz[-1] - lead_nz[-2]) + abs(lead_dt[-1] - lead_dt[-2])))


# =============================================================================
# C · NOMİNAL ÇÖZÜM — zaman serileri ve profiller
# =============================================================================
def part_C():
    log("C · nominal cozum: zaman serisi + profiller")
    soil = Soil()
    col = CoupledColumn(soil, depth=0.60, nz=240)
    rec = [t * 3600 for t in (3.0, 3.5, 4.0, 4.5, 5.0, 6.0)]
    res = col.run(theta0=0.22, t_amb=22.0, scenario="preignition", t_end=9 * 3600,
                  dt=5.0, probe_depth=0.06, spin_dt=300.0, record=rec)
    al = fusion_alarm(res)
    t_h = res["t"] / 3600.0
    step = max(1, len(t_h) // 900)
    sl = slice(None, None, step)
    table("nominal_ts", "t Tsurf Tprobe theta lnR dTdt dlnR",
          t_h[sl], res["T_surf"][0][sl], res["T_probe"][0][sl], res["th_probe"][0][sl],
          res["lnR"][0][sl], al["dTdt"][0][sl], al["dlnR"][0][sl])

    z_cm = res["z"] * 100.0
    cols, hdr = [z_cm], "z"
    for t_ in rec:
        T_, th_ = res["profiles"][t_]
        cols += [T_[0], th_[0]]
        hdr += f" T{t_ / 3600:.1f} th{t_ / 3600:.1f}".replace(".", "p")
    table("nominal_profile", hdr, *cols)

    # kuraklık ve normal gün — yanlış alarm referansı
    out = {}
    for sc, th0, ta in [("drought", 0.16, 30.0), ("normal", 0.22, 22.0)]:
        r = col.run(theta0=th0, t_amb=ta, scenario=sc, t_end=24 * 3600, dt=20.0,
                    probe_depth=0.06, spin_dt=300.0)
        a = fusion_alarm(r)
        out[sc] = dict(max_dTdt=float(a["dTdt"].max()),
                       max_abs_dlnR=float(np.abs(a["dlnR"]).max()),
                       alarm=bool(np.isfinite(a["t_alarm"][0])))
        tt = r["t"] / 3600.0
        st = max(1, len(tt) // 600)
        table(f"scenario_{sc}", "t Tsurf Tprobe theta dTdt dlnR",
              tt[::st], r["T_surf"][0][::st], r["T_probe"][0][::st],
              r["th_probe"][0][::st], a["dTdt"][0][::st], a["dlnR"][0][::st])

    d_damp, amp6, rate6 = damped_thermal_wave(0.06, 8.9e-7)
    S["nominal"] = dict(lead_min=float(al["lead"][0] / 60),
                        t_alarm_h=float(al["t_alarm"][0] / 3600),
                        t_ignite_h=float(al["t_ignite"][0] / 3600),
                        t_beta_h=float(al["t_beta"][0] / 3600),
                        t_gamma_h=float(al["t_gamma"][0] / 3600),
                        max_dTdt=float(al["dTdt"].max()),
                        min_dlnR=float(al["dlnR"].min()),
                        damping_depth_cm=float(d_damp * 100),
                        diurnal_amp6=float(amp6), diurnal_rate6=float(rate6),
                        **out)

    # ---- tek yönlü ve iki yönlü γ kuralının prob derinliğine göre farkı ----
    log("C · prob derinligi taramasi")
    zs = np.arange(0.02, 0.221, 0.01)
    l2, l1 = [], []
    for zp in zs:
        r = col.run(theta0=0.22, t_amb=22.0, scenario="preignition", t_end=9 * 3600,
                    dt=10.0, probe_depth=float(zp), spin_dt=300.0)
        l2.append(fusion_alarm(r, two_sided=True)["lead"][0] / 60)
        l1.append(fusion_alarm(r, two_sided=False)["lead"][0] / 60)
    l2 = np.array(l2); l1 = np.nan_to_num(np.array(l1), nan=-999.0)
    table("depth_sweep", "z lead_two lead_one", zs * 100, l2, l1)
    ok = np.isfinite(l2)
    S["depth"] = dict(z_cm=[float(v * 100) for v in zs],
                      lead_two=[float(v) for v in l2],
                      lead_one=[float(v) for v in l1],
                      lead_at_6=float(np.interp(0.06, zs, l2)),
                      lead_at_18=float(np.interp(0.18, zs, l2)),
                      z_zero_cross=float(np.interp(0.0, l2[ok][::-1], zs[ok][::-1] * 100)))


# =============================================================================
# D · ELEKTRİKSEL DUYARLILIK ÇEKİRDEĞİ (Geselowitz) ve Born doğrulaması
# =============================================================================
def part_D():
    log("D · ERT duyarlilik cekirdegi + Born yaklasimi dogrulamasi")
    soil = Soil()
    # dört elektrotlu düşey dizilim, prob derinliği 6 cm çevresinde
    zc1, zp1, zp2, zc2 = 0.03, 0.05, 0.07, 0.09
    ert = AxisymmetricERT(rmax=0.60, zmax=0.60, nr=240, nz=240)
    R, Z = np.meshgrid(ert.r, ert.z, indexing="ij")

    # homojen arka planda çekirdek (σ_h = σ_v = σ₀, anizotropi λ² = 2)
    s0 = 0.0015
    lam2 = 2.0
    sh0 = np.full_like(R, s0 * np.sqrt(lam2))
    sv0 = np.full_like(R, s0 / np.sqrt(lam2))
    phiA = ert.solve(sh0, sv0, [(zc1, 1.0), (zc2, -1.0)])
    phiB = ert.solve(sh0, sv0, [(zp1, 1.0), (zp2, -1.0)])
    sens = ert.sensitivity(phiA, phiB, sh0, sv0)
    Sz = sens.sum(axis=0)                       # r üzerinden integre → S(z)
    Sz_abs = np.abs(Sz)
    w = Sz_abs / Sz_abs.sum()
    cum = np.cumsum(w)
    z_cm = ert.z * 100
    table("ert_kernel", "z w cum", z_cm, w / (ert.dz * 100), cum)
    z_med = float(np.interp(0.5, cum, z_cm))
    z_10 = float(np.interp(0.10, cum, z_cm))
    z_90 = float(np.interp(0.90, cum, z_cm))

    # radyal yayılım — düğümün "gördüğü" yatay yarıçap
    Sr = np.abs(sens).sum(axis=1)
    cr = np.cumsum(Sr) / Sr.sum()
    r_90 = float(np.interp(0.90, cr, ert.r * 100))

    # ---- Born (birinci mertebe) yaklaşımının tam çözümle karşılaştırması ---
    col = CoupledColumn(soil, depth=0.60, nz=240)
    rec = [t * 3600 for t in np.arange(3.0, 6.01, 0.25)]
    res = col.run(theta0=0.22, t_amb=22.0, scenario="preignition", t_end=7 * 3600,
                  dt=10.0, probe_depth=0.06, spin_dt=300.0, record=rec,
                  kernel_weights=np.interp(np.linspace(0, 0.6, 240), ert.z, w))
    R_full, R_born, tt = [], [], []
    kwe = np.interp(col.z, ert.z, w); kwe /= kwe.sum()
    for t_ in rec:
        T_, th_ = res["profiles"][t_]
        sig_z = soil.sigma(th_[0], T_[0])                    # (240,) katmanlı
        sig_grid = np.interp(ert.z, col.z, sig_z)[None, :] * np.ones((ert.nr, 1))
        sh = sig_grid * np.sqrt(lam2); sv = sig_grid / np.sqrt(lam2)
        phi = ert.solve(sh, sv, [(zc1, 1.0), (zc2, -1.0)])
        j1 = int(round(zp1 / ert.dz - 0.5)); j2 = int(round(zp2 / ert.dz - 0.5))
        R_full.append(phi[0, j1] - phi[0, j2])
        R_born.append(1.0 / np.sum(np.interp(ert.z, col.z, sig_z) * w))
        tt.append(t_ / 3600)
    R_full = np.array(R_full); R_born = np.array(R_born)
    ln_full = np.log(R_full / R_full[0])
    ln_born = np.log(R_born / R_born[0])
    table("born_check", "t lnfull lnborn", tt, ln_full, ln_born)
    err = float(np.max(np.abs(ln_full - ln_born)) / max(np.max(np.abs(ln_full)), 1e-9))

    S["ert"] = dict(z_median_cm=z_med, z_p10_cm=z_10, z_p90_cm=z_90,
                    r_p90_cm=r_90, born_rel_err=err,
                    array="C1=3, P1=5, P2=7, C2=9 cm (dusey Wenner)",
                    anisotropy_lambda2=lam2, sigma0=s0)


# =============================================================================
# E · MONTE CARLO — öncü süre dağılımı, ROC, eşik tasarım kutusu
# =============================================================================
PARAMS = [
    ("theta0",     0.10,   0.32,   "baslangic nem"),
    ("t_amb",      15.0,   32.0,   "ortam sicakligi"),
    ("ramp",       2700.0, 10800.0, "piroliz ramp suresi"),
    ("t_peak",     250.0,  400.0,  "yuzey plato sicakligi"),
    ("lam_sat",    1.40,   2.40,   "doygun isil iletkenlik"),
    ("n_archie",   1.60,   2.40,   "Archie ussu"),
    ("probe",      0.04,   0.12,   "prob derinligi"),
    ("sigma_w25",  0.010,  0.050,  "gozenek suyu iletkenligi (bos parametre)"),
]


def _run_batch(X, scenario, t_end, dt, nz=120):
    """X: (M,d) parametre matrisi (fiziksel birimlerde). Bir yığın koşum."""
    M = X.shape[0]
    soil = Soil(lam_sat=X[:, 4][:, None], n_archie=X[:, 5][:, None],
                sigma_w25=X[:, 7][:, None])
    col = CoupledColumn(soil, depth=0.60, nz=nz, batch=M)
    return col.run(theta0=X[:, 0], t_amb=X[:, 1], scenario=scenario,
                   ramp=X[:, 2], t_peak=X[:, 3], probe_depth=X[:, 6],
                   t_end=t_end, dt=dt, spin_dt=300.0)


def _stat(res, beta0=1.5, gamma0=0.002):
    """Normalleştirilmiş AND istatistiği: Λ = max_t min(dT/dt / β₀, |dlnR/dt| / γ₀).
    Eşik τ üzerinden ROC taranır; τ = 1 belgedeki eşik çiftine karşılık gelir."""
    a = fusion_alarm(res)
    lam = np.minimum(a["dTdt"] / beta0, np.abs(a["dlnR"]) / gamma0)
    return (np.nanmax(lam, axis=1), np.nanmax(a["dTdt"], axis=1) / beta0,
            np.nanmax(np.abs(a["dlnR"]), axis=1) / gamma0, a)


def part_E():
    log("E · Monte Carlo: oncu sure, ROC, esik kutusu")
    n_pos = 256 if QUICK else 1024
    n_neg = 128 if QUICK else 512
    d = len(PARAMS)
    lo = np.array([p[1] for p in PARAMS]); hi = np.array([p[2] for p in PARAMS])

    sob = qmc.Sobol(d, scramble=True, seed=20260730)
    Xp = lo + (hi - lo) * sob.random(n_pos)
    res_p = _run_batch(Xp, "preignition", 9 * 3600, 20.0)
    lam_p, b_p, g_p, a_p = _stat(res_p)
    lead = a_p["lead"] / 60.0
    lead_ok = lead[np.isfinite(lead)]
    log(f"  pozitif: {len(lead_ok)}/{n_pos} alarm, medyan {np.median(lead_ok):.1f} dk")

    neg_lam, neg_b, neg_g = [], [], []
    for sc, th_lo, th_hi in [("drought", 0.08, 0.20), ("normal", 0.12, 0.32)]:
        Xn = lo + (hi - lo) * qmc.Sobol(d, scramble=True, seed=7 + len(neg_lam)).random(n_neg)
        Xn[:, 0] = th_lo + (th_hi - th_lo) * (Xn[:, 0] - lo[0]) / (hi[0] - lo[0])
        r = _run_batch(Xn, sc, 24 * 3600, 30.0)
        l_, b_, g_, _ = _stat(r)
        neg_lam.append(l_); neg_b.append(b_); neg_g.append(g_)
    lam_n = np.concatenate(neg_lam); b_n = np.concatenate(neg_b); g_n = np.concatenate(neg_g)

    # ---- öncü süre dağılımı (ampirik CDF) ----
    ls = np.sort(lead_ok)
    cdf = np.arange(1, ls.size + 1) / ls.size
    k = max(1, ls.size // 400)
    table("lead_cdf", "lead cdf", ls[::k], cdf[::k])

    # ---- ROC: füzyon vs tek kanal ----
    def roc(pos, neg):
        thr = np.unique(np.concatenate([pos, neg, [0.0]]))
        thr = np.sort(thr)[::-1]
        tpr = np.array([(pos >= t).mean() for t in thr])
        fpr = np.array([(neg >= t).mean() for t in thr])
        o = np.argsort(fpr)
        auc = float(np.trapezoid(tpr[o], fpr[o]))
        n = max(1, len(thr) // 300)
        return fpr[::n], tpr[::n], auc, thr[::n]

    f_f, t_f, auc_f, _ = roc(lam_p, lam_n)
    f_b, t_b, auc_b, _ = roc(b_p, b_n)
    f_g, t_g, auc_g, _ = roc(g_p, g_n)
    m = min(len(f_f), len(f_b), len(f_g))
    table("roc", "fpr_fusion tpr_fusion fpr_beta tpr_beta fpr_gamma tpr_gamma",
          f_f[:m], t_f[:m], f_b[:m], t_b[:m], f_g[:m], t_g[:m])

    # τ = 1 çalışma noktası (belgedeki eşik çifti)
    tpr1 = float((lam_p >= 1.0).mean()); fpr1 = float((lam_n >= 1.0).mean())

    # ---- eşik tasarım kutusu: β ve γ için güvenli aralık ----
    # Alt sınır olumsuz kümenin üst kuyruğu, üst sınır olumlu kümenin alt
    # kuyruğudur; aradaki bant, hem yanlış alarmı hem de kaçırmayı önleyen
    # eşiklerin kümesidir.
    b_lo, b_hi = float(np.percentile(b_n, 99) * 1.5), float(np.percentile(b_p, 5) * 1.5)
    g_lo, g_hi = float(np.percentile(g_n, 99) * 0.002), float(np.percentile(g_p, 5) * 0.002)
    table("threshold_box", "beta_neg beta_pos gamma_neg gamma_pos",
          np.sort(b_n * 1.5), np.sort(b_p * 1.5)[:len(b_n)],
          np.sort(g_n * 0.002), np.sort(g_p * 0.002)[:len(b_n)])

    S["mc"] = dict(n_pos=n_pos, n_neg=2 * n_neg,
                   detect_rate=float(np.isfinite(lead).mean()),
                   lead_p05=float(np.percentile(lead_ok, 5)),
                   lead_median=float(np.median(lead_ok)),
                   lead_p95=float(np.percentile(lead_ok, 95)),
                   lead_mean=float(lead_ok.mean()),
                   p_lead_gt15=float((lead_ok >= 15).mean()),
                   p_lead_gt30=float((lead_ok >= 30).mean()),
                   auc_fusion=auc_f, auc_beta=auc_b, auc_gamma=auc_g,
                   tpr_at_tau1=tpr1, fpr_at_tau1=fpr1,
                   beta_window=[b_lo, b_hi], gamma_window=[g_lo, g_hi],
                   beta_margin=float(b_hi / max(b_lo, 1e-9)),
                   gamma_margin=float(g_hi / max(g_lo, 1e-12)))
    return Xp, lead


# =============================================================================
# F · SOBOL KÜRESEL DUYARLILIK
# =============================================================================
def part_F():
    log("F · Sobol kuresel duyarlilik indisleri")
    d = len(PARAMS)
    N = 128 if QUICK else 512
    lo = np.array([p[1] for p in PARAMS]); hi = np.array([p[2] for p in PARAMS])
    eng = qmc.Sobol(2 * d, scramble=True, seed=424242)
    U = eng.random(N)
    A = lo + (hi - lo) * U[:, :d]
    B = lo + (hi - lo) * U[:, d:]
    mats = [A, B] + [np.where(np.arange(d) == i, B, A) for i in range(d)]
    X = np.vstack(mats)
    res = _run_batch(X, "preignition", 9 * 3600, 30.0)
    a = fusion_alarm(res)
    Y = np.nan_to_num(a["lead"] / 60.0, nan=0.0)
    YA, YB = Y[:N], Y[N:2 * N]
    var = float(np.var(np.concatenate([YA, YB])))
    S1, ST = [], []
    for i in range(d):
        YAB = Y[(2 + i) * N:(3 + i) * N]
        S1.append(float(np.mean(YB * (YAB - YA)) / var))          # Saltelli 2010
        ST.append(float(np.mean((YA - YAB) ** 2) / (2 * var)))    # Jansen 1999
    idx = np.arange(d)
    table("sobol", "idx S1 ST", idx, S1, ST)
    S["sobol"] = dict(N=N, runs=int(X.shape[0]), var=var,
                      names=[p[0] for p in PARAMS],
                      labels=[p[3] for p in PARAMS],
                      S1=S1, ST=ST, sum_S1=float(sum(S1)))


# =============================================================================
# G · 2B ANİZOTROPİK YAYILIM — yanal tespit ayak izi
# =============================================================================
def part_G():
    log("G · 2B anizotropik yayilim: yanal tespit yaricapi")
    Lx, Lz = 6.0, 0.60
    nx, nz = 300, 60
    rho_c, k_par, k_perp = 2.0e6, 1.60, 0.85
    r_spot, beta = 0.60, 1.5
    out = {}
    curves = {}
    for dip in (0.0, 25.0):
        sl = AnisotropicSlab(Lx, Lz, nx, nz)
        K = AnisotropicSlab.tensor(k_par, k_perp, dip)
        Kxx = np.full((nx, nz), K[0, 0]); Kxz = np.full((nx, nz), K[0, 1])
        Kzz = np.full((nx, nz), K[1, 1])
        T = np.full((nx, nz), 22.0)
        dt, t_end = 5.0, 7.0 * 3600
        jz = int(round(0.06 / sl.dz - 0.5))
        first = np.full(nx, np.nan)
        Tprev = T[:, jz].copy()
        nsteps = int(t_end / dt)
        for n in range(1, nsteps + 1):
            t = n * dt
            Ts = surface_temperature(t, "preignition", 22.0, 3 * 3600.0, 5400.0, 300.0)
            hot = np.abs(sl.x - Lx / 2) < r_spot
            T[:, 0] = np.where(hot, Ts, 22.0)
            T[:, -1] = 22.0
            T = T + dt * sl.divergence(T, Kxx, Kxz, Kzz) / rho_c
            T[:, 0] = np.where(hot, Ts, 22.0); T[:, -1] = 22.0
            if n % 12 == 0:
                rate = (T[:, jz] - Tprev) / (12 * dt) * 600.0
                new = np.isnan(first) & (rate > beta)
                first[new] = t
                Tprev = T[:, jz].copy()
        x_rel = sl.x - Lx / 2
        det = np.isfinite(first)
        curves[dip] = (x_rel, first)
        out[f"dip{int(dip)}"] = dict(
            r_left=float(-x_rel[det].min()) if det.any() else 0.0,
            r_right=float(x_rel[det].max()) if det.any() else 0.0)
    x0, f0 = curves[0.0]; x1, f1 = curves[25.0]
    table("lateral", "x t_dip0 t_dip25", x0,
          np.nan_to_num(f0 / 60, nan=-999), np.nan_to_num(f1 / 60, nan=-999))
    S["lateral"] = dict(spot_radius_m=r_spot, beta=beta, **out)


# =============================================================================
# H · MİSELYUM AĞI KABLO DENKLEMİ — kapsama yarıçapı ve düğüm aralığı
# =============================================================================
def part_H():
    log("H · 2B kablo denklemi: kapsama ve dugum araligi")
    # 2B kararlı kablo denklemi: ∇²V − V/λ² = 0  →  V(r) = V₀ K₀(r/λ)/K₀(a/λ)
    a_src = 0.02                      # m   stres kaynağı yarıçapı
    V0, Vdet = 30.0, 0.5              # mV  kaynak genliği / tespit eşiği
    lams = np.array([0.5, 1.0, 3.0, 10.0, 30.0])
    rr = np.logspace(-2, 2, 240)
    cols = [rr]; hdr = "r"
    rdet = []
    for lam in lams:
        att = bessel_k0(rr / lam) / bessel_k0(a_src / lam)
        cols.append(V0 * att); hdr += f" V{lam:g}".replace(".", "p")
        f = V0 * att - Vdet
        i = np.nonzero(f < 0)[0]
        rdet.append(float(np.interp(0.0, [f[i[0]], f[i[0] - 1]], [rr[i[0]], rr[i[0] - 1]]))
                    if i.size else float(rr[-1]))
    table("cable", hdr, *cols)
    table("cable_rdet", "lam rdet", lams, rdet)

    # düğüm aralığı ↔ kapsama ekonomisi (altıgen örgü)
    node_tl = 103.8 * 47.3            # HW §6: düğüm çifti maliyeti
    Ss = np.linspace(15.0, 200.0, 120)
    rows = []
    for lam, rd in zip(lams, rdet):
        nodes_ha = 1e4 / (0.866 * Ss ** 2)
        capex = nodes_ha * node_tl
        r_circ = Ss / np.sqrt(3.0)                       # en uzak nokta
        p_pre = np.clip(np.pi * rd ** 2 / (0.866 * Ss ** 2), 0, 1)
        area_det = np.pi * np.maximum(r_circ - rd, 0.0) ** 2 / 1e4    # ha
        t_det = np.maximum(r_circ - rd, 0.0) / 1.2 / 1.0              # dk (1.2 m/dk)
        rows.append((nodes_ha, capex, p_pre, area_det, t_det))
    hdr = "S nodes capex"
    cols = [Ss, rows[0][0], rows[0][1]]
    for lam, r in zip(lams, rows):
        hdr += f" p{lam:g} a{lam:g} t{lam:g}".replace(".", "p")
        cols += [r[2], r[3], r[4]]
    table("coverage", hdr, *cols)

    S["coverage"] = dict(V0_mV=V0, Vdet_mV=Vdet, a_src_m=a_src,
                         lambdas=[float(x) for x in lams],
                         r_det_m=[float(x) for x in rdet],
                         node_tl=node_tl,
                         lambda_required_for_S100=float(
                             np.interp(100.0 / np.sqrt(3.0), rdet, lams)),
                         example=dict(S=100.0, nodes_ha=float(1e4 / (0.866 * 100 ** 2)),
                                      capex_ha=float(1e4 / (0.866 * 100 ** 2) * node_tl),
                                      area_det_ha=float(np.pi * (100 / np.sqrt(3) - rdet[2]) ** 2 / 1e4),
                                      t_det_min=float((100 / np.sqrt(3) - rdet[2]) / 1.2)))


# =============================================================================
# I · ENERJİ FİZİBİLİTESİ — stokastik güneş, SOC, yük kaybı olasılığı
# =============================================================================
def _extraterrestrial(day, lat_deg=38.4):
    """Yatay yüzeye günlük dış-atmosfer ışınımı H₀ [MJ/m²] — Duffie & Beckman."""
    n = np.asarray(day, float) % 365 + 1
    dec = np.deg2rad(23.45 * np.sin(2 * np.pi * (284 + n) / 365))
    lat = np.deg2rad(lat_deg)
    ws = np.arccos(np.clip(-np.tan(lat) * np.tan(dec), -1, 1))
    G = 1367.0
    return (24 * 3600 / np.pi) * G * (1 + 0.033 * np.cos(2 * np.pi * n / 365)) * \
           (np.cos(lat) * np.cos(dec) * np.sin(ws) + ws * np.sin(lat) * np.sin(dec)) / 1e6


def _avg_current(duty, tx=0.0005, rx=0.0160):
    """HW §5 güç bütçesi — dijital ikizle birebir aynı model [mA]."""
    d = duty
    under = d * 8.5 + (1 - d) * 0.0013 + d * 0.15 + (1 - d) * 0.0005 + \
        d * 0.017 + d * 0.30 + (1 - d) * 0.001
    lora = tx * 110 + rx * 4.2 + max(0.0, 1 - tx - rx) * 0.005
    surf = d * 0.30 + (1 - d) * 0.001 + lora + 0.002 + 0.002
    return under + surf


def part_I():
    log("I · enerji fizibilitesi: stokastik SOC, LoLP")
    rng = np.random.default_rng(1812)
    days = 365 * 3
    n = np.arange(days)
    H0 = _extraterrestrial(n)
    # açıklık indisi K_t: mevsimsel ortalama + AR(1) sapma, Beta benzeri kırpma
    kt_bar = 0.52 + 0.14 * np.sin(2 * np.pi * (n - 80) / 365)
    eps = np.zeros(days); rho = 0.42
    e = 0.0
    for i in range(days):
        e = rho * e + np.sqrt(1 - rho ** 2) * rng.normal(0, 0.11)
        eps[i] = e
    Kt = np.clip(kt_bar + eps, 0.05, 0.78)
    H = H0 * Kt                                     # MJ/m² gün
    psh = H / 3.6                                   # eşdeğer tepe güneş saati

    eta_mppt, canopy, vbat, dod = 0.90, 0.55, 3.2, 0.90
    # Tasarım sorusu panel gücü değil, kanopi altında kalan ışık payıdır:
    # 5 W panel zaten yükün on katını üretir, kritik değişken gölgelenmedir.
    duties = np.linspace(0.05, 1.00, 40)
    panels = np.linspace(0.01, 0.30, 40)          # kanopi geçirgenliği
    lolp = np.zeros((panels.size, duties.size))
    for i, pw in enumerate(panels):
        gain = 5.0 * psh * eta_mppt * pw * 1000.0 / vbat         # mAh/gün
        for j, dd in enumerate(duties):
            load = _avg_current(dd) * 24.0
            cap = 6000.0 * dod
            soc = cap
            fail = 0
            for k in range(days):
                soc = min(cap, soc + gain[k] - load)
                if soc <= 0.0:
                    fail += 1; soc = 0.0
            lolp[i, j] = fail / days
    with (DATA / "energy_lolp.dat").open("w", encoding="ascii") as fh:
        fh.write("canopy duty lolp\n")
        for i, pw in enumerate(panels):
            for j, dd in enumerate(duties):
                fh.write(f"{pw:.6g} {dd:.6g} {lolp[i, j]:.6g}\n")
            fh.write("\n")
    log("  -> energy_lolp.dat")

    # SOC izi: referans gölgelenme ile derin gölge, ikisi de %50 görev döngüsü.
    # Referans koşulda batarya hiç boşalmadığı için asıl bilgi derin gölgededir.
    load50 = _avg_current(0.50) * 24.0
    traces = {}
    for tag, cv in (("ref", 0.55), ("shade", 0.04)):
        gain = 5.0 * psh * eta_mppt * cv * 1000.0 / vbat
        cap = 6000.0 * dod; soc = cap; tr = []
        for k in range(days):
            soc = min(cap, max(0.0, soc + gain[k] - load50)); tr.append(soc / cap)
        traces[tag] = np.array(tr)
    sel = slice(365, 365 + 365)
    table("energy_soc", "day soc_ref soc_shade kt",
          np.arange(365), traces["ref"][sel], traces["shade"][sel], Kt[sel])

    def lolp_at(cv, dd):
        i = int(np.argmin(np.abs(panels - cv))); j = int(np.argmin(np.abs(duties - dd)))
        return float(lolp[i, j])

    crit50 = next((float(p) for p in panels if lolp_at(p, 0.50) < 0.01), float("nan"))
    crit100 = next((float(p) for p in panels if lolp_at(p, 1.00) < 0.01), float("nan"))
    S["energy"] = dict(i_avg_50=float(_avg_current(0.50)), i_avg_10=float(_avg_current(0.10)),
                       lolp_ref_50=lolp_at(0.55, 0.50), lolp_ref_10=lolp_at(0.55, 0.10),
                       lolp_shade_50=lolp_at(0.10, 0.50),
                       psh_winter=float(psh[350:365].mean()), psh_summer=float(psh[170:185].mean()),
                       canopy_crit_50=crit50, canopy_crit_100=crit100,
                       margin_ratio=float(5.0 * psh[350:365].mean() * 0.9 * 0.55 * 1000 / 3.2
                                          / (_avg_current(0.50) * 24.0)))


# =============================================================================
# J · HABERLEŞME — LoRa bağlantı bütçesi (Weissberger bitki örtüsü sönümü)
# =============================================================================
def part_J():
    log("J · LoRa baglanti butcesi")
    f_ghz, ptx, gtx, grx, sens = 0.868, 22.0, 2.0, 2.0, -134.0
    d = np.logspace(np.log10(5), np.log10(8000), 320)
    d0, n_exp = 100.0, 3.2          # kırılma mesafesi ve engebeli arazi üssü
    fspl0 = 20 * np.log10(d0) + 20 * np.log10(f_ghz * 1e9) - 147.55
    fspl = np.where(d <= d0,
                    20 * np.log10(d) + 20 * np.log10(f_ghz * 1e9) - 147.55,
                    fspl0 + 10 * n_exp * np.log10(d / d0))
    veg = np.where(d < 14, 0.45 * f_ghz ** 0.284 * d,
                   1.33 * f_ghz ** 0.284 * np.minimum(d, 400) ** 0.588)
    prx_open = ptx + gtx + grx - (20 * np.log10(d) + 20 * np.log10(f_ghz * 1e9) - 147.55)
    prx_forest = ptx + gtx + grx - fspl - veg
    margin = prx_forest - sens
    i = np.nonzero(margin < 0)[0]
    d_max = float(np.interp(0.0, [margin[i[0]], margin[i[0] - 1]], [d[i[0]], d[i[0] - 1]])) if i.size else float(d[-1])
    d_max10 = float(np.interp(10.0, margin[::-1], d[::-1]))
    table("link", "d fspl veg prx_open prx_forest margin", d, fspl, veg, prx_open, prx_forest, margin)
    # hava süresi sınırı: SF9, 20 bayt ≈ 100 ms; düğüm başına 10 dakikada bir
    # paket; sekiz kanalda %20 doluluk hedefi
    airtime = 0.10
    cap_airtime = 8 * 0.20 * 600.0 / airtime
    S["link"] = dict(d_max_m=d_max, d_margin10_m=d_max10, sens_dbm=sens,
                     path_exponent=n_exp,
                     nodes_in_range=float(np.pi * d_max10 ** 2 / (0.866 * 100.0 ** 2)),
                     nodes_airtime=float(cap_airtime),
                     nodes_per_gw=float(min(np.pi * d_max10 ** 2 / (0.866 * 100.0 ** 2),
                                            cap_airtime)))


# =============================================================================
# K · EKONOMİK FİZİBİLİTE — NPV / IRR Monte Carlo, tornado, başabaş
# =============================================================================
def part_K():
    log("K · ekonomik fizibilite: NPV, IRR, tornado")
    rng = np.random.default_rng(2026)
    M = 20000
    years = 7
    # belirsiz girdiler (üçgen/lognormal)
    hw_cost = rng.triangular(3800, 4910, 6500, M)       # TL / düğüm çifti
    markup = rng.triangular(1.35, 1.60, 2.00, M)
    saas = rng.triangular(600, 1100, 1800, M)           # TL / düğüm / yıl
    churn = rng.triangular(0.03, 0.08, 0.18, M)
    disc = rng.triangular(0.22, 0.32, 0.45, M)
    growth = rng.triangular(1.35, 1.85, 2.40, M)
    opex0 = rng.triangular(2.2e6, 3.1e6, 4.4e6, M)
    n0 = rng.triangular(220, 420, 800, M)               # 2. yıl kurulan düğüm

    def npv_irr(hw, mk, ss, ch, dr, gr, ox, n_first):
        cf = np.zeros((M, years))
        installed = np.zeros(M)
        for y in range(years):
            new = np.where(y < 1, 0.0, n_first * gr ** (y - 1))
            installed = installed * (1 - ch) + new
            rev_hw = new * hw * mk
            rev_ss = installed * ss
            cogs = new * hw
            opex = ox * (1 + 0.28) ** y
            cf[:, y] = rev_hw + rev_ss - cogs - opex
        disc_f = 1.0 / (1.0 + dr[:, None]) ** (np.arange(1, years + 1))[None, :]
        npv = (cf * disc_f).sum(axis=1) - 1.35e6
        # IRR — Newton, sınırlı
        r = np.full(M, 0.3)
        for _ in range(60):
            p = (1 + r[:, None]) ** (np.arange(1, years + 1))[None, :]
            f = (cf / p).sum(axis=1) - 1.35e6
            df = (-cf * np.arange(1, years + 1)[None, :] / (p * (1 + r[:, None]))).sum(axis=1)
            r = np.clip(r - f / np.where(np.abs(df) < 1e-9, 1e-9, df), -0.9, 5.0)
        return npv, r, cf

    npv, irr, cf = npv_irr(hw_cost, markup, saas, churn, disc, growth, opex0, n0)
    hist, edges = np.histogram(npv / 1e6, bins=60, range=(np.percentile(npv / 1e6, 0.5),
                                                          np.percentile(npv / 1e6, 99.5)))
    table("npv_hist", "npv count", 0.5 * (edges[:-1] + edges[1:]), hist)

    # tornado: her girdi p10/p90'a sabitlenirken diğerleri medyanda
    base = dict(hw=np.median(hw_cost), mk=np.median(markup), ss=np.median(saas),
                ch=np.median(churn), dr=np.median(disc), gr=np.median(growth),
                ox=np.median(opex0), n_first=np.median(n0))
    labels = ["hw", "mk", "ss", "ch", "dr", "gr", "ox", "n_first"]
    samples = dict(hw=hw_cost, mk=markup, ss=saas, ch=churn, dr=disc,
                   gr=growth, ox=opex0, n_first=n0)
    lows, highs = [], []
    for lab in labels:
        for q, store in ((10, lows), (90, highs)):
            kw = {k: np.full(M, v) for k, v in base.items()}
            kw[lab] = np.full(M, np.percentile(samples[lab], q))
            store.append(float(npv_irr(**kw)[0][0] / 1e6))
    med = float(npv_irr(**{k: np.full(M, v) for k, v in base.items()})[0][0] / 1e6)
    table("tornado", "idx low high", np.arange(len(labels)), lows, highs)

    # başabaş: kümülatif iskonto edilmiş nakit akışı
    disc_f = 1.0 / (1.0 + np.median(disc)) ** np.arange(1, years + 1)
    cum = np.cumsum(np.median(cf, axis=0) * disc_f) - 1.35e6
    table("cashflow", "year cum", np.arange(1, years + 1), cum / 1e6)

    S["econ"] = dict(M=M, years=years,
                     npv_p10=float(np.percentile(npv, 10) / 1e6),
                     npv_median=float(np.median(npv) / 1e6),
                     npv_p90=float(np.percentile(npv, 90) / 1e6),
                     p_npv_pos=float((npv > 0).mean()),
                     irr_median=float(np.median(irr)),
                     irr_p10=float(np.percentile(irr, 10)),
                     tornado_labels=labels, tornado_low=lows, tornado_high=highs,
                     tornado_base=med,
                     payback_year=int(np.argmax(cum > 0) + 1) if (cum > 0).any() else -1)


# =============================================================================
def main():
    part_A(); part_B(); part_C(); part_D()
    part_E(); part_F(); part_G(); part_H()
    part_I(); part_J(); part_K()
    S["meta"] = dict(quick=QUICK, seconds=round(time.time() - T0, 1))
    (ROOT / "summary.json").write_text(json.dumps(S, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    log(f"bitti — summary.json yazildi ({S['meta']['seconds']}s)")


if __name__ == "__main__":
    main()
