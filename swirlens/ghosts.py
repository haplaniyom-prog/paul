"""Paraxial two-reflection ghost analysis (ghost-focus generator).

For every ordered surface pair (j > i) the axial beam is traced forward to
surface j, reflected back to surface i, reflected forward again and traced
to the image plane.  Reported per ghost: paraxial ghost focus position
relative to the sensor, the marginal-ray footprint diameter on the sensor
and the irradiance ratio for an AR reflectance R per surface:
    E_ghost / E_star(peak pixel) ~ R^2 * (pixel area) / (footprint area) / EE1px
which is the ghost energy landing on one pixel relative to the peak-pixel
energy of a star of the same flux.
"""
import json, sys
import numpy as np
from .optimize import load
from . import glass as G


def _refract(n1, n2, c, y, u):
    return (n1 * u - y * c * (n2 - n1)) / n2


def ghost_table(lens, R=0.005, ee1=0.36, lam=None, R_sensor=0.25):
    """Sequential paraxial trace with the 'negative index' convention for
    reversed propagation (as in Zemax): after a reflection the medium index
    sign flips and thicknesses are traversed in reverse."""
    lam = lens.ref_wl if lam is None else lam
    S = lens.surfaces; n = len(S)
    nidx = [1.0] + [float(lens._index(s, lam)) for s in S]
    ts = [s.t for s in S]; cs = [s.c for s in S]
    par = lens.paraxial(); epd = lens.epd
    z = lens.vertex_z(); zimg = z[-1]
    out = []
    for j in range(1, n):
        for i in range(j):
            y, u = 0.5 * epd, 0.0
            # forward from surface 0 to j-1, refracting
            for k in range(j):
                u = _refract(nidx[k], nidx[k + 1], cs[k], y, u); y += ts[k] * u
            # reflect at surface j: n' = -n (medium before j)
            n1 = nidx[j]; n2 = -nidx[j]
            u = _refract(n1, n2, cs[j], y, u)
            # travel backwards to surface i (thickness negative)
            for k in range(j - 1, i, -1):
                y += -ts[k] * u
                u = _refract(-nidx[k + 1], -nidx[k], cs[k], y, u)   # refract backwards through k
            y += -ts[i] * u
            # reflect at surface i: medium after i (nidx[i+1]) travelling backward -> sign flips back
            n1 = -nidx[i + 1]; n2 = nidx[i + 1]
            u = _refract(n1, n2, cs[i], y, u)
            # forward from i+1 to image
            zpos = z[i]
            for k in range(i, n):
                if k > i:
                    u = _refract(nidx[k], nidx[k + 1], cs[k], y, u)
                y += ts[k] * u
            y_img = y; u_img = u
            focus = -y_img / u_img if abs(u_img) > 1e-12 else np.inf   # ghost focus relative to sensor (mm)
            foot = abs(2 * y_img)                                      # footprint diameter on the sensor (mm)
            ratio = R ** 2 * (0.020 ** 2) / max(np.pi * (foot / 2) ** 2, 1e-12) / ee1
            out.append(dict(i=i + 1, j=j + 1, focus_mm=float(focus), footprint_mm=float(foot), ratio=float(ratio)))
    # sensor-reflection ghosts: image plane (R_sensor) -> surface j (R) -> image plane
    for j in range(n):
        y, u = 0.5 * epd, 0.0
        for k in range(n):
            u = _refract(nidx[k], nidx[k + 1], cs[k], y, u); y += ts[k] * u
        u = -u                       # reflect at the flat sensor
        for k in range(n - 1, j, -1):     # backwards to surface j
            u = _refract(-nidx[k + 1], -nidx[k], cs[k], y, u); y += -ts[k - 1] * u if k - 1 >= j else 0.0
        # at surface j now (travelling backwards in medium after j): reflect
        u = _refract(-nidx[j + 1], nidx[j + 1], cs[j], y, u)
        for k in range(j, n):
            if k > j:
                u = _refract(nidx[k], nidx[k + 1], cs[k], y, u)
            y += ts[k] * u
        focus = -y / u if abs(u) > 1e-12 else np.inf
        foot = abs(2 * y)
        ratio = R_sensor * R * (0.020 ** 2) / max(np.pi * (foot / 2) ** 2, 1e-12) / ee1
        out.append(dict(i="IMG", j=j + 1, focus_mm=float(focus), footprint_mm=float(foot), ratio=float(ratio)))
    out.sort(key=lambda d: d["footprint_mm"])
    return out


def main(design="results/design_final.json", out="results/ghosts.json", R=0.005):
    L = load(design); L.set_apertures()
    g = ghost_table(L, R=R)
    json.dump(dict(R=R, ghosts=g), open(out, "w"), indent=1)
    print(f"{'S_i':>4s} {'S_j':>4s} {'ghost focus vs sensor (mm)':>28s} {'footprint (mm)':>15s} {'E_ghost/E_star,pix':>20s}")
    for d in g[:15]:
        print(f"{str(d['i']):>4s} {d['j']:4d} {d['focus_mm']:28.2f} {d['footprint_mm']:15.2f} {d['ratio']:20.1e}")
    return g


if __name__ == "__main__":
    main(*sys.argv[1:3])
