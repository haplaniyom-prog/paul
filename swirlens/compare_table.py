"""results/zemax_karsilastirma/all_metrics.json -> karsilastirma.md (Zemax sütunları boş).

usage: python -m swirlens.compare_table [outdir]
"""
import os, sys, json

OUT = sys.argv[1] if len(sys.argv) > 1 else "results/zemax_karsilastirma"
STAGES = [("00_baslangic", "Başlangıç (§2 kontrolü)"), ("01_f2.8", "Kademe 1 — f/2.8"),
          ("02_f2.2", "Kademe 2 — f/2.2"), ("03_f1.8", "Kademe 3 — f/1.8"),
          ("04_keskin_referans", "Aşama 4 — keskin referans (yanal renk)"),
          ("05_yildiz_izleyici", "Aşama 5 — yıldız izleyici (18 µm hedef)")]
FIELDS = ["0.00", "3.13", "4.40", "6.24"]


def f(x, d=3):
    return f"{x:.{d}f}"


def main():
    M = json.load(open(os.path.join(OUT, "all_metrics.json")))
    L = ["# Karşılaştırma tablosu — Python ışın izleyici (bu depo) vs Zemax OpticStudio", "",
         "Sütun **Benim** bu depodaki koşudan; **Zemax** sütununu sen doldur. Uzunluklar mm, RMS/renk µm.",
         "Alanlar 0 / 3.13 / 4.40 / 6.24°, dalga boyları 0.9 / 1.1 / 1.3 / 1.55 / 1.7 µm.", ""]
    for tag, title in STAGES:
        if tag not in M:
            continue
        m = M[tag]
        L += [f"## {title}  (`{tag}/`)", "", "| Ölçüt | Benim | Zemax | Fark |", "|---|---|---|---|"]
        L.append(f"| EPD / f/# | {f(m['epd'])} / {f(m['fno'], 2)} | | |")
        L.append(f"| EFL | {f(m['efl'])} | | |")
        L.append(f"| BFL (S13 kalınlığı) | {f(m['bfl'])} | | |")
        L.append(f"| Toplam uzunluk S1→IMA | {f(m['track'], 2)} | | |")
        L.append(f"| Arka tepe → flanş | {f(m['rear_vertex_to_flange'], 2)} | | |")
        L.append(f"| Çıkış gözbebeği (görüntüden) | {f(m['exit_pupil_from_image'], 1)} | | |")
        L.append(f"| Ana ışın açısı, kenar (°) | {f(m['chief_angle_deg'][-1], 2)} | | |")
        rp = m["rms_poly_um"]
        L.append("| RMS nokta yarıçapı polikrom. 0/3.13/4.4/6.24° | " + " / ".join(f(rp[k], 1) for k in FIELDS) + " | | |")
        rl = m["rms_lambda_um"]
        for k in ("0.00", "6.24"):
            L.append(f"| RMS dalga boyuna göre @ {k}° (0.9/1.1/1.3/1.55/1.7) | " + " / ".join(f(v, 1) for v in rl[k]) + " | | |")
        L.append(f"| Yanal renk maks. 1.1–1.7 µm (tümü) | {f(m['lateral_color_um_max_1p1_1p7'], 1)} ({f(m['lateral_color_um_max_all'], 1)}) | | |")
        L.append(f"| Distorsiyon kenar (kalibre EFL) | {f(m['distortion_pct_edge'], 3)} % | | |")
        fc = m["field_curv_um_edge"]
        L.append(f"| Alan eğriliği kenar T / S (paraksiyel odağa göre) | {f(fc['T'], 0)} / {f(fc['S'], 0)} | | |")
        cf = m["chromatic_focal_shift_um"]
        L.append(f"| Kromatik odak kayması 0.9→1.7 µm | {f(cf['min'], 0)} … {f(cf['max'], 0)} | | |")
        e = m["ensquared_1px_2px_3px"]
        L.append("| Kare-içi enerji 1×1/2×2/3×3 px, eksen | " + " / ".join(f"{100*v:.0f} %" for v in e["0.00"]) + " | | |")
        L.append("| Kare-içi enerji 1×1/2×2/3×3 px, 6.24° | " + " / ".join(f"{100*v:.0f} %" for v in e["6.24"]) + " | | |")
        sd = m["semi_diameters"]
        L.append(f"| Yarı-açıklık S1 / S6 (stop) / S12 / S13 | {f(sd[0], 2)} / {f(sd[5], 2)} / {f(sd[11], 2)} / {f(sd[12], 2)} | | |")
        if "centroid_bias_px_rms_max" in m:
            cb = m["centroid_bias_px_rms_max"]
            L.append("| Piksel-fazı merkezleme hatası RMS/maks. (px), 0° / 6.24° | "
                     + f"{cb['0.00'][0]:.3f}/{cb['0.00'][1]:.3f} · {cb['6.24'][0]:.3f}/{cb['6.24'][1]:.3f} | | |")
        if "through_focus" in m:
            tf = m["through_focus"]; dz = tf["dz_um"]; r = tf["rms_um"]
            i = [min(range(len(dz)), key=lambda j: abs(dz[j] - v)) for v in (-50.0, 0.0, 50.0)]
            L.append("| Odak boyunca RMS eksen @ −50/0/+50 µm | " + " / ".join(f(r[j][0], 1) for j in i) + " | | |")
            L.append("| Odak boyunca RMS 6.24° @ −50/0/+50 µm | " + " / ".join(f(r[j][-1], 1) for j in i) + " | | |")
        L.append("")
        # prescription
        L += ["<details><summary>Reçete (benim)</summary>", "", "```",
              open(os.path.join(OUT, tag, "prescription.txt")).read().rstrip(), "```", "</details>", ""]
    open(os.path.join(OUT, "karsilastirma.md"), "w").write("\n".join(L) + "\n")
    print("\n".join(L[:60]))


if __name__ == "__main__":
    main()
