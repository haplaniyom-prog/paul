"""Build the self-contained HTML design report (docs/tasarim_raporu.html)
from results/*.json, results/*.png and results/prescription.txt.

usage: python -m swirlens.make_report [results_dir] [out.html]
"""
import base64, json, os, sys, datetime
import numpy as np
from . import glass as G

TODAY = datetime.date.today().strftime("%d.%m.%Y")


def img(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def fmt(x, d=1):
    return f"{x:.{d}f}".replace(".", ",")


def table(head, rows, cls="", align=None):
    al = align or [""] * len(head)
    th = "".join(f"<th class='{a}'>{h}</th>" for h, a in zip(head, al))
    tr = "".join("<tr>" + "".join(f"<td class='{a}'>{c}</td>" for c, a in zip(r, al)) + "</tr>" for r in rows)
    return f"<div class='tw'><table class='{cls}'><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>"


def figure(n, src, caption):
    return f"<figure><img src='{src}' alt='Şekil {n}'><figcaption><b>Şekil {n}.</b> {caption}</figcaption></figure>"


def build(rd="results", out="docs/tasarim_raporu.html"):
    S = json.load(open(f"{rd}/summary.json"))
    R = json.load(open(f"{rd}/reference_sharp/summary.json"))
    X = json.load(open(f"{rd}/extra_metrics.json"))
    search = json.load(open(f"{rd}/search/summary.json")) if os.path.exists(f"{rd}/search/summary.json") else []
    pres = [l for l in open(f"{rd}/prescription.txt").read().split("\n") if l[:5].strip().isdigit()]
    sens = [l for l in open(f"{rd}/sensitivity.txt").read().split("\n")[3:] if l.strip()]
    F = ["0.00", "3.13", "4.40", "6.24"]
    N = [0]

    def fig(src, cap):
        N[0] += 1
        return figure(N[0], img(f"{rd}/{src}"), cap)

    # ---------------------------------------------------------------- tables
    pres_rows = []
    for l in pres:
        p = l.split()
        pres_rows.append([p[0], p[1].replace(".", ","), p[2].replace(".", ","), p[3] if p[3] != "AIR" else "—",
                          p[4].replace(".", ","), "STOP" if "STOP" in l else " ".join(p[5:])])
    pres_rows.append(["IMG", "düz", "—", "—", "8,200", "görüntü düzlemi"])
    pres_tbl = table(["Yüzey", "Yarıçap (mm)", "Kalınlık (mm)", "Cam", "Yarı-açıklık (mm)", "Not"], pres_rows,
                     "num", ["c", "r", "r", "c", "r", ""])

    glasses = ["N-PSK53A", "N-KZFS4", "N-SF6", "N-LAK9", "N-PK52A", "N-KZFS11", "N-BK7"]
    role = {"N-PSK53A": "pozitif elemanlar (E1, E2, E5, E6)", "N-KZFS4": "negatif dublet elemanları (E3, E4)",
            "N-SF6": "alan düzleştirici (E7)", "N-LAK9": "elendi (görünür-bölge kronu)",
            "N-PK52A": "elendi (düşük indis, kenar alan)", "N-KZFS11": "alternatif flint", "N-BK7": "referans"}
    glass_rows = [[g, fmt(float(G.index(g, 0.9)), 4), fmt(float(G.index(g, 1.3)), 4), fmt(float(G.index(g, 1.7)), 4),
                   fmt(G.swir_abbe(g), 1), fmt(G.swir_partial(g), 3), role[g]] for g in glasses]
    glass_tbl = table(["Cam", "n(0,9 µm)", "n(1,3 µm)", "n(1,7 µm)", "V<sub>SWIR</sub>", "P<sub>SWIR</sub>", "Rol"],
                      glass_rows, "num", ["", "r", "r", "r", "r", "r", ""])

    search_rows = [[r["crown"], r["flint"]] + [fmt(v) for v in r["rms_um"]] for r in search]
    search_tbl = table(["Kron", "Flint", "RMS 0° (µm)", "RMS 3,1°", "RMS 4,4°", "RMS 6,24°"], search_rows,
                       "num", ["", "", "r", "r", "r", "r"]) if search else "<p><i>Tarama tablosu bu çalışma dizininde yok.</i></p>"

    def pair(d, k, key):
        return d[key][k]

    rms = S["rms_poly_um"]; rmsr = R["rms_poly_um"]
    comp_rows = [
        ["Polikromatik RMS nokta yarıçapı, 0° / 3,1° / 4,7° / 6,24°",
         " / ".join(fmt(rms[k]) for k in ("0.00", "3.12", "4.68", "6.24")) + " µm",
         " / ".join(fmt(rmsr[k]) for k in ("0.00", "3.12", "4.68", "6.24")) + " µm"],
        ["Kare-içi enerji 1×1 / 2×2 / 3×3 px, eksen",
         " / ".join(f"{v*100:.0f} %" for v in S["ensquared_1px_2px_3px"]["0.00"]),
         " / ".join(f"{v*100:.0f} %" for v in R["ensquared_1px_2px_3px"]["0.00"])],
        ["Kare-içi enerji 1×1 / 2×2 / 3×3 px, 6,24°",
         " / ".join(f"{v*100:.0f} %" for v in S["ensquared_1px_2px_3px"]["6.24"]),
         " / ".join(f"{v*100:.0f} %" for v in R["ensquared_1px_2px_3px"]["6.24"])],
        ["Sistematik merkezleme hatası RMS / maks., eksen",
         f"<b>{fmt(S['centroid_bias_px']['0.00']['rms'],3)} / {fmt(S['centroid_bias_px']['0.00']['max'],3)} px</b>",
         f"{fmt(R['centroid_bias_px']['0.00']['rms'],3)} / {fmt(R['centroid_bias_px']['0.00']['max'],3)} px"],
        ["Sistematik merkezleme hatası RMS / maks., 6,24°",
         f"{fmt(S['centroid_bias_px']['6.24']['rms'],3)} / {fmt(S['centroid_bias_px']['6.24']['max'],3)} px",
         f"{fmt(R['centroid_bias_px']['6.24']['rms'],3)} / {fmt(R['centroid_bias_px']['6.24']['max'],3)} px"],
        ["Yanal renk 1,1–1,7 µm, kenar (0,9 µm dâhil)",
         f"{fmt(S['lateral_color_1p1_1p7_um'])} µm ({fmt(S['lateral_color_um_max'])} µm)",
         f"{fmt(R.get('lateral_color_1p1_1p7_um', 4.1))} µm ({fmt(R['lateral_color_um_max'])} µm)"],
        ["Distorsiyon, kalibre EFL'ye göre, maks.", f"{fmt(S['distortion_pct_max'],2)} %", f"{fmt(R['distortion_pct_max'],2)} %"],
        ["MTF @ 25 lp/mm (T), eksen → 6,24°", f"{fmt(S['mtf25']['0.00']['T'],2)} → {fmt(S['mtf25']['6.24']['T'],2)}",
         f"{fmt(R['mtf25']['0.00']['T'],2)} → {fmt(R['mtf25']['6.24']['T'],2)}"],
        ["Paraksiyel kromatik odak kayması 0,9→1,7 µm",
         f"{S['chromatic_focal_shift_um']['min']:.0f} … +{S['chromatic_focal_shift_um']['max']:.0f} µm",
         f"{R['chromatic_focal_shift_um']['min']:.0f} … +{R['chromatic_focal_shift_um']['max']:.0f} µm"],
        ["Bağıl aydınlatma, kenar", f"{S['relative_illumination_edge']*100:.1f} %", f"{R['relative_illumination_edge']*100:.1f} %"],
    ]
    comp_tbl = table(["Ölçüt", "Nihai tasarım (yayılmış PSF)", "Keskin referans"], comp_rows, "num", ["", "r", "r"])

    ens = S["ensquared_vs_field"]
    ens_rows = [[fmt(float(k), 2) + "°"] + [f"{v*100:.0f} %" for v in vals] for k, vals in ens.items()]
    ens_tbl = table(["Alan", "1×1 px", "2×2 px", "3×3 px"], ens_rows, "num", ["", "r", "r", "r"])

    cb = S["centroid_bias_px"]
    cb_rows = [[fmt(float(k), 2) + "°", fmt(v["rms"], 3), fmt(v["max"], 3), fmt(v["rms"] * 55, 1)] for k, v in cb.items()]
    cb_tbl = table(["Alan", "RMS hata (px)", "Maks. hata (px)", "RMS hata (″)"], cb_rows, "num", ["", "r", "r", "r"])

    lam_rms = X.get("rms_lambda", {})
    lam_tbl = table(["λ (µm)", "RMS eksen (µm)", "RMS kenar 6,24° (µm)"],
                    [[l, fmt(v[0]), fmt(v[1])] for l, v in lam_rms.items()], "num", ["", "r", "r"]) if lam_rms else ""

    tf = S["through_focus"]; dz = tf["dz_um"]; rt = np.array(tf["rms_um"])
    tf_rows = [[f"{d:+.0f}"] + [fmt(v) for v in row] for d, row in zip(dz, rt)]
    tf_tbl = table(["Odak kayması (µm)", "RMS 0°", "RMS 3,13°", "RMS 4,40°", "RMS 6,24°"], tf_rows, "num", ["r", "r", "r", "r", "r"])

    wf = X["wavefront_rms_pv_waves"]
    wf_rows = [[k + "°", fmt(v[0], 2), fmt(v[1], 2)] for k, v in wf.items()]
    wf_tbl = table(["Alan", "RMS OPD (λ)", "P-V OPD (λ)"], wf_rows, "num", ["", "r", "r"])

    fc = S["field_curv_um"]; nf = len(fc["T"]); ffs = np.linspace(0, 6.24, nf)
    fc_rows = [[fmt(f, 2) + "°", f"{t:+.0f}", f"{s:+.0f}"] for f, t, s in list(zip(ffs, fc["T"], fc["S"]))[::2]]
    fc_tbl = table(["Alan", "Tanjantsal odak (µm)", "Sagital odak (µm)"], fc_rows, "num", ["", "r", "r"])

    lc = X.get("lateral_color", None)
    lc_tbl = ""
    if lc:
        lc_tbl = table(["Alan"] + [f"{l} µm" for l in lc["wavelengths"]],
                       [[fmt(f, 2) + "°"] + [f"{v:+.1f}".replace(".", ",") for v in row] for f, row in zip(lc["fields"], lc["um"])],
                       "num", [""] + ["r"] * len(lc["wavelengths"]))
    cfs = X.get("chromatic_focal_shift", None)
    cfs_tbl = table(["λ (µm)", "Odak kayması (µm)"], [[fmt(l, 2), f"{v:+.0f}"] for l, v in zip(cfs["lam"], cfs["um"])],
                    "num", ["", "r"]) if cfs else ""
    dist = X.get("distortion", None)
    dist_tbl = table(["Alan", "Ana ışın yüksekliği (mm)", "Distorsiyon (%)"],
                     [[fmt(f, 2) + "°", fmt(y, 3), f"{d:+.3f}".replace(".", ",")] for f, y, d in zip(dist["fields"], dist["y"], dist["pct"])],
                     "num", ["", "r", "r"]) if dist else ""

    sens_rows = []
    for l in sens[:16]:
        name = l[:40].strip(); a, b, c = l[40:].split()
        sens_rows.append([name, f"{float(a):+.2f}".replace(".", ","), f"{float(b):+.0f}", f"{float(c):+.1f}".replace(".", ",")])
    sens_tbl = table(["Sapma", "ΔRMS (µm)", "Gerekli odak düzeltmesi (µm)", "Boresight kayması (µm)"], sens_rows,
                     "num", ["", "r", "r", "r"])

    ri = X["ri"]; ch = X["chief"]; rif = X["fields"]
    ri_tbl = table(["Alan", "Bağıl aydınlatma", "Ana ışın açısı"],
                   [[fmt(f, 2) + "°", f"{r*100:.1f} %", fmt(c, 1) + "°"] for f, r, c in list(zip(rif, ri, ch))[::2]],
                   "num", ["", "r", "r"])

    hu = X.get("huygens", {})
    hu_tbl = table(["Alan", "RMS yarıçap (µm)", "1×1 px", "2×2 px", "3×3 px", "Merkezleme hatası RMS / maks. (px)"],
                   [[k + "°", fmt(v["rms_um"]), f"{v['ee_1px']*100:.0f} %", f"{v['ee_2px']*100:.0f} %", f"{v['ee_3px']*100:.0f} %",
                     f"{fmt(v['centroid_bias_rms_px'],3)} / {fmt(v['centroid_bias_max_px'],3)}"] for k, v in hu.items()],
                   "num", ["", "r", "r", "r", "r", "r"]) if hu else ""
    TH = json.load(open(f"{rd}/thermal.json")) if os.path.exists(f"{rd}/thermal.json") else None
    th_tbl = th_budget = th_comp = th_bias = th_glass = ""
    if TH:
        Ts = TH["Ts"]; i40 = Ts.index(-40); i20 = Ts.index(20); i70 = Ts.index(70)
        rows = []
        for name, d in TH["materials"].items():
            r = d["rows"]
            rows.append([name, fmt(d["cte"]), f"{r[i40]['defocus_um']:+.0f} / {r[i70]['defocus_um']:+.0f}",
                         f"{r[i40]['rms_um'][0]:.0f} / {r[i20]['rms_um'][0]:.0f} / {r[i70]['rms_um'][0]:.0f}",
                         f"{r[i40]['rms_um'][-1]:.0f} / {r[i20]['rms_um'][-1]:.0f} / {r[i70]['rms_um'][-1]:.0f}",
                         f"{min(r[i40]['ee3'])*100:.0f} % / {min(r[i70]['ee3'])*100:.0f} %", fmt(d["efl_ppm_per_K"])])
        th_tbl = table(["Gövde malzemesi", "CTE (10⁻⁶/K)", "Odak kayması −40 / +70 °C (µm)", "RMS eksen −40/20/70 °C (µm)",
                        "RMS kenar −40/20/70 °C (µm)", "3×3 enerji min. −40 / +70 °C", "EFL sürüklenmesi (ppm/K)"],
                       rows, "num", ["", "r", "r", "r", "r", "r", "r"])
        b = TH["budget_70C_um"]; e = TH["efl_budget_70C_ppm"]
        th_budget = table(["Bileşen (+50 K, 20→70 °C)", "Odak kayması (µm)", "EFL değişimi (ppm)"], [
            ["Cam kırılma indisi (dn/dT, hava indisi dâhil)", f"{b['glass_index']:+.0f}", f"{e['glass_index']:+.0f}"],
            ["Cam genleşmesi (yarıçap ve kalınlık)", f"{b['glass_expansion']:+.0f}", f"{e['glass_expansion']:+.0f}"],
            ["Kamera gövdesi (Al, flanş→sensör 17,526 mm)", f"{b['camera_body_Al']:+.0f}", "0"],
            ["Gövde hava aralıkları, CTE başına 10⁻⁶/K", f"{b['housing_per_1e6']:+.1f}", f"{e['housing_per_1e6']:+.0f}"],
        ], "num", ["", "r", "r"])
        th_comp = table(["Gövde", "POM (110·10⁻⁶/K)", "PTFE (120·10⁻⁶/K)", "PA6 (80·10⁻⁶/K)"],
                        [[k] + [fmt(v[kk]) + " mm" for kk in ("POM (110e-6/K)", "PTFE (120e-6/K)", "PA6 (80e-6/K)")]
                         for k, v in TH["compensator_spacer_mm"].items()], "num", ["", "r", "r", "r"])
        th_bias = table(["Gövde", "Montaj odak ön-ofseti (µm)", "En kötü RMS −40…+70 °C (µm)", "En düşük 3×3 enerji"],
                        [[k, f"{v['bias_um']:+.0f}", fmt(v["worst_rms_um"]), f"{v['min_ee3']*100:.0f} %"]
                         for k, v in TH["focus_bias_opt"].items()], "num", ["", "r", "r", "r"])
        th_glass = table(["Cam", "dn/dT (rel., 1,3 µm, 20→70 °C) 10⁻⁶/K", "α (−30/+70 °C) 10⁻⁶/K", "Yoğunluk g/cm³"],
                         [[g, fmt((float(G.index_T(g, 1.3, 70)) - float(G.index_T(g, 1.3, 20))) / 50 * 1e6, 2),
                           fmt(v["alpha"] * 1e6, 2), fmt(v["rho"], 3)] for g, v in TH["glass_thermal"].items()],
                         "num", ["", "r", "r", "r"])
    mass_g = TH["glass_mass_g"] if TH else 160.0
    m = S
    # ---------------------------------------------------------------- html
    css = """
:root{--bg:#F6F7F9;--paper:#FFFFFF;--ink:#1C2230;--ink2:#4A5468;--mute:#7C8598;--rule:#D9DEE6;--acc:#A8322A;--acc-soft:#F3E1DE;--tint:#EEF1F5;--mono:'IBM Plex Mono',ui-monospace,SFMono-Regular,Menlo,monospace;--sans:'IBM Plex Sans',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;--cond:'IBM Plex Sans Condensed','IBM Plex Sans',system-ui,sans-serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0F1218;--paper:#161A22;--ink:#E7EAF0;--ink2:#B6BDCB;--mute:#8590A3;--rule:#2B3240;--acc:#E0736A;--acc-soft:#3A2220;--tint:#1E232D}}
:root[data-theme="dark"]{--bg:#0F1218;--paper:#161A22;--ink:#E7EAF0;--ink2:#B6BDCB;--mute:#8590A3;--rule:#2B3240;--acc:#E0736A;--acc-soft:#3A2220;--tint:#1E232D}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.page{max-width:900px;margin:0 auto;padding:40px 28px 80px}
header.cover{border-top:6px solid var(--acc);padding-top:22px;margin-bottom:44px}
.eyebrow{font-family:var(--mono);font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--mute)}
h1{font-family:var(--cond);font-weight:700;font-size:44px;line-height:1.05;margin:10px 0 14px;text-wrap:balance;letter-spacing:-.01em}
.sub{font-size:18px;color:var(--ink2);max-width:40em;text-wrap:balance;margin:0 0 22px}
.meta{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px 22px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);padding:14px 0}
.meta div{font-size:13px;color:var(--ink2)}.meta b{display:block;color:var(--ink);font-family:var(--mono);font-size:14px;font-weight:500;margin-top:2px}
h2{font-family:var(--cond);font-weight:700;font-size:27px;margin:56px 0 14px;padding-top:18px;border-top:1px solid var(--rule);text-wrap:balance}
h2 span{color:var(--acc);font-family:var(--mono);font-weight:500;font-size:16px;margin-right:12px;vertical-align:middle}
h3{font-family:var(--cond);font-weight:600;font-size:19px;margin:30px 0 8px;text-wrap:balance}
p,li{max-width:68ch}p{margin:0 0 12px}ul{padding-left:20px;margin:0 0 14px}li{margin:4px 0}
.lead{font-size:16.5px;color:var(--ink2)}
.key{background:var(--tint);border-left:3px solid var(--acc);padding:14px 18px;margin:18px 0 22px;border-radius:0 6px 6px 0}
.key p{margin:0 0 6px}.key p:last-child{margin:0}
.tw{overflow-x:auto;margin:14px 0 20px}
table{border-collapse:collapse;width:100%;font-size:13.5px}
th{font-family:var(--mono);font-weight:500;font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;color:var(--mute);text-align:left;padding:8px 10px;border-bottom:2px solid var(--rule);white-space:nowrap}
td{padding:7px 10px;border-bottom:1px solid var(--rule);vertical-align:top}
table.num td{font-variant-numeric:tabular-nums}
th.r,td.r{text-align:right}th.c,td.c{text-align:center}
tbody tr:nth-child(even){background:color-mix(in srgb,var(--tint) 60%,transparent)}
figure{margin:22px 0 26px;background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:10px}
figure img{display:block;width:100%;height:auto;border-radius:3px}
figcaption{font-size:13px;color:var(--ink2);padding:10px 6px 2px;max-width:none}
.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media(max-width:700px){.two{grid-template-columns:1fr}}
.stat{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0}@media(max-width:760px){.stat{grid-template-columns:repeat(2,1fr)}}
.stat div{background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:12px 14px}
.stat small{display:block;font-family:var(--mono);font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--mute)}
.stat b{display:block;font-family:var(--cond);font-size:26px;font-weight:700;margin-top:4px;font-variant-numeric:tabular-nums}
.stat i{display:block;font-style:normal;font-size:12.5px;color:var(--ink2);margin-top:2px}
code,kbd{font-family:var(--mono);font-size:.92em;background:var(--tint);padding:1px 5px;border-radius:3px}
.foot{margin-top:60px;border-top:1px solid var(--rule);padding-top:14px;font-size:12.5px;color:var(--mute)}
@media print{body{background:#fff;color:#111;font-size:11pt}.page{max-width:none;padding:0}figure,h2{break-inside:avoid}h2{break-after:avoid}tr{break-inside:avoid}figure{border:none;padding:0}a{color:inherit;text-decoration:none}}
"""
    misc = S
    ep = abs(misc["exit_pupil_from_image"])
    html = f"""<title>Wildcat 640 SWIR Yıldız İzleyici Objektifi</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>{css}</style>
<div class="page">
<header class="cover">
<div class="eyebrow">Optik tasarım raporu · {TODAY} · Rev. B</div>
<h1>75 mm f/1,8 SWIR C&#8209;mount objektif — gündüz yıldız izleyici için</h1>
<p class="sub">Xenics Wildcat 640 InGaAs kamerası (640 × 512, 20 µm) için sıfırdan tasarlanmış, alt-piksel merkezleme amacıyla PSF'si bilinçli olarak yayılmış 7 elemanlı Petzval türevi objektifin tasarım gerekçesi, reçetesi ve tüm performans analizleri.</p>
<div class="meta">
<div>Odak uzaklığı<b>{fmt(misc['efl'],2)} mm</b></div>
<div>Diyafram<b>f/{fmt(misc['fno'],2)} · EPD {fmt(misc['epd'],2)} mm</b></div>
<div>Spektral bant<b>0,9 – 1,7 µm</b></div>
<div>Görüş alanı<b>9,75° × 7,81° (Ø 12,5°)</b></div>
<div>Arka odak / flanş<b>{fmt(misc['bfl'],3)} mm / 17,526 mm</b></div>
<div>Toplam uzunluk<b>{fmt(misc['track'],1)} mm</b></div>
</div>
</header>

<h2><span>1</span>Özet</h2>
<p class="lead">Objektif, Wildcat 640'ın 16,4 mm görüntü dairesini 75 mm odak uzaklığı ve f/1,8 açıklıkla, C-mount'un 1″-32 dişinden geçen 20,5 mm'lik arka elemanla örter. Tasarım hedefi kırınım sınırı değildir: bir yıldız izleyicide merkezleme doğruluğu, yıldızın enerjisinin 3×3 piksele Gauss benzeri ve alan boyunca tekdüze yayılmasını gerektirir. Bu yüzden her alan ve her dalga boyu için 18 µm RMS nokta yarıçapı hedeflenmiş, PSF şekli ve odak duyarsızlığı optimizasyona kısıt olarak girmiştir.</p>
<div class="stat">
<div><small>RMS nokta yarıçapı</small><b>{fmt(min(rms.values()))}–{fmt(max(rms.values()))} µm</b><i>alan boyunca, polikromatik</i></div>
<div><small>Enerji 3×3 piksel</small><b>≥ {min(v[2] for v in ens.values())*100:.0f} %</b><i>1×1 pikselde ≤ {max(v[0] for v in ens.values())*100:.0f} %</i></div>
<div><small>Merkezleme hatası</small><b>{fmt(max(v['rms'] for v in cb.values()),3)} px</b><i>sistematik, RMS, en kötü alan</i></div>
<div><small>Yanal renk 1,1–1,7 µm</small><b>{fmt(S['lateral_color_1p1_1p7_um'])} µm</b><i>kenar alan, ≈ {fmt(S['lateral_color_1p1_1p7_um']/20,2)} px</i></div>
<div><small>Distorsiyon</small><b>{fmt(S['distortion_pct_max'],2)} %</b><i>yastık, düzgün</i></div>
</div>
<div class="key">
<p><b>Yıldız izleyici için kritik sonuç.</b> Aynı optik formun keskin çözümü enerjinin %{R['ensquared_1px_2px_3px']['0.00'][0]*100:.0f}'ini tek piksele toplar ve piksel-fazına bağlı sistematik merkezleme hatası {fmt(R['centroid_bias_px']['0.00']['rms'],2)} px RMS olur. Nihai tasarımda bu hata {fmt(S['centroid_bias_px']['0.00']['rms'],3)} px'e iner (≈ 5 kat), PSF alan ve dalga boyu boyunca tekdüze kalır ve ±50 µm odak hatasına duyarsızdır.</p>
</div>

<h2><span>2</span>Gereksinimler ve kamera arayüzü</h2>
{table(["Parametre","Değer","Kaynak / not"],[
["Kamera","Xenics Wildcat 640 (CL/U3V 100/200)","XDS020 veri sayfası"],
["Dedektör","InGaAs, 640 × 512, 20 µm, %100 dolgu faktörü, TE soğutmalı","aktif alan 12,8 × 10,24 mm, köşegen 16,4 mm"],
["Spektral bant / QE","900–1700 nm, tepe ≈ %80","tasarım ağırlıkları 0,9:0,3 · 1,1:0,6 · 1,3:1,0 · 1,55:1,0 · 1,7:0,8"],
["Odak uzaklığı","75,00 mm","55″/piksel, GA 9,75° × 7,81°"],
["Diyafram","f/1,8 (gerçek giriş demeti 41,67 mm)","kullanıcı kabulü"],
["Bağlantı","C-mount 1″-32 UN, FFD 17,526 mm","arka eleman ≤ 20,5 mm serbest açıklık, arka tepe flanşın önünde"],
["PSF hedefi","RMS yarıçap 18 µm (σ ≈ 0,64 px, FWHM ≈ 1,5 px), Gauss benzeri, alan × dalga boyu × odak boyunca tekdüze","alt-piksel merkezleme"],
["Yanal renk","küçük ve alanla doğrusal","yıldız rengine bağlı merkez kayması"],
["Distorsiyon","düşük ve düzgün","3. derece radyal modelle kalibre edilir"],
["Ortam","−40…+70 °C, 40 g şok, 5 g titreşim (kamera)","mekanik hücre tasarımına girdi"],
])}
<h3>Gündüz çalışmanın tasarıma etkisi</h3>
<p>Gündüz koşullarında sınırlayıcı, gök fonunun atış gürültüsüdür; gök parlaklığı 0,9–1,2 µm'de 1,4–1,7 µm'ye göre çok daha yüksektir. Pratikte 1,2–1,7 µm (veya 1,4–1,7 µm) bant geçiren filtre kullanılır; tasarım ağırlıkları buna göre uzun dalga boylarına kaydırılmış, 0,9 µm yine de kabul edilebilir düzeyde tutulmuştur. Yıldızın enerjisi tek piksele toplanırsa merkez hesabı piksel-kilitli olur; çok yayılırsa gök fonu gürültüsü baskın çıkar. Optimum, σ ≈ 0,6–0,7 piksel genişliğinde Gauss benzeri bir PSF'dir.</p>
<h3>C-mount kısıtı</h3>
<p>1″-32 dişin iç çapı ≈ 24,5 mm'dir. Kameraya giren arka eleman için 20,5 mm serbest açıklık (yarı-çap 10,25 mm; diş dibinde ≈ 2 mm hücre duvarı kalır) ve arka tepe noktasının flanşın ≥ 1 mm önünde olması şart koşuldu. 16,4 mm görüntü dairesi ve f/1,8 konisiyle bunu sağlamak için çıkış gözbebeği görüntüden {ep:.0f} mm önde tutuldu; kenar alanda ana ışın açısı {fmt(misc['chief_angle_deg'][-1])}° olur. Mikro-lenssiz, %100 dolgu faktörlü InGaAs dizisi için bu açı sorunsuzdur.</p>

<h2><span>3</span>Optik form ve cam seçimi</h2>
<p>Form, Petzval türevi 7 eleman / 5 gruptur: (+) menisk tekil, (+/−) yapıştırılmış dublet, <b>stop</b>, (−/+) yapıştırılmış dublet, (+) tekil ve görüntü yakınında (−) alan düzleştirici. Tüm yüzeyler küreseldir. Negatif düzleştirici hem Petzval eğriliğini giderir hem de çıkış gözbebeğini öne çekerek arka elemanın C-mount içinden geçmesini sağlar.</p>
{fig("layout.png","Optik yerleşim, λ = 1,3 µm; 0°, 4,4° ve 6,24° alanlar. Kırmızı kesikli çizgi C-mount flanş düzlemi ve 1″ diş açıklığıdır; alan düzleştirici flanşın hemen önünde, diş içinde durur.")}
<h3>SWIR'de cam dispersiyonu</h3>
<p>Görünür bölge Abbe sayıları SWIR'de anlamını yitirir. 0,9 / 1,3 / 1,7 µm için <i>V</i><sub>SWIR</sub> = (n<sub>1,3</sub> − 1)/(n<sub>0,9</sub> − n<sub>1,7</sub>) ve kısmi dispersiyon <i>P</i><sub>SWIR</sub> = (n<sub>0,9</sub> − n<sub>1,3</sub>)/(n<sub>0,9</sub> − n<sub>1,7</sub>) hesaplandı. Klasik N-LAK9/N-SF6 çifti SWIR'de yalnızca ΔV ≈ 8 ve büyük ΔP verir; ikincil spektrum tüm alanlarda ~30 µm RMS bırakır. Seçilen N-PSK53A / N-KZFS4 çiftinin kısmi dispersiyonları eşittir (ΔP ≈ 0), ΔV ≈ 16'dır.</p>
{glass_tbl}
<h3>Cam çifti taraması</h3>
<p>16 kron/flint çifti aynı başlangıç formundan kademeli (f/2,8 → f/2,2 → f/1,8) optimize edildi; tablo keskin (blur'suz) merit ile elde edilen polikromatik RMS nokta yarıçaplarını verir.</p>
{search_tbl}

<h2><span>4</span>Reçete</h2>
<p>Sonsuz konjuge, mm. Yarı-açıklıklar vinyetlemesiz ışın izlerinden gelen serbest açıklıklardır; mekanik kenar için 0,5–0,8 mm eklenmelidir. Stop (yüzey 6) E4'ün 3,1 mm önünde bağımsız bir halkadır; çapı, gerçek eksenel kenar ışınının 41,67 mm giriş demetiyle geçmesine göre belirlenmiştir. Zemax dosyası: <code>results/swir_75mm_f18_cmount.zmx</code>.</p>
{pres_tbl}
{table(["Paraksiyel büyüklük","Değer"],[
["Etkin odak uzaklığı (1,3 µm)",f"{fmt(misc['efl'],3)} mm"],["Giriş gözbebeği çapı / f-sayısı",f"{fmt(misc['epd'],2)} mm / f/{fmt(misc['fno'],2)}"],
["Arka odak uzaklığı (BFL)",f"{fmt(misc['bfl'],3)} mm"],["Arka tepe → flanş",f"{fmt(misc['rear_vertex_to_flange'],2)} mm"],
["Çıkış gözbebeği konumu",f"görüntüden {ep:.1f} mm önde"],["Toplam uzunluk S1 → görüntü",f"{fmt(misc['track'],2)} mm"],
["Görüntü yüksekliği (6,24°)","8,18 mm (yarı köşegen 8,2 mm)"],["Cam kütlesi (katalog yoğunlukları)",f"≈ {mass_g:.0f} g"],
],"num",["","r"])}

<h2><span>5</span>Optimizasyon yöntemi</h2>
<p>Tasarım, bu depoda yazılmış vektörleştirilmiş bir gerçek ışın izleyici ve SciPy sönümlü en küçük kareler (TRF) çözücüsüyle yapıldı. Merit fonksiyonu üç kademede kullanıldı:</p>
<ul>
<li><b>Keskin referans:</b> 4 alan × 5 dalga boyu × ~50 ışın için polikromatik merkez etrafında RMS nokta + kısıtlar (EFL = 75, arka açıklık ≤ 10 mm yarı-çap, arka tepe ≥ 1 mm flanş önünde, kenar kalınlıkları ≥ 1 mm, stop halkası–cam boşluğu ≥ 0,5 mm, toplam uzunluk ≤ 110 mm, ana ışın ≤ 16°) ve yanal renk terimi.</li>
<li><b>Yıldız izleyici PSF'si:</b> her alan <i>ve</i> her dalga boyu için RMS yarıçapı → 18 µm; PSF basıklığı ⟨r⁴⟩/⟨r²⟩² → 2 (Gauss); aynı hedefler −50 ve +50 µm odak kaymasında da (odak duyarsızlığı); yanal renk terimi. Blur böylece odak kaydırmayla değil, dengelenmiş küresel sapma + hafif odak kaymasıyla üretildi.</li>
<li><b>Doğrulama:</b> piksel-fazı merkezleme hatası simülasyonu (geometrik ve Huygens PSF, 20 µm ızgara, 5×5 ağırlık merkezi), Huygens kırınım PSF'si ve kırınım MTF'si (gözbebeği otokorelasyonu, yanal renk dâhil polikromatik OTF).</li>
</ul>

<h2><span>6</span>Nokta görüntüsü ve PSF</h2>
{fig("spots.png","Polikromatik nokta diyagramları (5 dalga boyu renk kodlu), kesikli kare 20 µm piksel. Dağılım tüm alanlarda benzer büyüklükte ve yumuşak kenarlıdır.")}
{fig("psf_pixels.png","Geometrik PSF'nin 20 µm piksel ızgarasına bölünmüş enerji yüzdeleri; üst sıra yıldız piksel merkezinde, alt sıra piksel köşesinde. Her iki durumda enerji 3×3 pencerede kalır ve komşu piksellere yeterli sinyal düşer.")}
{fig("rms_vs_field.png","RMS nokta yarıçapı alan boyunca; renkli kesikli çizgiler tek dalga boyu, siyah polikromatik. Gri çizgi ½ piksel.")}
<div class="two">{ens_tbl}{lam_tbl}</div>
<p>Dalga boyuna göre blur büyüklüğü zayıf değişir; bu, blur'un dalga boyundan bağımsız küresel sapmayla üretilmesinin sonucudur. Salt odak kaydırmayla aynı blur üretilseydi ±125 µm kromatik odak kayması nedeniyle 0,9 µm yıldızlar keskin, 1,7 µm yıldızlar iki kat büyük görünürdü.</p>

<h2><span>7</span>Huygens PSF (kırınım dâhil)</h2>
<p>Geometrik nokta diyagramı kırınımı içermez. Huygens PSF, gözbebeği ızgarasındaki her ışını görüntü düzleminde optik yol uzunluğu fazlı bir düzlem dalgacık olarak alır ve dalgacıkları tutarlı toplar (OpticStudio'nun Huygens PSF yöntemiyle aynı yaklaşım). Beş dalga boyunun yoğunlukları spektral ağırlıklarla toplanmış, koordinatlar 1,3 µm ana ışınına göre alınmıştır; böylece yanal renk de PSF'ye dâhildir. Görüntü penceresi ±50 µm (5 piksel), örnekleme 1 µm, gözbebeği 81 × 81.</p>
{fig("huygens_psf.png","Polikromatik Huygens PSF, dört alan; renk ölçeği her karede kendi tepe değerine normalize ve karekök (γ = 0,5) sıkıştırmalıdır, beyaz ızgara 20 µm pikselleri gösterir. Başlıklarda PSF'nin ikinci-moment RMS yarıçapı ve 1×1 / 3×3 piksel kare-içi enerjisi verilmiştir.")}
{fig("huygens_profiles.png","Huygens PSF'nin x ve y kesitleri (gri bant tek piksel) ve çevrelenen enerji eğrileri; noktalı çizgiler ½ ve 1½ piksel yarıçapı.")}
{hu_tbl}
<p>Kırınım PSF'si geometrik sonuçları doğrular: ikinci-moment RMS yarıçapı ve kare-içi enerji geometrik değerlerle ±1 µm / ±2 puan içinde örtüşür. Blur dengelenmiş küresel sapmayla üretildiği için PSF, eş merkezli girişim halkaları ve eksende parlak bir çekirdek gösterir; bu ince yapı 20 µm piksel içinde integre olur ve tabloda verilen kare-içi enerji ile merkezleme hatası bu yapıyı içerir. Kırınım PSF'siyle hesaplanan sistematik merkezleme hatası geometrik PSF'ye göre yaklaşık 0,01 px daha yüksektir; rapor boyunca temkinli değer olarak bu alınmalıdır.</p>

<h2><span>8</span>Merkezleme performansı</h2>
<p>Yıldız görüntüsü 8 × 8 alt-piksel fazında ızgaraya kaydırılıp 20 µm piksellere bölündü; en parlak piksel etrafındaki 5×5 pencerede ağırlık merkezi hesaplandı ve gerçek merkezle farkı alındı. Gürültü eklenmemiştir; tablo yalnızca PSF şeklinden kaynaklanan sistematik hatayı gösterir.</p>
{fig("startracker_metrics.png","Soldan sağa: kare-içi enerji (1×1, 2×2, 3×3 px) alan boyunca; çevrelenen enerji profili (tüm alanlar üst üste biner); piksel-fazı merkezleme hatası RMS ve maksimum.")}
{cb_tbl}
<p>Aynı simülasyon Huygens (kırınım dâhil) PSF'si ile tekrarlandığında sistematik hata {fmt(max(v['centroid_bias_rms_px'] for v in hu.values()),3)} px RMS'yi aşmaz (Bölüm 7 tablosu); geometrik ve kırınım sonuçları birbirini doğrular.</p>
<div class="key"><p>Keskin referansta aynı simülasyon {fmt(R['centroid_bias_px']['0.00']['rms'],3)} px RMS / {fmt(R['centroid_bias_px']['0.00']['max'],3)} px maks. verir. Farklı merkezleme algoritmaları (Gauss uydurma, eşikli ağırlık merkezi) için hedef blur 15–22 µm arasında yeniden seçilebilir; optimizasyon bunu tek parametreyle destekler.</p></div>

<h2><span>9</span>Odak boyunca davranış</h2>
<p>Blur büyüklüğü odak hatasına duyarsız olacak şekilde optimize edilmiştir. Tablo, görüntü düzlemi nominalden kaydırıldığında polikromatik RMS nokta yarıçapını verir; montajda odak, 3×3 kare-içi enerji ≥ %95 ve 1×1 ≤ %40 kriteriyle ayarlanır.</p>
{fig("through_focus.png","Odak boyunca RMS nokta yarıçapı (sol) ve 25 lp/mm'de MTF (sağ). RMS minimumu bilinçli olarak nominal düzlemin ~50 µm önündedir; nominal düzlem, alan boyunca tekdüzelik ve odak duyarsızlığı için seçilmiştir.")}
{tf_tbl}

<h2><span>10</span>MTF ve dalga cephesi</h2>
<p>MTF, yayılmış PSF tasarımında bilinçli olarak düşüktür ve buradaki rolü görüntü kalitesi ölçütü değil, PSF'nin alan boyunca tekdüzeliğinin doğrulanmasıdır. Dalga cephesi haritaları blur'un ağırlıkla dönel simetrik (küresel + odak) bileşenlerden oluştuğunu, kenar alanda hafif astigmatizma eklendiğini gösterir.</p>
{fig("mtf.png","Polikromatik kırınım MTF'si, tanjantsal (düz) ve sagital (kesikli), 4 alan; gri noktalı çizgi 1,3 µm kırınım sınırı, düşey çizgi 25 lp/mm Nyquist.")}
{fig("wavefront.png","Çıkış gözbebeğinde OPD haritaları, λ = 1,3 µm (birim: dalga).")}
{wf_tbl}

<h2><span>11</span>Alan eğriliği, distorsiyon ve renk</h2>
{fig("field_curv_dist_color.png","Soldan sağa: tanjantsal/sagital paraksiyel odak konumu (görüntü düzlemine göre; nominal düzlem paraksiyel odağın önündedir), kalibre EFL'ye göre distorsiyon, dalga boyuna göre nokta merkezi kayması (yanal renk), paraksiyel kromatik odak kayması.")}
<div class="two">{fc_tbl}{dist_tbl}</div>
<h3>Yanal renk</h3>
<p>Nokta merkezinin 1,3 µm'ye göre kayması (µm). Alanla doğrusaldır ve yıldız rengi bilindiğinde ya da bant geçiren filtreyle 1,1–1,7 µm'ye sınırlandığında kalıntı ≤ {fmt(S['lateral_color_1p1_1p7_um'])} µm ({fmt(S['lateral_color_1p1_1p7_um']/20,2)} px) kalır.</p>
{lc_tbl}
<h3>Kromatik odak kayması</h3>
<p>Paraksiyel odak 0,9→1,7 µm boyunca tek yönlü kayar; bu birincil renk kalıntısı, blur büyüklüğünün dalga boyuyla dengelenmesinin (Bölüm 6) bir parçasıdır ve PSF'nin dalga boyuna göre büyüklüğü tablo 6'da görüldüğü gibi küçük değişir.</p>
{cfs_tbl}

<h2><span>12</span>Aydınlatma ve ana ışın açısı</h2>
{fig("illumination_chief.png","Bağıl aydınlatma (yön kosinüsü uzayında çıkış konisi alanı, eksene göre) ve görüntü düzleminde ana ışın açısı.")}
{ri_tbl}

<h2><span>13</span>Tolerans duyarlılığı</h2>
<p>Yarıçap (+%0,1), kalınlık/hava aralığı (+50 µm) ve eleman kaçıklığı (20 µm) tekil sapmaları. Odak telafi elemanıdır: her sapma sonrası odak, alan-ortalamalı RMS'yi nominal {fmt(S['sensitivity_base_rms_um'])} µm'ye geri getirecek şekilde ayarlanmıştır. Kaçıklık satırlarında ΔRMS blur'un alan boyunca tepe-tepe değişimidir; boresight sütunu eksen yıldızının merkez kaymasıdır.</p>
{sens_tbl}
<p>Yarıçap ve kalınlık hataları yalnızca odak düzeltmesi gerektirir (en hassası E6–düzleştirici aralığı: +50 µm → ≈ −135 µm odak). Kaçıklıklar PSF tekdüzeliğini ≤ 0,5 µm bozar; boresight kaymaları (≤ 17 µm / 20 µm kaçıklık) uçuşta yıldızlarla kalibre edilir, kritik olan ısıl/mekanik kararlılıktır.</p>

<h2><span>14</span>Termal analiz — dört gövde malzemesi</h2>
<p>Homojen sıcaklık değişimi (−40…+70 °C, referans 20 °C) modeli: cam yarıçapları ve kalınlıkları camın kendi genleşme katsayısıyla, hava aralıkları gövde malzemesinin katsayısıyla, flanş–sensör mesafesi (17,526 mm) alüminyum kamera gövdesiyle (23,6·10⁻⁶/K) ölçeklenir; cam indisleri SCHOTT dn/dT dispersiyon formülüyle (D₀…E₁, λ<sub>TK</sub>) ve o sıcaklıktaki hava indisine göre hesaplanır. Odak mekanizması yoktur (sabit odak); tablolar 20 °C'de ayarlanmış objektifin sıcaklıkla davranışını verir.</p>
{th_glass}
{fig("thermal.png","Soldan sağa: sensördeki odak kayması (20 °C'ye göre; gri bant ±50 µm tasarım toleransı), eksen ve kenar alanda polikromatik RMS nokta yarıçapı (gri bant nominal 16–23 µm), eksen/kenar minimum 3×3 piksel kare-içi enerji.")}
{th_tbl}
<h3>Bileşen bütçesi</h3>
<p>Odak kaymasının ve odak uzaklığı değişiminin kaynakları (+50 K için, doğrusal):</p>
{th_budget}
<div class="key"><p><b>Sonuç.</b> Baskın etki camdır: N-PSK53A'nın negatif ve N-KZFS4'ün pozitif dn/dT'si aynı yöne çalışır ve tasarımın yüksek tekil eleman güçleri (E2 f ≈ +32 mm, E3 f ≈ −42 mm) indis değişimini EFL'ye ~4–5 kat büyütür. Gövde genleşmesi ise ters yönde ve zayıf bir kaldıraçtır (10⁻⁶/K başına −1,7 µm). Bu yüzden <b>dört malzemenin hiçbiri tek başına atermal değildir</b> ve sıralama beklentinin tersidir: yüksek genleşmeli alüminyum camın etkisini en çok telafi eder (−60/+55 µm), düşük genleşmeli Invar en kötüsüdür (−106/+93 µm). Atermal davranış için gerekli gövde katsayısı ≈ {fmt(TH['alpha_athermal_1e6'],0) if TH else '—'}·10⁻⁶/K'dir; bu değer metallerin dışında, polimer/kompozit bölgesindedir.</p></div>
<h3>Odak uzaklığı (plaka ölçeği) sürüklenmesi</h3>
<p>EFL sıcaklıkla {fmt(min(d['efl_ppm_per_K'] for d in TH['materials'].values()),0) if TH else '—'}–{fmt(max(d['efl_ppm_per_K'] for d in TH['materials'].values()),0) if TH else '—'} ppm/K değişir (−40 °C'de {fmt(TH['efl_rows'][0]['efl'],3) if TH else '—'} mm, +70 °C'de {fmt(TH['efl_rows'][2]['efl'],3) if TH else '—'} mm). Bu, alan kenarındaki yıldızı ±55 K'da yaklaşık ±0,9 piksel kaydırır; gövde malzemesinden neredeyse bağımsızdır (%95'i camdan gelir). Yıldız izleyicide bu etki sıcaklık ölçümüyle indekslenmiş bir plaka-ölçeği kalibrasyon tablosuyla giderilir; tek sıcaklıkta kalibrasyon yeterli değildir.</p>
<h3>Çözüm seçenekleri</h3>
<p><b>1. Montaj odak ön-ofseti (ek maliyet yok).</b> Objektif 20 °C'de nominal yerine soğuk tarafa doğru ön-ofsetle odaklanırsa −40…+70 °C aralığındaki en kötü PSF küçülür:</p>
{th_bias}
<p><b>2. Pasif atermalizasyon.</b> Metal gövde ile seri çalışan yüksek genleşmeli bir ara parça (spacer) kalan odak kaymasını sıfırlar; gereken uzunluklar (+50 K'da tam telafi, doğrusal):</p>
{th_comp}
<p>Alüminyum gövde ile ≈ 12–13 mm POM ya da ≈ 11 mm PTFE ara parça yeterlidir; bu parça C-mount adaptörü ile mercek tüpü arasına yerleştirilebilir. Polimerlerin genleşme katsayısı sıcaklığa bağlı ve nem hassasiyeti olduğu için ±%20 hata ile bile kalan kayma ±15 µm'yi aşmaz.</p>
<p><b>3. Aktif odak.</b> Motorlu ya da ısıya duyarlı (bimetal) odak ayarı; ±0,1 mm strok yeterlidir. Bu seçenek plaka ölçeği sürüklenmesini gidermez; kalibrasyon tablosu her durumda gerekir.</p>
<p><b>Sınırlamalar:</b> radyal ve eksenel sıcaklık gradyanları, camların ısıl iletim gecikmesi ve kamera gövdesinin gerçek malzemesi/ölçüsü modelde yoktur; kamera flanş–sensör mesafesinin sıcaklıkla değişimi (17,526 mm alüminyum varsayımıyla ±23 µm) üreticiden doğrulanmalıdır.</p>

<h2><span>15</span>Mekanik ve entegrasyon</h2>
<ul>
<li>Toplam uzunluk S1 → görüntü {fmt(misc['track'],1)} mm; flanştan öne ≈ {fmt(misc['track']-17.526,1)} mm; ön eleman çapı ≈ 48 mm (kamera gövdesi 55 × 55 mm ile uyumlu). Arka eleman serbest açıklığı 20,5 mm, arka tepe flanşın {fmt(misc['rear_vertex_to_flange'],2)} mm önünde.</li>
<li>Odaklama: ±0,3 mm ayar (helikoid veya shim); gövde malzemesi ve termal ön-ofset için Bölüm 14. Montaj kriteri: kolimatör/yıldız görüntüsünde 3×3 kare-içi enerji ≥ %95 ve 1×1 ≤ %40 (RMS ≈ 17–18 µm). PSF ±50 µm odak hatasına toleranslıdır.</li>
<li>Gündüz kullanım: derin, siyah anodize güneş siperliği (yarım görüş alanı 6,3°), yivli iç yüzeyler, 0,9–1,7 µm geniş bant AR kaplama (&lt; %0,5); gök fonu için 1,2–1,7 µm (veya 1,4–1,7 µm) bant geçiren filtre. Filtre C-mount içine konursa BFL kalınlığın ≈ ⅓'ü kadar uzar; mevcut {fmt(misc['rear_vertex_to_flange'],2)} mm boşluk ≈ 3 mm filtre için yeterlidir.</li>
<li>Camlar: SCHOTT N-PSK53A, N-KZFS4, N-SF6; 1,7 µm'ye kadar iç geçirgenlik yüksek. Cam kütlesi ≈ {mass_g:.0f} g, alüminyum hücreyle ≈ 450 g (titanyum/çelik/Invar hücre ile 550–650 g).</li>
</ul>

<h2><span>16</span>Sınırlamalar ve sonraki adımlar</h2>
<ul>
<li>Kamera penceresi/soğuk filtre kalınlığı veri sayfasında verilmediği için görüntü uzayı hava kabul edildi; pencere odak ayarıyla telafi edilir.</li>
<li>Sellmeier katsayıları SCHOTT kataloğundandır ve n<sub>d</sub> ile doğrulanmıştır; üretim öncesi eriyik verileriyle yeniden optimizasyon önerilir.</li>
<li>Isıl analiz homojen sıcaklık için yapılmıştır (Bölüm 14); gradyanlar ve geçici rejim ayrı çalışılmalıdır.</li>
<li>Merkezleme simülasyonu gürültüsüz ve basit ağırlık merkeziyle yapılmıştır (geometrik ve Huygens PSF ile); gerçek algoritma ve gök fonu gürültüsü ile uçtan uca SNR/merkezleme bütçesi bir sonraki adımdır.</li>
<li>Hayalet (ghost) ve saçılma analizi yapılmamıştır; gündüz kullanımında güneş açısı bütçesiyle birlikte değerlendirilmelidir.</li>
</ul>
<div class="foot">Tüm analizler depodaki <code>swirlens</code> ışın izleyicisiyle üretilmiştir; sayısal kaynak <code>results/summary.json</code>, <code>results/extra_metrics.json</code>, <code>results/sensitivity.txt</code>. Zemax dosyası <code>results/swir_75mm_f18_cmount.zmx</code>.</div>
</div>
"""
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(html)
    print("wrote", out, f"{os.path.getsize(out)/1e6:.1f} MB")


if __name__ == "__main__":
    build(*(sys.argv[1:3]))
