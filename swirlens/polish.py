"""Final polish: re-optimise at f/1.8 with lateral-colour (and optional axial-colour) terms.

usage: python -m swirlens.polish <lc_weight> <out.json> [ac_weight] [in.json]
"""
import sys, time, numpy as np
sys.path.insert(0, ".")
from swirlens.optimize import *
from scipy.optimize import least_squares
lcw = float(sys.argv[1]); out = sys.argv[2]; acw = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
L = load(sys.argv[4] if len(sys.argv) > 4 else "results/design_final.json")
layout = var_layout(L)
m = Merit(L, layout, field_w=(1.0, 1.0, 1.0, 1.2), lc_weight=lcw, ac_weight=acw)
lo, hi = bounds(L, layout); x0 = np.clip(get_x(L, layout), lo + 1e-9, hi - 1e-9)
xs = np.array([0.002 if k == "c" else 0.5 for k, i in layout])
t = time.time()
r = least_squares(m.residuals, x0, bounds=(lo, hi), x_scale=xs, method="trf", max_nfev=400, ftol=1e-12, xtol=1e-12, gtol=1e-12)
set_x(L, layout, r.x); res, info = m.residuals(r.x, return_info=True); info["merit"] = float((res**2).sum())
report(info); L.set_apertures(); save(L, out); print("done", time.time() - t)
