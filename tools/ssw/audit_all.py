#!/usr/bin/env python3
"""Audit read-only seluruh bidang SSW. Angka dihitung dari data/ssw/<slug> dan assets/ssw/<slug>.
Jalankan dari root repo: python3 tools/ssw/audit_all.py  -> menulis SSW_AUDIT_2026-11-18.json (stdout: tabel markdown)."""
import json, os, re, glob, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "data", "ssw")
A = os.path.join(ROOT, "assets", "ssw")

core = open(os.path.join(ROOT, "js", "ssw-core.js"), encoding="utf-8").read()
spec = {}
for m in re.finditer(r'"([a-z0-9-]+)":\s*\{\s*n:\s*(\d+),\s*img:\s*(\d+),\s*mb:\s*(\d+)', core):
    spec[m.group(1)] = dict(n=int(m.group(2)), img=int(m.group(3)), mb=int(m.group(4)))

def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def count(path, exts):
    return sum(1 for f in glob.glob(os.path.join(path, "*")) if f.lower().endswith(exts))

rows = []
for slug in sorted(os.listdir(D)):
    d = os.path.join(D, slug)
    if not os.path.isdir(d) or not os.path.exists(os.path.join(d, "index.json")):
        continue
    idx = load(os.path.join(d, "index.json"))
    subs, full_id, full_jp, broken = [], 0, 0, []
    for b in idx.get("bab", []):
        p = os.path.join(d, b["file"])
        if not os.path.exists(p):
            broken.append(b["file"]); continue
        bab = load(p)["bab"]
        for s in bab.get("subs", []):
            subs.append((bab["id"], s["id"]))
            f = s.get("full") or {}
            full_id += bool(f.get("id")); full_jp += bool(f.get("jp"))
    quiz = load(os.path.join(d, "quiz.json")) if os.path.exists(os.path.join(d, "quiz.json")) else {"bab": {}}
    groups = [g for gs in quiz.get("bab", {}).values() for g in gs]
    pool = [it for g in groups if not g.get("rev") and not g.get("kosakata") for it in g.get("items", [])] or [it for g in groups if not g.get("kosakata") for it in g.get("items", [])]
    vq = sum(len(g["items"]) for g in groups if g.get("kosakata"))
    gid = " ".join(g["id"] for g in groups)
    subs_noquiz = [s for _, s in subs if not re.search(r"(^|\s)" + re.escape(s) + r"[-_]", gid)]
    babs_noquiz = [b["id"] for b in idx.get("bab", []) if not quiz.get("bab", {}).get(b["id"])]
    v = load(os.path.join(d, "vocab.json")) if os.path.exists(os.path.join(d, "vocab.json")) else []
    vi = v.get("items", []) if isinstance(v, dict) else v
    ids = [x.get("id") for x in vi]
    no_arti = sum(1 for x in vi if not x.get("arti"))
    no_kana = sum(1 for x in vi if re.search(r"[\u4e00-\u9fff]", x.get("kata", "")) and not x.get("kana"))
    with_img = sum(1 for x in vi if x.get("img") or x.get("fig"))
    a = os.path.join(A, slug)
    sp = spec.get(slug, {})
    n = sp.get("n", 20)
    rows.append(dict(
        slug=slug, nama=idx.get("nama"), jp=idx.get("jp"), book=idx.get("book"),
        bab=len(idx.get("bab", [])), sub=len(subs), full_id=full_id, full_jp=full_jp,
        page_jp=count(os.path.join(a, "jp"), (".webp", ".png", ".jpg")),
        page_id=count(os.path.join(a, "id"), (".webp", ".png", ".jpg")),
        fig=count(os.path.join(a, "fig"), (".webp", ".png", ".jpg", ".svg")),
        pdf=count(os.path.join(a, "pdf"), (".pdf",)),
        vocab=len(vi), vocab_dup_id=len(ids) - len(set(ids)), vocab_no_arti=no_arti,
        vocab_no_kana=no_kana, vocab_img=with_img,
        quiz_groups=len(groups), quiz_items=len(pool), vocab_quiz=vq,
        quiz_img=sum(1 for x in pool if x.get("img")), quiz_mb=sum(1 for x in pool if x.get("mb")),
        quiz_no_exp=sum(1 for x in pool if not x.get("exp")),
        quiz_bad_key=sum(1 for x in pool if not x.get("mb") and not (isinstance(x.get("a"), int) and 0 <= x["a"] < len(x.get("opts", [])))),
        subs_noquiz=subs_noquiz, babs_noquiz=babs_noquiz, broken=broken,
        exam_n=n, exam_spec=bool(sp), pool_ratio=round(len(pool) / n, 1) if n else 0,
    ))

def status(r):
    if r["broken"] or r["quiz_bad_key"] or r["vocab_dup_id"]:
        return "BROKEN"
    if r["sub"] == 0:
        return "MISSING"
    if r["subs_noquiz"] or r["babs_noquiz"] or r["vocab"] < 100 or r["pool_ratio"] < 4:
        return "PARTIAL"
    return "COMPLETE*"

for r in rows:
    r["status"] = status(r)
    r["full_tests"] = 20 if r["pool_ratio"] >= 4 else 10

json.dump(rows, open(os.path.join(ROOT, "SSW_AUDIT_2026-11-18.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("| Slug | Bab | Sub | Teks ID/JP | Hal. JP/ID | PDF | Kosakata (bergambar) | Soal (gbr/○×) | Sub tanpa soal | Bank/ujian | Full Test | Status |")
print("|---|--:|--:|--|--|--:|--|--|--:|--:|--:|---|")
for r in rows:
    print(f"| {r['slug']} | {r['bab']} | {r['sub']} | {r['full_id']}/{r['full_jp']} | {r['page_jp']}/{r['page_id']} | {r['pdf']} | {r['vocab']} ({r['vocab_img']}) | {r['quiz_items']} ({r['quiz_img']}/{r['quiz_mb']}) | {len(r['subs_noquiz'])} | {r['pool_ratio']}× | {r['full_tests']} | {r['status']} |")
