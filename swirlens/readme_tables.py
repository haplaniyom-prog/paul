"""Rebuild the data-driven parts of README.md (sections 3-6) from results/."""
import json, re, sys


def build():
    s = json.load(open("results/summary.json")); ref = json.load(open("results/reference_sharp/summary.json"))
    pres = open("results/prescription.txt").read().split("\n")
    rows = [l for l in pres if l[:5].strip().isdigit() or l.startswith("  IMG")]

    def cells(l):
        p = l.split()
        if p[0] == "IMG":
            return ["IMG", "düz", "—", "—", "8.200", "görüntü düzlemi (16,4 mm köşegen)"]
        return [p[0], p[1], p[2], p[3], p[4], " ".join(p[5:]) if len(p) > 5 else ""]
    tbl = ("| Yüzey | Yarıçap (mm) | Kalınlık (mm) | Cam | Yarı-açıklık (mm) | Not |\n|---|---|---|---|---|---|\n"
           + "\n".join("| " + " | ".join(cells(l)) + " |" for l in rows))
    rmsf = s["rms_poly_um"]; rmsr = ref["rms_poly_um"]; r1 = lambda x: f"{x:.1f}"
    E = lambda d, k: " / ".join(f"{v*100:.0f} %" for v in d["ensquared_1px_2px_3px"][k])
    cb = lambda d, k: f"{d['centroid_bias_px'][k]['rms']:.3f} / {d['centroid_bias_px'][k]['max']:.3f} px"
    sens = open("results/sensitivity.txt").read().split("\n"); srows = [l for l in sens[3:] if l.strip()]

    def srow(l):
        name = l[:40].strip(); a, b, c = l[40:].split()
        return f"| {name} | {float(a):+.2f} | {float(b):+.0f} | {float(c):+.1f} |"
    sens_tbl = ("| Sapma | ΔRMS (µm) | Gerekli odak düzeltmesi (µm) | Boresight kayması (µm) |\n|---|---|---|---|\n"
                + "\n".join(srow(l) for l in srows[:12]))
    track = s["track"]; fg = s["rear_vertex_to_flange"]
    tf = s["through_focus"]; import numpy as np
    rms_tf = np.array(tf["rms_um"]); dz = np.array(tf["dz_um"])
    sel = (dz >= -75) & (dz <= 25)
    lam_rms = json.load(open("results/extra_metrics.json")).get("rms_lambda", {})
    hu = json.load(open("results/extra_metrics.json")).get("huygens", {})
    hu_line = ("Huygens düzlem-dalgacık toplamıyla hesaplanan polikromatik kırınım PSF'si geometrik sonucu doğrular: RMS yarıçap "
               + "–".join(f"{min(v['rms_um'] for v in hu.values()):.1f}".split()) + f"–{max(v['rms_um'] for v in hu.values()):.1f} µm, 3×3 piksel enerjisi ≥ {min(v['ee_3px'] for v in hu.values())*100:.0f} %, "
               f"kırınım PSF'siyle sistematik merkezleme hatası ≤ {max(v['centroid_bias_rms_px'] for v in hu.values()):.3f} px RMS (`results/huygens_psf.png`).") if hu else ""
    th = json.load(open("results/thermal.json"))
    Ts = th["Ts"]; i40 = Ts.index(-40); i20 = Ts.index(20); i70 = Ts.index(70)
    th_tbl = ("| Gövde | CTE (10⁻⁶/K) | Odak kayması −40 / +70 °C | RMS eksen −40/20/70 °C | RMS kenar −40/20/70 °C | 3×3 enerji min −40 / +70 °C | EFL ppm/K |\n|---|---|---|---|---|---|---|\n"
              + "\n".join(f"| {n} | {d['cte']} | {d['rows'][i40]['defocus_um']:+.0f} / {d['rows'][i70]['defocus_um']:+.0f} µm | "
                          f"{d['rows'][i40]['rms_um'][0]:.0f} / {d['rows'][i20]['rms_um'][0]:.0f} / {d['rows'][i70]['rms_um'][0]:.0f} µm | "
                          f"{d['rows'][i40]['rms_um'][-1]:.0f} / {d['rows'][i20]['rms_um'][-1]:.0f} / {d['rows'][i70]['rms_um'][-1]:.0f} µm | "
                          f"{min(d['rows'][i40]['ee3'])*100:.0f} % / {min(d['rows'][i70]['ee3'])*100:.0f} % | {d['efl_ppm_per_K']:.0f} |"
                          for n, d in th["materials"].items()))
    lam_txt = " · ".join(f"{l} µm: {v[0]:.0f} / {v[1]:.0f}" for l, v in lam_rms.items()) if lam_rms else ""
    return f"""## 3. Reçete

`results/prescription.txt` · `results/prescription.csv` · `results/swir_75mm_f18_cmount.zmx` (Zemax OpticStudio) · `results/design_final.json`

EFL 75,000 mm · f/1,80 (gerçek giriş demeti çapı 41,67 mm) · BFL {s['bfl']:.3f} mm · toplam uzunluk S1→görüntü {track:.2f} mm · flanştan öne {track-17.526:.1f} mm

{tbl}

Yarı-açıklıklar vinyetlemesiz ışın izlerinden gelen serbest açıklıklardır; mekanik kenar için +0,5–0,8 mm eklenmelidir. Stop (yüzey 6) E4'ün 3,1 mm önünde, camdan bağımsız bir halkadır; çapı gerçek eksenel kenar ışınının 41,67 mm giriş demetiyle geçmesine göre belirlenmiştir.

## 4. Performans özeti

**Nihai tasarım (yıldız izleyici PSF'si)** ile aynı optik formun **keskin referans çözümü** (`results/reference_sharp/`; aynı camlar ve mekanik zarf, blur tasarımının başlangıç noktası) yan yana:

| Ölçüt | Nihai (yayılmış PSF) | Keskin referans | Yıldız izleyici için anlamı |
|---|---|---|---|
| Polikromatik RMS nokta yarıçapı, 0° / 3,1° / 4,7° / 6,24° | {r1(rmsf['0.00'])} / {r1(rmsf['3.12'])} / {r1(rmsf['4.68'])} / {r1(rmsf['6.24'])} µm | {r1(rmsr['0.00'])} / {r1(rmsr['3.12'])} / {r1(rmsr['4.68'])} / {r1(rmsr['6.24'])} µm | hedef 18 µm ≈ σ 0,64 px (FWHM ≈ 1,5 px) |
| Kare-içi enerji 1×1 / 2×2 / 3×3 px, eksen | {E(s,'0.00')} | {E(ref,'0.00')} | enerji 3×3 pencerede, 1×1'de < %40 |
| Kare-içi enerji 1×1 / 2×2 / 3×3 px, 6,24° | {E(s,'6.24')} | {E(ref,'6.24')} | kenarda da aynı dağılım |
| **Sistematik (piksel-fazı) merkezleme hatası**, RMS / maks., eksen | **{cb(s,'0.00')}** | {cb(ref,'0.00')} | 5×5 ağırlık merkezi, gürültüsüz; 0,03 px ≈ 1,7″ |
| Sistematik merkezleme hatası, RMS / maks., 6,24° | {cb(s,'6.24')} | {cb(ref,'6.24')} | |
| PSF şekli ⟨r⁴⟩/⟨r²⟩² | 1,8–2,0 (Gauss = 2) | 2,7–4,0 (çekirdek + hale) | pürüzsüz, yumuşak kenarlı PSF |
| Yanal renk 1,1–1,7 µm (0,9 µm dâhil) maks., kenar | {s['lateral_color_1p1_1p7_um']:.1f} µm ({s['lateral_color_um_max']:.1f} µm) | 4,1 µm ({ref['lateral_color_um_max']:.1f} µm) | yıldız rengine bağlı merkez kayması ≤ 0,16 px, doğrusal |
| Distorsiyon (kalibre EFL'ye göre, maks.) | {s['distortion_pct_max']:.2f} % yastık | {ref['distortion_pct_max']:.2f} % | düzgün; 3. derece radyal polinomla kalibre edilir |
| MTF @ 25 lp/mm (Nyquist), T, eksen → kenar | {s['mtf25']['0.00']['T']:.2f} → {s['mtf25']['6.24']['T']:.2f} | {ref['mtf25']['0.00']['T']:.2f} → {ref['mtf25']['6.24']['T']:.2f} | blur tasarımında bilinçli olarak düşük |
| Bağıl aydınlatma (kenar) | {s['relative_illumination_edge']*100:.1f} % | {ref['relative_illumination_edge']*100:.1f} % | vinyetleme yok |
| Ana ışın açısı (kenar) / çıkış gözbebeği | {s['chief_angle_deg'][-1]:.1f}° / görüntüden {abs(s['exit_pupil_from_image']):.0f} mm önde | aynı | InGaAs FPA için sorunsuz |
| Paraksiyel kromatik odak kayması 0,9→1,7 µm | {s['chromatic_focal_shift_um']['min']:.0f} … +{s['chromatic_focal_shift_um']['max']:.0f} µm | {ref['chromatic_focal_shift_um']['min']:.0f} … +{ref['chromatic_focal_shift_um']['max']:.0f} µm | blur büyüklüğü dalga boyuna göre dengelenmiştir |

**Odak boyunca davranış:** −75 … +25 µm odak kaymasında eksen RMS {rms_tf[sel,0].min():.0f}–{rms_tf[sel,0].max():.0f} µm, kenar {rms_tf[sel,3].min():.0f}–{rms_tf[sel,3].max():.0f} µm arasında kalır (bkz. `results/through_focus.png`).

**Dalga boyuna göre blur (eksen / kenar, RMS µm):** {lam_txt}. PSF büyüklüğü yıldız rengine zayıf bağlıdır; blur salt odak kaydırmayla üretilseydi (±125 µm kromatik odak kayması nedeniyle) bu mümkün olmazdı.

### Grafikler
![yerleşim](results/layout.png)
![nokta](results/spots.png)
![piksel ızgarasında PSF](results/psf_pixels.png)
![Huygens PSF](results/huygens_psf.png)
![Huygens PSF kesitleri](results/huygens_profiles.png)
![yıldız izleyici ölçütleri](results/startracker_metrics.png)
![odak](results/through_focus.png)
![alan-renk](results/field_curv_dist_color.png)
![dalga cephesi](results/wavefront.png)

| | |
|---|---|
| ![RMS](results/rms_vs_field.png) | ![MTF](results/mtf.png) |
| ![aydınlatma](results/illumination_chief.png) | |

Keskin referans çözümün nokta diyagramı ve ölçütleri: `results/reference_sharp/`. Ayrıntılı rapor: `docs/tasarim_raporu.html` / `.pdf`.

### Yorum (yıldız izleyici bakışıyla)
- **Neden 18 µm RMS?** Alt-piksel merkezleme için PSF'nin komşu piksellere yayılması gerekir; Gauss benzeri bir PSF için σ ≈ 0,6–0,7 px (FWHM ≈ 1,5 px), merkezleme hatası ile gök-fonu gürültüsü arasındaki bilinen optimumdur. Keskin referans tasarımda (enerjinin %{ref['ensquared_1px_2px_3px']['0.00'][0]*100:.0f}'i tek pikselde) piksel-fazına bağlı sistematik merkezleme hatası **{ref['centroid_bias_px']['0.00']['rms']:.2f} px RMS** iken nihai tasarımda **{s['centroid_bias_px']['0.00']['rms']:.3f} px**'tir (≈ 4–5 kat iyileşme; kalan kısım alanla yavaş değişir ve kalibre edilebilir).
- **Kırınım dâhil (Huygens PSF):** {hu_line}
- **Blur nasıl üretildi?** Odak kaydırarak değil, optimizasyonla: her alan **ve her dalga boyu** için RMS yarıçapı 18 µm hedeflendi, PSF şekli için ⟨r⁴⟩/⟨r²⟩² = 2 (Gauss) hedefi eklendi ve aynı hedef ±50 µm odak kaymasında da istendi (odak/ısıya duyarsız blur). Sonuç, dengelenmiş küresel sapma + hafif odak kayması ile üretilen, alan boyunca tekdüze bir PSF'dir.
- **Yanal renk** 1,1–1,7 µm'de ≤ {s['lateral_color_1p1_1p7_um']:.1f} µm (kenarda, alanla doğrusal → kalibre edilebilir). 0,9 µm'de {s['lateral_color_um_max']:.0f} µm; gündüz kullanımında bant geçiren filtre bu bölgeyi zaten dışlar.
- **Distorsiyon** %{s['distortion_pct_max']:.2f} yastık ve alanla düzgün → yıldız kataloğu eşleştirmesinde 3. derece radyal modelle kalıntı < 0,05 px beklenir.
- **Boresight kararlılığı:** 20 µm eleman kaçıklığı ≤ 17 µm (0,85 px) boresight kayması verir; mutlak boresight uçuşta yıldızlarla kalibre edildiği için önemli olan ısıl/mekanik kararlılıktır (bkz. §5).

## 5. Tolerans duyarlılığı
`results/sensitivity.txt` — yarıçap (%0,1), kalınlık/hava aralığı (+50 µm) ve eleman kaçıklığı (20 µm)
sapmaları. Odak telafi elemanıdır: her sapma sonrası odak, alan-ortalamalı RMS'yi nominal değerine
geri getirecek şekilde ayarlanmıştır (montajda PSF büyüklüğü zaten odakla ayarlanır). Kaçıklık
satırlarında ΔRMS, blur'un alan boyunca tepe-tepe değişimidir. Tasarım **gevşek toleranslıdır**:
yarıçap/kalınlık hataları yalnızca odak düzeltmesi gerektirir, kaçıklıklar PSF tekdüzeliğini ≤ 0,5 µm bozar.

{sens_tbl}

Boresight sütunu, elemanın 20 µm merkez kaçıklığının eksen üzerindeki yıldız merkezini ne kadar
kaydırdığını gösterir.

## 6. Mekanik / entegrasyon notları
- Toplam uzunluk (S1 tepe → görüntü) {track:.1f} mm; flanştan öne uzunluk ≈ {track-17.526:.1f} mm; ön eleman çapı ~48 mm
  (kamera gövdesi 55 × 55 mm ile uyumlu). Arka eleman serbest açıklığı 20,5 mm, arka tepe flanşın {fg:.2f} mm önünde.
- Odaklama: sonsuz için BFL = {s['bfl']:.3f} mm (FFD 17,526 mm + {fg:.2f} mm). ±0,3 mm odak ayarı (helikoid ya da shim)
  önerilir. Montajda odak, kolimatör/yıldız görüntüsünde 3×3 kare-içi enerji ≥ %95 ve 1×1 ≤ %40 (RMS ≈ 17–18 µm)
  olacak şekilde ayarlanır; en hassas hava aralığı S11 (E6–düzleştirici; +50 µm → −135 µm odak) bu ayarla telafi edilir.
  PSF büyüklüğü ±50 µm odak hatasına toleranslıdır.
- Gündüz kullanım: derin, siyah anodize **güneş siperliği/baffle** (yarım görüş alanı 6,3°), iç yüzeylerde yiv,
  tüm yüzeylerde 0,9–1,7 µm geniş bant AR (< %0,5); gök fonunu bastırmak için **1,2–1,7 µm (veya 1,4–1,7 µm)
  bant geçiren filtre**. Filtre C-mount içine konursa BFL filtre kalınlığının ~⅓'ü kadar uzar; {fg:.2f} mm boşluk
  ~3 mm filtre için yeterlidir (odak ayarı ile).
- Merkezleme için sıkı hassasiyet gerekmez: 20 µm eleman kaçıklığı PSF tekdüzeliğini ≤ 0,5 µm bozar.
- Kütle (cam, katalog yoğunlukları): ≈ {th['glass_mass_g']:.0f} g; alüminyum hücre ve C-mount arayüzü ile ≈ 450 g.

### Termal analiz (dört gövde malzemesi)
`python -m swirlens.thermal` → `results/thermal.png`, `results/thermal.json`. Homojen sıcaklık, −40…+70 °C, sabit odak;
cam indisleri SCHOTT dn/dT modeli, cam ve gövde genleşmesi, alüminyum kamera gövdesi (flanş→sensör).

![termal](results/thermal.png)

{th_tbl}

- Atermal gövde katsayısı ≈ {th['alpha_athermal_1e6']:.0f}·10⁻⁶/K; en iyi metal gövde tablodaki en küçük odak kaymasını verendir.
- Plaka ölçeği (EFL) {min(d['efl_ppm_per_K'] for d in th['materials'].values()):.0f}–{max(d['efl_ppm_per_K'] for d in th['materials'].values()):.0f} ppm/K sürüklenir (kenarda ±0,9 px / ±55 K) → sıcaklık indeksli kalibrasyon tablosu gerekir.
- Çözümler: montajda soğuk tarafa odak ön-ofseti (Al gövde: {th['focus_bias_opt']['Alüminyum 6061']['bias_um']:+.0f} µm → en kötü RMS {th['focus_bias_opt']['Alüminyum 6061']['worst_rms_um']:.0f} µm),
  ya da Al gövde ile seri ≈ {th['compensator_spacer_mm']['Alüminyum 6061']['POM (110e-6/K)']:.0f} mm POM / ≈ {th['compensator_spacer_mm']['Alüminyum 6061']['PTFE (120e-6/K)']:.0f} mm PTFE telafi ara parçası (pasif atermalizasyon), ya da aktif odak. Ayrıntı: `docs/tasarim_raporu.html` §14.

"""


if __name__ == "__main__":
    p = "README.md"; r = open(p).read()
    a = r.index("## 3. Reçete"); b = r.index("## 7. Kodun kullanımı")
    open(p, "w").write(r[:a] + build() + r[b:])
    print("README sections 3-6 rebuilt")
