"""Sellmeier glass catalogue (SCHOTT N-glasses) valid 0.3-2.3 um.

n^2 - 1 = sum_i B_i * l^2 / (l^2 - C_i),  l in micrometres.
Coefficients from the SCHOTT optical glass data sheets.
"""
import numpy as np

SELLMEIER = {
    # name:      (B1, B2, B3, C1, C2, C3)
    "N-BK7":    (1.03961212, 0.231792344, 1.01046945, 0.00600069867, 0.0200179144, 103.560653),
    "N-PK52A":  (1.029607, 0.1880506, 0.736488165, 0.00516800155, 0.0166658798, 138.964129),
    "N-FK51A":  (0.971247817, 0.216901417, 0.904651666, 0.00472301995, 0.0153575612, 168.68133),
    "N-PSK53A": (1.38121836, 0.196745645, 0.886089205, 0.00706416337, 0.0233251345, 97.4847345),
    "N-SK16":   (1.34317774, 0.241144399, 0.994317969, 0.00704687339, 0.0229005, 92.7508526),
    "N-BAK4":   (1.28834642, 0.132817724, 0.945395373, 0.00779980626, 0.0315631177, 105.965875),
    "N-SSK8":   (1.44857867, 0.117965926, 1.06937528, 0.00869310149, 0.0421566593, 111.300666),
    "N-LAK9":   (1.46231905, 0.344399589, 1.15508372, 0.00724270156, 0.0243353131, 85.4686868),
    "N-LAK14":  (1.50781212, 0.318866829, 1.14287213, 0.00746098727, 0.0242024834, 80.5945159),
    "N-BAF10":  (1.5851495, 0.143559385, 1.08521269, 0.00926681282, 0.0424489805, 105.613573),
    "N-LAF2":   (1.80984227, 0.15729555, 1.0930037, 0.01017116, 0.0442431765, 100.687748),
    "N-LAF7":   (1.74028764, 0.226710554, 1.32525548, 0.010792558, 0.0538626639, 106.268665),
    "N-LAF34":  (1.75836958, 0.313537785, 1.18925231, 0.00872810026, 0.0293020832, 85.1780644),
    "N-LASF44": (1.78897471, 0.38675483, 1.30506251, 0.00872506277, 0.0308085023, 92.7743824),
    "N-LASF9":  (2.00029547, 0.298926886, 1.80691843, 0.0121426017, 0.0538736236, 156.530829),
    "N-LASF31A":(1.96485075, 0.475231259, 1.48360109, 0.00982060155, 0.0344713438, 110.739863),
    "N-KZFS4":  (1.35055424, 0.197575506, 1.09962992, 0.0087628207, 0.0371767201, 90.3866994),
    "N-KZFS8":  (1.62693651, 0.24369876, 1.62007141, 0.010880863, 0.0494207753, 131.009163),
    "N-KZFS11": (1.3322245, 0.28924161, 1.15161734, 0.0084029848, 0.034423972, 88.4310532),
    "N-SF2":    (1.47343127, 0.163681849, 1.36920899, 0.0109019098, 0.0585683687, 127.404933),
    "N-SF5":    (1.52481889, 0.187085527, 1.42729015, 0.011254756, 0.0588995392, 129.141675),
    "N-SF6":    (1.77931763, 0.338149866, 2.08734474, 0.0133714182, 0.0617533621, 174.01759),
    "N-SF11":   (1.73759695, 0.313747346, 1.89878101, 0.013188707, 0.0623068142, 155.23629),
    "N-SF57":   (1.87543831, 0.37375749, 2.30001797, 0.0141749518, 0.0640509927, 177.389795),
    "N-SF66":   (2.0245976, 0.470187196, 2.59970433, 0.0147053225, 0.0692998276, 161.817601),
}

# Reference nd values (587.56 nm) from the SCHOTT catalogue, used as a self-check.
ND_REF = {
    "N-BK7": 1.5168, "N-PK52A": 1.4970, "N-FK51A": 1.48656, "N-PSK53A": 1.6180,
    "N-SK16": 1.62041, "N-BAK4": 1.56883, "N-SSK8": 1.6177, "N-LAK9": 1.6910,
    "N-LAK14": 1.6968, "N-BAF10": 1.67003, "N-LAF2": 1.74397,
    "N-LAF7": 1.7495, "N-LAF34": 1.7725, "N-LASF44": 1.8042, "N-LASF9": 1.85025,
    "N-LASF31A": 1.8830, "N-KZFS4": 1.61336, "N-KZFS8": 1.72047, "N-KZFS11": 1.63775,
    "N-SF2": 1.64769, "N-SF5": 1.67271, "N-SF6": 1.80518, "N-SF11": 1.78472,
    "N-SF57": 1.84666, "N-SF66": 1.92286,
}


# Full SCHOTT catalogue (122 glasses) extracted from the SCHOTT optical glass
# Excel table (2018) bundled with the opticalglass package; the hand-typed
# SELLMEIER/THERMAL entries above are kept as an independent cross-check.
import json as _json, os as _os
_CAT_PATH = _os.path.join(_os.path.dirname(__file__), "schott_catalog.json")
CATALOG = _json.load(open(_CAT_PATH)) if _os.path.exists(_CAT_PATH) else {}
for _g, _d in CATALOG.items():
    SELLMEIER.setdefault(_g, tuple(_d["sellmeier"]))


def index(name, lam_um):
    """Refractive index of `name` at wavelength(s) lam_um (micrometres)."""
    lam = np.asarray(lam_um, dtype=float)
    if name in ("AIR", "", None):
        return np.ones_like(lam)
    B1, B2, B3, C1, C2, C3 = SELLMEIER[name]
    l2 = lam ** 2
    n2 = 1.0 + B1 * l2 / (l2 - C1) + B2 * l2 / (l2 - C2) + B3 * l2 / (l2 - C3)
    return np.sqrt(n2)


def swir_abbe(name, lam_short=0.9, lam_mid=1.3, lam_long=1.7):
    """SWIR Abbe-like number V = (n_mid-1)/(n_short-n_long)."""
    ns, nm, nl = (index(name, l) for l in (lam_short, lam_mid, lam_long))
    return float((nm - 1.0) / (ns - nl))


def swir_partial(name, lam_short=0.9, lam_mid=1.3, lam_long=1.7):
    """Relative partial dispersion P = (n_short-n_mid)/(n_short-n_long)."""
    ns, nm, nl = (index(name, l) for l in (lam_short, lam_mid, lam_long))
    return float((ns - nm) / (ns - nl))


def selfcheck(tol=2e-4):
    bad = []
    for g, nd in list(ND_REF.items()) + [(g, d["nd"]) for g, d in CATALOG.items()]:
        n = float(index(g, 0.58756))
        if abs(n - nd) > tol:
            bad.append((g, n, nd))
    return bad


if __name__ == "__main__":
    print("Sellmeier self-check (nd):", "OK" if not selfcheck() else selfcheck())
    print(f"{'glass':10s} {'n(0.9)':>8s} {'n(1.3)':>8s} {'n(1.7)':>8s} {'V_swir':>8s} {'P_swir':>8s}")
    for g in SELLMEIER:
        print(f"{g:10s} {float(index(g,0.9)):8.4f} {float(index(g,1.3)):8.4f} "
              f"{float(index(g,1.7)):8.4f} {swir_abbe(g):8.2f} {swir_partial(g):8.4f}")


# ------------------------------------------------------------ thermal data
# SCHOTT dn/dT dispersion constants (D0, D1, D2, E0, E1, lambda_TK [um]),
# thermal expansion alpha(-30/+70 C) [1e-6/K] and density [g/cm3].
# Source: SCHOTT optical glass catalogue (Excel table, as bundled in the
# opticalglass package, 2018 edition).
THERMAL = {
    "N-PSK53A": dict(D0=-9.28e-6, D1=7.19e-9, D2=1.45e-12, E0=4.06e-7, E1=3.17e-10, lTK=0.19, alpha=9.56e-6, rho=3.568),
    "N-KZFS4":  dict(D0=1.81e-6, D1=1.16e-8, D2=-7.99e-12, E0=6.2e-7, E1=7.94e-10, lTK=0.205, alpha=7.3e-6, rho=3.002),
    "N-SF6":    dict(D0=-4.93e-6, D1=7.02e-9, D2=-2.4e-11, E0=9.84e-7, E1=1.54e-9, lTK=0.29, alpha=9.03e-6, rho=3.369),
    "N-LAK9":   dict(D0=2.11e-6, D1=1.11e-8, D2=1.82e-12, E0=4.74e-7, E1=-3.47e-10, lTK=0.146, alpha=6.3e-6, rho=3.51),
}
for _g, _d in CATALOG.items():
    THERMAL.setdefault(_g, dict(D0=_d["D0"], D1=_d["D1"], D2=_d["D2"], E0=_d["E0"], E1=_d["E1"], lTK=_d["lTK"],
                                alpha=_d["alpha"], rho=_d["rho"]))
T_REF = 20.0  # C


def n_air(lam_um, T_c=20.0, P_MPa=0.10133):
    """Refractive index of air (SCHOTT TIE-19 formula)."""
    lam = np.asarray(lam_um, float)
    n15 = 1.0 + (6432.8 + 2949810.0 * lam ** 2 / (146.0 * lam ** 2 - 1.0)
                 + 25540.0 * lam ** 2 / (41.0 * lam ** 2 - 1.0)) * 1e-8
    return 1.0 + (n15 - 1.0) * (P_MPa / 0.10133) / (1.0 + 3.4785e-3 * (T_c - 15.0))


def index_T(name, lam_um, T_c):
    """Refractive index relative to air at temperature T_c (SCHOTT dn/dT model)."""
    lam = np.asarray(lam_um, float)
    n0 = index(name, lam)                       # relative index at 20 C
    if name in ("AIR", "", None) or name not in THERMAL:
        return n0
    d = THERMAL[name]; dT = T_c - T_REF
    dn_abs = (n0 ** 2 - 1.0) / (2.0 * n0) * (d["D0"] * dT + d["D1"] * dT ** 2 + d["D2"] * dT ** 3
                                             + (d["E0"] * dT + d["E1"] * dT ** 2) / (lam ** 2 - d["lTK"] ** 2))
    n_abs0 = n0 * n_air(lam, T_REF)
    return (n_abs0 + dn_abs) / n_air(lam, T_c)
