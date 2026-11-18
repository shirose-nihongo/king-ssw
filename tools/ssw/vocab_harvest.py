#!/usr/bin/env python3
"""Panen kosakata dari teks materi tiap bidang SSW -> vocab.json (tanpa menghapus entri lama).
Kata  : pasangan {kanji|kana} di teks JP, dan istilah Jepang yang ditulis di teks ID.
Arti  : (1) glosa di teks ID bidang itu sendiri: '**JP** (arti)', 'JP (arti)', 'arti (JP)';
        (2) kamus yang sudah ada di website (kosakata JLPT N5-N1/IR + vocab semua bidang SSW).
Kata tanpa arti TIDAK ditambahkan (dicatat di laporan). Idempoten: entri sumber 'panen-teks' dibangun ulang."""
import json, re, os, glob, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
KAN = r"[一-鿿々]"; JPW = r"[぀-ヿ一-鿿々ー・]+"
RUBY = re.compile(r"\{([^|{}]+)\|([^{}|]+)\}")
def items(p):
    v = json.load(open(p))
    if isinstance(v, dict): v = v.get("items", v)
    return v if isinstance(v, list) else []
def strings(x, lang=None, out=None):
    out = [] if out is None else out
    if isinstance(x, str): out.append((lang, x))
    elif isinstance(x, list):
        for i in x: strings(i, lang, out)
    elif isinstance(x, dict):
        for k, v in x.items():
            if k in ("img", "fig", "src", "pages"): continue
            strings(v, k if k in ("id", "jp") else lang, out)
    return out
plain = lambda t: RUBY.sub(r"\1", t).replace("**", "")
# kamus global
D, K = {}, {}
for f in sorted(glob.glob("data/kosakata-*.json")) + sorted(glob.glob("data/ssw/*/vocab.json")):
    for x in items(f):
        if x.get("source") == "panen-teks" or x.get("sumber") == "panen-teks": continue
        if x.get("kata") and x.get("arti"):
            D.setdefault(x["kata"], x["arti"])
            if x.get("kana"): K.setdefault(x["kata"], x["kana"])
GLOSS = [re.compile(r"\*\*(" + JPW + r")\*\*\s*\(([^()（）]{2,60})\)"),
         re.compile(r"(?<![\w぀-鿿])(" + JPW + r")\s*\(([A-Za-z][^()（）]{1,60})\)"),
         re.compile(r"\*\*(" + JPW + r")\s*\(([A-Za-z][^()（）]{1,60})\)\*\*")]
GLOSS_R = re.compile(r"([A-Za-z][A-Za-z /\-']{2,50})\s*\((?:\*\*)?(" + JPW + r")(?:\*\*)?\)")
rep = {}
JPD = {}
_jp = os.environ.get("JPDICT", "/home/claude/jpdict/jpdict_min.json")
if os.path.exists(_jp): JPD = json.load(open(_jp))
OKURI = "みりいるえしけきぎめせちつくうれかがじ"
def jpd(k):
    if k in JPD: return k, JPD[k][0], JPD[k][1]
    if re.search(KAN + "$", k):
        for o in OKURI:
            if k + o in JPD: return k + o, JPD[k + o][0], JPD[k + o][1]
    return None
EXTRA = {}
for line in open("tools/ssw/src/vocab_tambahan_baru.txt", encoding="utf-8"):
    if line.strip() and not line.startswith("#"):
        b, k, r, a = [x.strip() for x in line.split("|")]
        EXTRA.setdefault(b, []).append((k, r, a))
for s in sorted(os.listdir("data/ssw")):
    d = f"data/ssw/{s}"
    if not os.path.exists(f"{d}/index.json"): continue
    P = f"{d}/vocab.json"; V = json.load(open(P)); L = V["items"] if isinstance(V, dict) else V
    L[:] = [x for x in L if x.get("sumber") != "panen-teks"]
    have = {x["kata"] for x in L}
    idx = json.load(open(f"{d}/index.json"))
    reading, gloss, words = {}, {}, set()
    for b in idx["bab"]:
        bab = json.load(open(f"{d}/{b['file']}"))["bab"]
        for lang, t in strings(bab):
            for k, r in RUBY.findall(t):
                if re.search(KAN, k) and len(k) >= 2 and re.fullmatch(r"[぀-ゟー]+", r):
                    reading.setdefault(k, r); words.add((k, bab["id"]))
            if lang == "id":
                pt = plain(t)
                for rx in GLOSS:
                    for k, a in rx.findall(t if "**" in rx.pattern else pt):
                        k = k.strip("・ "); a = a.strip(" ,;.")
                        if re.search(KAN + "|[゠-ヿ]{2,}", k) and len(k) >= 2 and not re.search(KAN, a):
                            gloss.setdefault(k, a); words.add((k, bab["id"]))
                for a, k in GLOSS_R.findall(pt):
                    if re.search(KAN, k) and len(k) >= 2: gloss.setdefault(k, a.strip()); words.add((k, bab["id"]))
    pre = re.match(r"(.*?)(\d+)$", L[0]["id"]) if L else None
    prefix, width = (pre.group(1), len(pre.group(2))) if pre else (s[:2] + "-", 3)
    n = max((int(re.sub(r"\D", "", x["id"].replace(prefix, "")) or 0) for x in L), default=0)
    add = miss = 0; seen = set()
    for k, bab in sorted(words):
        if k in have or k in seen: continue
        arti = gloss.get(k) or D.get(k)
        kana = reading.get(k) or K.get(k) or (k if not re.search(KAN, k) else "")
        asal = "teks bidang" if k in gloss else "kamus website"
        if not arti and (hit := jpd(k)):
            k2, r2, a2 = hit
            if k2 in have or k2 in seen: continue
            if k2 != k: kana = r2
            k, arti, kana, asal = k2, a2, r2, "JPdict (lawlie/dom, terjemahan AI)"
        if not arti or not kana: miss += 1; continue
        seen.add(k); n += 1; add += 1
        L.append({"id": f"{prefix}{n:0{width}d}", "kata": k, "kana": kana, "arti": arti,
                  "cat": "Kosakata dari teks materi", "bab": bab, "src": [], "sumber": "panen-teks",
                  "asal_arti": asal})
    first_bab = idx["bab"][0]["id"]
    for k, r, a in EXTRA.get(s, []):
        if k in have or k in seen: continue
        seen.add(k); n += 1; add += 1
        L.append({"id": f"{prefix}{n:0{width}d}", "kata": k, "kana": r, "arti": a, "cat": "Kosakata dari teks materi",
                  "bab": next((bb for kk, bb in words if kk.startswith(k[:2])), first_bab), "src": [], "sumber": "panen-teks", "asal_arti": "terjemahan Shirose"})
    json.dump(V, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1 if "\n" in open(P).read(200) else None)
    rep[s] = (len(L) - add, add, miss)
    print(f"{s:22} lama {len(L)-add:5} +baru {add:5} tanpa-arti {miss:5}")
print("TOTAL baru", sum(v[1] for v in rep.values()), "tanpa arti", sum(v[2] for v in rep.values()))
