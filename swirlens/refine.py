"""Refinement runs (parallel variants) starting from a searched design."""
import json, os, sys, time
from multiprocessing import Pool
import numpy as np
from .optimize import load, save, optimize, var_layout, Merit, get_x, FNO_TARGET, report
from .raytrace import Lens


def variant(args):
    name, src, subs, iters, field_w = args
    t0 = time.time()
    L = load(src)
    for k, g in subs.items():          # k: 0-based surface index whose *following* medium is glass
        L.surfaces[k].glass = g
    layout = var_layout(L)
    # short warm-up at f/2.2 if glasses changed, then full aperture
    if subs:
        L, _ = optimize(L, 2.2, layout=layout, iters=80)
    L.epd = 75.0 / FNO_TARGET
    m = Merit(L, layout, field_w=field_w)
    from scipy.optimize import least_squares
    from .optimize import bounds
    x0 = np.clip(get_x(L, layout), *[b + (1e-9 if i == 0 else -1e-9) for i, b in enumerate(bounds(L, layout))])
    lo, hi = bounds(L, layout)
    xs = np.array([0.002 if k == "c" else 0.5 for k, i in layout])
    r = least_squares(m.residuals, x0, bounds=(lo, hi), x_scale=xs, method="trf", max_nfev=iters,
                      ftol=1e-12, xtol=1e-12, gtol=1e-12)
    from .optimize import set_x
    set_x(L, layout, r.x)
    res, info = m.residuals(r.x, return_info=True)
    info["merit"] = float(np.sum(res ** 2))
    L.set_apertures()
    path = f"results/refine/{name}.json"
    save(L, path)
    rms = [info[k] for k in sorted(info) if k.startswith("rms_field")]
    return dict(name=name, merit=info["merit"], rms_um=rms, efl=info["efl"], bfl=info["bfl"],
                track=info["track"], chief=info["chief_angle"], cons_max=float(np.abs(info["cons"]).max()),
                path=path, secs=time.time() - t0, glasses=[s.glass for s in L.surfaces if s.glass != "AIR"])


if __name__ == "__main__":
    os.makedirs("results/refine", exist_ok=True)
    src = sys.argv[1]
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 600
    fw = (1.0, 1.0, 1.0, 1.2)
    # surface indices (0-based) with glass after them: 0(E1) 2(E2) 3(E3) 6(E4) 7(E5) 9(E6) 11(E7)
    variants = [
        ("base_long", src, {}, iters, fw),
        ("singlets_LAK14", src, {0: "N-LAK14", 9: "N-LAK14"}, iters, fw),
        ("singlets_LASF44", src, {0: "N-LASF44", 9: "N-LASF44"}, iters, fw),
        ("flattener_SF6", src, {11: "N-SF6"}, iters, fw),
    ]
    with Pool(4) as p:
        out = []
        for r in p.imap_unordered(variant, variants):
            out.append(r); print(json.dumps(r), flush=True)
    out.sort(key=lambda d: d["merit"])
    json.dump(out, open("results/refine/summary.json", "w"), indent=1)
    print("BEST:", out[0]["name"], out[0]["rms_um"])
