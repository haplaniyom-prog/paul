"""Aşamalı tasarım zinciri (Zemax ile karşılaştırma için).

Her aşama için JSON, Zemax .zmx, reçete, nokta diyagramı ve ölçüt JSON'u
results/zemax_karsilastirma/ altına yazılır; sonda karsilastirma.md üretilir.

usage: python -m swirlens.walkthrough [outdir]
"""
import os, sys, json, time
import numpy as np
from .optimize import (build_start, optimize, Merit, var_layout, bounds, get_x, set_x,
                       save, report, EFL_TARGET, FNO_TARGET)
from . import analysis as A
from scipy.optimize import least_squares

OUT = sys.argv[1] if len(sys.argv) > 1 else "results/zemax_karsilastirma"
CROWN, FLINT, FLAT = "N-PSK53A", "N-KZFS4", "N-SF6"


def metrics(L):
    """Zemax'te kolayca okunabilen ölçütler."""
    L.set_apertures()
    par = L.paraxial(); z = L.vertex_z()
    fs, poly, mono = A.rms_vs_field(L, nfield=4, n=17)   # fields 0, 2.08, 4.16, 6.24
    # design fields (0, 3.13, 4.4, 6.24) with a 21x21 grid
    rms_f = {}; rms_lam = {}
    for f in L.fields_deg:
        _, _, _, _, r = A.poly_spot(L, f, 21); rms_f[f"{f:.2f}"] = float(r * 1000)
        m = []
        for lam in L.wavelengths:
            P = A.spot(L, f, lam, 21); m.append(float(np.sqrt(((P - P.mean(0)) ** 2).sum(1).mean()) * 1000))
        rms_lam[f"{f:.2f}"] = m
    lcf, lcv = A.lateral_color(L, 7, 17)
    dfs, zt, zs, dist, ych = A.field_curves(L, 7)
    cl, cv = A.chromatic_focal_shift(L, 9)
    ens = {f"{f:.2f}": [float(v) for v in A.ensquared(L, f)] for f in L.fields_deg}
    iref = list(L.wavelengths).index(L.ref_wl)
    lc_all = float(np.abs(lcv).max())
    lc_1p1 = float(np.abs(lcv[:, 1:]).max())
    return dict(
        efl=float(par["efl"]), fno=float(par["efl"] / L.epd), epd=float(L.epd), bfl=float(par["bfl"]),
        track=float(z[-1]), rear_vertex_to_flange=float(par["bfl"] - A.FFD),
        exit_pupil_from_image=float(par["xp_z"]), chief_angle_deg=A.chief_angles(L),
        rms_poly_um=rms_f, rms_lambda_um=rms_lam,
        lateral_color_um_max_all=lc_all, lateral_color_um_max_1p1_1p7=lc_1p1,
        lateral_color_edge_um=[float(v) for v in lcv[-1]],
        distortion_pct_max=float(np.abs(dist).max()), distortion_pct_edge=float(dist[-1]),
        field_curv_um_edge=dict(T=float(zt[-1] * 1000), S=float(zs[-1] * 1000), axis=float(zt[0] * 1000)),
        chromatic_focal_shift_um=dict(min=float(cv.min()), max=float(cv.max())),
        ensquared_1px_2px_3px=ens, semi_diameters=[float(s.sd) for s in L.surfaces],
    )


def dump(L, tag, extra=None):
    d = os.path.join(OUT, tag); os.makedirs(d, exist_ok=True)
    L.set_apertures()
    save(L, os.path.join(d, "design.json"))
    A.export_zmx(L, os.path.join(d, f"{tag}.zmx"))
    A.export_csv(L, os.path.join(d, "prescription.csv"))
    open(os.path.join(d, "prescription.txt"), "w").write(A.prescription_text(L) + "\n")
    A.plot_spots(L, os.path.join(d, "spots.png"))
    m = metrics(L)
    if extra: m.update(extra)
    json.dump(m, open(os.path.join(d, "metrics.json"), "w"), indent=1)
    print(f"\n=== {tag} ===\n{A.prescription_text(L)}")
    print(json.dumps({k: v for k, v in m.items() if k not in ("semi_diameters", "rms_lambda_um")}, indent=1))
    return m


def polish(L, lcw=0.0, acw=0.0, tgt=None, shw=0.0, tfo=0.0, iters=400):
    layout = var_layout(L)
    m = Merit(L, layout, field_w=(1.0, 1.0, 1.0, 1.0), lc_weight=lcw, ac_weight=acw, target_rms=tgt,
              shape_weight=shw, tf_offsets=(-tfo, tfo) if tfo else ())
    lo, hi = bounds(L, layout); x0 = np.clip(get_x(L, layout), lo + 1e-9, hi - 1e-9)
    xs = np.array([0.002 if k == "c" else 0.5 for k, i in layout])
    r = least_squares(m.residuals, x0, bounds=(lo, hi), x_scale=xs, method="trf", max_nfev=iters,
                      ftol=1e-12, xtol=1e-12, gtol=1e-12)
    set_x(L, layout, r.x); res, info = m.residuals(r.x, return_info=True); info["merit"] = float((res ** 2).sum())
    report(info)
    return L, info


def main():
    t0 = time.time(); os.makedirs(OUT, exist_ok=True)
    allm = {}
    L = build_start(CROWN, FLINT, FLAT)
    allm["00_baslangic"] = dump(L, "00_baslangic")
    for tag, fno, it in (("01_f2.8", 2.8, 150), ("02_f2.2", 2.2, 100), ("03_f1.8", FNO_TARGET, 250)):
        L, info = optimize(L, fno, iters=it); print(f"stage {tag}:"); report(info)
        allm[tag] = dump(L, tag, dict(merit=info["merit"]))
    L, info = polish(L, lcw=3.0)
    allm["04_keskin_referans"] = dump(L, "04_keskin_referans", dict(merit=info["merit"]))
    Ls = L.copy()
    L, info = polish(L, lcw=3.0, tgt=0.018, shw=0.1, tfo=0.050)
    allm["05_yildiz_izleyici"] = dump(L, "05_yildiz_izleyici", dict(merit=info["merit"]))
    # star-tracker specific metrics for the last two stages
    for tag, LL in (("04_keskin_referans", Ls), ("05_yildiz_izleyici", L)):
        cb = {f"{f:.2f}": A.centroid_bias(LL, f) for f in (0.0, 3.12, 6.24)}
        allm[tag]["centroid_bias_px_rms_max"] = cb
        dz, rms, _ = A.through_focus(LL, dz=np.linspace(-0.1, 0.1, 9))
        allm[tag]["through_focus"] = dict(dz_um=[float(v * 1000) for v in dz], rms_um=rms.tolist())
        json.dump(allm[tag], open(os.path.join(OUT, tag, "metrics.json"), "w"), indent=1)
    json.dump(allm, open(os.path.join(OUT, "all_metrics.json"), "w"), indent=1)
    print(f"\nTOTAL {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
