#!/usr/bin/env python3
"""Tahap 2 panen kosakata (jalankan SETELAH vocab_harvest.py).
(1) Potongan frasa berfurigana yang tidak ada di kamus dipecah jadi kata kamus (cocok-terpanjang).
(2) Teks PDF materi/ujian tiap bidang (assets/ssw/<slug>/pdf; dokumen administrasi docs-resmi tidak dipakai), kata muncul >=2x, kata JLPT N5-N3 dilewati via pdftotext; PDF hasil scan via OCR tesseract (jpn), teks OCR disimpan di tools/ssw/src/ocr/.
Hanya kata yang ada di kamus (website / JPdict) yang masuk; idempoten (sumber 'panen-pdf')."""
import json, re, os, glob, subprocess
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
KAN = r"[一-鿿々]"
RUBY = re.compile(r"\{([^|{}]+)\|([^{}|]+)\}")
def items(p):
    v = json.load(open(p))
    if isinstance(v, dict): v = v.get("items", v)
    return v if isinstance(v, list) else []
D, K = {}, {}
for f in sorted(glob.glob("data/kosakata-*.json")) + sorted(glob.glob("data/ssw/*/vocab.json")):
    for x in items(f):
        if x.get("sumber") in ("panen-teks", "panen-pdf"): continue
        if x.get("kata") and x.get("arti") and x.get("kana"): D.setdefault(x["kata"], x["arti"]); K.setdefault(x["kata"], x["kana"])
JPD = json.load(open(os.environ.get("JPDICT", "/home/claude/jpdict/jpdict_min.json")))
BASIC = {x["kata"] for f in ("data/kosakata-n5.json","data/kosakata-n4.json","data/kosakata-n3.json") for x in items(f)}
W = {k for k in set(D) | set(JPD) if re.search(KAN, k) and 2 <= len(k) <= 10}
def lookup(k):
    if k in D: return K[k], D[k], "kamus website"
    if k in JPD: return JPD[k][0], JPD[k][1], "JPdict (lawlie/dom, terjemahan AI)"
def segment(run):
    out, i = [], 0
    while i < len(run):
        for L in range(min(10, len(run) - i), 1, -1):
            if run[i:i + L] in W: out.append(run[i:i + L]); i += L; break
        else: i += 1
    return out
RUN = re.compile(r"[一-鿿々゠-ヿー]{2,}")
def pdf_text(p):
    t = subprocess.run(["pdftotext", "-q", p, "-"], capture_output=True, text=True).stdout
    if len(re.findall(KAN, t)) >= 50: return t
    o = f"tools/ssw/src/ocr/{os.path.basename(p)}.txt"
    if not os.path.exists(o):
        os.makedirs(os.path.dirname(o), exist_ok=True); tmp = "/tmp/ocrpg"; os.makedirs(tmp, exist_ok=True)
        for f in glob.glob(tmp + "/*"): os.remove(f)
        subprocess.run(["pdftoppm", "-r", "200", "-gray", "-png", "-l", "40", p, tmp + "/p"], capture_output=True)
        txt = "".join(subprocess.run(["tesseract", f, "-", "-l", "jpn", "--psm", "6"], capture_output=True, text=True).stdout for f in sorted(glob.glob(tmp + "/*.png")))
        open(o, "w").write(txt)
    return open(o).read()
tot = 0
for s in sorted(os.listdir("data/ssw")):
    d = f"data/ssw/{s}"
    if not os.path.exists(f"{d}/index.json"): continue
    P = f"{d}/vocab.json"; V = json.load(open(P)); L = V["items"] if isinstance(V, dict) else V
    L[:] = [x for x in L if x.get("sumber") != "panen-pdf"]
    have = {x["kata"] for x in L}
    idx = json.load(open(f"{d}/index.json")); first = idx["bab"][0]["id"]
    cand = {}
    for b in idx["bab"]:
        raw = open(f"{d}/{b['file']}").read()
        for k, r in RUBY.findall(raw):
            if re.fullmatch(KAN + "+", k) and k not in have and not lookup(k):
                for w in segment(k):
                    if w not in BASIC: cand.setdefault(w, (b["id"], "frasa"))
    pdfs = glob.glob(f"assets/ssw/{s}/pdf/*.pdf")
    from collections import Counter
    cnt = Counter(w for p in pdfs for run in RUN.findall(pdf_text(p)) for w in segment(run))
    for w, c in cnt.items():
        if c >= 2 and w not in BASIC: cand.setdefault(w, (first, "pdf"))
    # OCR halaman scan buku (tools/ssw/ocr_pages.py): lebih ketat karena salah baca OCR -> >=3x, tanpa huruf kembar (人人), bukan scan dokumen administrasi
    if os.environ.get("OCR_PAGES") == "1" and s not in ("logistics", "recycling"):   # default MATI: hasil kecil & banyak salah baca (teks bidang ini sudah diketik di website)
        oc = Counter(w for f in sorted(glob.glob(f"tools/ssw/src/ocr/pages/{s}-*.txt")) for run in RUN.findall(open(f).read()) for w in segment(run))
        for w, c in oc.items():
            if c >= 3 and w not in BASIC and len(set(w)) > 1: cand.setdefault(w, (first, "ocr"))
    pre = re.match(r"(.*?)(\d+)$", L[0]["id"]); prefix, width = pre.group(1), len(pre.group(2))
    n = max(int(re.sub(r"\D", "", x["id"].replace(prefix, "")) or 0) for x in L)
    add = {"frasa": 0, "pdf": 0, "ocr": 0}
    for w, (bab, how) in sorted(cand.items()):
        if w in have: continue
        kana, arti, asal = lookup(w); have.add(w); n += 1; add[how] += 1
        L.append({"id": f"{prefix}{n:0{width}d}", "kata": w, "kana": kana, "arti": arti, "cat": "Kosakata dari teks/PDF materi",
                  "bab": bab, "src": [], "sumber": "panen-pdf", "asal_arti": asal, "asal_kata": {"frasa": "pecahan frasa teks", "pdf": "PDF bidang", "ocr": "OCR halaman buku"}[how]})
    json.dump(V, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot += sum(add.values())
    print(f"{s:22} pdf {len(pdfs):2} ocr-hal {len(glob.glob(f'tools/ssw/src/ocr/pages/{s}-*.txt')):3}  +dari-frasa {add['frasa']:5}  +dari-pdf {add['pdf']:5}  +ocr {add['ocr']:4}  total {len(L)}")
print("TOTAL baru", tot)
