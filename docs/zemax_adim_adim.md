# Zemax OpticStudio ile adım adım: 640 × 512 / 20 µm kamera için yıldız izleyici objektifi

Bu kılavuz, `results/zemax_karsilastirma/` altındaki arka-plan tasarım koşusuyla **birebir aynı**
adımları Zemax OpticStudio'da (sequential mod) elle uygulamak için yazıldı. Her aşamanın sonunda
benim ışın izleyicimin verdiği değerler `results/zemax_karsilastirma/karsilastirma.md` tablosunda;
Zemax'te okuduğun değerleri aynı tablonun boş sütununa yaz, sonda karşılaştıralım.

> **Numara/harf uyarısı:** Zemax'te ondalık ayırıcı Windows bölgesel ayarına bağlıdır. Aşağıdaki
> tüm sayılar nokta (`.`) ile yazıldı.

---

## 0. Gereksinimler (kabuller)

Kamera dışında bir şey söylemediğin için depodaki önceki çalışmanın kabullerini aynen aldım.
Farklı bir bant / odak uzaklığı istersen §1'deki üç girdiyi değiştirmek yeterli; akış aynı kalır.

| Parametre | Değer | Neden |
|---|---|---|
| Dedektör | 640 × 512, 20 µm → 12.8 × 10.24 mm, köşegen **16.4 mm**, yarı-köşegen 8.2 mm | verilen kamera (InGaAs Wildcat 640 sınıfı) |
| Spektral bant | 0.9 – 1.7 µm (SWIR) | 20 µm / 640×512 formatı InGaAs'a özgüdür; gündüz yıldız izleme için SWIR |
| EFL | **75 mm** → 9.75° × 7.81°, köşegen 12.5°, ölçek 55″/px | gündüz için dar alan + yüksek plaka ölçeği |
| Diyafram | **f/1.8**, EPD = 75/1.8 = **41.6667 mm** | gök-fonu sınırlı çalışmada ışık toplama |
| Arayüz | C-mount: FFD 17.526 mm, arka eleman ≤ 20.5 mm serbest açıklık | kamera gövdesi |
| Hedef PSF | **RMS nokta yarıçapı 18 µm** (σ ≈ 0.64 px, FWHM ≈ 1.5 px), Gauss benzeri, alan/dalga boyu boyunca tekdüze | alt-piksel merkezleme (centroiding) optimumu |
| Yanal renk | küçük ve doğrusal (≤ ~0.2 px) | yıldız rengine bağlı astrometrik sapma |
| Optik form | Petzval türevi 7 eleman / 5 grup, tüm yüzeyler küresel | C-mount içinden geçen küçük arka grup + alan düzleştirici |
| Camlar | N-PSK53A (pozitifler), N-KZFS4 (negatif dublet üyeleri), N-SF6 (alan düzleştirici) | SWIR'de kısmi dispersiyonları eşit çift (ikincil spektrum ≈ 0) |

---

## 1. System Explorer ayarları

1. **Units:** Lens units = Millimeters.
2. **Aperture:** Aperture Type = *Entrance Pupil Diameter*. Değer aşamaya göre değişecek
   (§4): başlangıçta **26.7857** (f/2.8). *Ray Aiming* = **Real** (benim izleyicim gerçek kenar
   ışınını stop kenarına nişanlıyor; Paraxial seçersen stop çapı biraz farklı çıkar).
   Apodization = Uniform.
3. **Fields:** Field Type = *Angle (deg)*, Normalization = Radial. Dört alan, hepsi Y ekseninde:

   | # | X | Y (°) | Weight |
   |---|---|---|---|
   | 1 | 0 | 0.00 | 1 |
   | 2 | 0 | 3.13 | 1 |
   | 3 | 0 | 4.40 | 1 |
   | 4 | 0 | 6.24 | 1 |

   (3.13° ≈ yarı-yükseklik 4.1 mm, 4.40° ≈ 5.8 mm, 6.24° ≈ köşe 8.2 mm.) Vinyetleme faktörlerine dokunma (0).
4. **Wavelengths** (µm / ağırlık): 0.900 / 0.3 · 1.100 / 0.6 · **1.300 / 1.0 (Primary)** · 1.550 / 1.0 · 1.700 / 0.8.
5. **Environment:** 20 °C, 1 atm (kataloğa göre havada indis; benim izleyicim mutlak yerine kataloğun hava-bağıl indisini kullanır, aynı).
6. **Material Catalogs:** SCHOTT işaretli olsun.
7. **Advanced:** Reference OPD = Exit Pupil (yalnızca dalga cephesi analizinde önemli).

---

## 2. Lens Data Editor — başlangıç reçetesi

Aşağıdaki başlangıç, form/güç dağılımı elle kurulmuş **kaba** bir Petzval'dır; performansı önemsiz
(RMS ~2 mm!), tek amacı optimizatöre doğru topolojiyi vermektir. Yüzey 6 **STOP** (Make Surface Stop).
Yarı-açıklıkları *Automatic* bırak.

| Yüzey | Yarıçap (mm) | Kalınlık (mm) | Cam | Not |
|---|---|---|---|---|
| OBJ | ∞ | ∞ | | |
| 1 | 179.5825 | 8.0 | N-PSK53A | E1 |
| 2 | −538.7476 | 1.0 | | |
| 3 | 89.7913 | 10.0 | N-PSK53A | E2 (yapıştırılmış) |
| 4 | −300.0000 | 4.0 | N-KZFS4 | E3 (yapıştırılmış) |
| 5 | 216.3890 | 5.0 | | |
| **6** | ∞ | 6.0 | | **STOP** |
| 7 | −115.9578 | 4.0 | N-KZFS4 | E4 (yapıştırılmış) |
| 8 | 238.0000 | 10.0 | N-PSK53A | E5 (yapıştırılmış) |
| 9 | −49.1666 | 2.0 | | |
| 10 | 224.4782 | 7.0 | N-PSK53A | E6 |
| 11 | −359.1651 | 20.0 | | |
| 12 | −149.9976 | 3.0 | N-SF6 | E7 alan düzleştirici |
| 13 | 249.9959 | 22.0 | | (BFL) |
| IMA | ∞ | — | | |

Aynı reçete hazır dosya olarak `results/zemax_karsilastirma/00_baslangic/00_baslangic.zmx` içinde
(File → Open ile doğrudan açabilirsin; sistem ayarları da içindedir).

**Kontrol (EPD 41.667 iken, Prescription Data / System Data):** EFL = **69.660 mm**, BFL = **20.013 mm**,
toplam uzunluk 102.00 mm, paraksiyel çıkış gözbebeği görüntüden 56.95 mm önde. Bu üçü tutuyorsa
reçete doğru girilmiştir (spot değerlerine bakma, anlamsız derecede büyük).

---

## 3. Değişkenler

- Yüzey 1–5 ve 7–13'ün **yarıçapları** değişken (V) — stop (6) düz kalır → 12 eğrilik.
- **Tüm kalınlıklar** değişken (1–13; 13 = BFL) → 13 kalınlık. Cam kalınlıkları da değişken.
- Toplam 25 değişken. Yüzey 13 için *Marginal Ray Height* solve kullanma; BFL doğrudan değişken,
  odak merit fonksiyonundan çıkıyor (blur aşamasında bu önemli: paraksiyel odak ≠ en iyi odak).

Benim tarafımda değişkenlere sınır kutusu da var; Zemax'te sınırlar merit fonksiyonundaki
CVGT/CVLT/MNCT/MXCT satırlarıyla verilir (§4.2).

---

## 4. Merit fonksiyonu ve aşamalı optimizasyon (keskin tasarım)

Optimizasyonu doğrudan f/1.8'de başlatma; başlangıç kaba olduğu için ışınlar kaçırır (ray failure).
Ben üç kademede açtım: **f/2.8 → f/2.2 → f/1.8**. Her kademede yalnızca System Explorer'daki EPD
değişir, merit fonksiyonu aynı kalır.

### 4.1 Optimization Wizard (varsayılan kısım)

Merit Function Editor → Optimization Wizard:

- Criterion = **Spot**, Reference = **Centroid**, Type = **RMS**, *Radius*.
- Pupil Integration = **Rectangular Array**, **20 × 20** (benim ızgaram 21 × 21 kare ızgaranın
  daireye kırpılmışı; Gaussian Quadrature 3 halka × 6 kol kaba blur'da %5–10 farklı RMS verir).
- Fields: All, Wavelengths: All, "Assume Axial Symmetry" işaretli.
- Boundary values (ışın-kaçırma ve kenar kalınlığı için): Glass **Min 2.0, Max 16.0, Edge 1.0**;
  Air **Min 0.5, Max 60.0, Edge 0.5**. (Wizard bunları MNCG/MXCG/MNEG, MNCA/MXCA/MNEA olarak ekler.)
- Start At: 1, Overall weight 1.

Sonra **alan 4'ün (6.24°) ağırlığını 0.8**'e çek: kolay yolu System Explorer → Fields → Weight = 0.8
(wizard alan ağırlığını spot operandlarına taşır). Keskin referans aşamasında (§5) tekrar 1.0 yapılır.

### 4.2 Elle eklenen operandlar (wizard satırlarının üstüne)

Benim merit fonksiyonumda artık (residual) `k·(değer − hedef)` şeklinde; Zemax'te ağırlık kareye
girdiği için **Zemax ağırlığı = k²**. Aşağıda buna göre verildi.

| Operand | Parametreler | Target | Weight | Anlamı |
|---|---|---|---|---|
| EFFL | Wave 3 | 75.0 | 4 | odak uzaklığı (k = 2) |
| CTGT | Surf 13 | 18.526 | 25 | BFL ≥ FFD + 1 mm → arka tepe flanşın ≥ 1 mm önünde (k = 5) |
| TTHI | Surf 12 → 13 | — | 0 | S12 tepesi → görüntü mesafesi (yalnızca hesaplar) |
| OPGT | önceki satır | 22.526 | 25 | düzleştirici önündeki eleman flanşın ≥ 5 mm önünde |
| DMLT | Surf 12 | 20.5 | 25 | arka eleman C-mount boğazından geçsin (∅ ≤ 20.5 mm) |
| DMLT | Surf 13 | 20.5 | 25 | aynı |
| TOTR | — | — | 0 | toplam uzunluk (hesaplar) |
| OPLT | önceki satır | 110.0 | 1 | S1 → görüntü ≤ 110 mm |
| RAID | Surf 14 (IMA), Wave 3, Hx 0, Hy 1, Px 0, Py 0 | — | 0 | kenar alan ana ışın açısı (°) |
| OPLT | önceki satır | 16.0 | 0.0025 | ana ışın açısı ≤ 16° (k = 0.05) |
| CVGT / CVLT | Surf 1–5 | ∓0.04545 | 1 | eğrilik |c| ≤ 1/22 mm⁻¹ (ön grup) |
| CVGT / CVLT | Surf 7–13 | ∓0.07143 | 1 | eğrilik |c| ≤ 1/14 mm⁻¹ (arka grup) |

Notlar:
- CTGT/OPGT/OPLT/DMLT tek taraflı sınırlar: hedef aşılmadıkça sıfır katkı verir; benim kısıtlarım da
  böyle (max(0, ·)).
- Stop halkasının camdan boşluğu (S5→S6 ve S6→S7 kenar aralığı ≥ 0.5 mm) wizard'ın MNEA satırıyla
  zaten sağlanıyor; stop yüzeyinin çapı benim tarafımda gerçek eksenel kenar ışınından hesaplanıyor,
  Zemax'te Ray Aiming = Real ile aynı.

### 4.3 Kademeler

| Kademe | EPD (mm) | f/# | Optimize | Benim koşum |
|---|---|---|---|---|
| 1 | 26.7857 | 2.8 | Local (DLS), Automatic, ≈150 döngü | `01_f2.8/` |
| 2 | 34.0909 | 2.2 | Automatic | `02_f2.2/` |
| 3 | 41.6667 | 1.8 | Automatic (uzun; 250 döngü) | `03_f1.8/` |

Her kademe sonunda **Prescription Data** (EFL, BFL, TOTR), **Spot Diagram** (RMS radius, centroid,
Rectangular 20×20, tüm dalga boyları) değerlerini tabloya yaz. Merit değerini kıyaslama: benim
artık ölçeğim Zemax'inkinden farklı; **RMS nokta yarıçapları, EFL/BFL, ana ışın açısı ve yarı-açıklıklar**
kıyaslanır.

Zemax'in DLS'i ile SciPy TRF'nin **aynı başlangıçtan farklı bir yerel minimuma** inmesi normaldir:
yarıçaplar birebir tutmayacak; RMS değerlerinin ±%20 içinde, EFL/BFL/açıklıkların ±%1 içinde
olması "aynı tasarım bölgesi" demektir. Kademe 3'te Zemax daha kötüde kalırsa bir kez
**Hammer** (5–10 dk) çalıştır.

---

## 5. Keskin referans: yanal renk terimi (aşama 4)

Yıldız rengi merkez kaymasını kontrol etmek için her alanda her dalga boyunun merkezini
polikromatik merkeze çeken bir terim eklenir (benim `lc_weight = 3.0`). Alan 4 ağırlığı → 1.0.

Zemax'te en yakın karşılık, **CENY** farkları:

```
CENY  Surf 14  Wave 0 (polikromatik)  Hx 0  Hy h   Samp 3        weight 0   -> satır A_h
CENY  Surf 14  Wave i                 Hx 0  Hy h   Samp 3        weight 0   -> satır B_hi
DIFF  A_h  B_hi                                   target 0   weight 9·w_i/3.7
```

(w_i dalga boyu ağırlığı; Σw = 3.7. Hy: 0, 0.5016, 0.7051, 1.0 = 3.13/6.24 vb.) Alan 1'de yanal
renk sıfırdır, o alanı atlayabilirsin → 3 alan × 5 dalga = 15 DIFF satırı. CENY'nin Wave 0
seçeneği sürümünde yoksa, referans olarak Wave 3 (1.3 µm) kullan; sonuç neredeyse aynıdır.
Alternatif: **LACL** operandı (iki dalga boyu arasında ana-ışın yanal rengi) — merkez yerine ana ışın
kullanır, blur büyük olduğunda biraz farklı çıkar.

Optimize (Automatic). Bu tasarım "keskin referans"tır (`04_keskin_referans/`): kendi içinde iyi bir
SWIR objektiftir ama yıldız izleyici için PSF fazla dardır (enerjinin ~%80'i tek pikselde → piksel-fazı
merkezleme hatası 0.1–0.15 px).

---

## 6. Yıldız izleyici PSF'si: hedef-RMS optimizasyonu (aşama 5)

Amaç, blur'u **odak kaydırarak değil optimizasyonla** üretmek: her alan **ve** her dalga boyunda RMS
yarıçapı 18 µm, PSF Gauss benzeri, ±50 µm odak kaymasında da aynı.

### 6.1 Spot satırlarını değiştir
Wizard'ın ürettiği spot (TRAC/TRAR…) satırlarını **sil**; yerine 4 alan × 5 dalga boyu için:

```
RSCE  Samp 3 (veya 4)  Wave i  Hx 0  Hy h       target 0.018   weight 9·w_f·w_i/3.7
```

RSCE = merkeze göre RMS nokta yarıçapı (mm). w_f = 1 (dört alan da), w_i = dalga boyu ağırlığı.
Bu 20 satır tasarımı "hedef büyüklükte blur"a çeker; EFFL/CTGT/DMLT/… kısıt satırları ve §5'teki
yanal renk satırları kalır.

### 6.2 Gauss şekli
Benim merit'teki ⟨r⁴⟩/⟨r²⟩² = 2 (Gauss basıklığı) terimi için Zemax operandı yok; en yakın karşılık
geometrik çevrelenen enerji **GENC** (verilen enerji kesrini çevreleyen yarıçapı döndürür): Gauss PSF
için enerjinin %63'ü r = r_RMS içinde, %94'ü r = 1.67·r_RMS içindedir.

```
GENC  Samp 3  Wave 0  Hx 0  Hy h  Type 1 (encircled)  Fract 0.63   target 0.018   weight 0.1
GENC  Samp 3  Wave 0  Hx 0  Hy h  Type 1              Fract 0.94   target 0.030   weight 0.05
```
(4 alan × 2 = 8 satır; düşük ağırlık — yalnızca çekirdek+hale çözümlerini caydırmak için. Keskin
çekirdek + geniş hale PSF'de %63 yarıçapı hedefin çok altında, %94 yarıçapı çok üstünde çıkar.)

### 6.3 Odak duyarsızlığı (±50 µm)
**Multi-Configuration Editor:** operand `THIC` yüzey 13; Config 1 = nominal (BFL), Config 2 = BFL − 0.050,
Config 3 = BFL + 0.050. Config 2–3'ün THIC değerleri Config 1'e *pick-up* + offset (∓0.050) olsun ki
BFL değişkeni tek kalsın. Merit fonksiyonunda `CONF 2` ve `CONF 3` satırlarının altına aynı 20 RSCE
satırını **weight × 0.49** (k = 0.7) ile kopyala; kısıt satırları yalnızca Config 1 altında kalsın.

### 6.4 Optimize
Local (DLS) Automatic; tipik 100–400 döngü. Hedef: bütün RSCE değerleri 0.017–0.019 mm bandında,
EFL 75.000, BFL ≥ 18.526, DMLT sınırlarında.

---

## 7. Kaydedilecek analizler (son iki aşama için)

| Zemax penceresi | Ayar | Okunan değer |
|---|---|---|
| Prescription Data / System Data | — | EFL, BFL, TOTR, çıkış gözbebeği konumu |
| Spot Diagram | Rectangular 20×20, ref. Centroid, tüm dalga boyları | RMS radius her alanda (polikromatik); Wave tek seçilerek dalga boyu başına RMS |
| Geometric Encircled Energy → Ensquared | Wave All, alan başına | 20 / 40 / 60 µm kenarlı karede enerji (1×1, 2×2, 3×3 px) |
| Lateral Color | Wave 1.1–1.7 (ve 0.9) | kenarda maks. yanal renk (µm) |
| Field Curvature / Distortion | Wave 3 | kenar distorsiyon (%) — Zemax paraksiyel EFL'ye göre verir, benim tablom kalibre EFL'ye göre; ~%0.1 fark normal |
| Chromatic Focal Shift | — | 0.9→1.7 µm paraksiyel odak kayması |
| Ray Trace (Single Ray) | Hy 1, Px=Py=0, yüzey 14 | ana ışın açısı (°) |
| Through Focus Spot Diagram | ±100 µm, 25 µm adım | odak boyunca RMS (blur kararlılığı) |
| Huygens PSF | 64×64, Image Delta 1 µm, Wave All | kırınım dâhil PSF (isteğe bağlı) |
| Relative Illumination | — | kenar aydınlatma |

Yarı-açıklıkları (Automatic) da not et: bu tasarımda arka iki yüzeyin ≤ 10.25 mm olması C-mount
kısıtının sağlandığını gösterir.

---

## 8. Karşılaştırma

`results/zemax_karsilastirma/karsilastirma.md` dosyasındaki tabloya Zemax değerlerini yaz.
Beklenen uyum:

- **Başlangıç kontrolü (§2)**: EFL/BFL 4 haneye kadar aynı (aynı cam formülü, aynı geometri).
- **Kademe 1–3**: farklı yerel minimum olabilir; RMS ±%20, EFL/BFL/TOTR ±%1, yarı-açıklıklar ±0.3 mm.
- **Keskin referans**: RMS 7–11 µm, yanal renk 1.1–1.7 µm ≤ ~8 µm, distorsiyon < %0.5 her ikisinde de.
- **Yıldız izleyici**: RSCE 17–21 µm her alan/dalga boyunda; 3×3 kare-içi enerji ≥ %90; 1×1 ≤ %40;
  piksel-fazı merkezleme hatası ≤ 0.05 px RMS (keskin referansta 0.11–0.14 px).
  Bu bölgede iki program aynı sayıları vermelidir, çünkü hedef-RMS optimizasyonu çözümü "kilitler".
  Benim koşumda eksen/ara alanlar 17.1–17.7 µm'de kilitlendi, **kenar alan 20.7 µm'de kaldı**
  (1.55/1.7 µm'de 21–24 µm; ikinci ve üçüncü optimizasyon turu değiştirmedi → yerel minimum).
  Kenar alanın ağırlığını 2'ye çıkarmak yalnızca 19.9 µm'ye indiriyor; depodaki nihai tasarım
  (`results/design_final.json`, farklı bir keskin başlangıçtan gelir) her alanda 18.2 µm'ye ulaşıyor.
  Zemax'te kenar alan 20 µm'nin üstünde kalırsa: Hammer (5–10 dk) ya da 6.24° RSCE satırlarının
  ağırlığını 2× yap; ikisi de sonucu değiştirmezse o senin çözümün de aynı yerel minimumdadır —
  karşılaştırma açısından bu da bilgidir.

Bulunacak farkların olası nedenleri: (1) örnekleme (20×20 rectangular vs 21×21 kırpılmış ızgara);
(2) Zemax'in Ray Aiming ayarı; (3) distorsiyon referansı (paraksiyel EFL vs kalibre EFL);
(4) DLS vs TRF yerel minimum farkı (yalnızca 1–3. kademelerde).

Karşılaştırma sonunda Zemax çözümünü `.zmx` olarak `results/zemax_karsilastirma/zemax/` altına
koyarsan aynı ölçütleri benim izleyicimle de hesaplayıp (aynı örnekleme ile) fark tablosu üretebilirim.
