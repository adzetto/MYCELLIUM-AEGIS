# -*- coding: utf-8 -*-
"""summary.json ve summary_geo.json içindeki sonuçları LaTeX makrolarına
çevirir (numbers.tex). Rapor metnindeki her sayı buradan gelir; böylece
sayısal çalışma yeniden koşturulduğunda metin kendiliğinden güncellenir."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
S = json.loads((ROOT / "summary.json").read_text(encoding="utf-8"))
try:
    G = json.loads((ROOT / "summary_geo.json").read_text(encoding="utf-8"))
except FileNotFoundError:
    G = {}

out = []


def tr(v, nd=1):
    """Türkçe ondalık ayırıcı ile biçimlendir."""
    if v is None or (isinstance(v, float) and v != v):
        return "--"
    s = f"{v:,.{nd}f}".replace(",", " ").replace(".", ",")
    return s


def mac(name, value):
    out.append(f"\\newcommand{{\\{name}}}{{{value}}}")


# ------------------------------------------------------------------ tensör --
t = S["tensor"]
mac("tKpar", tr(t["k_par"], 2)); mac("tKperp", tr(t["k_perp"], 2))
mac("tAniso", tr(t["anisotropy"], 2))
mac("tMisMax", tr(t["misalign_max"], 1)); mac("tDipMax", tr(t["dip_at_max"], 0))
mac("tKxzTf", tr(t["Kxz_at_25"], 3))

# ------------------------------------------------------------- doğrulama ----
v = S["verification"]
mac("pThermal", tr(v["p_mms_thermal"][-1], 2))
mac("pErt", tr(v["p_mms_ert"][-1], 2))
mac("pPoint", tr(v["p_point_source"][-1], 2))
mac("pGrid", tr(v["p_grid"], 2))
mac("gciGrid", tr(v["gci_grid_pct"], 2))
mac("pTime", tr(v["p_time"], 2))
mac("dtExplicit", tr(v["dt_explicit_max"], 1))
def sci(x, nd=2):
    """Bilimsel gösterim — matematik modu gövdesi (dolar işareti içermez)."""
    m, e = f"{x:.{nd}e}".split("e")
    return m.replace(".", "{,}") + r"\times 10^{" + str(int(e)) + "}"


mac("coercivity", sci(v["coercivity"]))
mac("dblkOO", sci(v["D_block"][0][0])); mac("dblkOT", sci(v["D_block"][0][1]))
mac("dblkTO", sci(v["D_block"][1][0])); mac("dblkTT", sci(v["D_block"][1][1]))
mac("stiffRatio", tr(v["D_eigs"][0] / v["D_eigs"][1], 0))
mac("latentOff", tr(v.get("latent_off", 0.0), 1))
mac("latentOn", tr(v.get("latent_on", 0.0), 1))
mac("latentDelta", tr(v.get("latent_delta_pct", 0.0), 1))
mac("leadRef", tr(v["lead_reference"], 1))
mac("numUnc", tr(v["num_uncertainty_min"], 1))
mac("leadCoarse", tr(v["lead_grid"][0], 1))
mac("leadFine", tr(v["lead_grid"][-1], 1))
mac("regSpread", tr(v.get("reg_spread_pct", 0.0), 1))
mac("regLo", tr(v.get("reg_lead_min", 0.0), 1))
mac("regHi", tr(v.get("reg_lead_max", 0.0), 1))

# ---------------------------------------------------------------- nominal ---
n = S["nominal"]
mac("leadNom", tr(n["lead_min"], 1))
mac("tAlarm", tr(n["t_alarm_h"], 2)); mac("tIgnite", tr(n["t_ignite_h"], 2))
mac("maxdTdt", tr(n["max_dTdt"], 1)); mac("mindlnR", tr(abs(n["min_dlnR"]), 4))
mac("dampDepth", tr(n["damping_depth_cm"], 1))
mac("diurnalRate", tr(n["diurnal_rate6"], 2))
mac("betaMarginNat", tr(1.5 / n["diurnal_rate6"], 1))
mac("droughtdT", tr(n["drought"]["max_dTdt"], 2))
mac("droughtdlnR", tr(n["drought"]["max_abs_dlnR"], 4))
mac("normaldT", tr(n["normal"]["max_dTdt"], 2))
mac("normaldlnR", tr(n["normal"]["max_abs_dlnR"], 4))
mac("sepBeta", tr(n["max_dTdt"] / max(n["drought"]["max_dTdt"], 1e-9), 0))

d = S["depth"]
mac("leadSix", tr(d["lead_at_6"], 1)); mac("leadEighteen", tr(d["lead_at_18"], 1))
mac("zZero", tr(d["z_zero_cross"], 1))
# lead_one dizisinde alarm uretmeyen derinlikler -999 ile isaretlidir
_ok = [(z, L) for z, L in zip(d["z_cm"], d["lead_one"]) if L > -900]
mac("zOneMax", tr(max(z for z, _ in _ok), 0) if _ok else "--")
mac("leadOneBest", tr(max(L for _, L in _ok), 1) if _ok else "--")
mac("zOneBest", tr(max(_ok, key=lambda t: t[1])[0], 0) if _ok else "--")

# ------------------------------------------------------------------- ERT ----
e = S["ert"]
mac("zMedian", tr(e["z_median_cm"], 1)); mac("zPten", tr(e["z_p10_cm"], 1))
mac("zPninety", tr(e["z_p90_cm"], 1)); mac("rPninety", tr(e["r_p90_cm"], 1))
mac("bornErr", tr(100 * e["born_rel_err"], 1))

# ------------------------------------------------------------ Monte Carlo ---
m = S["mc"]
mac("mcPos", str(m["n_pos"])); mac("mcNeg", str(m["n_neg"]))
mac("detRate", tr(100 * m["detect_rate"], 1))
mac("leadPfive", tr(m["lead_p05"], 1)); mac("leadMed", tr(m["lead_median"], 1))
mac("leadPnf", tr(m["lead_p95"], 1))
mac("pLeadFifteen", tr(100 * m["p_lead_gt15"], 1))
mac("pLeadThirty", tr(100 * m["p_lead_gt30"], 1))
mac("aucFusion", tr(m["auc_fusion"], 3)); mac("aucBeta", tr(m["auc_beta"], 3))
mac("aucGamma", tr(m["auc_gamma"], 3))
mac("tprOne", tr(100 * m["tpr_at_tau1"], 1)); mac("fprOne", tr(100 * m["fpr_at_tau1"], 2))
mac("betaLo", tr(m["beta_window"][0], 2)); mac("betaHi", tr(m["beta_window"][1], 2))
mac("gammaLo", tr(m["gamma_window"][0], 4)); mac("gammaHi", tr(m["gamma_window"][1], 4))

# ----------------------------------------------------------------- Sobol ----
sb = S["sobol"]
mac("sobolRuns", str(sb["runs"])); mac("sobolN", str(sb["N"]))
mac("sobolSum", tr(sb["sum_S1"], 2))
order = sorted(range(len(sb["ST"])), key=lambda i: -sb["ST"][i])
lbl = {"theta0": "başlangıç nem içeriği", "t_amb": "ortam sıcaklığı",
       "ramp": "piroliz ramp süresi", "t_peak": "yüzey plato sıcaklığı",
       "lam_sat": "doygun ısıl iletkenlik", "n_archie": "Archie üssü",
       "probe": "prob derinliği", "sigma_w25": "gözenek suyu iletkenliği"}
mac("sobolFirst", lbl[sb["names"][order[0]]])
mac("sobolFirstST", tr(sb["ST"][order[0]], 2))
mac("sobolSecond", lbl[sb["names"][order[1]]])
mac("sobolSecondST", tr(sb["ST"][order[1]], 2))
mac("sobolThird", lbl[sb["names"][order[2]]])
mac("sobolThirdST", tr(sb["ST"][order[2]], 2))
i_null = sb["names"].index("sigma_w25")
mac("sobolNull", tr(abs(sb["ST"][i_null]), 3))

# ---------------------------------------------------------------- yanal -----
la = S["lateral"]
mac("latSpot", tr(la["spot_radius_m"], 2))
mac("latRzero", tr(la["dip0"]["r_right"], 2))
mac("latRup", tr(la["dip25"]["r_left"], 2))
mac("latRdown", tr(la["dip25"]["r_right"], 2))

# -------------------------------------------------------------- kapsama -----
c = S["coverage"]
mac("cableVzero", tr(c["V0_mV"], 0)); mac("cableVdet", tr(c["Vdet_mV"], 1))
# LaTeX makro adlari yalnizca harf icerebilir
_LAMNAME = {0.5: "rdetHalf", 1.0: "rdetOne", 3.0: "rdetThree",
            10.0: "rdetTen", 30.0: "rdetThirty"}
for lam, rd in zip(c["lambdas"], c["r_det_m"]):
    mac(_LAMNAME[float(lam)], tr(rd, 1))
ex = c["example"]
mac("covNodes", tr(ex["nodes_ha"], 2)); mac("covCapex", tr(ex["capex_ha"], 0))
mac("covArea", tr(ex["area_det_ha"], 2)); mac("covTime", tr(ex["t_det_min"], 0))
mac("nodeTL", tr(c["node_tl"], 0))

# ---------------------------------------------------------------- enerji ----
en = S["energy"]
mac("iavgFifty", tr(en["i_avg_50"], 2)); mac("iavgTen", tr(en["i_avg_10"], 2))
mac("lolpFifty", tr(100 * en.get("lolp_ref_50", 0.0), 2)); mac("lolpTen", tr(100 * en.get("lolp_ref_10", 0.0), 2))
mac("lolpShade", tr(100 * en.get("lolp_shade_50", 0.0), 1))
mac("canopyCritFifty", tr(100 * en.get("canopy_crit_50", 0.0), 1))
mac("canopyCritFull", tr(100 * en.get("canopy_crit_100", 0.0), 1))
mac("energyMargin", tr(en.get("margin_ratio", 0.0), 1))
mac("pshWinter", tr(en["psh_winter"], 2)); mac("pshSummer", tr(en["psh_summer"], 2))


# ------------------------------------------------------------ haberleşme ----
lk = S["link"]
mac("dMax", tr(lk["d_max_m"], 0)); mac("dMarginTen", tr(lk["d_margin10_m"], 0))
mac("nodesPerGw", tr(lk["nodes_per_gw"], 0))
mac("nodesRange", tr(lk.get("nodes_in_range", 0.0), 0))
mac("nodesAirtime", tr(lk.get("nodes_airtime", 0.0), 0))
mac("pathExp", tr(lk.get("path_exponent", 0.0), 1))

# -------------------------------------------------------------- ekonomi -----
ec = S["econ"]
mac("npvMed", tr(ec["npv_median"], 1)); mac("npvPten", tr(ec["npv_p10"], 1))
mac("npvPninety", tr(ec["npv_p90"], 1))
mac("pNpvPos", tr(100 * ec["p_npv_pos"], 1))
mac("irrMed", tr(100 * ec["irr_median"], 0)); mac("irrPten", tr(100 * ec["irr_p10"], 0))
mac("paybackYear", str(ec["payback_year"]))
mac("econRuns", f"{ec['M']:,}".replace(",", " "))

# ------------------------------------------------------------- coğrafya -----
if G:
    gr = G["grid"]
    mac("geoLandArea", tr(gr["land_km2"], 0))
    mac("geoElevMax", tr(gr["elev_max"], 0))
    mac("geoSlopeMean", tr(gr["slope_mean"], 1))
    mac("geoHighArea", tr(gr["risk_high_km2"], 0))
    mac("geoRes", tr(gr["res_m"], 0))
    lf = G["lead_field"]
    mac("geoCells", str(lf["n"]))
    mac("geoLeadMed", tr(lf["median"], 1))
    mac("geoLeadPfive", tr(lf["p05"], 1)); mac("geoLeadPnf", tr(lf["p95"], 1))
    pv = G["provinces"]
    mac("geoTopProv", pv[0]["name"]); mac("geoTopRisk", tr(pv[0]["risk_mean"], 3))
    mac("geoSecondProv", pv[1]["name"] if len(pv) > 1 else "--")
    mac("geoNprov", str(len(pv)))
    tr_ = G["transect"]
    mac("geoTransLen", tr(tr_["length_km"], 0))
    mac("geoTransZmax", tr(tr_["z_max"], 0))
    mac("geoTransLead", tr(tr_["lead_median"], 1))
    st = G["sites"]
    mac("geoSiteN", str(len(st)))
    mac("geoSiteRisk", tr(st[0]["risk"], 3))
    mac("geoSiteElev", tr(st[0]["elev"], 0))
    mac("geoSiteSlope", tr(st[0]["slope"], 1))

(ROOT / "numbers.tex").write_text(
    "% OTOMATİK ÜRETİLDİ — numeric/make_numbers.py · elle düzenlemeyin\n"
    + "\n".join(out) + "\n", encoding="utf-8")
print(f"numbers.tex: {len(out)} makro")
