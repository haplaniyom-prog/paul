"""Side-by-side evaluation of candidate designs (blurred star-tracker versions).

usage: python -m swirlens.compare results/cand/*_blur.json
"""
import json, sys
import numpy as np
from .optimize import load
from .raytrace import sag
from . import analysis as A
from . import glass as G

ALPHA_AL = 23.6e-6


def evaluate(path):
    L = load(path); L.set_apertures()
    par = L.paraxial()
    fs, poly, _ = A.rms_vs_field(L, 5, 15)
    ens = [A.ensquared(L, f, n=31) for f in (0.0, 3.13, 6.24)]
    cb = [A.centroid_bias(L, f, n=41, nphase=6)[0] for f in (0.0, 6.24)]
    fl, lc = A.lateral_color(L, 5, 15)
    off0 = par["bfl"] - L.surfaces[-1].t
    th = []
    for T in (-40.0, 70.0):
        Lt = L.at_temperature(T, ALPHA_AL); pt = Lt.paraxial()
        th.append(((pt["bfl"] - Lt.surfaces[-1].t) - off0) * 1000)
    Lt = L.at_temperature(70.0, ALPHA_AL); efl_ppm_K = (Lt.paraxial()["efl"] / par["efl"] - 1) * 1e6 / 50
    # RMS at +/-50 K with Al housing (fixed focus)
    rms_T = {}
    for T in (-40.0, 70.0):
        Lt = L.at_temperature(T, ALPHA_AL)
        rms_T[T] = [A.poly_spot(Lt, f, 13)[4] * 1000 for f in (0.0, 6.24)]
    # edge thickness & mass
    edges = []; mass = 0.0
    S = L.surfaces
    for k, s in enumerate(S):
        if s.glass != "AIR":
            h = max(s.sd, S[k + 1].sd) + 0.5
            edges.append(s.t - sag(s.c, h) + sag(S[k + 1].c, h))
            hs = np.linspace(0, h + 0.3, 200); th_ = s.t - sag(s.c, hs) + sag(S[k + 1].c, hs)
            mass += np.trapezoid(2 * np.pi * hs * th_, hs) * G.THERMAL[s.glass]["rho"] / 1000
    glasses = []
    for s in S:
        if s.glass != "AIR" and s.glass not in glasses:
            glasses.append(s.glass)
    return dict(path=path, glasses=glasses, rms=[float(v) for v in poly], rms_spread=float(poly.max() - poly.min()),
                ee1=[e[0] for e in ens], ee3=[e[2] for e in ens], cb=cb, latcol=float(np.abs(lc[:, 1:]).max()),
                th_defocus=th, efl_ppm_K=float(efl_ppm_K), rms_T=rms_T, min_edge=float(min(edges)), mass_g=float(mass),
                max_thick=float(max(s.t for s in S if s.glass != "AIR")), rear_sd=[float(S[-2].sd), float(S[-1].sd)],
                track=float(L.vertex_z()[-1]), bfl=float(par["bfl"]))


if __name__ == "__main__":
    out = [evaluate(p) for p in sys.argv[1:]]
    json.dump(out, open("results/cand/compare.json", "w"), indent=1)
    hdr = f"{'glasses':22s} {'RMS 0/3/4.7/6.2':>22s} {'EE3 0/3/6':>16s} {'cb0/cb6':>12s} {'latc':>5s} {'th-40/+70':>10s} {'ppm/K':>5s} {'RMS@-40 0/6':>12s} {'RMS@70 0/6':>12s} {'edge':>5s} {'mass':>5s} {'tmax':>5s}"
    print(hdr)
    for r in out:
        g = "/".join(x.replace("N-", "") for x in r["glasses"])
        print(f"{g:22s} {'/'.join(f'{v:.0f}' for v in r['rms']):>22s} {'/'.join(f'{v*100:.0f}' for v in r['ee3']):>16s} "
              f"{r['cb'][0]:.3f}/{r['cb'][1]:.3f} {r['latcol']:5.1f} {r['th_defocus'][0]:+5.0f}/{r['th_defocus'][1]:+4.0f} {r['efl_ppm_K']:5.0f} "
              f"{r['rms_T'][-40.0][0]:5.0f}/{r['rms_T'][-40.0][1]:<5.0f} {r['rms_T'][70.0][0]:5.0f}/{r['rms_T'][70.0][1]:<5.0f} {r['min_edge']:5.2f} {r['mass_g']:5.0f} {r['max_thick']:5.1f}")
