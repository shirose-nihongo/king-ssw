#!/usr/bin/env python3
"""Impor soal format DSL (bab|soal|benar|salah1|salah2|salah3) ke data/ssw/<slug>/quiz.json.
Opsi diacak deterministik. Grup ber-id '<prefix>-<bab>' diganti utuh (idempoten). Soal kembar (teks sama) dilewati.
Pakai: python3 tools/ssw/dsl_import.py <slug> <file.txt> <prefix> "<label sumber>" """
import json, random, sys, re
slug, src, prefix, label = sys.argv[1:5]
p = f"data/ssw/{slug}/quiz.json"; Q = json.load(open(p))
for b in Q["bab"]: Q["bab"][b] = [g for g in Q["bab"][b] if not g["id"].startswith(prefix + "-")]
seen = {re.sub(r"\W", "", it["q"]["id"]).lower() for gs in Q["bab"].values() for g in gs for it in g["items"]}
out, dup = {}, 0
for line in open(src, encoding="utf-8"):
    line = line.strip()
    if not line or line.startswith("#"): continue
    f = [x.strip() for x in line.split("|")]
    assert len(f) == 6, line
    bab, q, ok, *wr = f
    k = re.sub(r"\W", "", q).lower()
    if k in seen: dup += 1; continue
    seen.add(k)
    opts = [ok] + wr; random.Random(q).shuffle(opts)
    out.setdefault(bab, []).append({"q": {"id": q}, "opts": [{"id": o} for o in opts], "a": opts.index(ok),
        "exp": {"id": f"Jawaban: {ok}. ({label})"}, "src": prefix})
for bab, items in out.items():
    for j in range(0, len(items), 25):
        Q["bab"].setdefault(bab, []).append({"id": f"{prefix}-{bab}-{j // 25 + 1}",
            "title": {"id": f"Latihan Teks Resmi {bab[3:]}.{j // 25 + 1}", "jp": "{練習問題|れんしゅうもんだい}"}, "items": items[j:j + 25]})
json.dump(Q, open(p, "w", encoding="utf-8"), ensure_ascii=False)
print(slug, {b: len(v) for b, v in out.items()}, "total", sum(len(v) for v in out.values()), "kembar dilewati", dup)
