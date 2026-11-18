#!/usr/bin/env python3
"""Tambah kosakata kelas Seizou (KOTOBA KIKAI, KOTOBA[1], KOSAKATA BARU, KOTOBA.docx) ke jaim-machine-metal/vocab.json.
Tidak menghapus/mengubah entri lama; ID baru melanjutkan nomor terakhir; kata yang sudah ada dilewati. Idempoten (src 'kelas-seizou')."""
import docx, json, re, sys, glob
D = sys.argv[1]; P = "data/ssw/jaim-machine-metal/vocab.json"
V = json.load(open(P)); items = V["items"] if isinstance(V, dict) else V
items[:] = [v for v in items if v.get("sumber") != "kelas-seizou"]
have = {re.sub(r"\s", "", v["kata"]) for v in items}
cleanA = lambda a: re.sub(r"\s*\d+\s*$", "", a).strip(" .")
rows = []
for f in ["KOTOBA KIKAI.docx", "KOTOBA[1].docx", "KOSAKATA BARU.docx"]:
    d = docx.Document(f"{D}/{f}")
    for t in d.tables:
        hdr = [c.text.strip().lower() for c in t.rows[0].cells]
        def col(*ks):
            for i, h in enumerate(hdr):
                if any(k in h for k in ks): return i
        ck, cr, ca = col("kanji", "istilah", "kotoba"), col("hiragana", "furigana"), col("arti", "terjemahan")
        if None in (ck, cr, ca): continue
        for r in t.rows[1:]:
            c = [x.text.strip() for x in r.cells]
            if len(c) <= max(ck, cr, ca): continue
            k = re.sub(r"\s*\(.*?\)\s*", "", c[ck]).strip(); kana = re.split(r"[/（(]", c[cr])[0].replace(" ", "").strip()
            if k and kana and c[ca]: rows.append((k, kana, cleanA(c[ca])))
for p in docx.Document(f"{D}/KOTOBA.docx").paragraphs:
    m = re.match(r"^([^\s(（/]+(?:\s[^\s(（/]+)*?)\s*[（(]([぀-ゟ\s]+)[）)].*?/[^:]*:\s*(.+?)\.?$", p.text.strip())
    if m and re.search(r"[一-鿿゠-ヿ]", m.group(1)): rows.append((m.group(1).replace(" ", ""), m.group(2).replace(" ", ""), cleanA(m.group(3))))
n = max(int(re.sub(r"\D", "", v["id"]) or 0) for v in items); add = 0
for k, kana, a in rows:
    key = re.sub(r"\s", "", k)
    if key in have or len(a) > 80: continue
    have.add(key); n += 1; add += 1
    items.append({"id": f"jaim-machine-metal-{n:03d}", "kata": k, "kana": kana, "arti": a, "cat": "Kosakata kelas Seizou", "bab": "bab4", "src": [], "sumber": "kelas-seizou"})
json.dump(V, open(P, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("baris", len(rows), "ditambah", add, "total", len(items))
