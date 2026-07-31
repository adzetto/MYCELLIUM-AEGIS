# -*- coding: utf-8 -*-
"""Fizibilite raporunun pgfplots şekillerini üretir (figures/*.tikz).
Her şekil hem ana raporda \\input edilir hem de build_figures.py tarafından
bağımsız derlenip sunum için SVG'ye çevrilir."""
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"


def cols(name):
    """Matris tablosundaki bir tarama satırının nokta sayısı (mesh/cols).
    pgfplots bunu boş satırlardan her zaman çıkaramadığı için açıkça verilir."""
    f = DATA / f"{name}.dat"
    if not f.exists():
        return 2
    n = 0
    with f.open(encoding="ascii") as fh:
        fh.readline()
        for line in fh:
            if not line.strip():
                break
            n += 1
    return max(n, 2)


F = Path(__file__).resolve().parents[1] / "figures"
F.mkdir(exist_ok=True)
figs = {}

figs["tensor"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xlabel={Yatak eğimi $\psi$ [derece]},
  ylabel={Tensör bileşeni [W\,m$^{-1}$K$^{-1}$]},
  legend pos=south west, legend columns=3, xmin=0, xmax=45, ymin=-0.55, ymax=1.85]
\addplot[aegisteal, thick] table[x=dip,y=Kxx] {\dataroot/tensor_dip.dat};
\addlegendentry{$K_{xx}$}
\addplot[aegisblue, thick, dashed] table[x=dip,y=Kzz] {\dataroot/tensor_dip.dat};
\addlegendentry{$K_{zz}$}
\addplot[aegisplum, thick, densely dotted] table[x=dip,y=Kxz] {\dataroot/tensor_dip.dat};
\addlegendentry{$K_{xz}$}
\addplot[aegisline, thin, forget plot] coordinates {(0,0) (45,0)};
\end{axis}
\begin{axis}[aegis, grid=none, axis y line*=right, axis x line=none,
  xmin=0, xmax=45, ymin=0, ymax=26,
  ylabel={$-\nabla T$ ile $\mathbf{q}$ arasındaki açı [derece]},
  ylabel style={aegisember}, y tick label style={aegisember}]
\addplot[aegisember, very thick] table[x=dip,y=misalign] {\dataroot/tensor_dip.dat};
\end{axis}
\end{tikzpicture}
"""

figs["convergence"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.9cm},
  aegis, width=6.0cm, height=5.2cm, xmode=log, ymode=log]
\nextgroupplot[xlabel={Ağ adımı $h$}, ylabel={Bağıl $L_2$ hatası},
  legend pos=south east, title={(a) Üretilmiş çözümle doğrulama}]
\addplot[aegisteal, thick, mark=*, mark size=1.6] table[x=h,y=l2] {\dataroot/conv_mms_thermal.dat};
\addlegendentry{tensörlü ısı operatörü}
\addplot[aegisblue, thick, mark=square*, mark size=1.6] table[x=h,y=smooth] {\dataroot/conv_mms_ert.dat};
\addlegendentry{$\nabla\!\cdot\!(\sigma\nabla\phi)$}
\addplot[aegismuted, dashed, domain=0.004:0.06] {6e2*x^2};
\addlegendentry{$\mathcal{O}(h^2)$}
\nextgroupplot[xlabel={Ağ adımı $h$}, ylabel={Bağıl $L_2$ hatası},
  legend pos=south east, title={(b) Nokta kaynağın etkisi}]
\addplot[aegisember, thick, mark=triangle*, mark size=2] table[x=h,y=point] {\dataroot/conv_mms_ert.dat};
\addlegendentry{$\delta$ kaynaklı tam çözüm}
\addplot[aegismuted, dashed, domain=0.004:0.02] {0.32*x};
\addlegendentry{$\mathcal{O}(h)$}
\end{groupplot}
\end{tikzpicture}
"""

figs["gridconv"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.8cm},
  aegis, width=5.6cm, height=4.9cm]
\nextgroupplot[xlabel={Hücre yüksekliği $\Delta z$ [mm]}, ylabel={Öncü süre [dk]},
  xmode=log, title={(a) Uzaysal ağ}]
\addplot[aegisteal, thick, mark=*, mark size=1.8] table[x=dz_mm,y=lead] {\dataroot/conv_grid.dat};
\nextgroupplot[xlabel={Zaman adımı $\Delta t$ [s]}, ylabel={Öncü süre [dk]},
  xmode=log, title={(b) Zaman adımı}]
\addplot[aegisember, thick, mark=square*, mark size=1.8] table[x=dt,y=lead] {\dataroot/conv_dt.dat};
\end{groupplot}
\end{tikzpicture}
"""

figs["nominal"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, name=top, width=11.2cm, height=4.3cm, xmin=2.6, xmax=7,
  ylabel={Sıcaklık [$^\circ$C]}, legend pos=north west,
  xticklabels={}, ymin=0, ymax=460]
\addplot[aegisember, thick] table[x=t,y=Tsurf] {\dataroot/nominal_ts.dat};
\addlegendentry{yüzey $T(0,t)$}
\addplot[aegisteal, thick] table[x=t,y=Tprobe] {\dataroot/nominal_ts.dat};
\addlegendentry{prob $T(6\,\mathrm{cm},t)$}
\draw[aegisink, dashed, thin] (axis cs:4.5,0) -- (axis cs:4.5,460);
\node[font=\scriptsize, anchor=south east] at (axis cs:4.48,300) {tutuşma};
\end{axis}
\begin{axis}[aegis, at={(top.below south west)}, anchor=north west,
  width=11.2cm, height=4.3cm, xmin=2.6, xmax=7,
  xlabel={Zaman [saat]}, ylabel={$\mathrm{d}T/\mathrm{d}t$ [$^\circ$C/10\,dk]},
  legend pos=north east, ymin=-4, ymax=42]
\addplot[aegisteal, thick] table[x=t,y=dTdt] {\dataroot/nominal_ts.dat};
\addlegendentry{$\mathrm{d}T/\mathrm{d}t$}
\addplot[aegismuted, dashed, domain=2.6:7] {1.5}; \addlegendentry{$\beta=1{,}5$}
\end{axis}
\begin{axis}[aegis, grid=none, at={(top.below south west)}, anchor=north west,
  width=11.2cm, height=4.3cm, axis y line*=right, axis x line=none,
  xmin=2.6, xmax=7, ymin=-0.055, ymax=0.015, scaled y ticks=false,
  yticklabel style={aegisember, /pgf/number format/.cd, fixed, precision=3},
  ylabel={$\mathrm{d}(\ln R)/\mathrm{d}t$ [dk$^{-1}$]},
  ylabel style={aegisember}]
\addplot[aegisember, thick] table[x=t,y=dlnR] {\dataroot/nominal_ts.dat};
\end{axis}
\end{tikzpicture}
"""

figs["profile"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.7cm},
  aegis, width=5.2cm, height=6.0cm, y dir=reverse, ymin=0, ymax=32]
\nextgroupplot[xlabel={Sıcaklık [$^\circ$C]}, ylabel={Derinlik [cm]},
  legend pos=south east, xmin=0, xmax=340, title={(a) $T(z)$}]
\addplot table[x=T3p0,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=3{,}0$ sa}
\addplot table[x=T4p0,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=4{,}0$ sa}
\addplot table[x=T4p5,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=4{,}5$ sa}
\addplot table[x=T6p0,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=6{,}0$ sa}
\draw[aegisink, dashed, thin] (axis cs:100,0) -- (axis cs:100,32);
\nextgroupplot[xlabel={Hacimsel su içeriği $\theta$}, ylabel={Derinlik [cm]},
  legend pos=south east, xmin=0, xmax=0.30, title={(b) $\theta(z)$}]
\addplot table[x=th3p0,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=3{,}0$ sa}
\addplot table[x=th4p0,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=4{,}0$ sa}
\addplot table[x=th4p5,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=4{,}5$ sa}
\addplot table[x=th6p0,y=z] {\dataroot/nominal_profile.dat}; \addlegendentry{$t=6{,}0$ sa}
\end{groupplot}
\end{tikzpicture}
"""

figs["depth"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xlabel={Prob derinliği [cm]}, ylabel={Öncü süre [dk]},
  legend pos=north east, xmin=2, xmax=22, ymin=-15, ymax=105,
  width=10.4cm, height=5.4cm, restrict y to domain=-20:110]
\fill[aegisteal, opacity=.07] (axis cs:15,-15) rectangle (axis cs:20,105);
\node[font=\scriptsize, aegismuted, anchor=south, align=center]
  at (axis cs:17.5,-13) {miselyumun yaşadığı bant};
\addplot[aegisteal, thick, mark=*, mark size=1.5]
  table[x=z,y=lead_two] {\dataroot/depth_sweep.dat};
\addlegendentry{iki yönlü kural $|\mathrm{d}\ln R/\mathrm{d}t|>\gamma$}
\addplot[aegisember, thick, dashed, mark=square*, mark size=1.5]
  table[x=z,y=lead_one] {\dataroot/depth_sweep.dat};
\addlegendentry{belgedeki kural $\mathrm{d}\ln R/\mathrm{d}t>\gamma$}
\addplot[aegismuted, dotted, domain=2:22] {0};
\end{axis}
\end{tikzpicture}
"""

figs["kernel"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.8cm},
  aegis, width=5.4cm, height=5.2cm, xmin=0, xmax=30]
\nextgroupplot[xlabel={Derinlik [cm]}, ylabel={Duyarlılık yoğunluğu},
  title={(a) Geselowitz çekirdeği}]
\addplot[aegisteal, thick, fill=aegisteal, fill opacity=.18]
  table[x=z,y=w] {\dataroot/ert_kernel.dat} \closedcycle;
\nextgroupplot[xlabel={Derinlik [cm]}, ylabel={Kümülatif duyarlılık},
  ymin=0, ymax=1.02, title={(b) Araştırma derinliği}]
\addplot[aegisblue, thick] table[x=z,y=cum] {\dataroot/ert_kernel.dat};
\addplot[aegismuted, dashed, domain=0:30] {0.5};
\addplot[aegismuted, dotted, domain=0:30] {0.9};
\end{groupplot}
\end{tikzpicture}
"""

figs["born"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xlabel={Zaman [saat]}, ylabel={$\ln\!\big(R(t)/R(t_0)\big)$},
  legend pos=south west, width=9.6cm, height=5.0cm]
\addplot[aegisteal, thick, mark=*, mark size=1.3] table[x=t,y=lnfull] {\dataroot/born_check.dat};
\addlegendentry{tam eksenel simetrik çözüm}
\addplot[aegisember, dashed, thick, mark=o, mark size=1.6] table[x=t,y=lnborn] {\dataroot/born_check.dat};
\addlegendentry{birinci mertebe (Born) yaklaşımı}
\end{axis}
\end{tikzpicture}
"""

figs["leadcdf"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xlabel={Öncü süre [dk]}, ylabel={Birikimli olasılık},
  xmin=0, xmax=150, ymin=0, ymax=1.02, width=9.6cm, height=5.2cm,
  legend pos=south east]
\addplot[aegisteal, very thick] table[x=lead,y=cdf] {\dataroot/lead_cdf.dat};
\addlegendentry{Monte Carlo ampirik dağılım}
\addplot[aegismuted, dashed, domain=0:150] {0.05};
\addplot[aegismuted, dashed, domain=0:150] {0.95};
\draw[aegisember, thin, dash dot] (axis cs:15,0) -- (axis cs:15,1);
\node[font=\scriptsize, aegisember, anchor=south west] at (axis cs:16,0.04)
  {müdahale eşiği};
\end{axis}
\end{tikzpicture}
"""

figs["separation"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.9cm},
  aegis, width=5.6cm, height=5.2cm, xmode=log, ymin=0, ymax=1.02,
  ylabel={Birikimli olasılık}]
\nextgroupplot[xlabel={$\max_t \mathrm{d}T/\mathrm{d}t$ [$^\circ$C/10\,dk]},
  legend pos=north west, title={(a) Isıl kanal}, xmin=0.05, xmax=200]
\addplot[aegisblue, thick] table[x=beta_neg, y expr=\coordindex/1023] {\dataroot/threshold_box.dat};
\addlegendentry{olumsuz küme}
\addplot[aegisteal, thick] table[x=beta_pos, y expr=\coordindex/1023] {\dataroot/threshold_box.dat};
\addlegendentry{alev öncesi}
\draw[aegisember, thick, dashed] (axis cs:1.5,0) -- (axis cs:1.5,1.02);
\node[font=\scriptsize, aegisember, anchor=south west, rotate=90]
  at (axis cs:1.6,0.06) {$\beta = 1{,}5$};
\nextgroupplot[xlabel={$\max_t |\mathrm{d}\ln R/\mathrm{d}t|$ [dk$^{-1}$]},
  legend pos=north west, title={(b) Elektriksel kanal}, xmin=1e-4, xmax=1]
\addplot[aegisblue, thick] table[x=gamma_neg, y expr=\coordindex/1023] {\dataroot/threshold_box.dat};
\addlegendentry{olumsuz küme}
\addplot[aegisteal, thick] table[x=gamma_pos, y expr=\coordindex/1023] {\dataroot/threshold_box.dat};
\addlegendentry{alev öncesi}
\draw[aegisember, thick, dashed] (axis cs:0.002,0) -- (axis cs:0.002,1.02);
\node[font=\scriptsize, aegisember, anchor=south west, rotate=90]
  at (axis cs:0.0022,0.06) {$\gamma = 0{,}002$};
\end{groupplot}
\end{tikzpicture}
"""

figs["sobol"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, ybar, bar width=7pt, width=10.4cm, height=5.0cm,
  ylabel={Sobol indisi},
  xtick=data, xticklabels={$\theta_0$,$T_\infty$,$t_r$,$T_{\max}$,$\lambda_{\mathrm{sat}}$,$n_A$,$z_p$,$\sigma_w$},
  x tick label style={font=\small}, ymin=0, legend pos=north east,
  enlarge x limits=0.07]
\addplot[fill=aegisteal, draw=aegisdeep] table[x=idx,y=S1] {\dataroot/sobol.dat};
\addlegendentry{birinci mertebe $S_i$}
\addplot[fill=aegisember!70, draw=aegisember] table[x=idx,y=ST] {\dataroot/sobol.dat};
\addlegendentry{toplam etki $S_{T_i}$}
\end{axis}
\end{tikzpicture}
"""

figs["lateral"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xlabel={Sıcak nokta merkezine yatay uzaklık [m]},
  ylabel={$\beta$ eşiğinin aşıldığı an [dk]}, xmin=-2.5, xmax=2.5,
  width=9.6cm, height=5.0cm, legend pos=north east,
  restrict y to domain=150:360]
\addplot[aegisteal, thick] table[x=x,y=t_dip0] {\dataroot/lateral.dat};
\addlegendentry{yatay yatak ($\psi=0^\circ$)}
\addplot[aegisember, thick, dashed] table[x=x,y=t_dip25] {\dataroot/lateral.dat};
\addlegendentry{eğimli yatak ($\psi=25^\circ$)}
\end{axis}
\end{tikzpicture}
"""

figs["cable"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.9cm},
  aegis, width=5.4cm, height=5.2cm]
\nextgroupplot[xlabel={Ağ boyunca uzaklık $r$ [m]}, ylabel={Genlik [mV]},
  xmode=log, ymode=log, xmin=0.05, xmax=60, ymin=1e-3, ymax=60,
  legend pos=south west, title={(a) $V(r)=V_0K_0(r/\lambda)/K_0(a/\lambda)$}]
\addplot table[x=r,y=V0p5] {\dataroot/cable.dat}; \addlegendentry{$\lambda=0{,}5$ m}
\addplot table[x=r,y=V1]   {\dataroot/cable.dat}; \addlegendentry{$\lambda=1$ m}
\addplot table[x=r,y=V10]  {\dataroot/cable.dat}; \addlegendentry{$\lambda=10$ m}
\addplot table[x=r,y=V30]  {\dataroot/cable.dat}; \addlegendentry{$\lambda=30$ m}
\addplot[aegisink, dashed, domain=0.05:60] {0.5};
\nextgroupplot[xlabel={Elektrotonik uzunluk $\lambda$ [m]},
  ylabel={Tespit yarıçapı $r_{\mathrm{det}}$ [m]},
  xmode=log, ymode=log, title={(b) Kapsama yarıçapı}]
\addplot[aegisteal, thick, mark=*, mark size=1.8] table[x=lam,y=rdet] {\dataroot/cable_rdet.dat};
\end{groupplot}
\end{tikzpicture}
"""

figs["coverage"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xlabel={Düğüm aralığı $S$ [m]},
  ylabel={Alev öncesi tespit olasılığı}, xmin=20, xmax=200, ymin=0, ymax=1,
  width=9.4cm, height=5.2cm, legend pos=north east]
\addplot table[x=S,y=p1]  {\dataroot/coverage.dat}; \addlegendentry{$\lambda=1$ m}
\addplot table[x=S,y=p3]  {\dataroot/coverage.dat}; \addlegendentry{$\lambda=3$ m}
\addplot table[x=S,y=p10] {\dataroot/coverage.dat}; \addlegendentry{$\lambda=10$ m}
\addplot table[x=S,y=p30] {\dataroot/coverage.dat}; \addlegendentry{$\lambda=30$ m}
\end{axis}
\begin{axis}[aegis, grid=none, width=9.4cm, height=5.2cm,
  axis y line*=right, axis x line=none, xmin=20, xmax=200,
  ymode=log, ymin=3e3, ymax=2e6, ylabel={Kurulum maliyeti [TL/ha]},
  ylabel style={aegisember}, y tick label style={aegisember}]
\addplot[aegisember, very thick] table[x=S,y=capex] {\dataroot/coverage.dat};
\end{axis}
\end{tikzpicture}
"""

figs["energy"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=2.6cm},
  aegis, width=5.2cm, height=5.0cm]
\nextgroupplot[xlabel={Görev döngüsü}, ylabel={Kanopi geçirgenliği},
  title={(a) Yük kaybı olasılığı}, grid=none,
  colorbar, colormap/viridis, point meta min=0, point meta max=0.4]
\addplot[matrix plot*, point meta=explicit, mesh/cols=@COLS:energy_lolp@]
  table[x=duty,y=canopy,meta=lolp] {\dataroot/energy_lolp.dat};
\nextgroupplot[xlabel={Gün}, ymin=0, ymax=1.06,
  xmin=0, xmax=365, title={(b) Şarj durumu, \%50 görev döngüsü},
  legend style={at={(0.03,0.05)}, anchor=south west}]
\addplot[aegisteal, thick] table[x=day,y=soc_ref] {\dataroot/energy_soc.dat};
\addlegendentry{referans gölgelenme}
\addplot[aegisember, thick] table[x=day,y=soc_shade] {\dataroot/energy_soc.dat};
\addlegendentry{derin gölge (\%4)}
\end{groupplot}
\end{tikzpicture}
"""

figs["link"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xlabel={Mesafe [m]}, ylabel={Alınan güç [dBm]},
  xmode=log, xmin=5, xmax=4000, ymin=-165, ymax=-20,
  width=9.6cm, height=5.0cm, legend pos=north east]
\addplot[aegisblue, thick] table[x=d,y=prx_open] {\dataroot/link.dat};
\addlegendentry{açık arazi (serbest uzay)}
\addplot[aegisteal, thick] table[x=d,y=prx_forest] {\dataroot/link.dat};
\addlegendentry{orman örtüsü (Weissberger)}
\addplot[aegisember, dashed, domain=5:4000] {-134};
\addlegendentry{alıcı duyarlılığı $-134$ dBm}
\end{axis}
\end{tikzpicture}
"""

figs["econ"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=1.9cm},
  aegis, width=5.4cm, height=5.0cm]
\nextgroupplot[xlabel={NBD [milyon TL]}, ylabel={Frekans}, ybar interval,
  title={(a) Net bugünkü değer}, ymin=0]
\addplot[fill=aegisteal!35, draw=aegisdeep] table[x=npv,y=count] {\dataroot/npv_hist.dat};
\nextgroupplot[xlabel={Yıl}, ylabel={Kümülatif iskontolu nakit [milyon TL]},
  title={(b) Başabaş noktası}]
\addplot[aegisteal, thick, mark=*, mark size=1.6] table[x=year,y=cum] {\dataroot/cashflow.dat};
\addplot[aegismuted, dashed, domain=1:7] {0};
\end{groupplot}
\end{tikzpicture}
"""

figs["tornado"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, xbar, y dir=reverse, width=8.4cm, height=5.6cm,
  xlabel={NBD [milyon TL]}, ytick=data,
  yticklabels={donanım maliyeti, kâr marjı, SaaS geliri, kayıp oranı,
               iskonto oranı, büyüme, işletme gideri, ilk yıl kurulum},
  y tick label style={font=\scriptsize}, bar width=6pt, enlarge y limits=0.09,
  legend pos=south east]
\addplot[fill=aegisember!60, draw=aegisember] table[x=low,y=idx] {\dataroot/tornado.dat};
\addlegendentry{p10}
\addplot[fill=aegisteal!60, draw=aegisdeep] table[x=high,y=idx] {\dataroot/tornado.dat};
\addlegendentry{p90}
\end{axis}
\end{tikzpicture}
"""

figs["geomap"] = r"""
\begin{tikzpicture}
\begin{axis}[aegismap, width=10.4cm, height=6.6cm,
  colorbar, colormap name=aegisterrain, point meta min=-120, point meta max=1500,
  colorbar style={ylabel={Yükseklik [m]}},
  unbounded coords=jump]
\addplot[matrix plot*, point meta=explicit, mesh/cols=@COLS:geo_dem@]
  table[x=x,y=y,meta=z] {\dataroot/geo_dem.dat};
\addplot[aegismuted, line width=.25pt, opacity=.55] table[x=x,y=y] {\dataroot/geo_graticule.dat};
\addplot[aegisink, line width=.5pt] table[x=x,y=y] {\dataroot/geo_coast.dat};
\addplot[aegismuted, line width=.35pt, dashed] table[x=x,y=y] {\dataroot/geo_prov_lines.dat};
\addplot[only marks, mark=*, mark size=2.0, aegisember,
  mark options={draw=white, line width=.4pt}]
  table[x=x,y=y] {\dataroot/geo_sites.dat};
\end{axis}
\end{tikzpicture}
"""

figs["georisk"] = r"""
\begin{tikzpicture}
\begin{groupplot}[group style={group size=2 by 1, horizontal sep=2.8cm},
  aegismap, width=5.0cm, height=4.4cm, unbounded coords=jump]
\nextgroupplot[colorbar, colormap/hot, point meta min=-0.06, point meta max=0.85,
  colorbar style={ylabel={indis}}, title={(a) Tutuşma duyarlılığı}]
\addplot[matrix plot*, point meta=explicit, mesh/cols=@COLS:geo_dem@]
  table[x=x,y=y,meta=risk] {\dataroot/geo_dem.dat};
\addplot[aegisink, line width=.4pt] table[x=x,y=y] {\dataroot/geo_coast.dat};
\nextgroupplot[colorbar, colormap/viridis,
  colorbar style={ylabel={öncü süre [dk]}}, title={(b) Modellenen öncü süre}]
\addplot[scatter, only marks, mark=square*, mark size=.55,
  scatter src=explicit, draw opacity=0]
  table[x=x,y=y,meta=lead] {\dataroot/geo_lead_pts.dat};
\addplot[aegisink, line width=.4pt] table[x=x,y=y] {\dataroot/geo_coast.dat};
\end{groupplot}
\end{tikzpicture}
"""

figs["geosection"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, name=prof, width=10.6cm, height=3.0cm, xmin=0, xmax=126,
  ylabel={Yükseklik [m]}, xticklabels={}, ymin=0]
\addplot[aegisteal, thick, fill=aegisteal!18] table[x=s,y=z] {\dataroot/geo_transect.dat}
  \closedcycle;
\end{axis}
\begin{axis}[aegis, at={(prof.below south west)}, anchor=north west,
  width=10.6cm, height=4.0cm, xmin=0, xmax=126,
  xlabel={Kesit boyunca uzaklık [km]}, ylabel={Derinlik [cm]},
  y dir=reverse, ymin=0, ymax=40, grid=none,
  colorbar, colormap/hot, point meta min=20, point meta max=220,
  colorbar style={ylabel={$T$ [$^\circ$C]}}]
\addplot[matrix plot*, point meta=explicit, mesh/cols=@COLS:geo_section@]
  table[x=s,y=z,meta=T] {\dataroot/geo_section.dat};
\end{axis}
\end{tikzpicture}
"""

figs["geoprov"] = r"""
\begin{tikzpicture}
\begin{axis}[aegis, ybar, bar width=9pt, width=9.4cm, height=4.6cm,
  ylabel={Ortalama duyarlılık indisi}, xtick=data,
  xticklabel style={font=\scriptsize, rotate=30, anchor=north east},
  ymin=0, enlarge x limits=0.12, legend pos=north east]
\addplot[fill=aegisember!55, draw=aegisember] table[x=idx,y=risk_mean] {\dataroot/geo_prov.dat};
\addlegendentry{ortalama}
\addplot[fill=aegisteal!45, draw=aegisdeep] table[x=idx,y=risk_p90] {\dataroot/geo_prov.dat};
\addlegendentry{90. yüzdelik}
\end{axis}
\end{tikzpicture}
"""

import re

for k, v in figs.items():
    v = re.sub(r"@COLS:(\w+)@", lambda m: str(cols(m.group(1))), v)
    (F / f"fig_{k}.tikz").write_text(v.strip() + "\n", encoding="utf-8")
print(f"{len(figs)} sekil yazildi ->", F)
