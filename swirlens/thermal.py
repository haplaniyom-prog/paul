"""Thermal (homogeneous soak) analysis of the lens for several housing
materials.

Model (uniform temperature T, reference 20 C):
* glass: radii and thicknesses scale with the glass CTE, index from the
  SCHOTT dn/dT model relative to air at T (glass.index_T)
* air spaces inside the lens scale with the housing CTE
* rear vertex -> flange scales with the housing CTE, flange -> sensor
  (17.526 mm) with the camera body CTE (aluminium)
Outputs defocus at the sensor, EFL / plate-scale change, polychromatic RMS
spot and 3x3-pixel ensquared energy versus T for each material.
"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .optimize import load
from . import glass as G
from . import analysis as A

FFD = 17.526
MATERIALS = {            # CTE 1e-6/K (20 C)
    "Alüminyum 6061": 23.6,
    "Paslanmaz çelik 304": 17.3,
    "Titanyum Ti-6Al-4V": 8.6,
    "Invar 36": 1.3,
}
ALPHA_CAMERA = 23.6e-6   # camera body assumed aluminium


def thermal_lens(lens, T, alpha_housing, alpha_camera=ALPHA_CAMERA, T0=G.T_REF):
    L = lens.copy(); dT = T - T0
    n = len(L.surfaces)
    for k, s in enumerate(L.surfaces):
        if s.glass != "AIR":
            a = G.THERMAL[s.glass]["alpha"]
            s.c = s.c / (1 + a * dT)          # radius grows
            s.t = s.t * (1 + a * dT)
            s.T = T
        elif k == n - 1:
            s.t = (s.t - FFD) * (1 + alpha_housing * dT) + FFD * (1 + alpha_camera * dT)
        else:
            s.t = s.t * (1 + alpha_housing * dT)
    # glass radius: also the previous surface (glass->air) belongs to the element
    for k, s in enumerate(L.surfaces):
        if s.glass == "AIR" and k > 0 and L.surfaces[k - 1].glass != "AIR":
            a = G.THERMAL[L.surfaces[k - 1].glass]["alpha"]
            s.c = s.c / (1 + a * dT)
    return L


def _offset(L):
    return (L.paraxial()["bfl"] - L.surfaces[-1].t) * 1000   # paraxial focus - sensor, um


def evaluate(lens, T, alpha_h, off0=None):
    L = thermal_lens(lens, T, alpha_h)
    par = L.paraxial()
    off0 = _offset(lens) if off0 is None else off0
    defocus = _offset(L) - off0                              # um, change vs 20 C; + = focus moves behind sensor
    rms = [A.poly_spot(L, f, 15)[4] * 1000 for f in L.fields_deg]
    ee3 = [A.ensquared(L, f, n=31)[2] for f in (0.0, L.fields_deg[-1])]
    return dict(T=T, defocus_um=defocus, efl=par["efl"], rms_um=rms, ee3=ee3)


def run(design="results/design_final.json", outdir="results", Ts=None):
    lens = load(design)
    Ts = np.arange(-40, 71, 10) if Ts is None else np.asarray(Ts)
    efl0 = lens.paraxial()["efl"]
    off0 = _offset(lens)
    res = {}
    for name, cte in MATERIALS.items():
        rows = [evaluate(lens, float(T), cte * 1e-6, off0) for T in Ts]
        res[name] = dict(cte=cte, rows=rows,
                         efl_ppm_per_K=float((rows[-1]["efl"] - rows[0]["efl"]) / efl0 / (Ts[-1] - Ts[0]) * 1e6))
    # contribution budget at +50 K (linearised): glass index, glass expansion, housing, camera
    def variant(alpha_h, alpha_cam, T, glass_index=True, glass_exp=True):
        L = lens.copy(); dT = T - G.T_REF; n = len(L.surfaces)
        for k, s_ in enumerate(L.surfaces):
            if s_.glass != "AIR":
                a = G.THERMAL[s_.glass]["alpha"] if glass_exp else 0.0
                s_.c /= (1 + a * dT); s_.t *= (1 + a * dT)
                if glass_index: s_.T = T
            elif k == n - 1:
                s_.t = (s_.t - FFD) * (1 + alpha_h * dT) + FFD * (1 + alpha_cam * dT)
            else:
                s_.t *= (1 + alpha_h * dT)
        for k, s_ in enumerate(L.surfaces):
            if s_.glass == "AIR" and k > 0 and L.surfaces[k - 1].glass != "AIR":
                a = G.THERMAL[L.surfaces[k - 1].glass]["alpha"] if glass_exp else 0.0
                s_.c /= (1 + a * dT)
        return _offset(L) - off0, (L.paraxial()["efl"] - efl0) / efl0 * 1e6
    T1 = 70.0
    b = dict(glass_index=variant(0, 0, T1, True, False), glass_expansion=variant(0, 0, T1, False, True),
             camera_body_Al=variant(0, ALPHA_CAMERA, T1, False, False), housing_per_1e6=variant(1e-6, 0, T1, False, False))
    budget = {k: v[0] for k, v in b.items()}; efl_budget = {k: v[1] for k, v in b.items()}
    # athermal housing CTE (defocus(70 C) = 0), linear in alpha_h
    d0 = variant(0, ALPHA_CAMERA, T1)[0]; d1 = variant(10e-6, ALPHA_CAMERA, T1)[0]
    alpha_athermal = -d0 / ((d1 - d0) / 10e-6)
    # passive compensator: a spacer of CTE alpha_s in series with the housing must move the lens by the
    # residual defocus; L_s * (alpha_s - alpha_h) * dT = residual  ->  L_s
    comp = {}
    for name, cte in MATERIALS.items():
        resid = variant(cte * 1e-6, ALPHA_CAMERA, T1)[0]          # um at +50 K
        comp[name] = {sp: float(resid / ((a_s - cte) * 1e-6 * 50.0) / 1000) for sp, a_s in
                      (("POM (110e-6/K)", 110.0), ("PTFE (120e-6/K)", 120.0), ("PA6 (80e-6/K)", 80.0))}
    efl_rows = [dict(T=float(T), efl=evaluate(lens, float(T), 23.6e-6, off0)["efl"]) for T in (-40.0, 20.0, 70.0)]
    # optimum assembly focus bias per material: minimise the worst-case RMS over the T range
    bias_opt = {}
    Tb = np.array([-40.0, -20.0, 0.0, 20.0, 40.0, 55.0, 70.0])
    for name, cte in MATERIALS.items():
        best = None
        for b in np.arange(-150, 31, 10):
            Lb = lens.copy(); Lb.surfaces[-1].t += b / 1000.0
            worst = 0.0; ee_min = 1.0
            for T in Tb:
                Lt = thermal_lens(Lb, float(T), cte * 1e-6)
                r = max(A.poly_spot(Lt, f, 13)[4] * 1000 for f in (0.0, lens.fields_deg[-1]))
                worst = max(worst, r)
                ee_min = min(ee_min, min(A.ensquared(Lt, f, n=25)[2] for f in (0.0, lens.fields_deg[-1])))
            if best is None or worst < best[1]:
                best = (float(b), float(worst), float(ee_min))
        bias_opt[name] = dict(bias_um=best[0], worst_rms_um=best[1], min_ee3=best[2])
    # glass mass with catalogue densities
    from .raytrace import sag
    Lm = lens.copy(); Lm.set_apertures(); mass = 0.0
    for k, s_ in enumerate(Lm.surfaces):
        if s_.glass != "AIR":
            h = max(s_.sd, Lm.surfaces[k + 1].sd) + 0.8; hs = np.linspace(0, h, 200)
            th = s_.t - sag(s_.c, hs) + sag(Lm.surfaces[k + 1].c, hs)
            mass += np.trapezoid(2 * np.pi * hs * th, hs) * G.THERMAL[s_.glass]["rho"] / 1000
    out = dict(materials=res, Ts=Ts.tolist(), budget_70C_um=budget, efl_budget_70C_ppm=efl_budget,
               compensator_spacer_mm=comp, alpha_athermal_1e6=alpha_athermal * 1e6, offset0_um=off0,
               focus_bias_opt=bias_opt, glass_mass_g=float(mass),
               efl0=efl0, efl_rows=efl_rows, alpha_camera_1e6=ALPHA_CAMERA * 1e6,
               glass_thermal={g: G.THERMAL[g] for g in ("N-PSK53A", "N-KZFS4", "N-SF6")})
    json.dump(out, open(os.path.join(outdir, "thermal.json"), "w"), indent=1)
    plot(out, os.path.join(outdir, "thermal.png"))
    return out


def plot(out, path):
    fig, axs = plt.subplots(1, 3, figsize=(16, 4.4))
    cols = {"Alüminyum 6061": "tab:blue", "Paslanmaz çelik 304": "tab:gray", "Titanyum Ti-6Al-4V": "tab:green", "Invar 36": "tab:red"}
    Ts = out["Ts"]
    for name, d in out["materials"].items():
        rows = d["rows"]; c = cols.get(name, "k")
        axs[0].plot(Ts, [r["defocus_um"] for r in rows], marker="o", ms=3, color=c, label=f"{name} ({d['cte']}·10⁻⁶/K)")
        axs[1].plot(Ts, [r["rms_um"][0] for r in rows], color=c, label=f"{name} eksen")
        axs[1].plot(Ts, [r["rms_um"][-1] for r in rows], color=c, ls="--", label=f"{name} 6,24°")
        axs[2].plot(Ts, [min(r["ee3"]) * 100 for r in rows], marker="o", ms=3, color=c, label=name)
    axs[0].axhspan(-50, 50, color="gray", alpha=0.12); axs[0].axhline(0, color="k", lw=0.6)
    axs[0].set_xlabel("sıcaklık (°C)"); axs[0].set_ylabel("odak kayması sensörde (µm)"); axs[0].grid(alpha=0.3)
    axs[0].set_title("Odak kayması (gri bant: ±50 µm tolerans)"); axs[0].legend(fontsize=7)
    axs[1].axhspan(16, 23, color="gray", alpha=0.12)
    axs[1].set_xlabel("sıcaklık (°C)"); axs[1].set_ylabel("polikromatik RMS nokta yarıçapı (µm)"); axs[1].grid(alpha=0.3)
    axs[1].set_title("PSF büyüklüğü (sabit odak)"); axs[1].legend(fontsize=6, ncol=2)
    axs[2].axhline(90, color="gray", ls=":")
    axs[2].set_xlabel("sıcaklık (°C)"); axs[2].set_ylabel("3×3 piksel kare-içi enerji, min. (%)"); axs[2].grid(alpha=0.3)
    axs[2].set_title("3×3 enerji (eksen / kenar minimumu)"); axs[2].legend(fontsize=7); axs[2].set_ylim(40, 102)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


if __name__ == "__main__":
    out = run(*(sys.argv[1:3]))
    print("athermal housing CTE (1e-6/K):", round(out["alpha_athermal_1e6"], 2))
    print("budget @70C (um):", {k: round(v, 1) for k, v in out["budget_70C_um"].items()})
    print("EFL budget @70C (ppm):", {k: round(v, 0) for k, v in out["efl_budget_70C_ppm"].items()})
    print("compensator spacer (mm):", {k: {kk: round(vv, 1) for kk, vv in v.items()} for k, v in out["compensator_spacer_mm"].items()})
    print("focus bias opt:", out["focus_bias_opt"]); print("glass mass g:", round(out["glass_mass_g"]))
    print("EFL ppm/K per material:", {k: round(v["efl_ppm_per_K"], 1) for k, v in out["materials"].items()})
    for name, d in out["materials"].items():
        r = d["rows"]
        print(f"{name:22s} defocus -40/70: {r[0]['defocus_um']:+.0f}/{r[-1]['defocus_um']:+.0f} um  RMS axis -40/20/70: {r[0]['rms_um'][0]:.0f}/{r[6]['rms_um'][0]:.0f}/{r[-1]['rms_um'][0]:.0f}  edge: {r[0]['rms_um'][-1]:.0f}/{r[6]['rms_um'][-1]:.0f}/{r[-1]['rms_um'][-1]:.0f}  EE3 min -40/70: {min(r[0]['ee3']):.2f}/{min(r[-1]['ee3']):.2f}")
    print("EFL:", [(e["T"], round(e["efl"], 4)) for e in out["efl_rows"]])
