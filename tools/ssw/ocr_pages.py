#!/usr/bin/env python3
"""OCR (tesseract jpn) halaman scan buku Jepang untuk bidang tanpa PDF teks -> tools/ssw/src/ocr/pages/<slug>-pNN.txt (dilewati bila sudah ada)."""
import glob, io, os, subprocess, sys
from multiprocessing import Pool
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
OUT = "tools/ssw/src/ocr/pages"; os.makedirs(OUT, exist_ok=True)
def job(f):
    s = f.split("/")[2]; o = f"{OUT}/{s}-{os.path.basename(f)[:-5]}.txt"
    if os.path.exists(o) and os.path.getsize(o): return
    b = io.BytesIO(); Image.open(f).convert("L").save(b, "PNG")
    t = subprocess.run(["tesseract", "stdin", "stdout", "-l", "jpn", "--psm", "6"], input=b.getvalue(), capture_output=True).stdout
    open(o, "wb").write(t)
if __name__ == "__main__":
    files = [f for s in sys.argv[1:] for f in sorted(glob.glob(f"assets/ssw/{s}/jp/*.webp"))]
    with Pool(4) as p: p.map(job, files)
    print(len(files), "halaman")
