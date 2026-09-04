"""Damped-least-squares optimisation of the 75 mm f/1.5 SWIR C-mount lens.

Merit = weighted polychromatic RMS spot radius over 4 fields
        + constraint residuals (EFL, C-mount rear-aperture, edge thicknesses,
          total track, chief-ray angle, ray failures).
"""
import json
import numpy as np
from scipy.optimize import least_squares
from .raytrace import Lens, Surface, pupil_grid_square, sag
from . import glass as G

EFL_TARGET = 75.0
FNO_TARGET = 1.8
IMG_SEMI_DIAG = 8.2          # mm (16.4 mm diagonal of the 640x512 / 20 um FPA)
FFD_CMOUNT = 17.526          # mm flange focal distance
REAR_SD_MAX = 10.0           # mm clear semi-diameter inside the 1"-32 throat (20 mm clear)
BFL_MIN = FFD_CMOUNT + 1.0   # rear vertex at least 1 mm in front of the flange
TRACK_MAX = 110.0            # mm first vertex -> image
CHIEF_ANGLE_MAX = 16.0       # deg at the sensor (edge of field)


# ------------------------------------------------------------------ start
def build_start(crown="N-LAK9", flint="N-SF6", flat="N-SF6"):
    """Petzval-type start: (+) singlet, (+/-) cemented doublet, STOP,
    (-/+) cemented doublet, (+) singlet, (-) field flattener."""
    S = Surface
    # radii below were derived for n_crown~1.672 / n_flint~1.7675 (at 1.3 um);
    # curvatures are rescaled to keep element powers when other glasses are used.
    kc = 0.672 / (float(G.index(crown, 1.3)) - 1.0)
    kf = 0.7675 / (float(G.index(flint, 1.3)) - 1.0)
    kff = 0.7675 / (float(G.index(flat, 1.3)) - 1.0)
    surfs = [
        S(kc / 200.0, 8.0, crown, comment="E1 front"),
        S(-kc / 600.0, 1.0),
        S(kc / 100.0, 10.0, crown, comment="E2 (cem.)"),
        S(-1 / 300.0, 4.0, flint, comment="E3 (cem.)"),
        S(kf / 231.0 - (kf - 1) / 300.0, 5.0),
        S(0.0, 6.0, stop=True),
        S(-kf / 150.0, 4.0, flint, comment="E4 (cem.)"),
        S(1 / 238.0, 10.0, crown, comment="E5 (cem.)"),
        S(-kc / 53.5 + (kc - 1) / 238.0, 2.0),
        S(kc / 250.0, 7.0, crown, comment="E6"),
        S(-kc / 400.0, 20.0),
        S(-kff / 150.0, 3.0, flat, comment="E7 field flattener"),
        S(kff / 250.0, 22.0),
    ]
    lens = Lens(surfs, epd=EFL_TARGET / FNO_TARGET, name="SWIR 75mm f/1.8 C-mount star tracker",
                wavelengths=(0.9, 1.1, 1.3, 1.55, 1.7), weights=(0.3, 0.6, 1.0, 1.0, 0.8))
    return lens


# ------------------------------------------------------------ parameters
def element_pairs(lens):
    """List of (i_front, i_back) surface indices for each glass element."""
    pairs = []
    for i, s in enumerate(lens.surfaces):
        if s.glass != "AIR":
            pairs.append((i, i + 1))
    return pairs


def var_layout(lens, vary_glass_thk=True):
    """Return list of ('c', i) / ('t', i) variable descriptors."""
    v = []
    for i, s in enumerate(lens.surfaces):
        if not s.stop:
            v.append(("c", i))
    for i, s in enumerate(lens.surfaces):
        if s.glass != "AIR":
            if vary_glass_thk:
                v.append(("t", i))
        else:
            v.append(("t", i))
    return v


def get_x(lens, layout):
    return np.array([lens.surfaces[i].c if k == "c" else lens.surfaces[i].t for k, i in layout])


def set_x(lens, layout, x):
    for (k, i), val in zip(layout, x):
        if k == "c":
            lens.surfaces[i].c = float(val)
        else:
            lens.surfaces[i].t = float(val)


def bounds(lens, layout):
    lo, hi = [], []
    n = len(lens.surfaces)
    for k, i in layout:
        if k == "c":
            cmax = 1 / 22.0 if i < 6 else 1 / 14.0
            lo.append(-cmax); hi.append(cmax)
        else:
            s = lens.surfaces[i]
            if s.glass != "AIR":
                lo.append(2.0); hi.append(16.0)
            elif i == n - 1:
                lo.append(BFL_MIN); hi.append(30.0)
            else:
                lo.append(0.5); hi.append(60.0)
    return np.array(lo), np.array(hi)


# ---------------------------------------------------------------- merit
class Merit:
    def __init__(self, lens, layout, npup=11, field_w=(1.0, 1.0, 1.0, 0.8), lc_weight=0.0, ac_weight=0.0, target_rms=None, shape_weight=0.0, tf_offsets=(), tf_weight=0.7,
                 th_weight=0.0, efl_th_weight=0.0, thick_weight=0.0, alpha_housing=23.6e-6):
        # thermal residuals (housing alpha): defocus (mm) and EFL change (mm) at -40 and +70 C
        self.th_weight = th_weight; self.efl_th_weight = efl_th_weight; self.alpha_housing = alpha_housing
        self.thick_weight = thick_weight   # penalty on glass centre thickness above 9 mm
        # tf_offsets (mm): also drive the blur to target_rms at these defocus
        # positions (focus-insensitive PSF); tf_weight scales those residuals
        self.tf_offsets = tuple(tf_offsets); self.tf_weight = tf_weight
        # shape_weight: penalise deviation of <r^4>/<r^2>^2 from 2 (Gaussian-like PSF)
        self.shape_weight = shape_weight
        # target_rms (mm): if set, drive the RMS spot radius of every field AND
        # wavelength to this value (deliberate, uniform blur for centroiding)
        self.target_rms = target_rms
        self.ac_weight = ac_weight  # weight on paraxial focal shift vs wavelength (axial colour)
        self.lc_weight = lc_weight  # weight on per-wavelength centroid shift (lateral colour)
        self.lens = lens
        self.layout = layout
        self.px, self.py = pupil_grid_square(npup, half=True)
        self.field_w = np.array(field_w)
        self.pairs = element_pairs(lens)

    def residuals(self, x, return_info=False):
        L = self.lens
        set_x(L, self.layout, x)
        res = []
        info = {}
        try:
            par = L.paraxial()
        except Exception:
            return np.full(4000, 1.0)
        if not np.isfinite(par["efl"]) or par["efl"] <= 0:
            return np.full(4000, 1.0)
        sds = np.zeros(len(L.surfaces))
        chief_angle = 0.0
        # ---- batched trace: all fields x wavelengths in one call
        nr = self.px.size
        Ps, Ds, O0, LAM, WL = [], [], [], [], []
        for f in L.fields_deg:
            P, D, opl0 = L.launch(self.px, self.py, f, L.ref_wl)
            for lam, wl in zip(L.wavelengths, L.weights):
                Ps.append(P); Ds.append(D); O0.append(opl0)
                LAM.append(np.full(nr, lam)); WL.append(np.full(nr, wl))
        Ps = np.concatenate(Ps); Ds = np.concatenate(Ds); O0 = np.concatenate(O0)
        LAM = np.concatenate(LAM); WL = np.concatenate(WL)
        r = L._trace(Ps, Ds, LAM, opl0=O0)
        okall = r["ok"]
        for k, h in enumerate(r["hits"]):
            rr = np.hypot(h[:, 0], h[:, 1])
            sds[k] = np.max(np.where(okall, rr, 0.0))
        nf, nw = len(L.fields_deg), len(L.wavelengths)
        Pimg = r["P"].reshape(nf, nw, nr, 3)
        Dimg = r["D"].reshape(nf, nw, nr, 3)
        OK = okall.reshape(nf, nw, nr)
        ic = int(np.argmin(self.px ** 2 + self.py ** 2))
        iref = list(L.wavelengths).index(L.ref_wl)
        chief_angle = float(np.degrees(np.arccos(np.clip(Dimg[:, iref, ic, 2], -1, 1))).max())
        WLr = np.array(L.weights)[None, :, None] * np.ones((nf, nw, nr))
        Pimg0 = Pimg
        for dz, wdz in [(0.0, 1.0)] + [(d, self.tf_weight) for d in (self.tf_offsets if self.target_rms else ())]:
          Pimg = Pimg0 + dz * Dimg / Dimg[..., 2:3]
          for fi, wf0 in enumerate(self.field_w):
            wf = wf0 * wdz
            xs = Pimg[fi, :, :, 0].ravel(); ys = Pimg[fi, :, :, 1].ravel()
            ok = OK[fi].ravel(); ws = WLr[fi].ravel()
            wsum = ws.sum()
            wok = np.where(ok, ws, 0.0)
            if wok.sum() > 0:
                xc = (wok * xs).sum() / wok.sum(); yc = (wok * ys).sum() / wok.sum()
            else:
                xc = yc = 0.0
            sc = np.sqrt(ws * wf / wsum)
            ex = np.where(ok, (xs - xc), 0.5) * sc
            ey = np.where(ok, (ys - yc), 0.5) * sc
            if self.target_rms is None:
                res += [ex, ey]
            elif dz == 0.0 or True:
                # per-wavelength RMS radius about its own centroid -> target
                rr = []
                for wi in range(nw):
                    okw = OK[fi, wi]
                    xw = Pimg[fi, wi, :, 0]; yw = Pimg[fi, wi, :, 1]
                    cnt = max(okw.sum(), 1)
                    xcw = np.where(okw, xw, 0).sum() / cnt; ycw = np.where(okw, yw, 0).sum() / cnt
                    r2 = np.where(okw, (xw - xcw) ** 2 + (yw - ycw) ** 2, 0.25).sum() / cnt
                    rr.append(np.sqrt(r2))
                rr = np.array(rr)
                res.append(3.0 * np.sqrt(wf * np.array(L.weights) / np.sum(L.weights)) * (rr - self.target_rms))
                if self.shape_weight > 0:
                    r2 = np.where(ok, (xs - xc) ** 2 + (ys - yc) ** 2, 0.0)
                    m2 = (wok * r2).sum() / max(wok.sum(), 1e-9)
                    m4 = (wok * r2 * r2).sum() / max(wok.sum(), 1e-9)
                    kurt = m4 / max(m2 * m2, 1e-12)
                    res.append(np.array([self.shape_weight * np.sqrt(wf) * (kurt - 2.0)]))
                    if return_info and dz == 0.0:
                        info[f"kurt_field{fi}"] = round(float(kurt), 2)
                if return_info and dz == 0.0:
                    info[f"rms_lambda_field{fi}"] = (rr * 1000).round(1).tolist()
            if self.lc_weight > 0:
                # lateral colour: centroid of each wavelength vs polychromatic centroid
                Xw = Pimg[fi, :, :, 1]; OKw = OK[fi]
                cnt = np.maximum(OKw.sum(1), 1)
                yc_l = np.where(OKw, Xw, 0.0).sum(1) / cnt
                res.append(self.lc_weight * (yc_l - yc) * np.sqrt(np.array(L.weights) / np.sum(L.weights)))
            if return_info and dz == 0.0:
                info[f"rms_field{fi}"] = float(np.sqrt(((ex ** 2 + ey ** 2).sum()) / wf) * 1000)  # um
        # ---- constraints
        efl, bfl = par["efl"], par["bfl"]
        cons = [2.0 * (efl - EFL_TARGET)]
        cons.append(5.0 * max(0.0, BFL_MIN - L.surfaces[-1].t))
        # rear clear aperture: last element inside the C-mount throat
        n = len(L.surfaces)
        for k in (n - 2, n - 1):
            cons.append(5.0 * max(0.0, sds[k] - REAR_SD_MAX))
        # element before the flattener must be >= 5 mm in front of the flange
        z = L.vertex_z()
        flange_z = z[-1] - FFD_CMOUNT
        cons.append(5.0 * max(0.0, (z[n - 2] + 5.0) - flange_z))
        # edge thicknesses of glass elements >= 1.0 mm (margin 0.5 mm on sd)
        for (a, b) in self.pairs:
            h = max(sds[a], sds[b]) + 0.5
            et = L.surfaces[a].t - sag(L.surfaces[a].c, h) + sag(L.surfaces[b].c, h)
            cons.append(5.0 * max(0.0, 1.0 - et))
            cons.append(5.0 * max(0.0, 2.0 - L.surfaces[a].t))
        # air gaps: edge separation >= 0.3 mm
        for i, s in enumerate(L.surfaces[:-1]):
            if s.glass == "AIR":
                # edge separation (incl. the stop ring, which must clear the glass)
                h = max(sds[i], sds[i + 1]) + 0.5
                eg = s.t - sag(s.c, h) + sag(L.surfaces[i + 1].c, h)
                cons.append(5.0 * max(0.0, 0.5 - eg))
        if self.ac_weight > 0:
            b0 = par["bfl"]
            for lam, wl in zip(L.wavelengths, L.weights):
                if lam != L.ref_wl:
                    cons.append(self.ac_weight * np.sqrt(wl) * (L.paraxial(lam)["bfl"] - b0))
        if self.th_weight > 0 or self.efl_th_weight > 0:
            off0 = par["bfl"] - L.surfaces[-1].t
            for Tc in (-40.0, 70.0):
                Lt = L.at_temperature(Tc, self.alpha_housing)
                pt = Lt.paraxial()
                cons.append(self.th_weight * ((pt["bfl"] - Lt.surfaces[-1].t) - off0))
                cons.append(self.efl_th_weight * (pt["efl"] - par["efl"]))
        if self.thick_weight > 0:
            for (a, b) in self.pairs:
                cons.append(self.thick_weight * max(0.0, L.surfaces[a].t - 9.0))
        cons.append(1.0 * max(0.0, z[-1] - TRACK_MAX))
        cons.append(0.05 * max(0.0, chief_angle - CHIEF_ANGLE_MAX))
        res.append(np.array(cons))
        out = np.concatenate(res)
        if return_info:
            info.update(efl=efl, bfl=bfl, track=z[-1], sds=sds, chief_angle=chief_angle,
                        cons=np.array(cons))
            return out, info
        return out


def optimize(lens, fno, layout=None, iters=60, verbose=0, npup=11, **mkw):
    lens.epd = EFL_TARGET / fno
    layout = var_layout(lens) if layout is None else layout
    m = Merit(lens, layout, npup=npup, **mkw)
    x0 = get_x(lens, layout)
    lo, hi = bounds(lens, layout)
    x0 = np.clip(x0, lo + 1e-9, hi - 1e-9)
    xs = np.array([0.002 if k == "c" else 0.5 for k, i in layout])
    r = least_squares(m.residuals, x0, bounds=(lo, hi), x_scale=xs, method="trf",
                      max_nfev=iters, verbose=verbose, ftol=1e-10, xtol=1e-10)
    set_x(lens, layout, r.x)
    res, info = m.residuals(r.x, return_info=True)
    info["merit"] = float(np.sum(res ** 2))
    return lens, info


def report(info):
    rms = [info[k] for k in sorted(info) if k.startswith("rms_field")]
    print(f"  merit={info['merit']:.3e}  EFL={info['efl']:.3f}  BFL={info['bfl']:.3f}  "
          f"track={info['track']:.2f}  chief={info['chief_angle']:.1f}deg  "
          f"RMS(um)={' '.join(f'{v:.1f}' for v in rms)}  rear sd={info['sds'][-2]:.2f}/{info['sds'][-1]:.2f}"
          f"  cons_max={np.abs(info['cons']).max():.3f}")


def save(lens, path):
    d = dict(name=lens.name, epd=lens.epd, wavelengths=list(lens.wavelengths),
             weights=list(lens.weights), ref_wl=lens.ref_wl, fields_deg=list(lens.fields_deg),
             surfaces=[dict(c=s.c, t=s.t, glass=s.glass, sd=s.sd, stop=s.stop, comment=s.comment)
                       for s in lens.surfaces])
    with open(path, "w") as f:
        json.dump(d, f, indent=2)


def load(path):
    with open(path) as f:
        d = json.load(f)
    L = Lens([Surface(**s) for s in d["surfaces"]], epd=d["epd"], wavelengths=tuple(d["wavelengths"]),
             weights=tuple(d["weights"]), ref_wl=d["ref_wl"], fields_deg=tuple(d["fields_deg"]),
             name=d["name"])
    return L


def staged(lens, verbose=True, iters=(150, 100, 250), **mkw):
    for fno, it in zip((2.8, 2.2, FNO_TARGET), iters):
        lens, info = optimize(lens, fno, iters=it, **mkw)
        if verbose:
            print(f"stage f/{fno}:"); report(info)
    return lens, info


if __name__ == "__main__":
    import sys, time
    crown = sys.argv[1] if len(sys.argv) > 1 else "N-LAK9"
    flint = sys.argv[2] if len(sys.argv) > 2 else "N-SF6"
    out = sys.argv[3] if len(sys.argv) > 3 else "results/design_opt.json"
    t0 = time.time()
    L = build_start(crown, flint, flint)
    print("start paraxial:", {k: round(float(v), 3) for k, v in L.paraxial().items()})
    L, info = staged(L)
    L.set_apertures()
    print(L.table())
    save(L, out)
    print(f"saved {out}  ({time.time()-t0:.0f} s)")
