"""Final polish: re-optimise at f/1.8 with optional lateral-colour, axial-colour,
target-blur (star tracker), PSF-shape, through-focus and thermal terms.

usage: python -m swirlens.polish <in.json> <out.json> [key=value ...]
keys: lc (lateral colour weight), ac (axial colour weight), target (RMS um),
      shape (kurtosis weight), tf (through-focus offset um), th (thermal
      defocus weight), efl_th (thermal EFL weight), thick (thickness weight),
      iters (max nfev), fw (edge-field weight)
example: python -m swirlens.polish results/sharp.json results/blur.json lc=3 target=18 shape=0.1 tf=50 th=0.25
"""
import sys, time
import numpy as np
from scipy.optimize import least_squares
from .optimize import load, save, var_layout, Merit, get_x, set_x, bounds, FNO_TARGET, report

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    kv = dict(a.split("=") for a in sys.argv[3:])
    f = lambda k, d: float(kv.get(k, d))
    L = load(src); layout = var_layout(L); L.epd = 75.0 / FNO_TARGET
    tgt = f("target", 0) / 1000 or None
    tfo = f("tf", 0) / 1000
    m = Merit(L, layout, field_w=(1.0, 1.0, 1.0, f("fw", 1.0)), lc_weight=f("lc", 0), ac_weight=f("ac", 0),
              target_rms=tgt, shape_weight=f("shape", 0), tf_offsets=(-tfo, tfo) if tfo else (),
              th_weight=f("th", 0), efl_th_weight=f("efl_th", 0), thick_weight=f("thick", 0))
    lo, hi = bounds(L, layout); x0 = np.clip(get_x(L, layout), lo + 1e-9, hi - 1e-9)
    xs = np.array([0.002 if k == "c" else 0.5 for k, i in layout])
    t = time.time()
    r = least_squares(m.residuals, x0, bounds=(lo, hi), x_scale=xs, method="trf", max_nfev=int(f("iters", 400)),
                      ftol=1e-12, xtol=1e-12, gtol=1e-12)
    set_x(L, layout, r.x); res, info = m.residuals(r.x, return_info=True); info["merit"] = float((res ** 2).sum())
    report(info); print({k: v for k, v in info.items() if k.startswith(("rms_lambda", "kurt"))})
    L.set_apertures(); save(L, out); print("done", round(time.time() - t), "s")
