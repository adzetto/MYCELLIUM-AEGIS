"""
=============================================================================
MYCELLIUM-AEGIS · FİZİBİLİTE ANALİZİ
geo.py — coğrafi fizibilite katmanı
-----------------------------------------------------------------------------
Bu modül, fiziksel modeli gerçek arazi üzerine oturtur. İzmir Orman Bölge
Müdürlüğü kapsama alanına karşılık gelen kutuda (26,5–28,2 D · 38,0–39,0 K)

  · SRTM 1 yay-saniye (≈30 m) sayısal yükseklik modeli indirilir ve UTM 35K
    (EPSG:32635) izdüşümüne yeniden örneklenir,
  · eğim, bakı, düzlemsel/profil eğrilik, D8 akış birikimi ve topografik
    ıslaklık indisi (TWI) türetilir,
  · eğimli arazide gökyüzü geometrisinden potansiyel doğrudan güneş ışınımı
    integre edilir (Kumar, Skidmore & Knowles 1997),
  · Natural Earth 1:10m il sınırları, kıyı çizgisi ve yerleşim noktaları
    geopandas ile okunur, aynı izdüşüme alınır ve orman–yerleşim arayüzü
    (WUI) mesafesi hesaplanır,
  · çok ölçütlü bir tutuşma duyarlılık indisi kurulur,
  · ve nihayet bağlaşık PDE modeli, arazi hücrelerinden örneklenen binlerce
    noktada YIĞIN olarak koşturularak mekânsal öncü süre haritası üretilir.

Arazi eğimi ψ, ısıl iletkenlik tensörünün yatak normalini döndürdüğü açıdır;
bu yüzden coğrafya doğrudan tensör matematiğine bağlanır:
    K(ψ) = k_∥ (I − n⊗n) + k_⊥ n⊗n,   n = (sin ψ, cos ψ)
ve düşey bileşen K_zz = k_∥ sin²ψ + k_⊥ cos²ψ olarak sütun modeline girer.

İndirilen ham veri `.cache/` altında tutulur (sürümlenmez); üretilen tablolar
`docs/feasibility/data/geo_*.dat` dosyalarına yazılır.
=============================================================================
"""
from __future__ import annotations

import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import reproject, Resampling
from shapely.geometry import LineString, Point, box

sys.path.insert(0, str(Path(__file__).parent))
from aegis_physics import Soil, CoupledColumn, fusion_alarm

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = Path(__file__).parent / ".cache"
DATA.mkdir(exist_ok=True)
CACHE.mkdir(exist_ok=True)

# İzmir OBM kapsama kutusu
LON0, LON1, LAT0, LAT1 = 26.5, 28.2, 38.0, 39.0
UTM = "EPSG:32635"                      # WGS84 / UTM 35K
RES = 90.0                              # m — çalışma çözünürlüğü
G = {}
T0 = time.time()


def log(m):
    print(f"[{time.time() - T0:7.1f}s] {m}", flush=True)


def table(name, header, *cols):
    arr = np.column_stack([np.asarray(c, float).ravel() for c in cols])
    with (DATA / f"{name}.dat").open("w", encoding="ascii") as fh:
        fh.write(header + "\n")
        for row in arr:
            fh.write(" ".join(f"{v:.7g}" for v in row) + "\n")
    log(f"  -> {name}.dat ({arr.shape[0]} satir)")


def matrix_table(name, header, X, Y, *fields, stride=1):
    """pgfplots matrix plot / surf için ızgara tablosu (satır blokları boş
    satırla ayrılır)."""
    Xs, Ys = X[::stride, ::stride], Y[::stride, ::stride]
    fs = [f[::stride, ::stride] for f in fields]
    with (DATA / f"{name}.dat").open("w", encoding="ascii") as fh:
        fh.write(header + "\n")
        for i in range(Xs.shape[0]):
            for j in range(Xs.shape[1]):
                vals = [Xs[i, j], Ys[i, j]] + [f[i, j] for f in fs]
                fh.write(" ".join("nan" if not np.isfinite(v) else f"{v:.6g}"
                                  for v in vals) + "\n")
            fh.write("\n")
    log(f"  -> {name}.dat ({Xs.shape[0]}x{Xs.shape[1]})")


# =============================================================================
# 1 · VERİ İNDİRME
# =============================================================================
def _get(url, name, timeout=180):
    p = CACHE / name
    if p.exists() and p.stat().st_size > 0:
        return p
    import requests
    log(f"  indiriliyor: {name}")
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "mycellium-aegis/1.0"})
    r.raise_for_status()
    p.write_bytes(r.content)
    return p


def load_dem():
    """SRTMGL1 karolarını indirir, mozaikler ve UTM 35K'ya yeniden örnekler."""
    log("1 · SRTM sayisal yukseklik modeli")
    arc = 3601
    lat_tiles = range(int(np.floor(LAT0)), int(np.ceil(LAT1)))
    lon_tiles = range(int(np.floor(LON0)), int(np.ceil(LON1)))
    nrows, ncols = len(list(lat_tiles)) * (arc - 1) + 1, len(list(lon_tiles)) * (arc - 1) + 1
    mosaic = np.full((nrows, ncols), -32768, dtype=np.int16)
    for li, lat in enumerate(sorted(lat_tiles, reverse=True)):
        for lj, lon in enumerate(sorted(lon_tiles)):
            tag = f"N{lat:02d}E{lon:03d}"
            url = f"https://s3.amazonaws.com/elevation-tiles-prod/skadi/N{lat:02d}/{tag}.hgt.gz"
            p = _get(url, f"{tag}.hgt.gz")
            with gzip.open(p, "rb") as fh:
                tile = np.frombuffer(fh.read(), dtype=">i2").reshape(arc, arc)
            mosaic[li * (arc - 1):li * (arc - 1) + arc,
                   lj * (arc - 1):lj * (arc - 1) + arc] = tile
    dem = mosaic.astype(np.float32)
    dem[dem < -1000] = np.nan
    # deniz: SRTM'de 0 m; su maskesini ayrı tutuyoruz
    lat_top = max(lat_tiles) + 1.0
    lon_left = min(lon_tiles)
    src_tr = from_origin(lon_left - 0.5 / 3600, lat_top + 0.5 / 3600, 1 / 3600, 1 / 3600)

    # hedef ızgara (UTM 35K, RES m)
    corners = gpd.GeoSeries([Point(LON0, LAT0), Point(LON1, LAT0),
                             Point(LON0, LAT1), Point(LON1, LAT1)], crs="EPSG:4326").to_crs(UTM)
    xmin = np.floor(corners.x.min() / RES) * RES
    xmax = np.ceil(corners.x.max() / RES) * RES
    ymin = np.floor(corners.y.min() / RES) * RES
    ymax = np.ceil(corners.y.max() / RES) * RES
    W = int((xmax - xmin) / RES); H = int((ymax - ymin) / RES)
    dst = np.full((H, W), np.nan, dtype=np.float32)
    dst_tr = from_origin(xmin, ymax, RES, RES)
    reproject(dem, dst, src_transform=src_tr, src_crs="EPSG:4326",
              dst_transform=dst_tr, dst_crs=UTM, resampling=Resampling.bilinear,
              src_nodata=np.nan, dst_nodata=np.nan)
    x = xmin + (np.arange(W) + 0.5) * RES
    y = ymax - (np.arange(H) + 0.5) * RES
    log(f"  DEM {H}x{W} @ {RES:.0f} m, yukseklik {np.nanmin(dst):.0f}..{np.nanmax(dst):.0f} m")
    return dst, x, y, dst_tr


def load_vectors():
    """Natural Earth 1:10m il sınırları, kıyı çizgisi, yerleşimler."""
    log("2 · Natural Earth vektor katmanlari")
    out = {}
    specs = {
        "admin1": ("https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip",
                   "ne_10m_admin_1_states_provinces.zip"),
        "coast": ("https://naciscdn.org/naturalearth/10m/physical/ne_10m_coastline.zip",
                  "ne_10m_coastline.zip"),
        "places": ("https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places.zip",
                   "ne_10m_populated_places.zip"),
    }
    bb = box(LON0 - 0.6, LAT0 - 0.6, LON1 + 0.6, LAT1 + 0.6)
    for key, (url, name) in specs.items():
        p = _get(url, name)
        gdf = gpd.read_file(f"zip://{p}")
        gdf = gdf[gdf.intersects(bb)].copy()
        out[key] = gdf.to_crs(UTM)
        log(f"  {key}: {len(gdf)} kayit")
    return out


# =============================================================================
# 2 · ARAZİ TÜREVLERİ
# =============================================================================
def terrain(dem, res=RES):
    """Eğim, bakı ve eğrilik — Horn (1981) 3×3 operatörü.

    Dizide satır indisi güneye doğru arttığı için `dzdr` = ∂z/∂(güney) olur;
    kuzey bileşeni bunun eksisidir. Bakı, aşağı-eğim yönünün kuzeyden saat
    yönünde ölçülen azimutudur: az = atan2(−∂z/∂x, ∂z/∂r)."""
    z = dem
    p = np.pad(z, 1, mode="edge")
    dzdx = ((p[:-2, 2:] + 2 * p[1:-1, 2:] + p[2:, 2:]) -
            (p[:-2, :-2] + 2 * p[1:-1, :-2] + p[2:, :-2])) / (8 * res)
    dzdr = ((p[2:, :-2] + 2 * p[2:, 1:-1] + p[2:, 2:]) -
            (p[:-2, :-2] + 2 * p[:-2, 1:-1] + p[:-2, 2:])) / (8 * res)
    slope = np.arctan(np.hypot(dzdx, dzdr))                 # rad
    aspect = (np.degrees(np.arctan2(-dzdx, dzdr)) + 360.0) % 360.0
    # profil eğriliği (Zevenbergen & Thorne 1987 basitleştirilmiş)
    curv = ((p[:-2, 1:-1] + p[2:, 1:-1] - 2 * z) +
            (p[1:-1, :-2] + p[1:-1, 2:] - 2 * z)) / (res * res)
    return slope, aspect, curv


def fill_and_accumulate(dem, res):
    """Priority-flood ile çukur doldurma (Barnes ve diğ. 2014) + D8 akış
    birikimi. TWI = ln(a / tan β) için gereken özgül su toplama alanını verir."""
    import heapq
    H, W = dem.shape
    z = np.where(np.isfinite(dem), dem, 1e6).astype(np.float64)
    filled = z.copy()
    closed = np.zeros((H, W), bool)
    heap = []
    for i in range(H):
        for j in (0, W - 1):
            heapq.heappush(heap, (z[i, j], i, j)); closed[i, j] = True
    for j in range(W):
        for i in (0, H - 1):
            if not closed[i, j]:
                heapq.heappush(heap, (z[i, j], i, j)); closed[i, j] = True
    nb = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    while heap:
        e, i, j = heapq.heappop(heap)
        for di, dj in nb:
            ii, jj = i + di, j + dj
            if 0 <= ii < H and 0 <= jj < W and not closed[ii, jj]:
                closed[ii, jj] = True
                filled[ii, jj] = max(z[ii, jj], e + 1e-4)
                heapq.heappush(heap, (filled[ii, jj], ii, jj))

    # D8: en dik iniş komşusu — hücreler yükseklik sırasına göre boşaltılır
    order = np.argsort(filled, axis=None)[::-1]
    acc = np.ones((H, W))
    fp = np.pad(filled, 1, constant_values=1e9)
    best = np.full((H, W), 0.0)
    bi = np.zeros((H, W), np.int8)
    for k, (di, dj) in enumerate(nb):
        d = np.hypot(di * res, dj * res)
        drop = (filled - fp[1 + di:H + 1 + di, 1 + dj:W + 1 + dj]) / d
        m = drop > best
        best[m] = drop[m]; bi[m] = k + 1
    for idx in order:
        i, j = divmod(int(idx), W)
        k = bi[i, j]
        if k == 0:
            continue
        di, dj = nb[k - 1]
        ii, jj = i + di, j + dj
        if 0 <= ii < H and 0 <= jj < W:
            acc[ii, jj] += acc[i, j]
    return filled, acc


def insolation(slope, aspect, lat_deg=38.5, day=196, tau=0.70):
    """Eğimli yüzeye günlük potansiyel doğrudan güneş ışınımı [MJ/m²].
    Kumar, Skidmore & Knowles (1997); açık gökyüzü ışın geçirgenliği τ."""
    lat = np.deg2rad(lat_deg)
    dec = np.deg2rad(23.45 * np.sin(2 * np.pi * (284 + day) / 365))
    asp = np.deg2rad(aspect)                       # 0 = kuzey, saat yönü
    total = np.zeros_like(slope)
    hours = np.linspace(-np.pi, np.pi, 145)        # 10 dakikalık adım
    dt = (hours[1] - hours[0]) / (2 * np.pi) * 86400.0
    for h in hours:
        cz = np.sin(lat) * np.sin(dec) + np.cos(lat) * np.cos(dec) * np.cos(h)
        if cz <= 0.02:
            continue
        az = np.arctan2(np.sin(h), np.cos(h) * np.sin(lat) - np.tan(dec) * np.cos(lat))
        az = (az + np.pi)                          # kuzeyden saat yönünde
        ci = np.cos(slope) * cz + np.sin(slope) * np.sqrt(1 - cz ** 2) * np.cos(az - asp)
        Ib = 1367.0 * tau ** (1.0 / max(cz, 0.05))
        total += np.maximum(ci, 0.0) * Ib * dt
    return total / 1e6


# =============================================================================
# 3 · ANA AKIŞ
# =============================================================================
def main():
    dem, x, y, tr = load_dem()
    vec = load_vectors()
    X, Y = np.meshgrid(x, y)
    land = np.isfinite(dem) & (dem > 0.5)

    log("3 · arazi turevleri")
    slope, aspect, curv = terrain(dem)
    slope_deg = np.degrees(slope)

    # TWI — 4× seyreltilmiş ızgarada (akış birikimi ardışıktır)
    log("4 · cukur doldurma + D8 akis birikimi (360 m izgara)")
    ds = 4
    dem_c = dem[::ds, ::ds]
    filled, acc = fill_and_accumulate(np.nan_to_num(dem_c, nan=0.0), RES * ds)
    sl_c = np.maximum(np.degrees(terrain(dem_c, RES * ds)[0]), 0.6)
    twi_c = np.log(np.maximum(acc, 1.0) * RES * ds / np.tan(np.deg2rad(sl_c)))
    twi = np.kron(twi_c, np.ones((ds, ds)))[:dem.shape[0], :dem.shape[1]]

    log("5 · potansiyel gunes isinimi (temmuz)")
    ins = insolation(slope, aspect)

    log("6 · yerlesim mesafesi (WUI arayuzu)")
    places = vec["places"]
    pts = np.array([[g.x, g.y] for g in places.geometry])
    pop = places.get("POP_MAX", pd.Series(np.full(len(places), 1e4))).fillna(1e4).to_numpy()
    keep = pop > 5000
    pts = pts[keep]
    from scipy.spatial import cKDTree
    tree = cKDTree(pts)
    dist_set = tree.query(np.column_stack([X.ravel(), Y.ravel()]))[0].reshape(X.shape)

    # ---------------------------------------------------- duyarlılık indisi --
    log("7 · cok olcutlu tutusma duyarlilik indisi")
    def nrm(a, lo=2, hi=98):
        v = a[land]
        a0, a1 = np.nanpercentile(v, lo), np.nanpercentile(v, hi)
        return np.clip((a - a0) / max(a1 - a0, 1e-9), 0, 1)

    # Rothermel eğim faktörü φ_s ∝ (tan β)² — yayılma hızını artırır
    phi_s = nrm(np.tan(slope) ** 2)
    f_ins = nrm(ins)                                   # kuruluk / ısınma
    f_dry = 1.0 - nrm(twi)                             # düşük ıslaklık
    f_wui = 1.0 - nrm(np.log10(np.maximum(dist_set, 50.0)))   # yerleşime yakınlık
    risk = 0.30 * phi_s + 0.28 * f_ins + 0.27 * f_dry + 0.15 * f_wui
    risk = np.where(land, risk, np.nan)

    # ------------------------------------------------------- il istatistiği --
    log("8 · il bazinda istatistik (pandas/geopandas)")
    prov = vec["admin1"]
    prov = prov[prov["admin"] == "Turkey"].copy()
    from rasterio.features import geometry_mask
    rows = []
    for _, r in prov.iterrows():
        m = ~geometry_mask([r.geometry], out_shape=dem.shape, transform=tr, invert=False)
        sel = m & land & np.isfinite(risk)
        if sel.sum() < 200:
            continue
        tr_names = {"Izmir": "İzmir", "Aydin": "Aydın", "Manisa": "Manisa",
                    "Balikesir": "Balıkesir", "Mugla": "Muğla", "Usak": "Uşak",
                    "Denizli": "Denizli", "Kutahya": "Kütahya"}
        rows.append(dict(name=tr_names.get(r["name"], r["name"]), cells=int(sel.sum()),
                         area_km2=sel.sum() * RES * RES / 1e6,
                         elev_mean=float(np.nanmean(dem[sel])),
                         slope_mean=float(np.nanmean(slope_deg[sel])),
                         risk_mean=float(np.nanmean(risk[sel])),
                         risk_p90=float(np.nanpercentile(risk[sel], 90)),
                         high_km2=float((risk[sel] > 0.62).sum() * RES * RES / 1e6)))
    pv = pd.DataFrame(rows).sort_values("risk_mean", ascending=False)
    pv.to_csv(DATA / "geo_provinces.csv", index=False, encoding="utf-8")
    table("geo_prov", "idx risk_mean risk_p90 high_km2 slope_mean elev_mean area_km2",
          np.arange(len(pv)), pv.risk_mean, pv.risk_p90, pv.high_km2,
          pv.slope_mean, pv.elev_mean, pv.area_km2)
    G["provinces"] = pv.to_dict("records")

    # ---------------------------------------------------- pilot saha seçimi --
    log("9 · pilot saha secimi (kisitli cok olcutlu siralama)")
    ok = land & np.isfinite(risk) & (slope_deg < 32) & (dem < 1300) & \
        (dist_set > 800) & (dist_set < 12000)
    score = np.where(ok, risk, -1)
    # 3 km yarıçapta tekrar seçimi engelleyerek en iyi 8 hücre
    sites = []
    sc = score.copy()
    for _ in range(8):
        k = int(np.nanargmax(sc))
        i, j = divmod(k, sc.shape[1])
        if sc[i, j] <= 0:
            break
        sites.append((X[i, j], Y[i, j], float(risk[i, j]), float(dem[i, j]),
                      float(slope_deg[i, j]), float(dist_set[i, j] / 1000)))
        rr = int(3000 / RES)
        sc[max(0, i - rr):i + rr, max(0, j - rr):j + rr] = -1
    sarr = np.array(sites)
    table("geo_sites", "x y risk elev slope dsett_km",
          sarr[:, 0] / 1000, sarr[:, 1] / 1000, sarr[:, 2], sarr[:, 3], sarr[:, 4], sarr[:, 5])
    G["sites"] = [dict(x=float(s[0]), y=float(s[1]), risk=float(s[2]), elev=float(s[3]),
                       slope=float(s[4]), d_settlement_km=float(s[5])) for s in sites]

    # --------------------------------------------- PDE'nin arazi üzerinde ----
    log("10 · baglasik PDE'nin arazi hucrelerinde yigin kosumu")
    ny, nx = dem.shape
    sub = 6                                            # 540 m örnekleme
    ii, jj = np.mgrid[0:ny:sub, 0:nx:sub]
    m = land[ii, jj] & np.isfinite(risk[ii, jj])
    ii, jj = ii[m], jj[m]
    if ii.size > 4000:
        sel = np.linspace(0, ii.size - 1, 4000).astype(int)
        ii, jj = ii[sel], jj[sel]
    log(f"  {ii.size} hucre")

    psi = np.deg2rad(slope_deg[ii, jj])
    k_par, k_perp = 1.60, 0.85
    # düşey iletim, yatak normalinin döndürülmesiyle: K_zz = k∥sin²ψ + k⊥cos²ψ
    Kzz = k_par * np.sin(psi) ** 2 + k_perp * np.cos(psi) ** 2
    lam_sat = 1.90 * Kzz / k_perp                      # nominal λ_sat ölçeklemesi
    twi_s = twi[ii, jj]
    theta0 = np.clip(0.10 + 0.030 * (twi_s - np.nanmedian(twi[land])), 0.08, 0.34)
    t_amb = 30.0 - 0.0065 * dem[ii, jj] + 6.0 * (ins[ii, jj] / np.nanmax(ins[land]) - 0.55)
    t_amb = np.clip(t_amb, 12.0, 36.0)

    soil = Soil(lam_sat=lam_sat[:, None])
    col = CoupledColumn(soil, depth=0.60, nz=120, batch=ii.size)
    res = col.run(theta0=theta0, t_amb=t_amb, scenario="preignition",
                  t_end=9 * 3600, dt=30.0, probe_depth=0.06, spin_dt=600.0)
    al = fusion_alarm(res)
    lead = al["lead"] / 60.0
    lead_map = np.full(dem.shape, np.nan)
    lead_map[ii, jj] = np.nan_to_num(lead, nan=0.0)
    G["lead_field"] = dict(n=int(ii.size), median=float(np.nanmedian(lead)),
                           p05=float(np.nanpercentile(lead, 5)),
                           p95=float(np.nanpercentile(lead, 95)),
                           detect_rate=float(np.isfinite(lead).mean()),
                           min=float(np.nanmin(lead)), max=float(np.nanmax(lead)))
    table("geo_lead_pts", "x y lead slope theta0 tamb elev",
          X[ii, jj] / 1000, Y[ii, jj] / 1000, np.nan_to_num(lead, nan=0.0),
          slope_deg[ii, jj], theta0, t_amb, dem[ii, jj])

    # ------------------------------------------------------------ haritalar --
    log("11 · harita ve kesit tablolari")
    st = 12                                            # ≈1.1 km ızgara
    # Deniz hucreleri NaN yerine sentinel deger alir: pgfplots matrix plot
    # duzgun izgara ister, NaN izgarayi bozar. Renk skalasinin alt ucu
    # bu degere denk gelecek sekilde ayarlanir.
    matrix_table("geo_dem", "x y z risk twi slope", X / 1000, Y / 1000,
                 np.where(land, dem, -120.0), np.where(land, risk, -0.06),
                 np.where(land, twi, 0.0),
                 np.where(land, slope_deg, 0.0), stride=st)

    # kıyı çizgisi ve il sınırları — çokgen/çizgi parçaları
    def dump_lines(gdf, name, maxpts=9000):
        segs, k = [], 0
        for geom in gdf.geometry:
            gs = [geom] if geom.geom_type in ("LineString",) else list(getattr(geom, "geoms", []))
            if geom.geom_type == "Polygon":
                gs = [geom.exterior]
            elif geom.geom_type == "MultiPolygon":
                gs = [g.exterior for g in geom.geoms]
            for g in gs:
                c = np.asarray(g.coords)
                if c.shape[0] < 2:
                    continue
                step = max(1, c.shape[0] // 800)
                c = c[::step]
                segs.append((k, c)); k += 1
        with (DATA / f"{name}.dat").open("w", encoding="ascii") as fh:
            fh.write("x y\n")
            n = 0
            for _, c in segs:
                if n > maxpts:
                    break
                for px, py in c:
                    fh.write(f"{px / 1000:.5f} {py / 1000:.5f}\n"); n += 1
                fh.write("\n")
        log(f"  -> {name}.dat ({n} nokta)")

    # enlem/boylam ağı (graticule) — düz coğrafi çizgiler izdüşümde eğrilir,
    # bu yüzden her çizgi çok noktalı örneklenip dönüştürülür
    grat = []
    for lon in np.arange(np.ceil(LON0 * 2) / 2, LON1 + 1e-9, 0.5):
        grat.append(LineString([(lon, la) for la in np.linspace(LAT0, LAT1, 60)]))
    for lat in np.arange(np.ceil(LAT0 * 4) / 4, LAT1 + 1e-9, 0.25):
        grat.append(LineString([(lo, lat) for lo in np.linspace(LON0, LON1, 60)]))
    gg = gpd.GeoDataFrame(geometry=grat, crs="EPSG:4326").to_crs(UTM)
    gg = gg.clip(box(X.min(), Y.min(), X.max(), Y.max()))
    dump_lines(gg, "geo_graticule")

    coast = vec["coast"].clip(box(X.min(), Y.min(), X.max(), Y.max()))
    dump_lines(coast, "geo_coast")
    pb = gpd.GeoDataFrame(geometry=prov.boundary, crs=prov.crs).clip(box(X.min(), Y.min(), X.max(), Y.max()))
    dump_lines(pb, "geo_prov_lines")

    # ------------------------------------------------------------- kesitler --
    log("12 · arazi kesitleri (cross-section)")
    # 1. kesit: Karaburun–Bozdağ ekseni boyunca batı→doğu
    p0 = gpd.GeoSeries([Point(26.65, 38.42)], crs="EPSG:4326").to_crs(UTM)[0]
    p1 = gpd.GeoSeries([Point(28.10, 38.42)], crs="EPSG:4326").to_crs(UTM)[0]
    line = LineString([p0, p1])
    n_s = 260
    s = np.linspace(0, line.length, n_s)
    pt = [line.interpolate(v) for v in s]
    px = np.array([p.x for p in pt]); py = np.array([p.y for p in pt])
    jx = np.clip(((px - x[0]) / RES).astype(int), 0, nx - 1)
    iy = np.clip(((y[0] - py) / RES).astype(int), 0, ny - 1)
    prof = dict(z=dem[iy, jx], slope=slope_deg[iy, jx], twi=twi[iy, jx],
                risk=risk[iy, jx], ins=ins[iy, jx])
    table("geo_transect", "s z slope twi risk ins", s / 1000, prof["z"], prof["slope"],
          np.nan_to_num(prof["twi"], nan=0), np.nan_to_num(prof["risk"], nan=0), prof["ins"])

    # kesit boyunca yeraltı sıcaklık alanı — her nokta için bağlaşık model
    log("13 · kesit boyunca yeralti sicaklik alani")
    good = np.isfinite(prof["z"]) & (prof["z"] > 0.5)
    idx = np.nonzero(good)[0]
    def smooth(a, k=5):
        """Kesit boyunca 5 noktalı hareketli ortalama. TWI 360 m ızgarada
        hesaplandığı için 90 m'lik komşu hücreler arasında alt-çözünürlük
        gürültüsü taşır; toprak nemi bu ölçekte mekânsal olarak
        ilişkilidir, bu yüzden model girdileri yumuşatılır."""
        ker = np.ones(k) / k
        return np.convolve(np.nan_to_num(a, nan=float(np.nanmean(a))), ker, mode="same")

    psi_t = np.deg2rad(np.clip(smooth(prof["slope"][idx]), 0, 45))
    Kzz_t = k_par * np.sin(psi_t) ** 2 + k_perp * np.cos(psi_t) ** 2
    th0_t = np.clip(0.10 + 0.030 * (smooth(prof["twi"][idx]) - np.nanmedian(twi[land])),
                    0.08, 0.34)
    ta_t = np.clip(30.0 - 0.0065 * smooth(prof["z"][idx]), 12.0, 36.0)
    soil_t = Soil(lam_sat=(1.90 * Kzz_t / k_perp)[:, None])
    col_t = CoupledColumn(soil_t, depth=0.60, nz=120, batch=idx.size)
    rt = col_t.run(theta0=th0_t, t_amb=ta_t, scenario="preignition", t_end=5 * 3600,
                   dt=30.0, probe_depth=0.06, spin_dt=600.0)
    Tf, thf = rt["T_final"], rt["th_final"]
    zc = col_t.z * 100
    Sg, Zg = np.meshgrid(s[idx] / 1000, zc, indexing="ij")
    matrix_table("geo_section", "s z T theta", Sg, Zg, Tf, thf, stride=1)

    at = fusion_alarm(rt)
    table("geo_transect_lead", "s lead z", s[idx] / 1000,
          np.nan_to_num(at["lead"] / 60, nan=0.0), prof["z"][idx])

    G["transect"] = dict(length_km=float(line.length / 1000),
                         z_max=float(np.nanmax(prof["z"])),
                         lead_median=float(np.nanmedian(at["lead"] / 60)))
    G["grid"] = dict(res_m=RES, shape=[int(ny), int(nx)],
                     bbox=[LON0, LAT0, LON1, LAT1], crs=UTM,
                     land_km2=float(land.sum() * RES * RES / 1e6),
                     elev_max=float(np.nanmax(dem)),
                     slope_mean=float(np.nanmean(slope_deg[land])),
                     risk_high_km2=float(np.nansum(risk > 0.62) * RES * RES / 1e6))

    (ROOT / "summary_geo.json").write_text(json.dumps(G, indent=2, ensure_ascii=False),
                                           encoding="utf-8")
    log(f"bitti ({time.time() - T0:.0f} s)")


if __name__ == "__main__":
    main()
