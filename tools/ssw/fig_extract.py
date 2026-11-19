#!/usr/bin/env python3
"""Ekstrak gambar tertanam dari PDF buku resmi -> assets/ssw/<slug>/fig/*.webp + data/ssw/<slug>/figs.json,
lalu aktifkan pop-up gambar di samping paragraf (index.json "figs"). Halaman buku dipetakan ke subbab lewat pagesJp/pages.
Filter: >=150x150 px, tidak terlalu gelap (transparansi hilang) / polos, rasio <= 6, gambar yang sama di >=3 halaman (logo/ikon) dibuang. Idempoten (ditulis ulang utuh).
Hanya untuk bidang yang BELUM punya figs.json buatan tangan."""
import json, os, re, subprocess, hashlib, glob, shutil
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
# slug -> daftar (pdf, halaman_buku_pertama - 1) : halaman buku = halaman_pdf + offset
MAP = {
  "jaim-elec-electronic": [("panduan-belajar-jp.pdf", 0)],
  "jaim-machine-metal":   [("panduan-belajar-jp.pdf", 0)],
  "jaim-metal-surface":   [("panduan-belajar-jp.pdf", 0)],
  "aviation-gh": [("jaea-gh-text1-anzen-hinshitsu-rev2.pdf", 0), ("jaea-gh-text2-gh-rev2-1.pdf", 26)],
  "aviation-am": [("jaea-am-text1-kihon-gijutsu.pdf", 0), ("jaea-am-text2-anzen-hinshitsu.pdf", 26), ("jaea-am-text3-kokuki-gaiyo.pdf", 46)],
  "railway-vehicle": [("rail-sharyo-gakushu-text-1go.pdf", 0)],
  "wood-industry": [("zenmoku-gakushu-text-ja.pdf", -3)],
}
plain = lambda t: re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", str(t or "")).replace("**", "")
for slug, pdfs in MAP.items():
    d = f"data/ssw/{slug}"; idx = json.load(open(f"{d}/index.json"))
    subs = []
    for b in idx["bab"]:
        bab = json.load(open(f"{d}/{b['file']}"))["bab"]
        for s in bab["subs"]:
            pr = s.get("pagesJp") or s.get("pages")
            if pr: subs.append((pr[0], pr[1], s))
    out_dir = f"assets/ssw/{slug}/fig"; shutil.rmtree(out_dir, ignore_errors=True); os.makedirs(out_dir)
    cand = []
    for pdf, off in pdfs:
        p = f"assets/ssw/{slug}/pdf/{pdf}"; tmp = f"/tmp/fx/{slug}/{pdf}"; shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
        lst = subprocess.run(["pdfimages", "-list", p], capture_output=True, text=True).stdout.splitlines()[2:]
        kinds = {}
        for l in lst:
            c = l.split()
            if len(c) > 4: kinds[(int(c[0]), int(c[1]))] = (c[2], int(c[3]), int(c[4]))
        subprocess.run(["pdfimages", "-png", "-p", p, tmp + "/i"], capture_output=True)
        for f in sorted(glob.glob(tmp + "/i-*.png")):
            m = re.search(r"i-(\d+)-(\d+)\.png$", f); pg, num = int(m.group(1)), int(m.group(2))
            k = kinds.get((pg, num))
            if not k or k[0] != "image" or k[1] < 150 or k[2] < 150 or max(k[1], k[2]) / min(k[1], k[2]) > 6: continue
            cand.append((pg + off, f, hashlib.md5(open(f, "rb").read()).hexdigest()))
    from collections import Counter
    rep = Counter(h for _, _, h in cand); seen = set(); figs = []; per = Counter()
    for page, f, h in sorted(cand):
        if rep[h] >= 3 or h in seen: continue
        seen.add(h)
        sub = next((s for a, b, s in subs if a <= page <= b), None)
        if not sub: continue
        im = Image.open(f).convert("RGB")
        from PIL import ImageStat
        st = ImageStat.Stat(im.convert("L"))
        if st.mean[0] < 60 or st.stddev[0] < 12: continue   # hitam/transparansi hilang atau polos satu warna
        if im.width > 900: im = im.resize((900, round(im.height * 900 / im.width)))
        n = per[page]; per[page] += 1
        name = f"jp-p{page:03d}-{n}.webp"; im.save(f"{out_dir}/{name}", "WEBP", quality=78)
        t = plain((sub.get("title") or {}).get("id")); tj = plain((sub.get("title") or {}).get("jp"))
        figs.append({"id": f"{slug}-jp-p{page:03d}-{n}", "sub": sub["id"], "book": "jp", "page": page, "y": round(0.2 + 0.6 * n / 4, 2),
                     "src": f"./{out_dir}/{name}", "w": im.width, "h": im.height, "cap": {"id": t, "jp": tj},
                     "exp": {"id": f"Gambar dari buku teks resmi, hal. {page}, untuk subbab «{t}». Ketuk gambar untuk memperbesar; tulisan pada gambar sama dengan buku.", "jp": f"テキスト{page}ページ「{tj}」の図。"},
                     "terms": [], "auto": True})
    json.dump({"slug": slug, "note": "Gambar diekstrak otomatis dari PDF buku resmi (tools/ssw/fig_extract.py); auto:true = perlu penyuntingan manusia.", "figs": figs},
              open(f"{d}/figs.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    idx["figs"] = "figs.json"; json.dump(idx, open(f"{d}/index.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    size = sum(os.path.getsize(x) for x in glob.glob(out_dir + "/*")) // 1024
    print(f"{slug:22} gambar {len(figs):4}  subbab bergambar {len({x['sub'] for x in figs}):3}/{len(subs):3}  ukuran {size} KB")
