"""Final polish: re-optimise at f/1.8 with lateral-colour (and optional axial-colour) terms.

usage: python -m swirlens.polish <lc_weight> <out.json> [ac_weight] [in.json] [target_rms_um] [shape_weight] [tf_offset_um]
"""
import sys, time, numpy as np
sys.path.insert(0, ".")
from swirlens.optimize import *
from scipy.optimize import least_squares
lcw = float(sys.argv[1]); out = sys.argv[2]; acw = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
tgt = float(sys.argv[5]) / 1000 if len(sys.argv) > 5 else None  # target RMS radius in um
shw = float(sys.argv[6]) if len(sys.argv) > 6 else 0.0  # PSF shape (kurtosis) weight
tfo = float(sys.argv[7]) / 1000 if len(sys.argv) > 7 else 0.0  # through-focus offset (um) for focus-insensitive blur
L = load(sys.argv[4] if len(sys.argv) > 4 else "results/design_final.json")
layout = var_layout(L)
m = Merit(L, layout, field_w=(1.0, 1.0, 1.0, 1.0), lc_weight=lcw, ac_weight=acw, target_rms=tgt, shape_weight=shw, tf_offsets=(-tfo, tfo) if tfo else ())
lo, hi = bounds(L, layout); x0 = np.clip(get_x(L, layout), lo + 1e-9, hi - 1e-9)
xs = np.array([0.002 if k == "c" else 0.5 for k, i in layout])
t = time.time()
r = least_squares(m.residuals, x0, bounds=(lo, hi), x_scale=xs, method="trf", max_nfev=400, ftol=1e-12, xtol=1e-12, gtol=1e-12)
set_x(L, layout, r.x); res, info = m.residuals(r.x, return_info=True); info["merit"] = float((res**2).sum())
report(info); print({k: v for k, v in info.items() if k.startswith(("rms_lambda", "kurt"))}); L.set_apertures(); save(L, out); print("done", time.time() - t)
