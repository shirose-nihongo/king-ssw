#!/usr/bin/env python3
"""Impor bank soal kelas Kaigo (file Word guru, Downloads/KELAS SSW/KAIGO) ke quiz.json kaigo & kaigo-jp.
Kunci jawaban ditentukan ulang per soal (kunci di file Word tidak sejajar dengan nomornya); soal ambigu dibuang.
Idempoten: grup ber-id 'kelas-*' diganti utuh setiap dijalankan."""
import json, re, sys
U, A = sys.argv[1], sys.argv[2]   # uniq.json, ans_all.json
L = json.load(open(U)); ANS = {int(k): v for k, v in json.load(open(A)).items()}
KW = {
 "bab4": r"mandi|makan|menelan|tersedak|ekskresi|buang air|BAB|urin|popok|pispot|toilet|commode|konstipasi|diare|inkontinensia|pakaian|baju|celana|kursi roda|berpindah|transfer|tongkat|walker|tangga|undakan|lereng|berdiri|berjalan|jalan|mulut|gigi|kuku|rambut|menyeka|cukur|memasak|mencuci|menyapu|mengepel|sampah|sprei|kamar|rumah tangga|tempat tidur|menjemur|debu|kaca|bantal|posisi",
 "bab3": r"komunikasi|berbicara|bicara|afasia|pendengaran|penglihatan|tuna netra|isyarat|catatan|mencatat|laporan|informasi|tim|rapat|sedih|empati|menyapa|hourensou|braille|demensia.*(komunikasi|pertanyaan|bicara)",
 "bab2": r"otak|saraf|jantung|paru|ginjal|tulang|otot|kulit|tidur|homeostasis|memori|penuaan|penyakit|diabetes|hipertensi|stroke|serebro|infark|angina|pneumonia|osteoporosis|edema|dehidrasi|pruritus|insomnia|demensia|alzheimer|parkinson|depresi|manik|delusi|kognitif|nadi|tekanan darah|suhu|pernapasan|vital|sianosis|organ|pencernaan|lambung|hati|pankreas|insulin|fraktur|disuse|lewy|frontotemporal|apokrin|ekrin|sel\b|stetoskop|termometer|tensimeter|spirometer|pulsoksimeter|otoskop|trendelenburg|supinasi|lateral",
}
def bab_of(t):
    for b in ("bab2", "bab4", "bab3"):
        if re.search(KW[b], t, re.I): return b
    return "bab1"
ruby = lambda t: re.sub(r"([一-鿿々]+)（([぀-ゟ]+)）", r"{\1|\2}", t)
plain = lambda t: re.sub(r"（[぀-ゟ]+）", "", t)
ID, JP = {}, []
for i, x in enumerate(L):
    a = ANS[i]
    if a == "X": continue
    k = "abcd".index(a)
    if re.search(r"[぀-ヿ]", x["q"]):
        JP.append({"q": {"id": "Baca percakapan, lalu pilih tindakan yang benar.", "jp": ruby(x["q"])},
                   "opts": [{"id": plain(o), "jp": ruby(o)} for o in x["opts"]], "a": k,
                   "exp": {"id": f"Jawaban: {plain(x['opts'][k])}.", "jp": f"{ruby(x['opts'][k])}"}, "src": "bank-kelas"})
    else:
        ID.setdefault(bab_of(x["q"] + " " + " ".join(x["opts"])), []).append(
            {"q": {"id": x["q"]}, "opts": [{"id": o} for o in x["opts"]], "a": k,
             "exp": {"id": f"Jawaban: {x['opts'][k]}."}, "src": "bank-kelas"})
def put(slug, groups):
    p = f"data/ssw/{slug}/quiz.json"; q = json.load(open(p))
    for b in q["bab"]: q["bab"][b] = [g for g in q["bab"][b] if not g["id"].startswith("kelas-")]
    n = 0
    for bab, items in groups.items():
        for j in range(0, len(items), 25):
            n += 1; part = items[j:j + 25]
            q["bab"].setdefault(bab, []).append({"id": f"kelas-{bab}-{j // 25 + 1}",
                "title": {"id": f"Bank Soal Kelas {bab[3:]}.{j // 25 + 1}", "jp": "{練習問題|れんしゅうもんだい}"}, "items": part})
    json.dump(q, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    print(slug, {b: len(v) for b, v in groups.items()}, "grup", n)
put("kaigo", ID)
put("kaigo-jp", {"bab2": JP})
