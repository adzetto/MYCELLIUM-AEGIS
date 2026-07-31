"""
=============================================================================
MYCELLIUM-AEGIS · FİZİBİLİTE ANALİZİ
aegis_physics.py — kurucu bağıntılar ve PDE çözücüleri
-----------------------------------------------------------------------------
Bu modül fizibilite raporunun sayısal çekirdeğidir. Dört bağımsız çözücü içerir:

  1. CoupledColumn   — 1B bağlaşık ısı/nem taşınımı (Philip & de Vries),
                       yığın (batched) yarı-örtük şema, Monte Carlo için
                       vektörleştirilmiş.
  2. AnisotropicSlab — 2B tam tensör iletkenlikli ısı iletimi; çapraz
                       (off-diagonal) terimler dahil, üretilmiş çözümle
                       (MMS) doğrulanabilir.
  3. AxisymmetricERT — eksenel simetrik ∇·(σ∇φ) = -Iδ çözücüsü; anizotropik
                       yarı-uzayın analitik çözümüne karşı doğrulanır,
                       Geselowitz duyarlılık çekirdeğini üretir.
  4. Yardımcılar     — von Neumann kararlılık matrisi, Richardson dışdeğer
                       biçme, GCI.

Kurucu modeller literatürdendir ve kaynakları kodda işaretlenmiştir. Model
parametreleri kumlu tın (sandy loam) toprağa aittir; saha kalibrasyonu
WP-2 iklim odası ölçümlerinin konusudur.
=============================================================================
"""
from __future__ import annotations

import numpy as np

# ============================================================ SABİTLER =====
R_GAS = 8.314462618          # J/(mol·K)
M_W = 0.018015268            # kg/mol       su molar kütlesi
G_ACC = 9.80665              # m/s²
RHO_W = 1000.0               # kg/m³
C_W = 4182.0                 # J/(kg·K)     su özgül ısısı
L_VAP = 2.45e6               # J/kg         buharlaşma gizli ısısı
T0_K = 273.15


# ==================================================== TOPRAK PARAMETRELERİ =
class Soil:
    """Kumlu tın toprak. van Genuchten–Mualem parametreleri Carsel & Parrish
    (1988); ısıl iletkenlik Côté & Konrad (2005) normalize modeli."""

    def __init__(self,
                 theta_r=0.065, theta_s=0.410, alpha_vg=7.5, n_vg=1.89,
                 Ks=1.228e-5, rho_b=1500.0, c_solid=800.0,
                 lam_dry=0.25, lam_sat=1.90, kappa=4.70,
                 clay=0.10, sigma_w25=0.020, m_archie=1.8, n_archie=2.0,
                 alpha_T=0.020):
        self.theta_r = theta_r
        self.theta_s = theta_s
        self.alpha = alpha_vg          # 1/m
        self.n = n_vg
        self.m = 1.0 - 1.0 / n_vg
        self.Ks = Ks                   # m/s
        self.rho_b = rho_b
        self.c_solid = c_solid
        self.lam_dry = lam_dry
        self.lam_sat = lam_sat
        self.kappa = kappa
        self.clay = clay
        # Ölçek parametreleri dizi olarak da verilebilir (Monte Carlo'da üye
        # başına (M,1) biçiminde); tüm işlemler eleman bazlı olduğu için
        # yayınlama (broadcasting) kendiliğinden çalışır.
        self.sigma_w25 = sigma_w25
        self.m_archie = m_archie
        self.n_archie = n_archie
        self.alpha_T = alpha_T

    # ---------------------------------------------------------- doygunluk --
    def Se(self, th):
        return np.clip((th - self.theta_r) / (self.theta_s - self.theta_r),
                       1e-6, 1.0)

    def psi(self, th):
        """Matris potansiyeli [m], negatif."""
        Se = self.Se(th)
        return -(1.0 / self.alpha) * (Se ** (-1.0 / self.m) - 1.0) ** (1.0 / self.n)

    def dpsi_dtheta(self, th):
        """dψ/dθ [m / (m³/m³)], analitik türev."""
        Se = self.Se(th)
        dSe = 1.0 / (self.theta_s - self.theta_r)
        x = Se ** (-1.0 / self.m) - 1.0
        # dψ/dSe = (1/(α n m)) x^(1/n - 1) Se^(-1/m - 1)
        dpsi_dSe = (1.0 / (self.alpha * self.n * self.m)) * \
                   x ** (1.0 / self.n - 1.0) * Se ** (-1.0 / self.m - 1.0)
        return dpsi_dSe * dSe

    def K_unsat(self, th):
        """Mualem–van Genuchten doymamış hidrolik iletkenlik [m/s]."""
        Se = self.Se(th)
        return self.Ks * np.sqrt(Se) * (1.0 - (1.0 - Se ** (1.0 / self.m)) ** self.m) ** 2

    def D_liquid(self, th):
        """İzotermal sıvı nem yayınımı D_θl = K |dψ/dθ| [m²/s]."""
        return self.K_unsat(th) * np.abs(self.dpsi_dtheta(th))

    # ------------------------------------------------------------- termal --
    def heat_capacity(self, th):
        """Hacimsel ısı kapasitesi C(θ) [J/(m³·K)]."""
        return self.rho_b * self.c_solid + RHO_W * C_W * th

    def lam_solid(self, th):
        """Côté & Konrad (2005): λ = (λ_sat − λ_dry)·κSr/(1+(κ−1)Sr) + λ_dry."""
        Sr = np.clip(th / self.theta_s, 0.0, 1.0)
        ke = self.kappa * Sr / (1.0 + (self.kappa - 1.0) * Sr)
        return self.lam_dry + (self.lam_sat - self.lam_dry) * ke

    # ------------------------------------------------------------- buhar ---
    @staticmethod
    def rho_sv(T_c):
        """Doygun buhar yoğunluğu [kg/m³]. Magnus–Tetens + ideal gaz.
        Formülün geçerlilik bandı dışına çıkmamak için 99 °C'de kesilir."""
        T = np.clip(T_c, -20.0, 99.0)
        es = 611.2 * np.exp(17.62 * T / (243.12 + T))          # Pa
        return es * M_W / (R_GAS * (T + T0_K))

    @staticmethod
    def drho_sv_dT(T_c):
        """dρ_sv/dT [kg/(m³·K)], analitik."""
        T = np.clip(T_c, -20.0, 99.0)
        es = 611.2 * np.exp(17.62 * T / (243.12 + T))
        des = es * 17.62 * 243.12 / (243.12 + T) ** 2
        Tk = T + T0_K
        return M_W / R_GAS * (des / Tk - es / Tk ** 2)

    def h_rel(self, th, T_c):
        """Gözenek bağıl nemi — Kelvin denklemi."""
        psi = self.psi(th)
        return np.exp(M_W * G_ACC * psi / (R_GAS * (T_c + T0_K)))

    def tortuosity(self, th):
        """Millington & Quirk (1961) gaz fazı tortuozitesi ξ = (φ−θ)^{7/3}/φ²."""
        air = np.clip(self.theta_s - th, 1e-6, None)
        return air ** (7.0 / 3.0) / self.theta_s ** 2

    def enhancement(self, th):
        """Cass, Campbell & Jones (1984) buhar taşınımı artırma katsayısı."""
        f = np.clip(th / self.theta_s, 0.0, 1.0)
        a = 1.0 + 2.6 / np.sqrt(max(self.clay, 1e-3))
        return 9.5 + 3.0 * f - 8.5 * np.exp(-((a * f) ** 4))

    def D_air(self, T_c):
        """Havada su buharı moleküler yayınımı [m²/s]."""
        return 2.12e-5 * ((T_c + T0_K) / T0_K) ** 2.0

    def D_Tv(self, th, T_c):
        """Isıl buhar yayınımı D_Tv [m²/(s·K)] — de Vries."""
        return (self.D_air(T_c) * self.tortuosity(th) / RHO_W) * \
               self.enhancement(th) * self.h_rel(th, T_c) * self.drho_sv_dT(T_c)

    def D_thv(self, th, T_c):
        """İzotermal buhar yayınımı D_θv [m²/s] — de Vries."""
        Tk = T_c + T0_K
        return (self.D_air(T_c) * self.tortuosity(th) / RHO_W) * \
               self.rho_sv(T_c) * self.h_rel(th, T_c) * \
               (M_W * G_ACC / (R_GAS * Tk)) * self.dpsi_dtheta(th)

    def lam_eff(self, th, T_c):
        """Etkin ısıl iletkenlik: katı/sıvı iletim + gizli ısı taşınımı."""
        return self.lam_solid(th) + L_VAP * RHO_W * self.D_Tv(th, T_c)

    # -------------------------------------------------------- elektriksel --
    def sigma(self, th, T_c, sigma_w25=None, m_archie=None, n_archie=None):
        """Archie yasası + sıcaklık düzeltmesi (Arps, ≈%2/°C).
        σ = σ_w(T) · φ^m · S^n   [S/m]"""
        S = np.clip(th / self.theta_s, 1e-4, 1.0)
        sw25 = self.sigma_w25 if sigma_w25 is None else sigma_w25
        m_a = self.m_archie if m_archie is None else m_archie
        n_a = self.n_archie if n_archie is None else n_archie
        sw = sw25 * (1.0 + self.alpha_T * (np.clip(T_c, -10, 200) - 25.0))
        return sw * self.theta_s ** m_a * S ** n_a


# ============================================== YÜZEY SICAKLIK SENARYOLARI =
def surface_temperature(t, scenario="preignition", t_amb=22.0, t_start=3 * 3600.0,
                        ramp=5400.0, t_peak=300.0):
    """Yüzey (z=0) sıcaklığı [°C]. Dijital ikizdeki senaryolarla aynı biçim,
    ancak parametreleri Monte Carlo için dışarıdan verilebilir."""
    diurnal = t_amb + 10.0 * np.sin(2.0 * np.pi * (t - 32400.0) / 86400.0)
    if scenario == "normal":
        return t_amb + 12.0 * np.sin(2.0 * np.pi * (t - 32400.0) / 86400.0)
    if scenario == "drought":
        return t_amb + 8.0 + 22.0 * np.maximum(0.0, np.sin(2.0 * np.pi * (t - 32400.0) / 86400.0))
    if scenario == "preignition":
        u = np.clip((t - t_start) / ramp, 0.0, 1.0)
        rise = t_amb + (t_peak - t_amb) * (u * u * (3.0 - 2.0 * u))
        plateau = 140.0 * np.clip((t - t_start - ramp) / 9000.0, 0.0, 1.0)
        return np.where(t < t_start, diurnal, rise + plateau)
    if scenario == "surface":
        dt_ = t - t_start
        early = t_amb + (900.0 - t_amb) * np.clip(dt_ / 300.0, 0.0, 1.0)
        late = np.maximum(t_amb + 20.0, 260.0 + 640.0 * np.exp(-np.maximum(dt_ - 1200.0, 0.0) / 2400.0))
        val = np.where(dt_ < 300.0, early, np.where(dt_ < 1200.0, 900.0, late))
        return np.where(t < t_start, diurnal, val)
    raise ValueError(scenario)


# ================================================ 1B BAĞLAŞIK SÜTUN ÇÖZÜCÜ =
def thomas_batch(a, b, c, d):
    """Yığın tridiagonal çözücü. a,b,c,d: (M,N). Thomas algoritması,
    M sistemi aynı anda çözer. Kısmi pivotlama yoktur; matrisler köşegen
    baskındır (yarı-örtük difüzyon), bu koşulda algoritma kararlıdır."""
    M, N = b.shape
    cp = np.empty((M, N))
    dp = np.empty((M, N))
    cp[:, 0] = c[:, 0] / b[:, 0]
    dp[:, 0] = d[:, 0] / b[:, 0]
    for i in range(1, N):
        den = b[:, i] - a[:, i] * cp[:, i - 1]
        cp[:, i] = c[:, i] / den
        dp[:, i] = (d[:, i] - a[:, i] * dp[:, i - 1]) / den
    x = np.empty((M, N))
    x[:, -1] = dp[:, -1]
    for i in range(N - 2, -1, -1):
        x[:, i] = dp[:, i] - cp[:, i] * x[:, i + 1]
    return x


class CoupledColumn:
    """1B bağlaşık ısı–nem taşınımı, sonlu hacim ayrıklaştırması.

        C(θ) ∂T/∂t = ∂_z(λ_eff ∂_z T) + L ρ_w ∂_z(D_θv ∂_z θ)
        ∂θ/∂t      = ∂_z(D_θ ∂_z θ)   + ∂_z(D_Tv ∂_z T) − ∂_z K(θ)

    Zaman ilerlemesi ardışık yarı-örtük (semi-implicit): katsayılar önceki
    adımdan alınır, difüzyon terimi örtük çözülür → doğrusal kararlılık
    koşulsuzdur; hata O(Δt) + O(Δz²).
    """

    def __init__(self, soil: Soil, depth=0.60, nz=120, batch=1,
                 t_boil=100.0, dT_boil=8.0, k_boil=1.0e-3, theta_dry=0.005,
                 latent_iso=False):
        self.soil = soil
        self.nz = nz
        self.dz = depth / nz
        self.z = (np.arange(nz) + 0.5) * self.dz     # hücre merkezleri
        self.M = batch
        self.t_boil = t_boil                          # °C  kaynama sıcaklığı
        self.dT_boil = dT_boil                        # K   kinetik ölçek
        self.k_boil = k_boil                          # s⁻¹ kinetik hız katsayısı
        self.theta_dry = theta_dry                    # hava-kurusu artık su
        self.latent_iso = latent_iso                  # izotermal gizli ısı terimi

    # ------------------------------------------------- faz değişimi (kaynama)
    def _boil_rate(self, T, th):
        """Buharlaşma cephesinin birinci mertebe kinetiği:

            Ṡ = k₀ · max(0, T − T_b)/ΔT · (θ − θ_dry)   [s⁻¹]

        Isı denkleminde L ρ_w Ṡ kadar gizli ısı çekilir. Sıcaklık, sıvı su
        tükenene kadar T_b'nin hemen üstünde tutulur; düzlüğün süresi k₀'a
        değil enerji arzına bağlıdır — L ρ_w Δθ / q. k₀ bu nedenle fiziksel
        bir parametre değil, cepheyi çözmeye yeten bir gevşeme hızıdır;
        sonuçların k₀'a duyarsızlığı raporun 3.6 bölümünde ölçülmüştür.
        Dönüş: birim θ başına hız katsayısı [s⁻¹] (θ'ya göre doğrusal)."""
        return self.k_boil * np.maximum(0.0, T - self.t_boil) / self.dT_boil

    # --------------------------------------------------------- başlangıç ---
    def initial(self, theta0, t_amb):
        M, N = self.M, self.nz
        th = np.empty((M, N))
        # ölü örtü yüzeyde daha kurudur; 12 cm'de profil taban değere oturur
        shape = 0.55 + 0.45 * np.clip(self.z / 0.12, 0, 1)
        th[:] = np.atleast_1d(theta0)[:, None] * shape[None, :]
        T = np.repeat(np.atleast_1d(t_amb)[:, None], N, axis=1).astype(float)
        return T, th

    # --------------------------------------------------------- tek adım ----
    def _step(self, T, th, Ts, dt, t_amb, r_aero, rh_air, theta_floor):
        """Bir yarı-örtük zaman adımı. Isı denklemi önce örtük çözülür, nem
        denklemi güncellenmiş sıcaklık alanıyla ardışık olarak çözülür."""
        soil = self.soil
        M, N, dz = T.shape[0], self.nz, self.dz

        lam = soil.lam_eff(th, T)
        Cv = soil.heat_capacity(th)
        kb = self._boil_rate(T, th)                    # s⁻¹ (θ katsayısı)
        Dtv = soil.D_Tv(th, T)
        Dthv = soil.D_thv(th, T)
        Dl = soil.D_liquid(th)
        Kh = soil.K_unsat(th)

        lam_f = 0.5 * (lam[:, :-1] + lam[:, 1:])
        Dth_f = 0.5 * (Dl[:, :-1] + Dl[:, 1:]) + 0.5 * (Dthv[:, :-1] + Dthv[:, 1:])
        DT_f = 0.5 * (Dtv[:, :-1] + Dtv[:, 1:])
        Dv_f = 0.5 * (Dthv[:, :-1] + Dthv[:, 1:])

        # ===================== ISI DENKLEMİ (örtük) =====================
        a = np.zeros((M, N)); b = np.ones((M, N))
        c = np.zeros((M, N)); d = np.zeros((M, N))
        coef = dt / (Cv * dz * dz)
        a[:, 1:] = -coef[:, 1:] * lam_f
        c[:, :-1] = -coef[:, :-1] * lam_f
        b[:, 1:] += coef[:, 1:] * lam_f
        b[:, :-1] += coef[:, :-1] * lam_f
        b[:, 0] += coef[:, 0] * 2.0 * lam[:, 0]        # yüzey Dirichlet
        b[:, -1] += coef[:, -1] * 2.0 * lam[:, -1]     # taban Dirichlet

        # İzotermal (nem gradyanı kaynaklı) buharın taşıdığı gizli ısı.
        # Bu terim varsayılan olarak KAPALIDIR. Gerekçesi iki yönlüdür:
        #   (i) fiziksel — cephe civarında ısıl sürüklenmenin taşıdığı buhar
        #       akısı, izotermal olanın yaklaşık otuz katıdır;
        #   (ii) sayısal — L ρ_w D_θv / C etkin yayınımı, çok kuru toprakta
        #       dψ/dθ sınırsız büyüdüğü için 10⁻⁴ m²/s mertebesine çıkar ve
        #       açık ayrıklaştırmada şemayı kararsızlaştırır (θ ≈ θ_r
        #       hücrelerinde adım başına onlarca kelvinlik salınım).
        # Terimin etkisi, kararlı bir Δt'de açık/kapalı koşularak raporun
        # 3.5 bölümünde ölçülmüştür. Nem denkleminde aynı katsayı ÖRTÜK
        # olarak korunur; orada kararlılık sorunu yoktur ve kuru toprakta
        # nem taşınımının baskın mekanizması zaten buhardır.
        if self.latent_iso:
            qv = Dv_f * (th[:, 1:] - th[:, :-1]) / dz
            div_qv = np.zeros((M, N))
            div_qv[:, :-1] += qv / dz
            div_qv[:, 1:] -= qv / dz
            d[:] = T + dt * L_VAP * RHO_W * div_qv / Cv
        else:
            d[:] = T
        d[:, 0] += coef[:, 0] * 2.0 * lam[:, 0] * Ts
        d[:, -1] += coef[:, -1] * 2.0 * lam[:, -1] * t_amb

        # kaynama gizli ısısı — T'ye göre doğrusal olduğu için örtük alınır:
        # −Lρ_w k₀(T−T_b)(θ−θ_dry)/ΔT  ⇒  köşegene A, sağ tarafa A·T_b
        Abo = dt * L_VAP * RHO_W * self.k_boil * \
            np.maximum(th - self.theta_dry, 0.0) / (self.dT_boil * Cv)
        act = (T > self.t_boil)
        b += np.where(act, Abo, 0.0)
        d += np.where(act, Abo * self.t_boil, 0.0)

        Tn = np.clip(thomas_batch(a, b, c, d), -30.0, 1200.0)

        # ===================== NEM DENKLEMİ (örtük) =====================
        a2 = np.zeros((M, N)); b2 = np.ones((M, N))
        c2 = np.zeros((M, N)); d2 = np.zeros((M, N))
        coef2 = dt / (dz * dz)
        a2[:, 1:] = -coef2 * Dth_f
        c2[:, :-1] = -coef2 * Dth_f
        b2[:, 1:] += coef2 * Dth_f
        b2[:, :-1] += coef2 * Dth_f

        qT = DT_f * (Tn[:, 1:] - Tn[:, :-1]) / dz      # ısıl sürüklenme
        div_qT = np.zeros((M, N))
        div_qT[:, :-1] += qT / dz
        div_qT[:, 1:] -= qT / dz

        qg = np.zeros((M, N + 1))                      # yerçekimi, yukarı-akım
        qg[:, 1:-1] = Kh[:, :-1]
        qg[:, -1] = Kh[:, -1]                          # serbest drenaj
        div_qg = (qg[:, 1:] - qg[:, :-1]) / dz

        hr = soil.h_rel(th[:, 0], Tn[:, 0])            # yüzey buharlaşması
        rv_soil = hr * soil.rho_sv(Tn[:, 0])
        rv_air = rh_air * soil.rho_sv(np.minimum(t_amb + 5.0, 45.0))
        E = np.maximum(0.0, (rv_soil - rv_air) / (RHO_W * r_aero))
        E = np.minimum(E, np.maximum(0.0, th[:, 0] - theta_floor) * dz / dt)

        # kaynama kaybı — ısı denkleminde çekilen gizli ısıyla birebir aynı
        # terim; θ'ya göre doğrusal olduğu için burada da örtük alınır.
        kbn = self._boil_rate(Tn, th)
        b2 += dt * kbn
        d2[:] = th + dt * div_qT - dt * div_qg + dt * kbn * self.theta_dry
        d2[:, 0] -= dt * E / dz

        thn = np.clip(thomas_batch(a2, b2, c2, d2), theta_floor, soil.theta_s * 0.999)
        return Tn, thn

    # ------------------------------------------------------------ yürüt ----
    def run(self, *, theta0, t_amb, scenario="preignition", t_start=3 * 3600.0,
            ramp=5400.0, t_peak=300.0, t_end=8 * 3600.0, dt=10.0,
            probe_depth=0.06, record=None, r_aero=100.0, rh_air=0.35,
            spin_days=2.0, spin_dt=120.0, kernel_weights=None):
        """Sütunu t_end'e kadar ilerletir.

        Önce `spin_days` gün boyunca yalnızca günlük döngü uygulanır; böylece
        başlangıç profili sönümlü ısı dalgasının periyodik rejimine oturur ve
        olay başlangıcında yapay bir geçici davranış görülmez.
        """
        soil = self.soil
        M, N, dz = self.M, self.nz, self.dz
        theta0 = np.broadcast_to(np.atleast_1d(theta0), (M,)).astype(float).copy()
        t_amb = np.broadcast_to(np.atleast_1d(t_amb), (M,)).astype(float).copy()
        t_start_v = np.broadcast_to(np.atleast_1d(t_start), (M,)).astype(float).copy()
        ramp_v = np.broadcast_to(np.atleast_1d(ramp), (M,)).astype(float).copy()
        t_peak_v = np.broadcast_to(np.atleast_1d(t_peak), (M,)).astype(float).copy()

        # van Genuchten fonksiyonları Se ∈ [1e−6, 1] aralığına kırpıldığı için
        # θ, artık su içeriğinin altına inebilir; kaynama cephesinin arkasında
        # toprak hava-kurusu hâle gelir ve iletim λ_dry'a çöker.
        theta_floor = self.theta_dry
        T, th = self.initial(theta0, t_amb)
        zp = np.broadcast_to(np.atleast_1d(probe_depth), (M,)).astype(float)
        ip = np.clip(np.round(zp / dz - 0.5).astype(int), 0, N - 1)

        if kernel_weights is None:
            # Elektrot çifti sıcaklık probuyla aynı çubuk üzerindedir; duyarlılık
            # bandı prob derinliğine merkezlenir. Gerçek çekirdek AxisymmetricERT
            # tarafından üretilir ve dışarıdan verilebilir.
            w = np.exp(-0.5 * ((self.z[None, :] - zp[:, None]) / 0.030) ** 2)
            kernel_weights = w / w.sum(axis=1, keepdims=True)
        kw = np.atleast_2d(np.asarray(kernel_weights, float))
        if kw.shape[0] == 1 and M > 1:
            kw = np.repeat(kw, M, axis=0)

        rows = np.arange(M)

        def logR(T_, th_):
            """Elektrot çiftinin gördüğü transfer direncinin logaritması.
            Duyarlılık çekirdeğiyle ağırlıklı iletkenlik ortalaması üzerinden
            birinci mertebe (Born) yaklaşımıdır; tam ERT çözümüyle
            karşılaştırması raporda verilmiştir."""
            return -np.log(np.sum(soil.sigma(th_, T_) * kw, axis=1))

        # ------------------------------------------------ ısınma (spin-up) --
        n_spin = int(round(spin_days * 86400.0 / spin_dt))
        for n in range(n_spin):
            tt = -(n_spin - n) * spin_dt
            # Isınma, senaryonun kendi yüzey fonksiyonuyla yapılır; olay
            # senaryolarında t < t_start olduğu için bu, günlük döngü dalıdır.
            # Böylece t = 0'da yapay bir sıçrama oluşmaz.
            Ts = surface_temperature(tt, scenario, t_amb, t_start_v, ramp_v, t_peak_v)
            T, th = self._step(T, th, Ts, spin_dt, t_amb, r_aero, rh_air, theta_floor)

        # ---------------------------------------------------------- olay ----
        nsteps = int(round(t_end / dt))
        rec_idx = {int(round(rt / dt)): rt for rt in (record or [])}
        profiles = {}

        ts = np.empty(nsteps + 1)
        T_probe = np.empty((M, nsteps + 1))
        th_probe = np.empty((M, nsteps + 1))
        lnR = np.empty((M, nsteps + 1))
        T_surf_hist = np.empty((M, nsteps + 1))

        ts[0] = 0.0
        T_probe[:, 0] = T[rows, ip]; th_probe[:, 0] = th[rows, ip]
        lnR[:, 0] = logR(T, th)
        T_surf_hist[:, 0] = surface_temperature(0.0, scenario, t_amb, t_start_v, ramp_v, t_peak_v)

        for n in range(1, nsteps + 1):
            t = n * dt
            Ts = surface_temperature(t, scenario, t_amb, t_start_v, ramp_v, t_peak_v)
            T, th = self._step(T, th, Ts, dt, t_amb, r_aero, rh_air, theta_floor)

            ts[n] = t
            T_probe[:, n] = T[rows, ip]
            th_probe[:, n] = th[rows, ip]
            lnR[:, n] = logR(T, th)
            T_surf_hist[:, n] = Ts
            if n in rec_idx:
                profiles[rec_idx[n]] = (T.copy(), th.copy())

        return dict(t=ts, T_probe=T_probe, th_probe=th_probe, lnR=lnR,
                    T_surf=T_surf_hist, profiles=profiles, z=self.z,
                    T_final=T, th_final=th, dt=dt, ip=ip, probe_depth=probe_depth)


# ------------------------------------------------------- alarm mantığı -----
def fusion_alarm(res, beta=1.5, gamma=0.002, hold=45 * 60.0, ignite_T=300.0,
                 two_sided=True):
    """β (ısı akısı hızı, °C/10 dk) ve γ (elektriksel kayma hızı, dk⁻¹)
    koşullarını kalıcılık penceresiyle birleştirir.

    `two_sided=True` ise γ koşulu |d(lnR)/dt| > γ biçiminde işletilir. Bunun
    gerekçesi raporun 4. bölümündedir: bağlaşık model altında prob
    derinliğinde direnç, kuruma cephesi varmadan önce ısınma ve buhar
    yoğuşması nedeniyle DÜŞER; tek yönlü (yalnızca artış) kural bu erken
    imzayı göremez. `two_sided=False` özgün belgedeki kuralı verir.

    Dönüş: alarm zamanı, tutuşma zamanı, öncü süre (saniye); alarm yoksa NaN.
    """
    t = res["t"]
    dt = t[1] - t[0]
    # Hızlar, gömülü yazılımın kullandığı pencerede ölçülür: β zaten
    # "°C / 10 dakika" olarak tanımlıdır, dolayısıyla anlık türev değil
    # 10 dakikalık merkezî fark doğru tahmin edicidir. Bu seçim ayrıca
    # buharlaşma cephesinin sabit ızgara üzerinde hücreden hücreye
    # atlamasından doğan merdiven artefaktını da bastırır.
    dTdt = window_rate(res["T_probe"], dt, 600.0, 600.0)           # °C/10 dk
    dlnR = window_rate(res["lnR"], dt, 600.0, 60.0)                # dk⁻¹
    c1 = dTdt > beta
    c2 = (np.abs(dlnR) > gamma) if two_sided else (dlnR > gamma)
    M, Nt = c1.shape

    last1 = np.full(M, -1e12); last2 = np.full(M, -1e12)
    t_alarm = np.full(M, np.nan)
    for k in range(Nt):
        last1 = np.where(c1[:, k], t[k], last1)
        last2 = np.where(c2[:, k], t[k], last2)
        both = ((t[k] - last1) <= hold) & ((t[k] - last2) <= hold)
        fresh = both & np.isnan(t_alarm)
        t_alarm = np.where(fresh, t[k], t_alarm)

    # --- eşik geçişlerinin doğrusal ara değerle sürekli hâle getirilmesi ---
    # Ayrık örnekleme, öncü süreyi Δt adımlarına kuantalar ve yakınsama
    # mertebesinin ölçülmesini imkânsız kılar. Geçiş zamanı, eşiği aşan iki
    # örnek arasında doğrusal ara değerle bulunur.
    t1 = _first_crossing(t, dTdt, beta)
    t2 = _first_crossing(t, np.abs(dlnR) if two_sided else dlnR, gamma)
    t_interp = np.maximum(t1, t2)
    ok = np.isfinite(t_alarm) & np.isfinite(t_interp) & \
        (np.abs(t_interp - t_alarm) <= 1.5 * dt)
    t_alarm = np.where(ok, t_interp, t_alarm)

    t_ign = _first_crossing(t, res["T_surf"], ignite_T)
    lead = t_ign - t_alarm
    return dict(t_alarm=t_alarm, t_ignite=t_ign, lead=lead,
                dTdt=dTdt, dlnR=dlnR, t_beta=t1, t_gamma=t2)


def window_rate(y, dt, window=600.0, scale=600.0):
    """y'nin `window` saniyelik merkezî pencere üzerindeki ortalama değişim
    hızı; `scale` saniyeye bölünmüş sonucu istenen birime çevirir
    (600 → birim/10 dk, 60 → birim/dk). Kenarlarda pencere kısalır."""
    y = np.atleast_2d(y)
    n = y.shape[1]
    w = max(1, int(round(window / dt)))
    if w >= n:
        w = max(1, n - 1)
    i = np.arange(n)
    hi = np.minimum(i + (w + 1) // 2, n - 1)
    lo = np.maximum(i - w // 2, 0)
    span = (hi - lo) * dt
    span[span == 0] = dt
    return (y[:, hi] - y[:, lo]) / span * scale


def _first_crossing(t, y, thr):
    """y > thr koşulunun ilk sağlandığı anı doğrusal ara değerle döndürür.
    Hiç sağlanmıyorsa NaN. y: (M,Nt)."""
    y = np.atleast_2d(y)
    hit = y > thr
    any_hit = hit.any(axis=1)
    k = np.argmax(hit, axis=1)
    kk = np.maximum(k, 1)
    y0 = np.take_along_axis(y, (kk - 1)[:, None], 1)[:, 0]
    y1 = np.take_along_axis(y, kk[:, None], 1)[:, 0]
    frac = np.where(np.abs(y1 - y0) > 1e-30, (thr - y0) / (y1 - y0), 0.0)
    tc = t[kk - 1] + np.clip(frac, 0.0, 1.0) * (t[kk] - t[kk - 1])
    tc = np.where(k == 0, t[0], tc)
    return np.where(any_hit, tc, np.nan)


# ========================================== 2B TAM TENSÖRLÜ ISI İLETİMİ ====
class AnisotropicSlab:
    """2B (x,z) ısı iletimi, tam anizotropik iletkenlik tensörü ile:

        ρc ∂T/∂t = ∇·(K ∇T) + f,     K = [[Kxx, Kxz], [Kxz, Kzz]]

    Ayrıklaştırma: yüz merkezli akılar; çapraz terimler dört noktalı
    ortalama ile → düzgün ızgarada ikinci mertebe. Açık zaman ilerlemesi
    (MMS doğrulaması için hata mertebesi temiz kalsın diye).
    """

    def __init__(self, Lx, Lz, nx, nz):
        self.Lx, self.Lz, self.nx, self.nz = Lx, Lz, nx, nz
        self.dx, self.dz = Lx / nx, Lz / nz
        self.x = (np.arange(nx) + 0.5) * self.dx
        self.z = (np.arange(nz) + 0.5) * self.dz
        self.X, self.Z = np.meshgrid(self.x, self.z, indexing="ij")

    @staticmethod
    def tensor(k_par, k_perp, dip_deg):
        """Katmanlı ortam için enine izotrop tensör:
            K = k_par (I − n⊗n) + k_perp n⊗n,  n = (sinψ, cosψ)
        ψ eğim (dip) açısıdır; ψ=0'da katmanlanma yataydır."""
        psi = np.deg2rad(dip_deg)
        n = np.array([np.sin(psi), np.cos(psi)])
        I = np.eye(2)
        K = k_par * (I - np.outer(n, n)) + k_perp * np.outer(n, n)
        return K

    def divergence(self, T, Kxx, Kxz, Kzz):
        """∇·(K∇T) — ikinci mertebe, çapraz terimler dahil.
        Sınırlarda Neumann (sıfır akı) varsayılır; MMS testinde çözüm
        sınırlarda düz olduğu için mertebeyi bozmaz."""
        dx, dz = self.dx, self.dz
        Tp = np.pad(T, 1, mode="edge")

        # x yüzlerindeki akı: Fx = Kxx ∂_x T + Kxz ∂_z T
        # Çapraz türev, yüzü paylaşan iki hücrenin merkezî farklarının
        # ortalamasıdır → düzgün ızgarada O(h²).
        Kxx_f = 0.5 * (Kxx[:-1, :] + Kxx[1:, :])
        Kxz_fx = 0.5 * (Kxz[:-1, :] + Kxz[1:, :])
        dTdx_f = (T[1:, :] - T[:-1, :]) / dx
        dTdz_fx = ((Tp[1:-2, 2:] - Tp[1:-2, :-2]) +
                   (Tp[2:-1, 2:] - Tp[2:-1, :-2])) / (4 * dz)
        Fx = Kxx_f * dTdx_f + Kxz_fx * dTdz_fx

        # z yüzlerindeki akı: Fz = Kxz ∂_x T + Kzz ∂_z T
        Kzz_f = 0.5 * (Kzz[:, :-1] + Kzz[:, 1:])
        Kxz_fz = 0.5 * (Kxz[:, :-1] + Kxz[:, 1:])
        dTdz_f = (T[:, 1:] - T[:, :-1]) / dz
        dTdx_fz = ((Tp[2:, 1:-2] - Tp[:-2, 1:-2]) +
                   (Tp[2:, 2:-1] - Tp[:-2, 2:-1])) / (4 * dx)
        Fz = Kzz_f * dTdz_f + Kxz_fz * dTdx_fz

        # ∇·F ≈ (F_{i+1/2} − F_{i−1/2}) / h
        div = np.zeros_like(T)
        div[:-1, :] += Fx / dx
        div[1:, :] -= Fx / dx
        div[:, :-1] += Fz / dz
        div[:, 1:] -= Fz / dz
        return div


# ------------------------------------------------- MMS doğrulama yardımı ---
def mms_fields(X, Z, t, Lx, Lz, k0=1.0, k1=0.35, dip=25.0, rho_c=2.0e6, tau=4000.0):
    """Üretilmiş çözüm ve karşılık gelen kaynak terimi.

        T*(x,z,t) = e^{-t/τ} cos(πx/Lx) cos(πz/Lz)
        K(x,z)    = K₀(dip) · (1 + 0.3 sin(2πx/Lx) sin(πz/Lz))

    Kaynak f = ρc ∂T/∂t − ∇·(K∇T) analitik olarak hesaplanır; çözücünün bu
    kaynakla ürettiği çözüm T*'ye yakınsamalıdır.
    """
    kx = np.pi / Lx
    kz = np.pi / Lz
    E = np.exp(-t / tau)
    T = E * np.cos(kx * X) * np.cos(kz * Z)
    dTdt = -T / tau
    Tx = -E * kx * np.sin(kx * X) * np.cos(kz * Z)
    Tz = -E * kz * np.cos(kx * X) * np.sin(kz * Z)
    Txx = -kx * kx * T
    Tzz = -kz * kz * T
    Txz = E * kx * kz * np.sin(kx * X) * np.sin(kz * Z)

    K0 = AnisotropicSlab.tensor(k0, k1, dip)
    g = 1.0 + 0.3 * np.sin(2 * np.pi * X / Lx) * np.sin(np.pi * Z / Lz)
    gx = 0.3 * (2 * np.pi / Lx) * np.cos(2 * np.pi * X / Lx) * np.sin(np.pi * Z / Lz)
    gz = 0.3 * (np.pi / Lz) * np.sin(2 * np.pi * X / Lx) * np.cos(np.pi * Z / Lz)

    Kxx = K0[0, 0] * g; Kxz = K0[0, 1] * g; Kzz = K0[1, 1] * g

    # ∇·(K∇T) = ∂_x(Kxx Tx + Kxz Tz) + ∂_z(Kxz Tx + Kzz Tz)
    div = (K0[0, 0] * (gx * Tx + g * Txx) + K0[0, 1] * (gx * Tz + g * Txz) +
           K0[0, 1] * (gz * Tx + g * Txz) + K0[1, 1] * (gz * Tz + g * Tzz))
    f = rho_c * dTdt - div
    return T, Kxx, Kxz, Kzz, f


# ============================================ EKSENEL SİMETRİK ERT ÇÖZÜCÜ ==
class AxisymmetricERT:
    """∇·(σ∇φ) = −I δ(x−x_s), σ = diag(σ_h, σ_h, σ_v), eksenel simetrik.

    Silindirik koordinatlarda:
        (1/r) ∂_r (r σ_h ∂_r φ) + ∂_z (σ_v ∂_z φ) = −I δ / (2πr)

    Sonlu hacim; z=0'da yalıtkan (Neumann) yüzey, dış sınırlarda φ→0
    (Dirichlet). Nokta kaynak, içinde bulunduğu hücreye hacimsel kaynak
    olarak dağıtılır.
    """

    def __init__(self, rmax=2.0, zmax=2.0, nr=180, nz=180):
        self.nr, self.nz = nr, nz
        self.dr, self.dz = rmax / nr, zmax / nz
        self.r = (np.arange(nr) + 0.5) * self.dr
        self.z = (np.arange(nz) + 0.5) * self.dz
        self.rf = np.arange(1, nr) * self.dr           # iç yüzler

    def solve(self, sigma_h, sigma_v, sources, phi_bc=None, source_density=None):
        """sources: [(z_konumu [m], akım [A]), ...] — hepsi r=0 ekseninde.
        phi_bc: f(r, z) → φ çağrılabiliri; dış sınır YÜZLERİNDE değerlendirilir
        (hücre merkezinde değil — merkezde değerlendirmek yarım hücrelik bir
        kaydırma yaratır ve şemayı birinci mertebeye düşürür). None ise φ=0.
        Doğrulamada analitik çözüm sınır koşulu olarak verilir, böylece alan
        kesme hatası yakınsama mertebesini kirletmez."""
        from scipy.sparse import coo_matrix
        from scipy.sparse.linalg import spsolve

        nr, nz, dr, dz = self.nr, self.nz, self.dr, self.dz
        r = self.r
        N = nr * nz
        sh = np.broadcast_to(np.asarray(sigma_h, float), (nr, nz))
        sv = np.broadcast_to(np.asarray(sigma_v, float), (nr, nz))
        if phi_bc is None:
            bc_out = np.zeros(nz); bc_bot = np.zeros(nr)
        else:
            bc_out = phi_bc(np.full(nz, nr * dr), self.z)     # r = r_max yüzü
            bc_bot = phi_bc(self.r, np.full(nr, nz * dz))     # z = z_max yüzü

        K = np.arange(N).reshape(nr, nz)
        rows, cols, vals = [], [], []
        diag = np.zeros((nr, nz))
        b = np.zeros((nr, nz))

        def harm(a, c):
            return 2.0 / (1.0 / a + 1.0 / c)

        # ---- r yönündeki iç yüzler: i ↔ i+1, alan 2π r_f dz -----------------
        rf = (np.arange(1, nr) * dr)[:, None]
        gr = harm(sh[:-1, :], sh[1:, :]) * (2 * np.pi * rf * dz) / dr
        rows.append(K[:-1, :].ravel()); cols.append(K[1:, :].ravel()); vals.append(gr.ravel())
        rows.append(K[1:, :].ravel()); cols.append(K[:-1, :].ravel()); vals.append(gr.ravel())
        diag[:-1, :] -= gr; diag[1:, :] -= gr

        # ---- z yönündeki iç yüzler: j ↔ j+1, alan 2π r dr -------------------
        gz = harm(sv[:, :-1], sv[:, 1:]) * (2 * np.pi * r[:, None] * dr) / dz
        rows.append(K[:, :-1].ravel()); cols.append(K[:, 1:].ravel()); vals.append(gz.ravel())
        rows.append(K[:, 1:].ravel()); cols.append(K[:, :-1].ravel()); vals.append(gz.ravel())
        diag[:, :-1] -= gz; diag[:, 1:] -= gz

        # ---- dış sınırlar: ikinci mertebeden Dirichlet kapanışı -------------
        # Hücre merkezli şemada (φ_b − φ_N)/(h/2) yalnızca birinci mertebedir.
        # Sınır yüzündeki türev, φ_b, φ_N ve φ_{N−1} üzerinden kurulan ikinci
        # dereceden interpolantla alınır:
        #     ∂φ/∂n|_b = [8φ_b − 9φ_N + φ_{N−1}] / (3h)
        # Bu, sınırdan geçen akı O(h²) doğru olur ve şema tüm alanda ikinci
        # mertebeye çıkar.
        G_out = sh[-1, :] * (2 * np.pi * (nr * dr) * dz) / dr
        diag[-1, :] -= 3.0 * G_out
        rows.append(K[-1, :]); cols.append(K[-2, :]); vals.append(G_out / 3.0)
        b[-1, :] -= (8.0 / 3.0) * G_out * bc_out

        G_bot = sv[:, -1] * (2 * np.pi * r * dr) / dz
        diag[:, -1] -= 3.0 * G_bot
        rows.append(K[:, -1]); cols.append(K[:, -2]); vals.append(G_bot / 3.0)
        b[:, -1] -= (8.0 / 3.0) * G_bot * bc_bot
        # j=0 (toprak yüzeyi) ve i=0 (eksen): sıfır akı → ek terim yok

        rows.append(K.ravel()); cols.append(K.ravel()); vals.append(diag.ravel())
        A = coo_matrix((np.concatenate(vals),
                        (np.concatenate(rows), np.concatenate(cols))),
                       shape=(N, N)).tocsr()

        for (zs, cur) in sources:
            j = int(np.clip(round(zs / dz - 0.5), 0, nz - 1))
            b[0, j] -= cur

        if source_density is not None:
            # düzgün dağılmış kaynak [A/m³] — yalnızca üretilmiş çözümle
            # doğrulamada kullanılır (tekillik yok, mertebe temiz ölçülür)
            b -= np.asarray(source_density, float) * (2 * np.pi * r[:, None] * dr * dz)

        return spsolve(A, b.ravel()).reshape(nr, nz)

    @staticmethod
    def analytic_halfspace(r, z, zs, sigma_h, sigma_v, cur=1.0):
        """Homojen anizotropik yarı-uzayda (yalıtkan yüzey) gömülü nokta
        kaynağın analitik potansiyeli:

            φ = I / (4π√(σ_h σ_v)) · [ 1/√(r²+λ²(z−z_s)²) + 1/√(r²+λ²(z+z_s)²) ],
            λ² = σ_h/σ_v

        Koordinat ölçekleme (x'=x/√σ_h, z'=z/√σ_v) ile Laplace denklemine
        indirgenerek türetilmiştir; izotropik limitte klasik I/(4πσR)'ye döner.
        """
        lam2 = sigma_h / sigma_v
        R1 = np.sqrt(r ** 2 + lam2 * (z - zs) ** 2)
        R2 = np.sqrt(r ** 2 + lam2 * (z + zs) ** 2)
        return cur / (4 * np.pi * np.sqrt(sigma_h * sigma_v)) * (1.0 / R1 + 1.0 / R2)

    def sensitivity(self, phiA, phiB, sigma_h, sigma_v, IA=1.0, IB=1.0):
        """Geselowitz karşılıklılık teoremi ile Fréchet türevi:

            ∂R/∂ln σ(x) = − (1/(I_A I_B)) σ(x) ∇φ_A(x)·∇φ_B(x) · dV

        Dönüş: (nr,nz) duyarlılık yoğunluğu (hücre başına, hacim çarpılmış).
        """
        nr, nz, dr, dz = self.nr, self.nz, self.dr, self.dz
        r = self.r

        def grads(p):
            gr = np.zeros((nr, nz)); gz = np.zeros((nr, nz))
            gr[1:-1, :] = (p[2:, :] - p[:-2, :]) / (2 * dr)
            gr[0, :] = (p[1, :] - p[0, :]) / dr
            gr[-1, :] = (p[-1, :] - p[-2, :]) / dr
            gz[:, 1:-1] = (p[:, 2:] - p[:, :-2]) / (2 * dz)
            gz[:, 0] = (p[:, 1] - p[:, 0]) / dz
            gz[:, -1] = (p[:, -1] - p[:, -2]) / dz
            return gr, gz

        gAr, gAz = grads(phiA)
        gBr, gBz = grads(phiB)
        sh = np.broadcast_to(sigma_h, (nr, nz))
        sv = np.broadcast_to(sigma_v, (nr, nz))
        dV = (2 * np.pi * r * dr * dz)[:, None]
        return -(sh * gAr * gBr + sv * gAz * gBz) * dV / (IA * IB)


def ert_mms(r, z, rmax, zmax, sigma_h, sigma_v):
    """Eksenel simetrik elektriksel operatör için üretilmiş çözüm.

        φ*(r,z) = cos(ar) cos(bz),  a = π/2r_max,  b = π/2z_max

    Bu seçim z=0'da ∂_zφ = 0 (yalıtkan yüzey), r=r_max ve z=z_max'ta φ = 0
    koşullarını tam olarak sağlar ve tekillik içermez; bu yüzden ayrıklaştırmanın
    kendi mertebesini nokta kaynağın etkisinden ayrık ölçmeye yarar.
    """
    a = np.pi / (2.0 * rmax)
    b = np.pi / (2.0 * zmax)
    phi = np.cos(a * r) * np.cos(b * z)
    # (1/r)∂_r(r ∂_r φ) = −a²φ − a sin(ar)cos(bz)/r  (r→0'da düzgün)
    with np.errstate(divide="ignore", invalid="ignore"):
        radial = -a * a * phi - a * np.sin(a * r) * np.cos(b * z) / np.where(r == 0, np.nan, r)
    radial = np.where(r == 0, -2.0 * a * a * np.cos(b * z), radial)
    div = sigma_h * radial - sigma_v * b * b * phi
    return phi, -div          # (analitik çözüm, kaynak yoğunluğu)


# ============================================== SAYISAL ANALİZ YARDIMCILARI =
def observed_order(errors, ratios=2.0):
    """Ardışık ızgara hatalarından gözlenen yakınsama mertebesi."""
    e = np.asarray(errors, float)
    return np.log(e[:-1] / e[1:]) / np.log(ratios)


def richardson_gci(f_coarse, f_fine, p, r=2.0, Fs=1.25):
    """Roache'un Izgara Yakınsama İndeksi (GCI) — bağıl belirsizlik bandı."""
    eps = abs((f_fine - f_coarse) / f_fine)
    return Fs * eps / (r ** p - 1.0)


def damped_thermal_wave(z, alpha, period=86400.0, amplitude=12.0):
    """Yarı-sonsuz ortamda harmonik yüzey zorlamasının analitik çözümü:

        T(z,t) = T̄ + A e^{−z/d} sin(ωt − z/d),   d = √(2α/ω)

    Dönüş: (sönüm derinliği d, z'deki genlik, z'deki azami |dT/dt| [°C/10 dk]).
    Bu, β eşiği için doğal (yangınsız) arka plan üst sınırını verir."""
    omega = 2.0 * np.pi / period
    d = np.sqrt(2.0 * alpha / omega)
    amp_z = amplitude * np.exp(-z / d)
    return d, amp_z, amp_z * omega * 600.0


def von_neumann_bound(D_block, dx):
    """Bağlaşık sistemin açık şeması için von Neumann kararlılık sınırı.

    u_t = D u_xx (D: 2×2 matris) için büyütme matrisi
        G(k) = I − (4Δt/Δx²) sin²(kΔx/2) D
    olup ρ(G) ≤ 1 koşulu Δt ≤ Δx²/(2 λ_max(D)) verir.
    """
    ev = np.linalg.eigvals(D_block)
    lam_max = np.max(np.abs(ev))
    return dx * dx / (2.0 * lam_max), ev
