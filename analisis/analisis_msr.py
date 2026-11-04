"""Reproduce el análisis MSR del script de Octave y genera las figuras y
estadísticos complementarios usados en el artículo y el informe.

Uso:  python3 analisis/analisis_msr.py   (desde la raíz del repositorio)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import cm
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "figuras"
FIG.mkdir(exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 9,
    "axes.titlesize": 9.5,
    "axes.labelsize": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.5,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

df = pd.read_excel(ROOT / "proyecto_octave/datos/datos_MSR.xlsx", sheet_name="Datos")
df.columns = ["Tw", "Te", "To", "x1c", "x2c", "Semana", "Fecha", "Horario", "Hora", "Zona"]
T1, T2, y = df.Tw.to_numpy(float), df.Te.to_numpy(float), df.To.to_numpy(float)
n = len(y)

# Codificación
c1, h1 = (T1.max() + T1.min()) / 2, (T1.max() - T1.min()) / 2
c2, h2 = (T2.max() + T2.min()) / 2, (T2.max() - T2.min()) / 2
x1, x2 = (T1 - c1) / h1, (T2 - c2) / h2

X = np.column_stack([np.ones(n), x1, x2, x1**2, x2**2, x1 * x2])
coef, *_ = np.linalg.lstsq(X, y, rcond=None)
yhat = X @ coef
res = y - yhat
p = X.shape[1]
SST = ((y - y.mean())**2).sum(); SSE = (res**2).sum(); SSR = SST - SSE
MSE = SSE / (n - p)
R2 = 1 - SSE / SST
R2a = 1 - (SSE / (n - p)) / (SST / (n - 1))
F = (SSR / (p - 1)) / MSE
pF = stats.f.sf(F, p - 1, n - p)
se = np.sqrt(np.diag(MSE * np.linalg.inv(X.T @ X)))
t = coef / se
pt = 2 * stats.t.sf(np.abs(t), n - p)
RMSE = np.sqrt(MSE)
MAE = np.abs(res).mean()

# PRESS / R2 predicción
H = X @ np.linalg.inv(X.T @ X) @ X.T
hii = np.diag(H)
PRESS = ((res / (1 - hii))**2).sum()
R2pred = 1 - PRESS / SST

# Modelo de primer orden (comparación) y prueba F de términos de 2.º orden
X1 = X[:, :3]
c_lin, *_ = np.linalg.lstsq(X1, y, rcond=None)
SSE1 = ((y - X1 @ c_lin)**2).sum()
R2_lin = 1 - SSE1 / SST
F_2o = ((SSE1 - SSE) / 3) / MSE
p_2o = stats.f.sf(F_2o, 3, n - p)

# Forma canónica
b = coef[1:3]
B = np.array([[coef[3], coef[5] / 2], [coef[5] / 2, coef[4]]])
xs = -0.5 * np.linalg.solve(B, b)
ys = coef[0] + 0.5 * xs @ b
lam, vec = np.linalg.eigh(B)

# Óptimo dentro de la región
g = np.linspace(-1, 1, 201)
G1, G2 = np.meshgrid(g, g)
Z = coef[0] + coef[1]*G1 + coef[2]*G2 + coef[3]*G1**2 + coef[4]*G2**2 + coef[5]*G1*G2
k = np.argmax(Z)
x1m, x2m, ymax = G1.flat[k], G2.flat[k], Z.flat[k]

# Diagnósticos
r12 = np.corrcoef(T1, T2)[0, 1]
VIF = 1 / (1 - r12**2)
DW = (np.diff(res)**2).sum() / SSE
skew, kurt = stats.skew(res), stats.kurtosis(res)
ad = stats.anderson(res, dist="norm")
ks_stat, ks_p = stats.kstest((res - res.mean()) / res.std(ddof=1), "norm")
r_sp, p_sp = stats.spearmanr(T1, y)
r_sp2, p_sp2 = stats.spearmanr(T2, y)
r_p1 = np.corrcoef(T1, y)[0, 1]
r_p2 = np.corrcoef(T2, y)[0, 1]

desc = df[["Tw", "Te", "To"]].describe().T
by = (df.groupby("Horario")[["Tw", "Te", "To"]].agg(["mean", "std"]).round(2)
      .reindex(["Mañana", "Tarde", "Noche"]))
by_week = df.groupby("Semana")[["Tw", "Te", "To"]].mean().round(2)
by_zone = df.groupby("Zona")[["Tw", "Te", "To"]].mean().round(2)
counts = df.groupby(["Semana", "Horario"]).size()
frac_comfort = float((y >= 20).mean() * 100)
frac_18 = float((y >= 18).mean() * 100)

# Efecto de la T de agua a distintas T exteriores (pendiente dy/dT1, °C/°C)
def slope_T1(x2v, x1v=0.0):
    return (coef[1] + 2*coef[3]*x1v + coef[5]*x2v) / h1

out = {
    "n": n, "c1": c1, "h1": h1, "c2": c2, "h2": h2,
    "coef": coef.tolist(), "se": se.tolist(), "t": t.tolist(), "pt": pt.tolist(),
    "SSR": SSR, "SSE": SSE, "SST": SST, "MSE": MSE, "F": F, "pF": pF,
    "R2": R2, "R2a": R2a, "R2pred": R2pred, "PRESS": PRESS, "RMSE": RMSE, "MAE": MAE,
    "R2_lin": R2_lin, "F_2o": F_2o, "p_2o": p_2o,
    "B": B.tolist(), "xs": xs.tolist(), "ys": ys, "lam": lam.tolist(), "vec": vec.tolist(),
    "T1s": c1 + h1*xs[0], "T2s": c2 + h2*xs[1],
    "x1m": x1m, "x2m": x2m, "ymax": ymax, "T1m": c1 + h1*x1m, "T2m": c2 + h2*x2m,
    "r12": r12, "VIF": VIF, "DW": DW, "skew": skew, "kurt": kurt,
    "AD": ad.statistic, "AD_crit5": float(ad.critical_values[2]), "KS": ks_stat, "KS_p": ks_p,
    "r_p1": r_p1, "r_p2": r_p2, "r_sp1": r_sp, "r_sp2": r_sp2,
    "frac_comfort20": frac_comfort, "frac_18": frac_18,
    "slope_T1_cold": slope_T1(-1), "slope_T1_mid": slope_T1(0), "slope_T1_warm": slope_T1(1),
    "desc": desc.round(2).to_dict(orient="index"),
    "by_horario": {h: {f"{a}_{s}": by.loc[h, (a, s)] for a in ["Tw", "Te", "To"] for s in ["mean", "std"]} for h in by.index},
    "by_week": by_week.to_dict(orient="index"),
    "by_zone": by_zone.to_dict(orient="index"),
    "counts": {f"{k[0]}-{k[1]}": int(v) for k, v in counts.items()},
    "fechas": sorted(df.Fecha.unique().tolist()),
}
(ROOT / "analisis/resultados_python.json").write_text(json.dumps(out, indent=2, ensure_ascii=False, default=float))

# ----------------------------------------------------------------- Figuras
R1, R2g = c1 + h1*G1, c2 + h2*G2
lev = np.arange(np.floor(Z.min()), np.ceil(Z.max()) + 0.5, 1.0)

# Fig 1: superficie 3D
fig = plt.figure(figsize=(5.2, 4.0))
ax = fig.add_subplot(111, projection="3d")
s = ax.plot_surface(R1, R2g, Z, cmap="viridis", linewidth=0, antialiased=True, alpha=0.92, rstride=4, cstride=4)
ax.scatter(T1, T2, y, s=1.5, c="k", alpha=0.35, depthshade=False)
ax.set_xlabel("T entrada agua, $T_w$ (°C)", labelpad=4)
ax.set_ylabel("T aire exterior, $T_e$ (°C)", labelpad=4)
ax.set_zlabel("T operativa, $T_{op}$ (°C)", labelpad=2)
ax.view_init(24, -130)
for a in (ax.xaxis, ax.yaxis, ax.zaxis):
    a.pane.set_facecolor((1, 1, 1, 0)); a._axinfo["grid"]["color"] = "#e5e5e5"
cb = fig.colorbar(s, ax=ax, shrink=0.6, pad=0.1); cb.set_label("$\\hat{T}_{op}$ (°C)")
fig.savefig(FIG / "fig1_superficie.png"); plt.close(fig)

# Fig 2: contorno
fig, ax = plt.subplots(figsize=(5.0, 3.8))
cs = ax.contourf(R1, R2g, Z, levels=lev, cmap="viridis")
cl = ax.contour(R1, R2g, Z, levels=lev, colors="w", linewidths=0.5)
ax.clabel(cl, fmt="%.0f", fontsize=7, colors="w")
ax.scatter(T1, T2, s=2, c="k", alpha=0.35, label="Observaciones (n = %d)" % n)
ax.plot(c1 + h1*x1m, c2 + h2*x2m, marker="*", ms=14, mfc="#ffd23f", mec="k", ls="", label="Mejor condición en la región")
ax.set_xlabel("T entrada agua, $T_w$ (°C)"); ax.set_ylabel("T aire exterior, $T_e$ (°C)")
ax.grid(False)
cb = fig.colorbar(cs, ax=ax); cb.set_label("$\\hat{T}_{op}$ (°C)")
ax.legend(loc="lower right", fontsize=7, framealpha=0.9)
fig.savefig(FIG / "fig2_contorno.png"); plt.close(fig)

# Fig 3: observado vs predicho
fig, ax = plt.subplots(figsize=(3.6, 3.4))
ax.scatter(y, yhat, s=4, c="#2b6cb0", alpha=0.5, edgecolor="none")
lim = [min(y.min(), yhat.min()) - 0.5, max(y.max(), yhat.max()) + 0.5]
ax.plot(lim, lim, color="#c53030", lw=1.2, label="Recta 1:1")
ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal")
ax.set_xlabel("$T_{op}$ observada (°C)"); ax.set_ylabel("$T_{op}$ predicha (°C)")
ax.text(0.04, 0.95, f"$R^2$ = {R2:.3f}\nRMSE = {RMSE:.2f} °C", transform=ax.transAxes, va="top", fontsize=8,
        bbox=dict(fc="white", ec="#cccccc", lw=0.5))
ax.legend(loc="lower right", fontsize=7)
fig.savefig(FIG / "fig3_obs_pred.png"); plt.close(fig)

# Fig 4: residuos (4 paneles)
fig, axs = plt.subplots(2, 2, figsize=(6.6, 4.8))
axs[0, 0].scatter(yhat, res, s=3, c="#2b6cb0", alpha=0.5, edgecolor="none"); axs[0, 0].axhline(0, c="#c53030", lw=1)
axs[0, 0].set_xlabel("Valor predicho (°C)"); axs[0, 0].set_ylabel("Residuo (°C)"); axs[0, 0].set_title("(a) Residuos vs. predichos")
axs[0, 1].hist(res, bins=30, color="#2b6cb0", alpha=0.8, edgecolor="white", density=True)
xx = np.linspace(res.min(), res.max(), 200)
axs[0, 1].plot(xx, stats.norm.pdf(xx, 0, res.std(ddof=1)), c="#c53030", lw=1.2)
axs[0, 1].set_xlabel("Residuo (°C)"); axs[0, 1].set_ylabel("Densidad"); axs[0, 1].set_title("(b) Histograma de residuos")
(osm, osr), (sl, ic, _) = stats.probplot(res, dist="norm")
axs[1, 0].scatter(osm, osr, s=3, c="#2b6cb0", alpha=0.5, edgecolor="none"); axs[1, 0].plot(osm, sl*osm + ic, c="#c53030", lw=1)
axs[1, 0].set_xlabel("Cuantiles teóricos"); axs[1, 0].set_ylabel("Cuantiles de residuos"); axs[1, 0].set_title("(c) Gráfico Q–Q normal")
axs[1, 1].plot(np.arange(1, n + 1), res, lw=0.5, c="#2b6cb0"); axs[1, 1].axhline(0, c="#c53030", lw=1)
axs[1, 1].set_xlabel("Orden de registro"); axs[1, 1].set_ylabel("Residuo (°C)"); axs[1, 1].set_title("(d) Residuos vs. orden")
fig.tight_layout(); fig.savefig(FIG / "fig4_residuos.png"); plt.close(fig)

# Fig 5: perfiles por horario (boxplots)
fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.5))
orden = ["Mañana", "Tarde", "Noche"]
cols = ["#4c78a8", "#f58518", "#54a24b"]
for ax, var, lab in zip(axs, ["Tw", "Te", "To"], ["$T_w$ entrada agua (°C)", "$T_e$ aire exterior (°C)", "$T_{op}$ interior (°C)"]):
    data = [df.loc[df.Horario == h, var] for h in orden]
    bp = ax.boxplot(data, tick_labels=orden, patch_artist=True, widths=0.55, flierprops=dict(ms=2))
    for patch, c in zip(bp["boxes"], cols):
        patch.set_facecolor(c); patch.set_alpha(0.75)
    for m in bp["medians"]:
        m.set_color("k")
    ax.set_title(lab)
fig.tight_layout(); fig.savefig(FIG / "fig5_horarios.png"); plt.close(fig)

# Fig 6: efecto de Tw sobre Top a distintas Te (interacción)
fig, ax = plt.subplots(figsize=(4.2, 3.0))
tw = np.linspace(T1.min(), T1.max(), 100); xw = (tw - c1) / h1
for te, c in zip([-5.3, 0, 5, 10, 15.3], ["#313695", "#4575b4", "#74add1", "#f46d43", "#a50026"]):
    xe = (te - c2) / h2
    yy = coef[0] + coef[1]*xw + coef[2]*xe + coef[3]*xw**2 + coef[4]*xe**2 + coef[5]*xw*xe
    ax.plot(tw, yy, c=c, lw=1.4, label=f"$T_e$ = {te:g} °C")
ax.axhspan(20, 24, color="#48bb78", alpha=0.12, lw=0)
ax.text(T1.min() + 0.5, 20.3, "Rango de confort invernal (20–24 °C)", fontsize=7, color="#276749")
ax.set_xlabel("T entrada agua, $T_w$ (°C)"); ax.set_ylabel("$\\hat{T}_{op}$ (°C)")
ax.set_ylim(4, 24.5)
ax.legend(fontsize=6.5, ncol=2, loc="lower right")
fig.savefig(FIG / "fig6_interaccion.png"); plt.close(fig)

print(json.dumps({k: out[k] for k in ["n", "R2", "R2a", "R2pred", "RMSE", "MAE", "R2_lin", "F_2o", "p_2o", "xs", "ys", "lam",
                                       "T1s", "T2s", "T1m", "T2m", "ymax", "r12", "VIF", "DW", "skew", "kurt", "AD", "AD_crit5",
                                       "KS", "KS_p", "r_p1", "r_p2", "frac_comfort20", "frac_18",
                                       "slope_T1_cold", "slope_T1_mid", "slope_T1_warm", "vec", "by_week", "by_zone"]},
                 indent=1, default=float, ensure_ascii=False))
print(by)
print(desc)
