"""Second glass search: full SCHOTT catalogue, analytic prefilter, then staged
optimisation with thermal (Al housing), lateral-colour and thickness terms.

usage: python -m swirlens.glass_search2 [n_pairs] [procs]
"""
import json, os, sys, time
from multiprocessing import Pool
import numpy as np
from . import glass as G
from .optimize import build_start, staged, save

ALPHA_AL = 23.6e-6


def gamma(g, lam=1.3):
    """Thermo-optic coefficient: dn/dT_rel/(n-1) - alpha  [1/K] (20->70 C)."""
    n = float(G.index(g, lam)); dn = (float(G.index_T(g, lam, 70)) - float(G.index_T(g, lam, 20))) / 50
    return dn / (n - 1) - G.THERMAL[g]["alpha"]


def candidates():
    names = [g for g in G.CATALOG if (g.startswith("N-") or g.startswith("P-")) and "HT" not in g]
    rows = []
    for g in names:
        try:
            rows.append(dict(g=g, n=float(G.index(g, 1.3)), V=G.swir_abbe(g), P=G.swir_partial(g), gam=gamma(g)))
        except Exception:
            pass
    crowns = [r for r in rows if r["V"] >= 47]
    flints = [r for r in rows if r["V"] <= 46]
    pairs = []
    for c in crowns:
        for f in flints:
            dV = c["V"] - f["V"]
            if dV < 10:
                continue
            phic = c["V"] / dV; phif = -f["V"] / dV          # achromat thin-lens powers (phi=1)
            ss_um = 75000.0 * abs(c["P"] - f["P"]) / dV        # secondary spectrum focal shift, um
            gam_d = phic * c["gam"] + phif * f["gam"]          # doublet thermo-optic coefficient
            mismatch = (-gam_d - ALPHA_AL) * 1e6               # ppm/K away from Al-athermal
            score = ss_um / 40.0 + abs(mismatch) / 15.0 + 20.0 / dV + max(0.0, 1.6 - c["n"]) * 3
            pairs.append(dict(crown=c["g"], flint=f["g"], dV=dV, ss_um=ss_um, phic=phic, gam_d_ppm=gam_d * 1e6,
                              mismatch_ppm=mismatch, n_c=c["n"], n_f=f["n"], score=score))
    pairs.sort(key=lambda d: d["score"])
    return pairs


MKW = dict(lc_weight=3.0, th_weight=0.5, efl_th_weight=0.1, thick_weight=0.02)


def run(pair):
    crown, flint = pair["crown"], pair["flint"]
    t0 = time.time()
    try:
        L = build_start(crown, flint, flint)
        L, info = staged(L, verbose=False, **MKW)
        L.set_apertures()
        path = f"results/search2/{crown}_{flint}.json"; save(L, path)
        rms = [info[k] for k in sorted(info) if k.startswith("rms_field")]
        # thermal summary with Al housing
        off0 = L.paraxial()["bfl"] - L.surfaces[-1].t
        th = {}
        for T in (-40.0, 70.0):
            Lt = L.at_temperature(T, ALPHA_AL); pt = Lt.paraxial()
            th[str(int(T))] = dict(defocus_um=float((pt["bfl"] - Lt.surfaces[-1].t - off0) * 1000),
                                   efl_ppm=float((pt["efl"] / info["efl"] - 1) * 1e6))
        return dict(crown=crown, flint=flint, merit=info["merit"], rms_um=rms, efl=info["efl"], bfl=info["bfl"],
                    track=info["track"], chief=info["chief_angle"], cons_max=float(np.abs(info["cons"]).max()),
                    rear_sd=[float(info["sds"][-2]), float(info["sds"][-1])], thermal=th,
                    glass_thick=[float(s.t) for s in L.surfaces if s.glass != "AIR"], path=path,
                    secs=time.time() - t0, prefilter=pair)
    except Exception as e:
        return dict(crown=crown, flint=flint, error=repr(e), secs=time.time() - t0)


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 64
    procs = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    os.makedirs("results/search2", exist_ok=True)
    pairs = candidates()
    json.dump(pairs, open("results/search2/prefilter.json", "w"), indent=0)
    print(f"{len(pairs)} candidate pairs; running top {n}", flush=True)
    for p in pairs[:n]:
        print(f"  {p['crown']:10s} {p['flint']:10s} dV={p['dV']:5.1f} SS={p['ss_um']:5.0f}um phic={p['phic']:.2f} "
              f"mismatch={p['mismatch_ppm']:+6.1f}ppm/K score={p['score']:.2f}", flush=True)
    sel = pairs[:n]
    # make sure the current pair is included for reference
    if not any(p["crown"] == "N-PSK53A" and p["flint"] == "N-KZFS4" for p in sel):
        sel.append(next(p for p in pairs if p["crown"] == "N-PSK53A" and p["flint"] == "N-KZFS4"))
    out = []
    with Pool(procs) as pool:
        for r in pool.imap_unordered(run, sel):
            out.append(r); print(json.dumps(r, default=float), flush=True)
            json.dump(out, open("results/search2/summary.json", "w"), indent=0, default=float)
    ok = [r for r in out if "error" not in r]
    ok.sort(key=lambda d: d["merit"])
    print("BEST:", [(r["crown"], r["flint"], round(r["merit"], 5)) for r in ok[:10]], flush=True)
