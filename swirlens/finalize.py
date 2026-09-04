"""End-to-end finalisation from a chosen sharp design:
sharp polish (thermal-aware) -> star-tracker blur polish -> all analyses
(final + sharp reference), thermal, ghosts, README tables, HTML report, PDF.

usage: python -m swirlens.finalize <sharp_design.json> [th_weight]
"""
import os, subprocess, sys, shutil

CH = "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell"


def sh(cmd):
    print("+", cmd, flush=True)
    subprocess.run(cmd, shell=True, check=True)


def main(src=None, th="0.25"):
    """src: sharp design to polish from; None = analyse the existing results/design_final.json
    and results/reference_sharp/design_sharp.json without re-optimising."""
    os.makedirs("results/reference_sharp", exist_ok=True)
    if src:
        sh(f"python -m swirlens.polish {src} results/reference_sharp/design_sharp.json lc=4 th={th} efl_th=0.05 thick=0.003 iters=400")
        sh(f"python -m swirlens.polish results/reference_sharp/design_sharp.json results/design_final.json "
           f"lc=4 target=18 shape=0.1 tf=50 th={th} efl_th=0.05 thick=0.003 iters=600")
    sh("python -m swirlens.run_analysis results/design_final.json results --refocus-restore")
    sh("python -m swirlens.run_analysis results/reference_sharp/design_sharp.json results/reference_sharp")
    for f in ("swir_75mm_f18_cmount.zmx", "prescription.csv", "layout.png", "through_focus.png", "rms_vs_field.png", "mtf.png",
              "field_curv_dist_color.png", "wavefront.png", "psf_pixels.png", "illumination_chief.png", "huygens_profiles.png"):
        p = os.path.join("results/reference_sharp", f)
        if os.path.exists(p):
            os.remove(p)
    sh("python -m swirlens.thermal results/design_final.json results")
    sh("python -m swirlens.ghosts results/design_final.json results/ghosts.json")
    sh("python -m swirlens.readme_tables")
    sh("python -m swirlens.make_report results docs/tasarim_raporu.html")
    if os.path.exists(CH):
        sh(f'{CH} --headless=new --no-sandbox --disable-gpu --virtual-time-budget=20000 --print-to-pdf=docs/tasarim_raporu.pdf '
           f'--no-pdf-header-footer "file://{os.path.abspath("docs/tasarim_raporu.html")}" 2>&1 | grep -i written || true')


if __name__ == "__main__":
    main(*(sys.argv[1:3] if len(sys.argv) > 1 else [None]))
