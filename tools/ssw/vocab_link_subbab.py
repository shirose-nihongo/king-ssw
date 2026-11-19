#!/usr/bin/env python3
"""Tautkan kosakata ber-src kosong ke subbab (jalankan setelah vocab_harvest.py & vocab_segment_pdf.py).
Menu Hafalan Penuh memilih kata lewat field src (ID subbab); kata tanpa src tidak pernah muncul.
src = subbab (maks 3) yang teksnya memuat kata itu; jika tidak ada -> '<bab>-x' (grup "Kosakata tambahan" per bab).
Hanya MENGISI src yang kosong; tidak menghapus/mengubah field lain."""
import json, re, os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(ROOT)
RUBY = re.compile(r"\{([^|{}]+)\|[^{}]*\}")
tot = {"sub": 0, "x": 0}
for s in sorted(os.listdir("data/ssw")):
    d = f"data/ssw/{s}"
    if not os.path.exists(f"{d}/index.json"): continue
    idx = json.load(open(f"{d}/index.json")); subs = []
    for b in idx["bab"]:
        bab = json.load(open(f"{d}/{b['file']}"))["bab"]
        for x in bab["subs"]: subs.append((bab["id"], x["id"], RUBY.sub(r"\1", json.dumps(x, ensure_ascii=False))))
    babs = {b["id"] for b in idx["bab"]}
    P = f"{d}/vocab.json"; V = json.load(open(P)); L = V["items"] if isinstance(V, dict) else V
    a = {"sub": 0, "x": 0}
    for v in L:
        if v.get("src"): continue
        hit = [sid for bid, sid, t in subs if v["kata"] in t]
        same = [sid for bid, sid, t in subs if bid == v.get("bab") and sid in hit]
        if hit: v["src"] = (same or hit)[:3]; a["sub"] += 1
        else:
            bab = v.get("bab") if v.get("bab") in babs else idx["bab"][0]["id"]
            v["bab"] = bab; v["src"] = [f"{bab}-x"]; a["x"] += 1
    json.dump(V, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    tot["sub"] += a["sub"]; tot["x"] += a["x"]
    if a["sub"] or a["x"]: print(f"{s:22} ke-subbab {a['sub']:5}  ke-tambahan {a['x']:5}")
print("TOTAL", tot)
