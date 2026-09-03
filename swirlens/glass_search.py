"""Parallel glass-pair search: staged optimisation for each (crown, flint) pair."""
import json, sys, time
from multiprocessing import Pool
import numpy as np
from .optimize import build_start, staged, save, load

PAIRS = [
    ("N-PK52A", "N-KZFS11"), ("N-PK52A", "N-KZFS4"), ("N-FK51A", "N-KZFS4"), ("N-FK51A", "N-KZFS11"),
    ("N-PK52A", "N-SF6"), ("N-PK52A", "N-SF57"), ("N-PSK53A", "N-KZFS11"), ("N-PSK53A", "N-SF6"),
    ("N-SK16", "N-KZFS11"), ("N-BAK4", "N-KZFS4"), ("N-LAF2", "N-SF57"), ("N-LASF31A", "N-SF66"),
    ("N-PK52A", "N-KZFS8"), ("N-PSK53A", "N-KZFS4"), ("N-LAK14", "N-KZFS11"), ("N-PK52A", "N-SF11"),
]


def run(pair):
    crown, flint = pair
    t0 = time.time()
    L = build_start(crown, flint, flint)
    try:
        L, info = staged(L, verbose=False)
    except Exception as e:
        return dict(crown=crown, flint=flint, error=str(e))
    L.set_apertures()
    path = f"results/search/{crown}_{flint}.json"
    save(L, path)
    rms = [info[k] for k in sorted(info) if k.startswith("rms_field")]
    return dict(crown=crown, flint=flint, merit=info["merit"], rms_um=rms, efl=info["efl"],
                bfl=info["bfl"], track=info["track"], chief=info["chief_angle"],
                cons_max=float(np.abs(info["cons"]).max()), path=path, secs=time.time() - t0)


if __name__ == "__main__":
    import os
    os.makedirs("results/search", exist_ok=True)
    with Pool(4) as p:
        out = []
        for r in p.imap_unordered(run, PAIRS):
            out.append(r)
            print(json.dumps(r), flush=True)
    out.sort(key=lambda d: d.get("merit", 1e9))
    json.dump(out, open("results/search/summary.json", "w"), indent=1)
    print("BEST:", out[0])
