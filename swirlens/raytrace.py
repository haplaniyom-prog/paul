"""Minimal sequential ray tracer for rotationally symmetric spherical systems.

Conventions
-----------
* Surfaces are listed object -> image.  Surface k has curvature c_k (1/R_k),
  thickness t_k (distance from vertex k to vertex k+1) and glass_k (medium
  *after* the surface).  The final thickness is the distance to the image plane.
* One surface is flagged as the aperture stop.  Rays are aimed at the stop.
* Object at infinity; a field is specified by its object-space angle (degrees)
  in the y-z (meridional) plane.
* Lengths in millimetres, wavelengths in micrometres.
"""
from dataclasses import dataclass, field
from typing import List
import numpy as np
from . import glass as G


@dataclass
class Surface:
    c: float            # curvature 1/mm
    t: float            # thickness to next surface (mm)
    glass: str = "AIR"  # medium after the surface
    sd: float = 0.0     # clear semi-diameter (mm); filled by set_apertures()
    stop: bool = False
    comment: str = ""
    T: float = None      # temperature (C) for thermal index model; None = 20 C catalogue

    @property
    def R(self):
        return np.inf if self.c == 0 else 1.0 / self.c


@dataclass
class Lens:
    surfaces: List[Surface] = field(default_factory=list)
    epd: float = 75.0 / 1.8      # entrance pupil diameter (mm)
    wavelengths: tuple = (0.9, 1.0, 1.3, 1.55, 1.7)
    weights: tuple = (0.5, 0.8, 1.0, 1.0, 0.6)
    ref_wl: float = 1.3
    fields_deg: tuple = (0.0, 3.13, 4.4, 6.24)
    name: str = "lens"

    # ------------------------------------------------------------------ basics
    @property
    def stop_index(self):
        return next(i for i, s in enumerate(self.surfaces) if s.stop)

    def n_after(self, lam):
        """Index after each surface for wavelength lam (scalar or array)."""
        return np.array([self._index(s, lam) for s in self.surfaces])

    @staticmethod
    def _index(s, lam):
        return G.index_T(s.glass, lam, s.T) if s.T is not None else G.index(s.glass, lam)

    def vertex_z(self):
        z = np.concatenate([[0.0], np.cumsum([s.t for s in self.surfaces])])
        return z  # z[k] = vertex of surface k, z[-1] = image plane

    # --------------------------------------------------------------- paraxial
    def paraxial(self, lam=None):
        """Paraxial quantities for an infinite object.

        Returns dict with efl, bfl, ep_z (entrance pupil z from 1st vertex),
        xp_z (exit pupil z from image plane, negative = in front), stop_mag
        (marginal ray height at stop for unit height at surface 1), F-number.
        """
        lam = self.ref_wl if lam is None else lam
        n = np.concatenate([[1.0], self.n_after(lam)])
        cs = [s.c for s in self.surfaces]
        ts = [s.t for s in self.surfaces]
        # marginal ray: y=1, u=0
        y, u = 1.0, 0.0
        y_stop = None
        for k, (c, t) in enumerate(zip(cs, ts)):
            if k == self.stop_index:
                y_stop = y
            u = (n[k] * u - y * c * (n[k + 1] - n[k])) / n[k + 1]
            y_img = y + t * u
            if k < len(cs) - 1:
                y = y_img
        efl = -1.0 / u
        bfl = -y / u
        # chief ray from stop centre, traced backwards to object space
        yb, ub = 0.0, 1.0
        k = self.stop_index
        while k > 0:
            # transfer back through thickness t_{k-1}
            yb = yb - ts[k - 1] * ub
            # refract backwards at surface k-1: u' known (ub) find u
            c = cs[k - 1]
            ub = (n[k] * ub + yb * c * (n[k] - n[k - 1])) / n[k - 1]
            k -= 1
        ep_z = -yb / ub if ub != 0 else np.inf  # relative to first vertex
        # chief ray forward from stop centre to image space
        yf, uf = 0.0, 1.0
        for k in range(self.stop_index, len(cs)):
            c, t = cs[k], ts[k]
            uf = (n[k] * uf - yf * c * (n[k + 1] - n[k])) / n[k + 1]
            yf = yf + t * uf
        # yf is height at image plane; exit pupil location relative to image
        xp_z = -yf / uf
        return dict(efl=efl, bfl=bfl, ep_z=ep_z, xp_z=xp_z, stop_mag=y_stop,
                    fno=efl / self.epd, y_img=y_img)

    def stop_semi_diameter(self):
        """Stop semi-diameter such that the *real* axial marginal ray launched
        at height epd/2 in the entrance pupil just passes the stop edge
        (i.e. epd is the true entrance-beam diameter, as in Zemax with ray
        aiming on).  Falls back to the paraxial value if the ray fails."""
        p = self.paraxial()
        z0 = p["ep_z"]
        P = np.array([[0.0, 0.5 * self.epd, z0]]); D = np.array([[0.0, 0.0, 1.0]])
        k = self.stop_index
        try:
            r = self._trace(P, D, np.array([self.ref_wl]), upto=k)
            if r["ok"][0]:
                return float(r["hits"][k][0, 1])
        except Exception:
            pass
        return 0.5 * self.epd * p["stop_mag"]

    # --------------------------------------------------------------- tracing
    def launch(self, px, py, field_deg, lam, aim=True):
        """Create starting rays (on the entrance-pupil plane) for normalised
        pupil coordinates (px,py) and one field angle.  Returns P, D, opl0."""
        px = np.asarray(px, float).ravel()
        py = np.asarray(py, float).ravel()
        par = self.paraxial()
        th = np.deg2rad(field_deg)
        D = np.tile(np.array([0.0, np.sin(th), np.cos(th)]), (px.size, 1))
        r = 0.5 * self.epd
        # start plane: entrance pupil plane, expressed relative to vertex 1
        z0 = par["ep_z"]
        off_y, scale = 0.0, 1.0
        if aim:   # also on axis: the real marginal ray must hit the stop edge
            off_y, scale = self._aim(field_deg, lam)
        x = px * r * scale
        y = py * r * scale + off_y
        P = np.stack([x, y, np.full_like(x, z0)], axis=1)
        # move start point back so all rays start well before the first surface
        # (transfer to first vertex plane is handled in trace via z relative)
        opl0 = (P * D).sum(1)  # plane wave phase referenced to origin
        return P, D, opl0

    def _aim(self, field_deg, lam, iters=4):
        """Fixed-point ray aiming: find launch offset/scale so the chief ray
        hits the stop centre and the marginal ray hits the stop edge."""
        th = np.deg2rad(field_deg)
        Dv = np.array([[0.0, np.sin(th), np.cos(th)]])
        par = self.paraxial()
        z0 = par["ep_z"]
        r = 0.5 * self.epd
        sd_stop = self.stop_semi_diameter()
        off, scale = 0.0, 1.0
        k = self.stop_index
        for _ in range(iters):
            P = np.array([[0.0, off, z0], [0.0, off + r * scale, z0]])
            D = np.tile(Dv, (2, 1))
            res = self._trace(P, D, np.full(2, lam), upto=k)
            ys = res["hits"][k][:, 1]
            off -= ys[0]
            scale *= sd_stop / max(ys[1] - ys[0], 1e-6)
        return off, scale

    def _trace(self, P, D, lam, upto=None, opl0=None, decenter=None):
        """Trace rays through surfaces 0..upto (inclusive) and to the image
        plane if upto is None.  P,D (N,3) in coordinates of vertex 0.

        decenter: optional dict {surface_index: (dx, dy)} lateral shift of a
        surface (applied to that surface only).
        Returns dict with P,D at image (or last surface), opl, ok mask,
        hits (list of (N,3) arrays per surface, local coords)."""
        N = P.shape[0]
        P = P.copy(); D = D.copy()
        lam = np.asarray(lam, float) * np.ones(N)
        n_in = np.ones(N)
        opl = np.zeros(N) if opl0 is None else opl0.copy()
        ok = np.ones(N, bool)
        hits = []
        nsurf = len(self.surfaces)
        last = nsurf - 1 if upto is None else upto
        z_prev = 0.0
        for k in range(last + 1):
            s = self.surfaces[k]
            # local coordinates: translate so vertex k is origin
            P[:, 2] -= z_prev
            z_prev = s.t
            dx = dy = 0.0
            if decenter and k in decenter:
                dx, dy = decenter[k]
                P[:, 0] -= dx; P[:, 1] -= dy
            c = s.c
            if abs(c) < 1e-12:
                tt = -P[:, 2] / D[:, 2]
            else:
                A = c
                B = c * (P * D).sum(1) - D[:, 2]
                C = c * (P * P).sum(1) - 2.0 * P[:, 2]
                disc = B * B - A * C
                miss = disc < 0
                ok &= ~miss
                disc = np.where(miss, 0.0, disc)
                denom = B - np.sqrt(disc)
                denom = np.where(np.abs(denom) < 1e-14, 1e-14, denom)
                tt = -C / denom
            P = P + tt[:, None] * D
            opl += n_in * tt
            hits.append(P.copy())
            # surface normal
            nrm = np.stack([-c * P[:, 0], -c * P[:, 1], 1.0 - c * P[:, 2]], axis=1)
            nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
            n_out = np.asarray(self._index(s, lam), float) * np.ones(N)
            if k == last and upto is not None:
                pass
            mu = n_in / n_out
            cosI = (D * nrm).sum(1)
            arg = 1.0 - mu * mu * (1.0 - cosI * cosI)
            tir = arg < 0
            ok &= ~tir
            arg = np.where(tir, 0.0, arg)
            cosIp = np.sign(cosI) * np.sqrt(arg)
            D = mu[:, None] * D + (cosIp - mu * cosI)[:, None] * nrm
            n_in = n_out
            if decenter and k in decenter:
                P[:, 0] += dx; P[:, 1] += dy
        if upto is None:
            # transfer to image plane (distance = last thickness)
            P[:, 2] -= z_prev
            tt = -P[:, 2] / D[:, 2]
            P = P + tt[:, None] * D
            opl += n_in * tt
        return dict(P=P, D=D, opl=opl, ok=ok, hits=hits)

    def trace_field(self, px, py, field_deg, lam, decenter=None):
        """Trace a bundle for one field and one wavelength to the image plane."""
        P, D, opl0 = self.launch(px, py, field_deg, lam)
        return self._trace(P, D, np.full(P.shape[0], lam), opl0=opl0, decenter=decenter)

    # ------------------------------------------------------------ apertures
    def set_apertures(self, margin=0.0, nring=8):
        """Set clear semi-diameters from the full-aperture ray footprints of
        all fields (no vignetting)."""
        px, py = pupil_grid_ring(nring)
        sds = np.zeros(len(self.surfaces))
        for f in self.fields_deg:
            for sgn in (1, -1):
                res = self.trace_field(px, py, sgn * f, self.ref_wl)
                for k, h in enumerate(res["hits"]):
                    r = np.hypot(h[:, 0], h[:, 1])[res["ok"]]
                    if r.size:
                        sds[k] = max(sds[k], r.max())
        for s, sd in zip(self.surfaces, sds):
            s.sd = sd + margin
        return sds

    # ------------------------------------------------------------ utilities
    def copy(self):
        import copy
        return copy.deepcopy(self)

    def table(self):
        lines = [f"{'#':>3s} {'Radius':>11s} {'Thick':>9s} {'Glass':10s} {'SemiDia':>8s}  {'':s}"]
        for k, s in enumerate(self.surfaces):
            R = "inf" if s.c == 0 else f"{s.R:11.4f}"
            tag = "STOP" if s.stop else s.comment
            lines.append(f"{k+1:3d} {R:>11s} {s.t:9.4f} {s.glass:10s} {s.sd:8.3f}  {tag}")
        return "\n".join(lines)


# ---------------------------------------------------------------- pupil grids
def pupil_grid_square(n=11, half=False):
    """Uniform square grid clipped to the unit disc.  half=True keeps px>=0."""
    v = np.linspace(-1, 1, n)
    px, py = np.meshgrid(v, v)
    m = px ** 2 + py ** 2 <= 1.0 + 1e-9
    if half:
        m &= px >= -1e-9
    return px[m], py[m]


def pupil_grid_ring(nring=6, nazi=None):
    """Hexapolar-like grid (centre + rings)."""
    pxs, pys = [0.0], [0.0]
    for i in range(1, nring + 1):
        r = i / nring
        na = 6 * i if nazi is None else nazi
        a = np.linspace(0, 2 * np.pi, na, endpoint=False)
        pxs += list(r * np.cos(a)); pys += list(r * np.sin(a))
    return np.array(pxs), np.array(pys)


def edge_thickness(s1: Surface, s2: Surface, h1, h2, t):
    """Edge thickness of the element formed by s1 (front) and s2 (back) with
    semi-diameters h1, h2 and centre thickness t."""
    return t - sag(s1.c, h1) + sag(s2.c, h2)


def sag(c, h):
    c = np.asarray(c, float); h = np.asarray(h, float)
    arg = np.clip(1.0 - (c * h) ** 2, 0.0, None)
    return c * h * h / (1.0 + np.sqrt(arg))
