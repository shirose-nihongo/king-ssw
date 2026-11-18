#!/usr/bin/env python3
"""Kuis kosakata untuk subbab yang belum punya kuis. Kata diambil dari vocab.json yang muncul di teks JP subbab itu.
Idempoten: id kuis <sub>-q, hanya ditambah bila belum ada. Soal tidak dikarang: arti dari vocab.json."""
import json, os, re, random, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
plain = lambda t: re.sub(r"\{([^|}]*)\|[^}]*\}", r"\1", t)
def txt(x):
    if isinstance(x, str): return x
    if isinstance(x, list): return " ".join(txt(i) for i in x)
    if isinstance(x, dict): return " ".join(txt(v) for v in x.values())
    return ""
total = {}
for slug in sys.argv[1:]:
    d = os.path.join(ROOT, "data", "ssw", slug)
    idx = json.load(open(f"{d}/index.json")); qp = f"{d}/quiz.json"; quiz = json.load(open(qp))
    v = json.load(open(f"{d}/vocab.json")); vi = v["items"] if isinstance(v, dict) else v
    vi = [w for w in vi if w.get("kata") and w.get("arti") and len(w["kata"]) >= 2]
    have = {g["id"] for gs in quiz["bab"].values() for g in gs}
    added = 0
    for b in idx["bab"]:
        bab = json.load(open(f"{d}/{b['file']}"))["bab"]
        for s in bab["subs"]:
            qid = f"{s['id']}-q"
            if qid in have or any(i.startswith(s["id"] + "-") for i in have): continue
            t = plain(txt(s.get("full") or {}) + " " + txt(s.get("title", {}).get("jp", "")))
            words = [w for w in vi if w["kata"] in t]
            seen = set(); words = [w for w in words if not (w["arti"] in seen or seen.add(w["arti"]))]
            if len(words) < 4: continue
            rnd = random.Random(qid); rnd.shuffle(words)
            items = []
            for w in words[:10]:
                wrong = rnd.sample([o["arti"] for o in vi if o["arti"] != w["arti"]], 3)
                opts = wrong + [w["arti"]]; rnd.shuffle(opts)
                r = f"{{{w['kata']}|{w['kana']}}}" if w.get("kana") and w["kana"] != w["kata"] else w["kata"]
                items.append({"q": {"id": f"Apa arti 「{w['kata']}」 ({w.get('kana','')}) dalam subbab ini?", "jp": f"「{r}」の{{意味|いみ}}は？"},
                              "opts": [{"id": o} for o in opts], "a": opts.index(w["arti"]),
                              "exp": {"id": f"{w['kata']} ({w.get('kana','')}) = {w['arti']}. Kata ini muncul di teks subbab {s['no']}."}})
            title = s.get("title", {})
            quiz["bab"].setdefault(bab["id"], []).append({"id": qid, "kosakata": True,
                "title": {"id": f"Latihan Kosakata: {plain(title.get('id', ''))}", "jp": "{語彙練習|ごいれんしゅう}"}, "items": items})
            added += 1
    json.dump(quiz, open(qp, "w", encoding="utf-8"), ensure_ascii=False)
    total[slug] = added
print(total)
