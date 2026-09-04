"""Performance analysis and plotting for the SWIR star-tracker lens."""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from scipy.interpolate import RegularGridInterpolator
from .raytrace import Lens, pupil_grid_square, pupil_grid_ring, sag
from . import glass as G

PIX = 0.020        # mm pixel pitch
FFD = 17.526       # mm C-mount flange focal distance
LAM_COLORS = {0.9: "tab:purple", 1.0: "tab:blue", 1.1: "tab:blue", 1.3: "tab:green",
              1.4: "tab:olive", 1.55: "tab:orange", 1.7: "tab:red"}


def lam_color(l):
    return LAM_COLORS.get(l, "k")


# ------------------------------------------------------------------ spots
def spot(lens, field, lam, n=21, decenter=None):
    px, py = pupil_grid_square(n)
    r = lens.trace_field(px, py, field, lam, decenter=decenter)
    P = r["P"][r["ok"]][:, :2]
    return P


def poly_spot(lens, field, n=21, decenter=None):
    pts, ws, lams = [], [], []
    for lam, w in zip(lens.wavelengths, lens.weights):
        P = spot(lens, field, lam, n, decenter)
        pts.append(P); ws.append(np.full(P.shape[0], w)); lams.append(np.full(P.shape[0], lam))
    pts = np.concatenate(pts); ws = np.concatenate(ws); lams = np.concatenate(lams)
    c = (pts * ws[:, None]).sum(0) / ws.sum()
    rms = np.sqrt((ws * ((pts - c) ** 2).sum(1)).sum() / ws.sum())
    return pts, ws, lams, c, rms


def rms_vs_field(lens, nfield=9, n=17):
    fs = np.linspace(0, lens.fields_deg[-1], nfield)
    poly, mono = [], []
    for f in fs:
        _, _, _, _, r = poly_spot(lens, f, n)
        poly.append(r * 1000)
        m = []
        for lam in lens.wavelengths:
            P = spot(lens, f, lam, n)
            m.append(np.sqrt(((P - P.mean(0)) ** 2).sum(1).mean()) * 1000)
        mono.append(m)
    return fs, np.array(poly), np.array(mono)


def ensquared(lens, field, sizes=(PIX, 2 * PIX, 3 * PIX), n=41):
    pts, ws, _, c, _ = poly_spot(lens, field, n)
    out = []
    for s in sizes:
        m = (np.abs(pts[:, 0] - c[0]) <= s / 2) & (np.abs(pts[:, 1] - c[1]) <= s / 2)
        out.append(ws[m].sum() / ws.sum())
    return out


# ---------------------------------------------------------- wavefront / MTF
def opd_grid(lens, field, lam, n=129, ref_center=None, R=None):
    """OPD (in waves of lam) on an n x n normalised pupil grid, NaN outside."""
    v = np.linspace(-1, 1, n)
    px, py = np.meshgrid(v, v)
    inside = px ** 2 + py ** 2 <= 1.0
    r = lens.trace_field(px[inside], py[inside], field, lam)
    P, D, opl, ok = r["P"], r["D"], r["opl"], r["ok"]
    if ref_center is None:
        # chief ray image point
        rc = lens.trace_field([0.0], [0.0], field, lam)
        ref_center = rc["P"][0]
    if R is None:
        R = abs(lens.paraxial(lam)["xp_z"])
    C = np.array([ref_center[0], ref_center[1], P[0, 2]])
    dP = P - C
    b = (dP * D).sum(1)
    disc = b * b - ((dP ** 2).sum(1) - R * R)
    t = -b - np.sqrt(np.clip(disc, 0, None))
    W = opl + t
    # chief reference: opl of chief ray minus R
    rc = lens.trace_field([0.0], [0.0], field, lam)
    W0 = rc["opl"][0] - R
    opd = (W - W0) / (lam * 1e-3)   # waves
    opd[~ok] = np.nan
    grid = np.full((n, n), np.nan)
    grid[inside] = opd
    return v, grid


def mtf(lens, field, freqs, n=129, wavelengths=None, weights=None):
    """Polychromatic diffraction MTF (tangential, sagittal) by pupil
    autocorrelation.  Lateral colour is included via a common reference
    (primary-wavelength chief ray)."""
    wavelengths = lens.wavelengths if wavelengths is None else wavelengths
    weights = lens.weights if weights is None else weights
    par = lens.paraxial()
    fno = par["efl"] / lens.epd
    rc = lens.trace_field([0.0], [0.0], field, lens.ref_wl)
    ref = rc["P"][0]
    R = abs(par["xp_z"])
    otf_t = np.zeros(len(freqs), complex); otf_s = np.zeros(len(freqs), complex)
    wsum = 0.0
    for lam, w in zip(wavelengths, weights):
        v, grid = opd_grid(lens, field, lam, n, ref_center=ref, R=R)
        interp = RegularGridInterpolator((v, v), grid, bounds_error=False, fill_value=np.nan)
        PX, PY = np.meshgrid(v, v)
        inside = PX ** 2 + PY ** 2 <= 1.0
        Nfull = inside.sum()
        for i, nu in enumerate(freqs):
            dp = 2.0 * (lam * 1e-3) * fno * nu   # shift in normalised pupil units
            for axis, acc in ((1, otf_t), (0, otf_s)):
                shift = np.zeros(2); shift[axis] = dp
                # interpolator takes (row=y, col=x)
                pts = np.stack([PY.ravel() - shift[1], PX.ravel() - shift[0]], axis=1)
                g2 = interp(pts).reshape(PX.shape)
                m = inside & np.isfinite(grid) & np.isfinite(g2)
                val = np.exp(2j * np.pi * (grid[m] - g2[m])).sum() / Nfull
                acc[i] += w * val
        wsum += w
    return np.abs(otf_t) / wsum, np.abs(otf_s) / wsum


def diffraction_limit(lens, freqs, lam=None):
    lam = lens.ref_wl if lam is None else lam
    fno = lens.paraxial()["efl"] / lens.epd
    nu0 = 1.0 / (lam * 1e-3 * fno)
    x = np.clip(np.asarray(freqs) / nu0, 0, 1)
    return 2 / np.pi * (np.arccos(x) - x * np.sqrt(1 - x ** 2))


# ------------------------------------------------- field curvature / distortion
def field_curves(lens, nfield=15, d=0.01):
    fs = np.linspace(0, lens.fields_deg[-1], nfield)
    zt, zs, dist, ych = [], [], [], []
    efl = lens.paraxial()["efl"]
    for f in fs:
        r = lens.trace_field([0, 0, 0, d, -d], [0, d, -d, 0, 0], f, lens.ref_wl)
        P, D = r["P"], r["D"]
        # tangential: rays 1,2 (py +/- d)
        my = D[:, 1] / D[:, 2]
        zt.append(-(P[1, 1] - P[2, 1]) / (my[1] - my[2]))
        mx = D[:, 0] / D[:, 2]
        zs.append(-(P[3, 0] - P[4, 0]) / (mx[3] - mx[4]))
        ych.append(P[0, 1])
    ych = np.array(ych)
    # calibrated distortion: relative to the focal length fitted at the smallest field
    f_cal = ych[1] / np.tan(np.deg2rad(fs[1]))
    y_par = f_cal * np.tan(np.deg2rad(fs))
    dist = np.zeros_like(fs)
    dist[1:] = (ych[1:] - y_par[1:]) / y_par[1:] * 100
    return fs, np.array(zt), np.array(zs), dist, ych


def lateral_color(lens, nfield=9, n=17):
    fs = np.linspace(0, lens.fields_deg[-1], nfield)
    iref = list(lens.wavelengths).index(lens.ref_wl)
    out = np.zeros((nfield, len(lens.wavelengths)))
    for i, f in enumerate(fs):
        cents = [spot(lens, f, lam, n).mean(0) for lam in lens.wavelengths]
        out[i] = [(c[1] - cents[iref][1]) * 1000 for c in cents]
    return fs, out


def chromatic_focal_shift(lens, nl=17):
    ls = np.linspace(lens.wavelengths[0], lens.wavelengths[-1], nl)
    b0 = lens.paraxial(lens.ref_wl)["bfl"]
    return ls, np.array([lens.paraxial(l)["bfl"] - b0 for l in ls]) * 1000


def relative_illumination(lens, nfield=9, n=41):
    fs = np.linspace(0, lens.fields_deg[-1], nfield)
    px, py = pupil_grid_square(n)
    areas = []
    for f in fs:
        r = lens.trace_field(px, py, f, lens.ref_wl)
        D = r["D"][r["ok"]]
        areas.append(ConvexHull(D[:, :2]).volume)
    return fs, np.array(areas) / areas[0]


def chief_angles(lens):
    return [float(np.degrees(np.arccos(lens.trace_field([0.0], [0.0], f, lens.ref_wl)["D"][0, 2])))
            for f in lens.fields_deg]


def through_focus(lens, dz=np.linspace(-0.15, 0.15, 13), freq=25.0):
    L = lens.copy()
    t0 = L.surfaces[-1].t
    rms = np.zeros((len(dz), len(L.fields_deg)))
    mt = np.zeros((len(dz), len(L.fields_deg), 2))
    for i, d in enumerate(dz):
        L.surfaces[-1].t = t0 + d
        for j, f in enumerate(L.fields_deg):
            rms[i, j] = poly_spot(L, f, 15)[4] * 1000
            t, s = mtf(L, f, [freq], n=65)
            mt[i, j] = t[0], s[0]
    return dz, rms, mt


# ------------------------------------------------------------ tolerancing
def _avg_rms(lens, decenter=None):
    return np.mean([poly_spot(lens, f, 15, decenter=decenter)[4] for f in lens.fields_deg]) * 1000


def refocus(lens, decenter=None, span=0.4):
    """Re-optimise the image distance (focus compensator); returns (lens, shift_mm)."""
    from scipy.optimize import minimize_scalar
    L = lens.copy(); t0 = L.surfaces[-1].t

    def f(d):
        L.surfaces[-1].t = t0 + d
        return _avg_rms(L, decenter)
    r = minimize_scalar(f, bounds=(-span, span), method="bounded", options=dict(xatol=1e-4))
    L.surfaces[-1].t = t0 + r.x
    return L, r.x


def refocus_restore(lens, target, span=0.3, ngrid=61):
    """Re-focus so that the field-averaged RMS spot returns to `target`
    (the deliberately blurred nominal value), choosing the focus position
    closest to nominal.  Returns (lens, shift_mm)."""
    from scipy.optimize import brentq
    L = lens.copy(); t0 = L.surfaces[-1].t

    def g(d):
        L.surfaces[-1].t = t0 + d
        return _avg_rms(L) - target
    ds = np.linspace(-span, span, ngrid)
    gs = np.array([g(d) for d in ds])
    best = None
    for i in range(ngrid - 1):
        if gs[i] == 0 or gs[i] * gs[i + 1] < 0:
            root = brentq(g, ds[i], ds[i + 1], xtol=1e-4)
            if best is None or abs(root) < abs(best):
                best = root
    if best is None:                      # cannot restore: take the minimum
        best = ds[int(np.argmin(np.abs(gs)))]
    L.surfaces[-1].t = t0 + best
    return L, best


def _compensate(lens, mode, base):
    if mode == "restore":
        return refocus_restore(lens, base)
    if mode:
        return refocus(lens)
    return lens, 0.0


def sensitivity(lens, dR_rel=0.001, dt=0.05, dec=0.02, do_refocus=True):
    """do_refocus: True (minimise RMS), False (no compensation) or "restore"
    (re-focus to the nominal blurred RMS - the right choice for a
    deliberately defocused star-tracker PSF)."""
    """Change of field-averaged polychromatic RMS spot (um) after refocusing
    (focus is the compensator), the required refocus (um) and the axial
    centroid (boresight) shift, for individual perturbations."""
    base = _avg_rms(lens)
    rows = []
    for k, s in enumerate(lens.surfaces):
        if s.stop:
            continue
        if s.c != 0:
            L = lens.copy(); L.surfaces[k].c = s.c / (1 + dR_rel)
            L2, d = _compensate(L, do_refocus, base)
            rows.append((f"S{k+1} radius +{dR_rel*100:.1f}%", _avg_rms(L2) - base, d * 1000, 0.0))
        if k < len(lens.surfaces) - 1:
            L = lens.copy(); L.surfaces[k].t = s.t + dt
            L2, d = _compensate(L, do_refocus, base)
            rows.append((f"S{k+1} thickness +{dt:.3f} mm", _avg_rms(L2) - base, d * 1000, 0.0))
    k = 0
    while k < len(lens.surfaces):
        s = lens.surfaces[k]
        if s.glass != "AIR":
            j = k
            while lens.surfaces[j].glass != "AIR":
                j += 1
            idx = list(range(k, j + 1))
            d = {i: (0.0, dec) for i in idx}
            c_ax = poly_spot(lens, 0.0, 15, decenter=d)[3]
            rows.append((f"Element S{k+1}-S{j+1} decentre {dec*1000:.0f} um",
                         _avg_rms(lens, decenter=d) - base, 0.0, c_ax[1] * 1000))
            # field non-uniformity of the blur caused by the decentre
            rows[-1] = rows[-1][:1] + (float(np.ptp([poly_spot(lens, f, 15, decenter=d)[4] for f in lens.fields_deg]) * 1000
                                       - np.ptp([poly_spot(lens, f, 15)[4] for f in lens.fields_deg]) * 1000),) + rows[-1][2:]
            k = j + 1
        else:
            k += 1
    return base, rows


# ------------------------------------------------------------------ plots
def plot_layout(lens, path, nrays=7):
    fig, ax = plt.subplots(figsize=(12, 5))
    z = lens.vertex_z()
    # elements
    k = 0
    S = lens.surfaces
    while k < len(S):
        if S[k].glass != "AIR":
            j = k
            while S[j].glass != "AIR":
                j += 1
            # polygon: front surface (k) from -sd..sd, then back surfaces
            pts = []
            hmax = max(s.sd for s in S[k:j + 1]) + 0.3
            ys = np.linspace(-hmax, hmax, 61)
            pts += list(zip(z[k] + sag(S[k].c, ys), ys))
            pts += list(zip((z[j] + sag(S[j].c, ys))[::-1], ys[::-1]))
            ax.fill(*zip(*pts), color="#9ecae1", alpha=0.6, ec="k", lw=0.8)
            for i in range(k + 1, j):  # cemented interface
                ax.plot(z[i] + sag(S[i].c, ys), ys, "k", lw=0.6)
            k = j + 1
        else:
            k += 1
    ks = lens.stop_index
    sd = S[ks].sd if S[ks].sd else lens.stop_semi_diameter()
    ax.plot([z[ks], z[ks]], [sd, sd + 3], "k", lw=2); ax.plot([z[ks], z[ks]], [-sd, -sd - 3], "k", lw=2)
    # image plane and flange
    ax.plot([z[-1], z[-1]], [-8.2, 8.2], "k", lw=2)
    zf = z[-1] - FFD
    ax.plot([zf, zf], [-12.7, 12.7], "r--", lw=1)
    ax.plot([zf, zf + 4], [12.7, 12.7], "r--", lw=1); ax.plot([zf, zf + 4], [-12.7, -12.7], "r--", lw=1)
    ax.text(zf, 13.2, "C-mount flanş (1\"-32)", color="r", fontsize=8, ha="center")
    # rays
    cols = ["tab:blue", "tab:green", "tab:red"]
    for col, f in zip(cols, (0.0, lens.fields_deg[2], lens.fields_deg[-1])):
        py = np.linspace(-1, 1, nrays)
        r = lens.trace_field(np.zeros_like(py), py, f, lens.ref_wl)
        P0, _, _ = lens.launch(np.zeros_like(py), py, f, lens.ref_wl)
        zs = [np.full(nrays, -15.0)]
        # start: extrapolate back from first hit
        h0 = r["hits"][0]
        D0 = np.tile([0, np.sin(np.deg2rad(f)), np.cos(np.deg2rad(f))], (nrays, 1))
        t = (-15.0 - h0[:, 2]) / D0[:, 2]
        yy = [h0[:, 1] + t * D0[:, 1]]
        for i, h in enumerate(r["hits"]):
            zs.append(z[i] + h[:, 2]); yy.append(h[:, 1])
        zs.append(r["P"][:, 2] + z[-1]); yy.append(r["P"][:, 1])
        zs = np.array(zs); yy = np.array(yy)
        for i in range(nrays):
            ax.plot(zs[:, i], yy[:, i], color=col, lw=0.7)
    ax.set_aspect("equal"); ax.set_xlabel("z (mm)"); ax.set_ylabel("y (mm)")
    ax.set_title(f"{lens.name} — yerleşim (λ={lens.ref_wl} µm; alanlar 0°, {lens.fields_deg[2]}°, {lens.fields_deg[-1]}°)")
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def plot_spots(lens, path):
    fig, axs = plt.subplots(1, len(lens.fields_deg), figsize=(4 * len(lens.fields_deg), 4.4))
    for ax, f in zip(axs, lens.fields_deg):
        pts, ws, lams, c, rms = poly_spot(lens, f, 17)
        for lam in lens.wavelengths:
            m = lams == lam
            ax.plot((pts[m, 0] - c[0]) * 1000, (pts[m, 1] - c[1]) * 1000, ".", ms=2,
                    color=lam_color(lam), label=f"{lam} µm")
        ax.add_patch(plt.Rectangle((-10, -10), 20, 20, fill=False, ec="k", ls="--", lw=1))
        ax.set_xlim(-25, 25); ax.set_ylim(-25, 25); ax.set_aspect("equal")
        ax.set_title(f"alan {f:.2f}°  (y={c[1]:.2f} mm)\nRMS yarıçap {rms*1000:.1f} µm")
        ax.set_xlabel("µm"); ax.grid(alpha=0.3)
    axs[0].legend(fontsize=7, loc="upper left")
    fig.suptitle("Nokta diyagramları (polikromatik; kesikli kare = 20 µm piksel)")
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)


def plot_rms(lens, path):
    fs, poly, mono = rms_vs_field(lens)
    fig, ax = plt.subplots(figsize=(6, 4))
    for i, lam in enumerate(lens.wavelengths):
        ax.plot(fs, mono[:, i], "--", color=lam_color(lam), lw=1, label=f"{lam} µm")
    ax.plot(fs, poly, "k", lw=2, label="polikromatik")
    ax.axhline(PIX * 1000 / 2, color="gray", ls=":", label="½ piksel (10 µm)")
    ax.set_xlabel("alan açısı (°)"); ax.set_ylabel("RMS nokta yarıçapı (µm)"); ax.set_ylim(0, None)
    ax.grid(alpha=0.3); ax.legend(fontsize=7, ncol=2); ax.set_title("RMS nokta yarıçapı – alan")
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)
    return fs, poly, mono


def plot_mtf(lens, path, fmax=60):
    freqs = np.linspace(0, fmax, 31)
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    cols = ["k", "tab:blue", "tab:green", "tab:red"]
    res = {}
    for col, f in zip(cols, lens.fields_deg):
        t, s = mtf(lens, f, freqs)
        res[f] = (t, s)
        ax.plot(freqs, t, color=col, label=f"{f:.2f}° T")
        ax.plot(freqs, s, color=col, ls="--", label=f"{f:.2f}° S")
    ax.plot(freqs, diffraction_limit(lens, freqs), color="gray", ls=":", label="kırınım sınırı (1.3 µm)")
    ax.axvline(25, color="gray", lw=0.8); ax.text(25.5, 0.95, "Nyquist 25 lp/mm", fontsize=7)
    ax.set_xlabel("uzamsal frekans (lp/mm)"); ax.set_ylabel("MTF"); ax.set_ylim(0, 1); ax.set_xlim(0, fmax)
    ax.grid(alpha=0.3); ax.legend(fontsize=7, ncol=2); ax.set_title("Polikromatik kırınım MTF")
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)
    return freqs, res


def plot_field_color(lens, path):
    fs, zt, zs, dist, ych = field_curves(lens)
    fl, lc = lateral_color(lens)
    ls, cfs = chromatic_focal_shift(lens)
    fig, axs = plt.subplots(1, 4, figsize=(16, 4))
    axs[0].plot(zt * 1000, fs, label="T"); axs[0].plot(zs * 1000, fs, "--", label="S")
    axs[0].set_xlabel("odak kayması (µm)"); axs[0].set_ylabel("alan (°)"); axs[0].set_title("Alan eğriliği (1.3 µm)")
    axs[0].legend(); axs[0].grid(alpha=0.3)
    axs[1].plot(dist, fs); axs[1].set_xlabel("distorsiyon (%)"); axs[1].set_title("Distorsiyon (kalibre EFL'ye göre)"); axs[1].grid(alpha=0.3)
    for i, lam in enumerate(lens.wavelengths):
        axs[2].plot(fl, lc[:, i], color=lam_color(lam), label=f"{lam} µm")
    axs[2].set_xlabel("alan (°)"); axs[2].set_ylabel("merkez kayması vs 1.3 µm (µm)")
    axs[2].set_title("Yanal renk (nokta merkezi)"); axs[2].legend(fontsize=7); axs[2].grid(alpha=0.3)
    axs[3].plot(cfs, ls); axs[3].set_xlabel("paraksiyel odak kayması (µm)"); axs[3].set_ylabel("λ (µm)")
    axs[3].set_title("Kromatik odak kayması"); axs[3].grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)
    return dict(fs=fs, zt=zt, zs=zs, dist=dist, lat=lc, lat_f=fl, cfs=cfs, cfs_l=ls)


def plot_through_focus(lens, path):
    dz, rms, mt = through_focus(lens)
    fig, axs = plt.subplots(1, 2, figsize=(11, 4))
    cols = ["k", "tab:blue", "tab:green", "tab:red"]
    for j, (c, f) in enumerate(zip(cols, lens.fields_deg)):
        axs[0].plot(dz * 1000, rms[:, j], color=c, label=f"{f:.2f}°")
        axs[1].plot(dz * 1000, mt[:, j, 0], color=c, label=f"{f:.2f}° T")
        axs[1].plot(dz * 1000, mt[:, j, 1], color=c, ls="--", label=f"{f:.2f}° S")
    axs[0].set_xlabel("odak kayması (µm)"); axs[0].set_ylabel("RMS nokta yarıçapı (µm)"); axs[0].grid(alpha=0.3)
    axs[0].legend(); axs[0].set_title("Odak boyunca RMS nokta")
    axs[1].set_xlabel("odak kayması (µm)"); axs[1].set_ylabel("MTF @ 25 lp/mm"); axs[1].set_ylim(0, 1)
    axs[1].grid(alpha=0.3); axs[1].legend(fontsize=7, ncol=2); axs[1].set_title("Odak boyunca MTF (Nyquist)")
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)
    return dz, rms, mt


# ----------------------------------------------------------------- exports
def prescription_text(lens):
    par = lens.paraxial()
    z = lens.vertex_z()
    lines = [f"{lens.name}", f"EFL {par['efl']:.3f} mm   F/{par['efl']/lens.epd:.2f}   EPD {lens.epd:.2f} mm   "
             f"BFL {par['bfl']:.3f} mm   toplam uzunluk (S1->görüntü) {z[-1]:.2f} mm",
             f"Dalga boyları (µm) / ağırlık: " + ", ".join(f"{l}/{w}" for l, w in zip(lens.wavelengths, lens.weights)),
             f"Alanlar (°): {lens.fields_deg}", "",
             f"{'Yüzey':>5s} {'Yarıçap (mm)':>13s} {'Kalınlık (mm)':>14s} {'Cam':10s} {'Yarı-çap açıklık (mm)':>22s}  Not"]
    for k, s in enumerate(lens.surfaces):
        R = "düz" if s.c == 0 else f"{s.R:.4f}"
        lines.append(f"{k+1:5d} {R:>13s} {s.t:14.4f} {s.glass:10s} {s.sd:22.3f}  {'DURDURUCU (STOP)' if s.stop else s.comment}")
    lines.append(f"{'IMG':>5s} {'düz':>13s} {'':14s} {'':10s} {8.2:22.3f}  görüntü düzlemi (16.4 mm köşegen)")
    return "\n".join(lines)


def export_zmx(lens, path):
    L = []
    L.append("VERS 190513 693 32601 L32601")
    L.append("MODE SEQ")
    L.append(f"NAME {lens.name}")
    L.append("UNIT MM X W X CM MR CPMM")
    L.append(f"ENPD {lens.epd:.6f}")
    L.append("ENVD 2.0E+1 1 0")
    L.append("GFAC 0 0")
    L.append("GCAT SCHOTT")
    L.append("RAIM 0 0 1 1 0 0 0 0 0")
    L.append("PUSH 0 0 0 0 0 0")
    L.append("SDMA 0 1 0")
    L.append("FTYP 0 0 4 5 0 0 0")
    L.append("ROPD 2")
    L.append("PICB 1")
    L.append("XFLN 0 0 0 0")
    L.append("YFLN " + " ".join(f"{f}" for f in lens.fields_deg))
    L.append("FWGN 1 1 1 1")
    L.append("VDXN 0 0 0 0"); L.append("VDYN 0 0 0 0"); L.append("VCXN 0 0 0 0"); L.append("VCYN 0 0 0 0"); L.append("VANN 0 0 0 0")
    L.append("WAVM 1 " + " ".join(f"{l:.6f} {w}" for l, w in zip(lens.wavelengths, lens.weights)))
    for i, (l, w) in enumerate(zip(lens.wavelengths, lens.weights)):
        L.append(f"WAVM {i+1} {l:.6f} {w}")
    L.append(f"PWAV {list(lens.wavelengths).index(lens.ref_wl)+1}")
    L.append("POLS 1 0 1 0 0 1 0")
    L.append("GLRS 1 0")
    L.append("GSTD 0 100.000 100.000 100.000 100.000 100.000 100.000 0 1 1 0 0 1 1 1 1 1 1")
    L.append("NSCD 100 500 0 1.0E-3 5 1.0E-6 0 0 0 0 0 0 1000000 0 2")
    L.append("COFN QF \"COATING.DAT\" \"SCATTER_PROFILE.DAT\" \"ABG_DATA.DAT\" \"PROFILE.GRD\"")
    L.append("COFN COATING.DAT SCATTER_PROFILE.DAT ABG_DATA.DAT PROFILE.GRD")
    L.append("SURF 0"); L.append("  TYPE STANDARD"); L.append("  CURV 0.0"); L.append("  DISZ INFINITY")
    for k, s in enumerate(lens.surfaces):
        L.append(f"SURF {k+1}")
        L.append("  TYPE STANDARD")
        if s.stop:
            L.append("  STOP")
        if s.comment:
            L.append(f"  COMM {s.comment}")
        L.append(f"  CURV {s.c:.12E} 0 0 0 0 \"\"")
        L.append("  HIDE 0 0 0 0 0 0 0 0 0 0")
        L.append("  MIRR 2 0")
        L.append(f"  DISZ {s.t:.12E}")
        if s.glass != "AIR":
            L.append(f"  GLAS {s.glass} 0 0 1.5 40 0 0 0 0 0 0")
        L.append(f"  DIAM {s.sd:.6f} 1 0 0 1 \"\"")
        L.append("  POPS 0 0 0 0 0 0 0 0 1 1 1 1 0 0 0")
    n = len(lens.surfaces) + 1
    L.append(f"SURF {n}"); L.append("  COMM image"); L.append("  TYPE STANDARD"); L.append("  CURV 0.0")
    L.append("  DISZ 0.0"); L.append("  DIAM 8.2 1 0 0 1 \"\"")
    L.append("BLNK"); L.append("TOL TOFF   0   0 0 0 0 0 0 0")
    with open(path, "w") as f:
        f.write("\n".join(L) + "\n")


def export_csv(lens, path):
    with open(path, "w") as f:
        f.write("surface,radius_mm,thickness_mm,glass,semi_diameter_mm,note\n")
        for k, s in enumerate(lens.surfaces):
            R = "inf" if s.c == 0 else f"{s.R:.4f}"
            f.write(f"{k+1},{R},{s.t:.4f},{s.glass},{s.sd:.3f},{'STOP' if s.stop else s.comment}\n")


# ------------------------------------------------- star-tracker centroiding
def ensquared_vs_field(lens, nfield=9, n=41):
    fs = np.linspace(0, lens.fields_deg[-1], nfield)
    return fs, np.array([ensquared(lens, f, n=n) for f in fs])


def centroid_bias(lens, field, n=61, nphase=8, window=5, decenter=None):
    """Systematic (pixel-phase) centroiding error of the polychromatic
    geometric PSF sampled on the 20 um pixel grid.

    The spot is shifted over a grid of sub-pixel phases; for each phase the
    image is binned into pixels, the centre of mass over a `window` x `window`
    pixel box around the brightest pixel is computed, and the error relative
    to the true centroid is recorded.  Returns (rms_err_px, max_err_px)."""
    pts, ws, _, c, _ = poly_spot(lens, field, n, decenter)
    rel = (pts - c) / PIX                     # spot in pixel units, centred
    errs = []
    ph = (np.arange(nphase) + 0.5) / nphase - 0.5
    half = (window - 1) / 2
    for dx in ph:
        for dy in ph:
            x = rel[:, 0] + dx; y = rel[:, 1] + dy      # true centroid at (dx, dy)
            ix = np.floor(x + 0.5).astype(int); iy = np.floor(y + 0.5).astype(int)
            img = {}
            for a, b, w in zip(ix, iy, ws):
                img[(a, b)] = img.get((a, b), 0.0) + w
            (bx, by) = max(img, key=img.get)
            tot = mx = my = 0.0
            for (a, b), w in img.items():
                if abs(a - bx) <= half and abs(b - by) <= half:
                    tot += w; mx += w * a; my += w * b
            errs.append((mx / tot - dx, my / tot - dy))
    errs = np.array(errs)
    e = np.hypot(errs[:, 0], errs[:, 1])
    return float(np.sqrt((e ** 2).mean())), float(e.max())


def psf_profile(lens, field, n=61, nbins=30, rmax=0.05):
    """Radial encircled-energy curve of the polychromatic geometric spot."""
    pts, ws, _, c, _ = poly_spot(lens, field, n)
    r = np.hypot(pts[:, 0] - c[0], pts[:, 1] - c[1])
    edges = np.linspace(0, rmax, nbins + 1)
    ee = np.array([ws[r <= e].sum() / ws.sum() for e in edges])
    return edges, ee


def plot_startracker(lens, path):
    fs, ee = ensquared_vs_field(lens)
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
    for i, lab in enumerate(("1×1 piksel", "2×2 piksel", "3×3 piksel")):
        axs[0].plot(fs, ee[:, i] * 100, marker="o", label=lab)
    axs[0].set_xlabel("alan (°)"); axs[0].set_ylabel("kare-içi enerji (%)"); axs[0].set_ylim(0, 105)
    axs[0].grid(alpha=0.3); axs[0].legend(); axs[0].set_title("Kare-içi enerji (nokta merkezine ortalanmış)")
    cols = ["k", "tab:blue", "tab:green", "tab:red"]
    for c, f in zip(cols, lens.fields_deg):
        edges, prof = psf_profile(lens, f)
        axs[1].plot(edges * 1000, prof * 100, color=c, label=f"{f:.2f}°")
    axs[1].axvline(10, color="gray", ls=":"); axs[1].axvline(30, color="gray", ls=":")
    axs[1].text(10.5, 5, "½ px", fontsize=7); axs[1].text(30.5, 5, "1½ px", fontsize=7)
    axs[1].set_xlabel("yarıçap (µm)"); axs[1].set_ylabel("çevrelenen enerji (%)"); axs[1].grid(alpha=0.3)
    axs[1].legend(); axs[1].set_title("Çevrelenen enerji (polikromatik)")
    fsb = np.linspace(0, lens.fields_deg[-1], 5)
    cb = np.array([centroid_bias(lens, f) for f in fsb])
    axs[2].plot(fsb, cb[:, 0], marker="o", label="RMS")
    axs[2].plot(fsb, cb[:, 1], marker="s", label="maks.")
    axs[2].set_xlabel("alan (°)"); axs[2].set_ylabel("sistematik merkezleme hatası (piksel)")
    axs[2].set_ylim(0, None); axs[2].grid(alpha=0.3); axs[2].legend()
    axs[2].set_title("Piksel-fazı merkezleme hatası (5×5 CoM, gürültüsüz)")
    fig.tight_layout(); fig.savefig(path, dpi=160); plt.close(fig)
    return fs, ee, fsb, cb
