# Karşılaştırma tablosu — Python ışın izleyici (bu depo) vs Zemax OpticStudio

Sütun **Benim** bu depodaki koşudan; **Zemax** sütununu sen doldur. Uzunluklar mm, RMS/renk µm.
Alanlar 0 / 3.13 / 4.40 / 6.24°, dalga boyları 0.9 / 1.1 / 1.3 / 1.55 / 1.7 µm.

## Başlangıç (§2 kontrolü)  (`00_baslangic/`)

| Ölçüt | Benim | Zemax | Fark |
|---|---|---|---|
| EPD / f/# | 41.667 / 1.67 | | |
| EFL | 69.660 | | |
| BFL (S13 kalınlığı) | 20.013 | | |
| Toplam uzunluk S1→IMA | 102.00 | | |
| Arka tepe → flanş | 2.49 | | |
| Çıkış gözbebeği (görüntüden) | -57.0 | | |
| Ana ışın açısı, kenar (°) | 7.93 | | |
| RMS nokta yarıçapı polikrom. 0/3.13/4.4/6.24° | 2003.6 / 2053.1 / 2111.1 / 2234.8 | | |
| RMS dalga boyuna göre @ 0.00° (0.9/1.1/1.3/1.55/1.7) | 2132.9 / 2072.7 / 2022.6 / 1962.8 / 1925.9 | | |
| RMS dalga boyuna göre @ 6.24° (0.9/1.1/1.3/1.55/1.7) | 2366.8 / 2305.3 / 2254.2 / 2193.2 / 2155.7 | | |
| Yanal renk maks. 1.1–1.7 µm (tümü) | 7.4 (12.2) | | |
| Distorsiyon kenar (kalibre EFL) | 0.139 % | | |
| Alan eğriliği kenar T / S (paraksiyel odağa göre) | -3012 / -2482 | | |
| Kromatik odak kayması 0.9→1.7 µm | -389 … 352 | | |
| Kare-içi enerji 1×1/2×2/3×3 px, eksen | 0 % / 0 % / 0 % | | |
| Kare-içi enerji 1×1/2×2/3×3 px, 6.24° | 0 % / 0 % / 0 % | | |
| Yarı-açıklık S1 / S6 (stop) / S12 / S13 | 23.38 / 17.81 / 9.72 / 9.26 | | |

<details><summary>Reçete (benim)</summary>

```
SWIR 75mm f/1.8 C-mount star tracker
EFL 69.660 mm   F/1.67   EPD 41.67 mm   BFL 20.013 mm   toplam uzunluk (S1->görüntü) 102.00 mm
Dalga boyları (µm) / ağırlık: 0.9/0.3, 1.1/0.6, 1.3/1.0, 1.55/1.0, 1.7/0.8
Alanlar (°): (0.0, 3.13, 4.4, 6.24)

Yüzey  Yarıçap (mm)  Kalınlık (mm) Cam         Yarı-çap açıklık (mm)  Not
    1      179.5825         8.0000 N-PSK53A                   23.384  E1 front
    2     -538.7476         1.0000 AIR                        22.679  
    3       89.7913        10.0000 N-PSK53A                   21.772  E2 (cem.)
    4     -300.0000         4.0000 N-KZFS4                    20.245  E3 (cem.)
    5      216.3890         5.0000 AIR                        18.964  
    6           düz         6.0000 AIR                        17.814  DURDURUCU (STOP)
    7     -115.9578         4.0000 N-KZFS4                    17.552  E4 (cem.)
    8      238.0000        10.0000 N-PSK53A                   17.683  E5 (cem.)
    9      -49.1666         2.0000 AIR                        17.811  
   10      224.4782         7.0000 N-PSK53A                   16.540  E6
   11     -359.1651        20.0000 AIR                        15.571  
   12     -149.9976         3.0000 N-SF6                       9.718  E7 field flattener
   13      249.9959        22.0000 AIR                         9.262  
  IMG           düz                                            8.200  görüntü düzlemi (16.4 mm köşegen)
```
</details>

## Kademe 1 — f/2.8  (`01_f2.8/`)

| Ölçüt | Benim | Zemax | Fark |
|---|---|---|---|
| EPD / f/# | 26.786 / 2.80 | | |
| EFL | 75.000 | | |
| BFL (S13 kalınlığı) | 21.344 | | |
| Toplam uzunluk S1→IMA | 110.00 | | |
| Arka tepe → flanş | 3.82 | | |
| Çıkış gözbebeği (görüntüden) | -96.5 | | |
| Ana ışın açısı, kenar (°) | 4.77 | | |
| RMS nokta yarıçapı polikrom. 0/3.13/4.4/6.24° | 30.8 / 19.5 / 16.6 / 38.0 | | |
| RMS dalga boyuna göre @ 0.00° (0.9/1.1/1.3/1.55/1.7) | 9.0 / 17.8 / 25.9 / 35.5 / 41.2 | | |
| RMS dalga boyuna göre @ 6.24° (0.9/1.1/1.3/1.55/1.7) | 56.8 / 46.9 / 39.1 / 30.6 / 25.9 | | |
| Yanal renk maks. 1.1–1.7 µm (tümü) | 4.6 (8.4) | | |
| Distorsiyon kenar (kalibre EFL) | 0.045 % | | |
| Alan eğriliği kenar T / S (paraksiyel odağa göre) | -160 / -44 | | |
| Kromatik odak kayması 0.9→1.7 µm | -162 … 134 | | |
| Kare-içi enerji 1×1/2×2/3×3 px, eksen | 9 % / 32 % / 64 % | | |
| Kare-içi enerji 1×1/2×2/3×3 px, 6.24° | 9 % / 41 % / 66 % | | |
| Yarı-açıklık S1 / S6 (stop) / S12 / S13 | 16.63 / 9.81 / 10.24 / 10.10 | | |

<details><summary>Reçete (benim)</summary>

```
SWIR 75mm f/1.8 C-mount star tracker
EFL 75.000 mm   F/2.80   EPD 26.79 mm   BFL 21.344 mm   toplam uzunluk (S1->görüntü) 110.00 mm
Dalga boyları (µm) / ağırlık: 0.9/0.3, 1.1/0.6, 1.3/1.0, 1.55/1.0, 1.7/0.8
Alanlar (°): (0.0, 3.13, 4.4, 6.24)

Yüzey  Yarıçap (mm)  Kalınlık (mm) Cam         Yarı-çap açıklık (mm)  Not
    1       76.4798         7.7083 N-PSK53A                   16.631  E1 front
    2     1067.9847         0.5002 AIR                        15.722  
    3       60.8382        12.2561 N-PSK53A                   15.173  E2 (cem.)
    4      -61.5370         4.6831 N-KZFS4                    12.979  E3 (cem.)
    5       63.9083         5.9357 AIR                        11.224  
    6           düz         9.6252 AIR                         9.808  DURDURUCU (STOP)
    7      -61.1547         5.3092 N-KZFS4                     9.881  E4 (cem.)
    8       57.0517        13.5458 N-PSK53A                   10.381  E5 (cem.)
    9      -79.9445         1.1437 AIR                        11.198  
   10      117.0096         7.0203 N-PSK53A                   11.262  E6
   11     -502.1501        18.9172 AIR                        11.133  
   12      110.5626         2.3756 N-SF6                      10.236  E7 field flattener
   13      404.6710        20.9801 AIR                        10.101  
  IMG           düz                                            8.200  görüntü düzlemi (16.4 mm köşegen)
```
</details>

## Kademe 2 — f/2.2  (`02_f2.2/`)

| Ölçüt | Benim | Zemax | Fark |
|---|---|---|---|
| EPD / f/# | 34.091 / 2.20 | | |
| EFL | 75.000 | | |
| BFL (S13 kalınlığı) | 20.639 | | |
| Toplam uzunluk S1→IMA | 106.24 | | |
| Arka tepe → flanş | 3.11 | | |
| Çıkış gözbebeği (görüntüden) | -61.2 | | |
| Ana ışın açısı, kenar (°) | 7.59 | | |
| RMS nokta yarıçapı polikrom. 0/3.13/4.4/6.24° | 53.7 / 32.6 / 27.3 / 68.6 | | |
| RMS dalga boyuna göre @ 0.00° (0.9/1.1/1.3/1.55/1.7) | 29.0 / 39.2 / 48.4 / 59.7 / 66.8 | | |
| RMS dalga boyuna göre @ 6.24° (0.9/1.1/1.3/1.55/1.7) | 88.0 / 78.8 / 70.9 / 61.6 / 56.3 | | |
| Yanal renk maks. 1.1–1.7 µm (tümü) | 2.5 (4.7) | | |
| Distorsiyon kenar (kalibre EFL) | 0.116 % | | |
| Alan eğriliği kenar T / S (paraksiyel odağa göre) | -349 / 26 | | |
| Kromatik odak kayması 0.9→1.7 µm | -149 … 138 | | |
| Kare-içi enerji 1×1/2×2/3×3 px, eksen | 1 % / 5 % / 16 % | | |
| Kare-içi enerji 1×1/2×2/3×3 px, 6.24° | 6 % / 16 % / 28 % | | |
| Yarı-açıklık S1 / S6 (stop) / S12 / S13 | 20.80 / 12.39 / 10.23 / 10.01 | | |

<details><summary>Reçete (benim)</summary>

```
SWIR 75mm f/1.8 C-mount star tracker
EFL 75.000 mm   F/2.20   EPD 34.09 mm   BFL 20.639 mm   toplam uzunluk (S1->görüntü) 106.24 mm
Dalga boyları (µm) / ağırlık: 0.9/0.3, 1.1/0.6, 1.3/1.0, 1.55/1.0, 1.7/0.8
Alanlar (°): (0.0, 3.13, 4.4, 6.24)

Yüzey  Yarıçap (mm)  Kalınlık (mm) Cam         Yarı-çap açıklık (mm)  Not
    1       84.6450         8.0069 N-PSK53A                   20.797  E1 front
    2      452.9173         1.8376 AIR                        19.845  
    3       56.5301        12.1903 N-PSK53A                   18.751  E2 (cem.)
    4      -56.6644         4.8600 N-KZFS4                    16.963  E3 (cem.)
    5       77.0605         7.4360 AIR                        14.455  
    6           düz         6.3267 AIR                        12.387  DURDURUCU (STOP)
    7      -52.0576         5.2086 N-KZFS4                    12.104  E4 (cem.)
    8       50.6746        13.1620 N-PSK53A                   12.693  E5 (cem.)
    9      -61.9847         0.5547 AIR                        13.391  
   10       75.9335         6.9957 N-PSK53A                   13.321  E6
   11     -352.9615        17.1393 AIR                        12.872  
   12     -870.8724         2.3646 N-SF6                      10.229  E7 field flattener
   13      206.8682        20.1614 AIR                        10.015  
  IMG           düz                                            8.200  görüntü düzlemi (16.4 mm köşegen)
```
</details>

## Kademe 3 — f/1.8  (`03_f1.8/`)

| Ölçüt | Benim | Zemax | Fark |
|---|---|---|---|
| EPD / f/# | 41.667 / 1.80 | | |
| EFL | 75.000 | | |
| BFL (S13 kalınlığı) | 19.273 | | |
| Toplam uzunluk S1→IMA | 99.01 | | |
| Arka tepe → flanş | 1.75 | | |
| Çıkış gözbebeği (görüntüden) | -44.1 | | |
| Ana ışın açısı, kenar (°) | 10.56 | | |
| RMS nokta yarıçapı polikrom. 0/3.13/4.4/6.24° | 14.6 / 14.1 / 14.8 / 18.2 | | |
| RMS dalga boyuna göre @ 0.00° (0.9/1.1/1.3/1.55/1.7) | 16.8 / 9.1 / 3.1 / 14.6 / 23.3 | | |
| RMS dalga boyuna göre @ 6.24° (0.9/1.1/1.3/1.55/1.7) | 28.8 / 21.6 / 13.1 / 4.2 / 9.4 | | |
| Yanal renk maks. 1.1–1.7 µm (tümü) | 14.4 (23.1) | | |
| Distorsiyon kenar (kalibre EFL) | 0.433 % | | |
| Alan eğriliği kenar T / S (paraksiyel odağa göre) | -49 / -56 | | |
| Kromatik odak kayması 0.9→1.7 µm | -145 … 157 | | |
| Kare-içi enerji 1×1/2×2/3×3 px, eksen | 44 % / 86 % / 100 % | | |
| Kare-içi enerji 1×1/2×2/3×3 px, 6.24° | 43 % / 83 % / 93 % | | |
| Yarı-açıklık S1 / S6 (stop) / S12 / S13 | 26.14 / 13.90 / 10.22 / 10.07 | | |

<details><summary>Reçete (benim)</summary>

```
SWIR 75mm f/1.8 C-mount star tracker
EFL 75.000 mm   F/1.80   EPD 41.67 mm   BFL 19.273 mm   toplam uzunluk (S1->görüntü) 99.01 mm
Dalga boyları (µm) / ağırlık: 0.9/0.3, 1.1/0.6, 1.3/1.0, 1.55/1.0, 1.7/0.8
Alanlar (°): (0.0, 3.13, 4.4, 6.24)

Yüzey  Yarıçap (mm)  Kalınlık (mm) Cam         Yarı-çap açıklık (mm)  Not
    1       63.7261         7.7442 N-PSK53A                   26.141  E1 front
    2      136.9487         2.8808 AIR                        25.102  
    3       45.5751        13.0370 N-PSK53A                   23.282  E2 (cem.)
    4      -55.7234         5.2869 N-KZFS4                    22.574  E3 (cem.)
    5       73.1625        10.4945 AIR                        17.828  
    6           düz         3.6105 AIR                        13.897  DURDURUCU (STOP)
    7      -34.9931         5.1773 N-KZFS4                    13.462  E4 (cem.)
    8       32.7921        10.9117 N-PSK53A                   14.064  E5 (cem.)
    9      -39.6776         1.2428 AIR                        14.496  
   10       56.3208         6.0644 N-PSK53A                   13.928  E6
   11     -113.7945        10.0299 AIR                        13.374  
   12      -32.9901         3.3360 N-SF6                      10.222  E7 field flattener
   13     -202.0446        19.1900 AIR                        10.071  
  IMG           düz                                            8.200  görüntü düzlemi (16.4 mm köşegen)
```
</details>

## Aşama 4 — keskin referans (yanal renk)  (`04_keskin_referans/`)

| Ölçüt | Benim | Zemax | Fark |
|---|---|---|---|
| EPD / f/# | 41.667 / 1.80 | | |
| EFL | 75.000 | | |
| BFL (S13 kalınlığı) | 18.574 | | |
| Toplam uzunluk S1→IMA | 97.85 | | |
| Arka tepe → flanş | 1.05 | | |
| Çıkış gözbebeği (görüntüden) | -45.7 | | |
| Ana ışın açısı, kenar (°) | 10.21 | | |
| RMS nokta yarıçapı polikrom. 0/3.13/4.4/6.24° | 7.0 / 6.8 / 7.5 / 11.0 | | |
| RMS dalga boyuna göre @ 0.00° (0.9/1.1/1.3/1.55/1.7) | 5.3 / 3.5 / 3.1 / 7.3 / 11.2 | | |
| RMS dalga boyuna göre @ 6.24° (0.9/1.1/1.3/1.55/1.7) | 18.9 / 12.8 / 8.2 / 3.9 / 5.2 | | |
| Yanal renk maks. 1.1–1.7 µm (tümü) | 7.2 (14.9) | | |
| Distorsiyon kenar (kalibre EFL) | 0.460 % | | |
| Alan eğriliği kenar T / S (paraksiyel odağa göre) | -73 / -80 | | |
| Kromatik odak kayması 0.9→1.7 µm | -90 … 111 | | |
| Kare-içi enerji 1×1/2×2/3×3 px, eksen | 89 % / 100 % / 100 % | | |
| Kare-içi enerji 1×1/2×2/3×3 px, 6.24° | 75 % / 95 % / 99 % | | |
| Yarı-açıklık S1 / S6 (stop) / S12 / S13 | 24.96 / 14.37 / 10.23 / 10.09 | | |
| Piksel-fazı merkezleme hatası RMS/maks. (px), 0° / 6.24° | 0.138/0.190 · 0.111/0.162 | | |
| Odak boyunca RMS eksen @ −50/0/+50 µm | 13.6 / 6.9 / 10.4 | | |
| Odak boyunca RMS 6.24° @ −50/0/+50 µm | 13.7 / 10.9 / 16.1 | | |

<details><summary>Reçete (benim)</summary>

```
SWIR 75mm f/1.8 C-mount star tracker
EFL 75.000 mm   F/1.80   EPD 41.67 mm   BFL 18.574 mm   toplam uzunluk (S1->görüntü) 97.85 mm
Dalga boyları (µm) / ağırlık: 0.9/0.3, 1.1/0.6, 1.3/1.0, 1.55/1.0, 1.7/0.8
Alanlar (°): (0.0, 3.13, 4.4, 6.24)

Yüzey  Yarıçap (mm)  Kalınlık (mm) Cam         Yarı-çap açıklık (mm)  Not
    1       60.1943         7.1155 N-PSK53A                   24.957  E1 front
    2      167.2769         0.5000 AIR                        24.146  
    3       52.3167        13.8351 N-PSK53A                   22.965  E2 (cem.)
    4      -41.5085         4.7059 N-KZFS4                    22.210  E3 (cem.)
    5       75.3261         8.4305 AIR                        17.313  
    6           düz         3.9244 AIR                        14.367  DURDURUCU (STOP)
    7      -34.0273         4.5376 N-KZFS4                    13.978  E4 (cem.)
    8       36.5175        10.6570 N-PSK53A                   14.906  E5 (cem.)
    9      -41.5181         2.9888 AIR                        15.347  
   10       66.3951         7.4125 N-PSK53A                   14.712  E6
   11      -77.1329        11.2168 AIR                        14.100  
   12      -30.6323         3.9958 N-SF6                      10.232  E7 field flattener
   13     -150.0248        18.5302 AIR                        10.092  
  IMG           düz                                            8.200  görüntü düzlemi (16.4 mm köşegen)
```
</details>

## Aşama 5 — yıldız izleyici (18 µm hedef)  (`05_yildiz_izleyici/`)

| Ölçüt | Benim | Zemax | Fark |
|---|---|---|---|
| EPD / f/# | 41.667 / 1.80 | | |
| EFL | 75.000 | | |
| BFL (S13 kalınlığı) | 18.717 | | |
| Toplam uzunluk S1→IMA | 97.61 | | |
| Arka tepe → flanş | 1.19 | | |
| Çıkış gözbebeği (görüntüden) | -45.6 | | |
| Ana ışın açısı, kenar (°) | 10.19 | | |
| RMS nokta yarıçapı polikrom. 0/3.13/4.4/6.24° | 17.3 / 17.3 / 17.7 / 20.9 | | |
| RMS dalga boyuna göre @ 0.00° (0.9/1.1/1.3/1.55/1.7) | 19.4 / 19.2 / 17.1 / 15.7 / 16.9 | | |
| RMS dalga boyuna göre @ 6.24° (0.9/1.1/1.3/1.55/1.7) | 18.6 / 18.6 / 18.8 / 20.5 / 23.0 | | |
| Yanal renk maks. 1.1–1.7 µm (tümü) | 5.9 (13.3) | | |
| Distorsiyon kenar (kalibre EFL) | 0.361 % | | |
| Alan eğriliği kenar T / S (paraksiyel odağa göre) | 99 / 75 | | |
| Kromatik odak kayması 0.9→1.7 µm | -104 … 122 | | |
| Kare-içi enerji 1×1/2×2/3×3 px, eksen | 40 % / 77 % / 98 % | | |
| Kare-içi enerji 1×1/2×2/3×3 px, 6.24° | 22 % / 64 % / 91 % | | |
| Yarı-açıklık S1 / S6 (stop) / S12 / S13 | 25.06 / 14.30 / 10.23 / 10.11 | | |
| Piksel-fazı merkezleme hatası RMS/maks. (px), 0° / 6.24° | 0.038/0.053 · 0.036/0.056 | | |
| Odak boyunca RMS eksen @ −50/0/+50 µm | 15.1 / 16.5 / 22.7 | | |
| Odak boyunca RMS 6.24° @ −50/0/+50 µm | 20.4 / 21.1 / 26.2 | | |

<details><summary>Reçete (benim)</summary>

```
SWIR 75mm f/1.8 C-mount star tracker
EFL 75.000 mm   F/1.80   EPD 41.67 mm   BFL 18.717 mm   toplam uzunluk (S1->görüntü) 97.61 mm
Dalga boyları (µm) / ağırlık: 0.9/0.3, 1.1/0.6, 1.3/1.0, 1.55/1.0, 1.7/0.8
Alanlar (°): (0.0, 3.13, 4.4, 6.24)

Yüzey  Yarıçap (mm)  Kalınlık (mm) Cam         Yarı-çap açıklık (mm)  Not
    1       50.9698         7.0830 N-PSK53A                   25.062  E1 front
    2      121.4433         0.7252 AIR                        24.261  
    3       56.2958        14.0667 N-PSK53A                   23.226  E2 (cem.)
    4      -39.9248         4.7385 N-KZFS4                    22.441  E3 (cem.)
    5       72.7592         8.5918 AIR                        17.289  
    6           düz         3.9989 AIR                        14.301  DURDURUCU (STOP)
    7      -33.0812         4.0312 N-KZFS4                    13.872  E4 (cem.)
    8       43.5108        10.0246 N-PSK53A                   14.693  E5 (cem.)
    9      -43.9256         2.9386 AIR                        15.193  
   10       58.0332         7.4615 N-PSK53A                   14.797  E6
   11      -70.2708        11.4246 AIR                        14.264  
   12      -29.5253         4.0000 N-SF6                      10.227  E7 field flattener
   13     -128.6336        18.5260 AIR                        10.112  
  IMG           düz                                            8.200  görüntü düzlemi (16.4 mm köşegen)
```
</details>

