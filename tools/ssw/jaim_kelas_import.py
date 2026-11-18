#!/usr/bin/env python3
"""Impor soal kelas Seizou (Downloads/KELAS SSW/SEIZOU: SOAL BUATAN MANTAP.docx, SOAL MANUFAKTUR BUATAN.docx) ke jaim-machine-metal.
Kunci dari file, dicek manual: ○× no.14 dikoreksi (toleransi poros = huruf kecil → ○). PG 41 & 43 dibuang (gambarnya tidak ada). Idempoten (grup 'kelas-*')."""
import docx, json, re, sys
D = sys.argv[1]
tf = [l.strip() for p in docx.Document(f"{D}/SOAL BUATAN MANTAP.docx").paragraphs for l in p.text.split("\n") if l.strip()]
stm = [l for l in tf if "○" in l and "×" in l]
key = {int(m.group(1)): m.group(2) for l in tf if (m := re.match(r"^(\d+)．([○×])\s*―\s*(.*)", l))}
expl = {int(m.group(1)): m.group(3) for l in tf if (m := re.match(r"^(\d+)．([○×])\s*―\s*(.*)", l))}
key[14] = "○"; expl[14] = "軸のはめあい公差は小文字（例：h7、g6）、穴は大文字（例：H7）で表す。"
ruby = lambda t: re.sub(r"([一-鿿々]+)\(([぀-ゟ]+)\)", r"{\1|\2}", t)
plain = lambda t: re.sub(r"\(([぀-ゟ]+)\)", "", t)
BTF = [6,2,2,2,5,2,2,2,7,3,8,7,5,7,6,4,8,9,6,8,8,6,2,2,2,8,2,9,9,2]
out = {}
for i, l in enumerate(stm, 1):
    s = re.sub(r"^\d+．|（\s*○\s*／\s*×\s*）", "", l).strip()
    out.setdefault(f"bab{BTF[i-1]}", []).append({"q": {"id": plain(s), "jp": ruby(s)},
        "opts": [{"id": "Benar (○)", "jp": "○ {正|ただ}しい"}, {"id": "Salah (×)", "jp": "× {間違|まちが}い"}],
        "a": 0 if key[i] == "○" else 1, "exp": {"id": f"{key[i]} — {expl[i]}"}, "mb": True, "src": "bank-kelas"})
# soal 31 (pilihan ganda JP)
i31 = next(k for k, l in enumerate(tf) if l.startswith("31．"))
o31 = re.findall(r"([A-D])．(.*?)(?=\s+[A-D]．|$)", tf[i31 + 1])
out["bab8"].append({"q": {"id": plain(tf[i31][3:]), "jp": ruby(tf[i31][3:])}, "opts": [{"id": plain(t.strip()), "jp": ruby(t.strip())} for _, t in o31],
    "a": [k for k, _ in o31].index("C"), "exp": {"id": "C — mesin dihentikan dulu, lalu geram dibersihkan dengan sikat."}, "src": "bank-kelas"})
# pilihan ganda Indonesia
mc = [l.strip() for p in docx.Document(f"{D}/SOAL MANUFAKTUR BUATAN.docx").paragraphs for l in p.text.split("\n") if l.strip()]
ki = mc.index("KUNCI JAWABAN"); keys = [k.replace("\uf0b7", "").strip() for k in mc[ki + 1:]]
qs, cur = [], None
for l in mc[:ki]:
    if (m := re.match(r"^(\d+)\.\s+(.*)", l)): cur = {"n": int(m.group(1)), "q": m.group(2), "o": []}; qs.append(cur)
    elif (m := re.match(r"^([A-D])\.\s+(.*)", l)) and cur: cur["o"].append(m.group(2).replace("Shutterstock", "").strip())
    elif cur and not cur["o"] and not l.startswith("Bagian"): cur["q"] += " " + l
BMC = {1:6,2:2,3:2,4:5,5:2,6:2,7:2,8:7,9:3,10:5,11:7,12:6,13:4,14:9,15:6,16:2,17:6,18:7,19:8,20:6,21:8,22:5,23:9,24:9,25:2,26:8,27:8,28:2,29:2,30:2,31:7,32:2,33:7,34:2,35:8,36:2,37:10,38:8,39:6,40:2,42:5,44:2,45:2}
fix = lambda t: t.replace("$\\pm 0,3$", "±0,3").replace("$\\mu m$", "µm").replace("$\\pi = 3,14$", "π = 3,14").replace("$V = I \\times R$", "V = I × R").replace("$", "")
for q in qs:
    if q["n"] not in BMC or len(q["o"]) != 4: continue
    if q["n"] > len(keys): print("SKIP", q["n"], q["q"][:50]); continue
    k = "ABCD".index(keys[q["n"] - 1])
    text = re.sub(r"^(Lihat|Perhatikan) (gambar|simbol)[^.]*\.\s*", "", fix(q["q"]))
    out.setdefault(f"bab{BMC[q['n']]}", []).append({"q": {"id": text}, "opts": [{"id": fix(o)} for o in q["o"]], "a": k,
        "exp": {"id": f"Jawaban: {fix(q['o'][k])}."}, "src": "bank-kelas"})
p = "data/ssw/jaim-machine-metal/quiz.json"; Q = json.load(open(p))
for b in Q["bab"]: Q["bab"][b] = [g for g in Q["bab"][b] if not g["id"].startswith("kelas-")]
for b, items in out.items():
    Q["bab"].setdefault(b, []).append({"id": f"kelas-{b}", "title": {"id": "Latihan Kelas (soal guru)", "jp": "{練習問題|れんしゅうもんだい}"}, "items": items})
json.dump(Q, open(p, "w", encoding="utf-8"), ensure_ascii=False)
print({b: len(v) for b, v in sorted(out.items())}, sum(len(v) for v in out.values()))
