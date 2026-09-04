"""Generate all plots, tables and export files for a design JSON.

usage: python -m swirlens.run_analysis results/design_final.json results/
"""
import os, sys, json
import numpy as np
from .optimize import load
from . import analysis as A


def main(design, outdir, do_refocus=True):
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
    # ---- extra metrics / plots used by the report
    wf = A.plot_wavefront(L, os.path.join(outdir, "wavefront.png"))
    A.plot_psf_pixels(L, os.path.join(outdir, "psf_pixels.png"))
    ri_f2, ri2, ch2 = A.plot_illum_chief(L, os.path.join(outdir, "illumination_chief.png"))
    hu = A.plot_huygens(L, os.path.join(outdir, "huygens_psf.png"), os.path.join(outdir, "huygens_profiles.png"))
    lam_rms = {}
    for lam in L.wavelengths:
        P0 = A.spot(L, 0.0, lam, 21); P1 = A.spot(L, L.fields_deg[-1], lam, 21)
        lam_rms[str(lam)] = [float(np.sqrt(((P0 - P0.mean(0)) ** 2).sum(1).mean()) * 1000),
                             float(np.sqrt(((P1 - P1.mean(0)) ** 2).sum(1).mean()) * 1000)]
    lcf, lcv = A.lateral_color(L, 7, 15)
    cl, cv = A.chromatic_focal_shift(L, 9)
    dfs, _, _, ddist, dych = A.field_curves(L, 7)
    iref = list(L.wavelengths).index(L.ref_wl)
    lc_1p1 = float(np.abs(np.delete(fc["lat"], [0], axis=1)).max()) if L.wavelengths[0] < 1.0 else float(np.abs(fc["lat"]).max())
    json.dump(dict(huygens=hu, wavefront_rms_pv_waves={f"{k:.2f}": list(v) for k, v in wf.items()},
                   ri=[float(v) for v in ri2], chief=[float(v) for v in ch2], fields=[float(v) for v in ri_f2],
                   rms_lambda=lam_rms,
                   lateral_color=dict(wavelengths=list(L.wavelengths), fields=[float(v) for v in lcf], um=lcv.tolist()),
                   chromatic_focal_shift=dict(lam=[float(v) for v in cl], um=[float(v) for v in cv]),
                   distortion=dict(fields=[float(v) for v in dfs], y=[float(v) for v in dych], pct=[float(v) for v in ddist])),
              open(os.path.join(outdir, "extra_metrics.json"), "w"), indent=1)
    base, rows = A.sensitivity(L, do_refocus=do_refocus)
    ee_f, ee, cb_f, cb = A.plot_startracker(L, os.path.join(outdir, "startracker_metrics.png"))
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
        lateral_color_1p1_1p7_um=lc_1p1,
        chromatic_focal_shift_um=dict(min=float(fc["cfs"].min()), max=float(fc["cfs"].max())),
        relative_illumination_edge=float(ri[-1]),
        ensquared_1px_2px_3px={f"{f:.2f}": [float(v) for v in e] for f, e in ens.items()},
        through_focus=dict(dz_um=[float(v * 1000) for v in dz],
                           rms_um=tf_rms.tolist(), mtf25_T=tf_mtf[:, :, 0].tolist()),
        centroid_bias_px={f"{f:.2f}": dict(rms=float(r), max=float(m)) for f, (r, m) in zip(cb_f, cb)},
        ensquared_vs_field={f"{f:.2f}": [float(v) for v in e] for f, e in zip(ee_f, ee)},
        sensitivity_base_rms_um=float(base),
        sensitivity=[dict(perturbation=r[0], d_rms_um=float(r[1]), refocus_um=float(r[2]), boresight_shift_um=float(r[3])) for r in rows],
        semi_diameters=[float(s.sd) for s in L.surfaces],
    )
    json.dump(summary, open(os.path.join(outdir, "summary.json"), "w"), indent=1)
    # sensitivity table
    with open(os.path.join(outdir, "sensitivity.txt"), "w") as f:
        f.write(f"Baseline field-averaged polychromatic RMS spot: {base:.2f} um\n")
        hdr = {True: "(focus re-optimised for minimum RMS after each perturbation; ",
               False: "(NO refocus - nominal focus kept; ",
               "restore": "(focus re-adjusted to restore the nominal blurred RMS; decentre rows: dRMS = change of field peak-to-peak RMS; "}[do_refocus]
        f.write(hdr + "dRMS = change of field-averaged RMS spot)\n")
        f.write(f"{'perturbation':40s} {'dRMS (um)':>10s} {'refocus (um)':>13s} {'boresight (um)':>15s}\n")
        for r in sorted(rows, key=lambda r: -abs(r[1])):
            f.write(f"{r[0]:40s} {r[1]:10.2f} {r[2]:13.1f} {r[3]:15.2f}\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("through_focus", "sensitivity", "field_curv_um", "ensquared_vs_field", "semi_diameters")}, indent=1))
    return summary


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "results", do_refocus=("restore" if "--refocus-restore" in sys.argv else ("--no-refocus" not in sys.argv)))
