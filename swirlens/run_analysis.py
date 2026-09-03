"""Generate all plots, tables and export files for a design JSON.

usage: python -m swirlens.run_analysis results/design_final.json results/
"""
import os, sys, json
import numpy as np
from .optimize import load
from . import analysis as A


def main(design, outdir):
    os.makedirs(outdir, exist_ok=True)
    L = load(design)
    L.set_apertures()
    par = L.paraxial()
    summary = {}
    print(A.prescription_text(L))
    open(os.path.join(outdir, "prescription.txt"), "w").write(A.prescription_text(L) + "\n")
    A.export_csv(L, os.path.join(outdir, "prescription.csv"))
    A.export_zmx(L, os.path.join(outdir, "swir_75mm_f18_cmount.zmx"))
    A.plot_layout(L, os.path.join(outdir, "layout.png"))
    A.plot_spots(L, os.path.join(outdir, "spots.png"))
    fs, poly, mono = A.plot_rms(L, os.path.join(outdir, "rms_vs_field.png"))
    freqs, mt = A.plot_mtf(L, os.path.join(outdir, "mtf.png"))
    fc = A.plot_field_color(L, os.path.join(outdir, "field_curv_dist_color.png"))
    dz, tf_rms, tf_mtf = A.plot_through_focus(L, os.path.join(outdir, "through_focus.png"))
    ri_f, ri = A.relative_illumination(L)
    ens = {f: A.ensquared(L, f) for f in L.fields_deg}
    base, rows = A.sensitivity(L)
    z = L.vertex_z()
    i25 = int(np.argmin(np.abs(freqs - 25)))
    summary = dict(
        efl=float(par["efl"]), fno=float(par["efl"] / L.epd), epd=L.epd, bfl=float(par["bfl"]),
        track=float(z[-1]), rear_vertex_to_flange=float(par["bfl"] - A.FFD),
        exit_pupil_from_image=float(par["xp_z"]), chief_angle_deg=A.chief_angles(L),
        rms_poly_um={f"{f:.2f}": float(v) for f, v in zip(fs, poly)},
        mtf25={f"{f:.2f}": dict(T=float(mt[f][0][i25]), S=float(mt[f][1][i25])) for f in L.fields_deg},
        distortion_pct_max=float(np.abs(fc["dist"]).max()),
        field_curv_um=dict(T=[float(v * 1000) for v in fc["zt"]], S=[float(v * 1000) for v in fc["zs"]]),
        lateral_color_um_max=float(np.abs(fc["lat"]).max()),
        chromatic_focal_shift_um=dict(min=float(fc["cfs"].min()), max=float(fc["cfs"].max())),
        relative_illumination_edge=float(ri[-1]),
        ensquared_1px_2px_3px={f"{f:.2f}": [float(v) for v in e] for f, e in ens.items()},
        through_focus=dict(dz_um=[float(v * 1000) for v in dz],
                           rms_um=tf_rms.tolist(), mtf25_T=tf_mtf[:, :, 0].tolist()),
        sensitivity_base_rms_um=float(base),
        sensitivity=[dict(perturbation=r[0], d_rms_um=float(r[1]), refocus_um=float(r[2]), boresight_shift_um=float(r[3])) for r in rows],
        semi_diameters=[float(s.sd) for s in L.surfaces],
    )
    json.dump(summary, open(os.path.join(outdir, "summary.json"), "w"), indent=1)
    # sensitivity table
    with open(os.path.join(outdir, "sensitivity.txt"), "w") as f:
        f.write(f"Baseline field-averaged polychromatic RMS spot: {base:.2f} um\n")
        f.write("(focus re-optimised after each perturbation; dRMS = change of field-averaged RMS spot)\n")
        f.write(f"{'perturbation':40s} {'dRMS (um)':>10s} {'refocus (um)':>13s} {'boresight (um)':>15s}\n")
        for r in sorted(rows, key=lambda r: -abs(r[1])):
            f.write(f"{r[0]:40s} {r[1]:10.2f} {r[2]:13.1f} {r[3]:15.2f}\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("through_focus", "sensitivity", "field_curv_um")}, indent=1))
    return summary


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "results")
