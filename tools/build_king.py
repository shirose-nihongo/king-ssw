# -*- coding: utf-8 -*-
"""Bangun KING SSW dari source Shirose Nihongo (hanya SSW + Mensetsu + login + dashboard).
Pakai: python3 build_king.py <src-shirose> <dst-king>.  Aman diulang (dst ditimpa kecuali .git)."""
import os, re, sys, shutil, subprocess
SRC, DST = sys.argv[1], sys.argv[2]
EXCL = [".git", "audio/choukai", "audio/vv/n1", "audio/vv/n2", "audio/vv/n3", "audio/vv/n4", "audio/vv/n5", "audio/vv/ir0", "audio/vv/ir1", "audio/vv/ir2",
        "audio/vv/test", "data/jft", "jlpt", "choukai", "backup", "tools", "docs", ".github", "cloudflare/gacha-worker.bundle.js", "firestore.rules.king-tambahan", "landing.html", "graphify-out"]
os.makedirs(DST, exist_ok=True)
for x in os.listdir(DST):
    if x != ".git": p = os.path.join(DST, x); shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)
def ign(d, names):
    rel = os.path.relpath(d, SRC).replace("\\", "/"); rel = "" if rel == "." else rel + "/"
    return [n for n in names if (rel + n) in EXCL]
for x in os.listdir(SRC):
    if x in EXCL: continue
    a = os.path.join(SRC, x); b = os.path.join(DST, x)
    shutil.copytree(a, b, ignore=ign) if os.path.isdir(a) else shutil.copy2(a, b)
def ed(path, pairs, must=True):
    p = os.path.join(DST, path); s = open(p, encoding="utf-8").read()
    for a, b in pairs:
        if a not in s and must: raise SystemExit("pola tidak ada di %s: %r" % (path, a[:60]))
        s = s.replace(a, b)
    open(p, "w", encoding="utf-8").write(s)

# 1) Firestore: koleksi KING terpisah (akun Auth tetap sama)
fs = os.path.join(DST, "js/firebase-sync.js"); s = open(fs, encoding="utf-8").read()
for c in ("siswa", "kelas", "ssw_rank", "ssw_bidang", "kategori_ujian", "soal", "komentar", "item_shop", "choukai", "kosakata_pos"):
    s = re.sub(r'((?:doc|collection)\(db, *)"%s"' % c, r'\1"king_%s"' % c, s)
# 2) Pendaftaran otomatis: akun Shirose yang belum punya profil KING langsung dibuatkan profil siswa
s = s.replace('if (!snap.exists() && !isOwner) {', 'if (false && !snap.exists() && !isOwner) {  // KING SSW: profil dibuat otomatis')
s = s.replace("    if (!snap.exists()) {\n      // Bootstrap", "    if (!snap.exists() && !isOwner) {  // KING SSW: ambil nama & kelas dari profil Shirose (akun yang sama)\n      try { const o = await getDoc(doc(db, \"sis\" + \"wa\", u.uid)); if (o.exists()) { const od = o.data(); base.nama = od.nama || base.nama; } } catch (_) {}\n    }\n    if (!snap.exists()) {\n      // Bootstrap", 1)
s = re.sub(r'export const BRAND_NAME = "[^"]*";', 'export const BRAND_NAME = "KING SSW";', s)
open(fs, "w", encoding="utf-8").write(s)

# 3) Hanya SSW + Mensetsu + akun
KING_JS = r'''
/* ===== KING SSW: hanya SSW, Mensetsu, akun & profil ===== */
const KING_OK = (n) => !n || ["home", "login", "masuk", "daftar", "profile", "hafalan"].includes(n) || String(n).startsWith("ssw") || String(n).startsWith("mensetsu") || (typeof MENSETSU_PUBLIC !== "undefined" && MENSETSU_PUBLIC.includes(n));
function renderKingHome(){
  if (!state.user) return `<div class="panel" style="text-align:center;padding:40px 16px"><div style="font-size:64px">👑</div><h1>KING SSW</h1>
    <p>Belajar SSW (特定技能) &amp; latihan Mensetsu (面接).</p><p style="color:var(--gray)">Masuk memakai akun Shirose Nihongo yang sudah kamu punya.</p>
    <button class="btn" onclick="route('login')">Masuk</button></div>`;
  const g = FB.userIsGuru();
  return `<div class="herobar"><div class="avatar-mini">👑</div><div class="info"><div class="nama">${state.siswa?.nama || "Siswa"}</div><div class="meta">KING SSW${state.siswa?.kelas ? " · Kelas " + state.siswa.kelas : ""}</div></div><button class="btn ghost" onclick="route('profile')">Profil</button></div>
  <div class="panel"><h2>Mau belajar apa hari ini?</h2><div class="hub-grid">
    <div class="hub-card" onclick="route('ssw')"><div class="ico">🏗️</div><div class="info"><div class="ttl">SSW 特定技能</div><div class="sub">Materi, buku, kosakata, kuis &amp; ujian per bidang</div></div></div>
    <div class="hub-card" onclick="route('mensetsu')"><div class="ico">🎤</div><div class="info"><div class="ttl">Mensetsu 面接</div><div class="sub">Simulasi wawancara dengan AI</div></div></div>
    <div class="hub-card" onclick="route('ssw-progres')"><div class="ico">📊</div><div class="info"><div class="ttl">Progres &amp; riwayat</div><div class="sub">Progres belajar dan hasil ujian SSW</div></div></div>
    ${g ? `<div class="hub-card" onclick="location.href='./teacher.html'"><div class="ico">🛠️</div><div class="info"><div class="ttl">Dashboard Guru</div><div class="sub">Siswa, kelas, akses SSW</div></div></div>` : ""}
  </div></div>`;
}
'''
ed("index.html", [
  ("function _renderRoute(name, rest){\n  const fn = routes[name] || renderHome;", KING_JS + "\nfunction _renderRoute(name, rest){\n  const fn = (KING_OK(name) && name !== \"home\" ? routes[name] : null) || renderKingHome;"),
  ('if (!location.hash && !standalone && !localStorage.getItem("shirose-returning")) location.replace("./landing.html");', '/* KING SSW: tanpa landing page */'),
  ('シ<span class="rose">🌹</span>ロセ <span style="font-family:var(--font-sans); font-size:13px; letter-spacing:.5px;">NIHONGO</span>', '👑 KING <span style="font-family:var(--font-sans); font-size:13px; letter-spacing:.5px;">SSW</span>'),
  ("if (state.user && !BEBAS_PILIH_LEVEL.has(name)", "if (false && state.user && !BEBAS_PILIH_LEVEL.has(name)"),
])
for f in ("index.html", "teacher.html", "sw.js"):
    t = open(os.path.join(DST, f), encoding="utf-8").read().replace("./landing.html", "./").replace('"./", \n', '').replace("シ<span class=\"rose\">🌹</span>ロセ", "👑 KING SSW")
    open(os.path.join(DST, f), "w", encoding="utf-8").write(t)
# 4) Branding
BR = [("SHIROSE NIHONGO", "KING SSW"), ("Shirose Nihongo", "KING SSW"), ("SHIROSE", "KING SSW")]
for root, _, files in os.walk(DST):
    if "/.git" in root or "/data" in root or "/assets" in root or "/audio" in root: continue
    for f in files:
        if f.endswith((".html", ".js", ".webmanifest", ".css", ".md")):
            p = os.path.join(root, f); t = open(p, encoding="utf-8", errors="ignore").read(); t2 = t
            for a, b in BR: t2 = re.sub(r"(?<![\w$])" + re.escape(a) + r"(?![\w$])", b, t2)
            if t2 != t: open(p, "w", encoding="utf-8").write(t2)
ed("sw.js", [('const CACHE = "shirose-nihongo-', 'const CACHE = "king-ssw-')])
ed("manifest.webmanifest", [], must=False)
# 5) Ikon mahkota
from PIL import Image, ImageDraw, ImageFont
F = "/usr/share/fonts/opentype/noto/NotoSansCJK-Black.ttc"
for name, sz in (("icon-192.png", 192), ("icon-512.png", 512), ("icon-maskable-512.png", 512), ("apple-touch-icon.png", 180)):
    im = Image.new("RGB", (sz, sz), "#14213d"); d = ImageDraw.Draw(im); u = sz / 100
    d.polygon([(18*u,70*u),(14*u,32*u),(34*u,50*u),(50*u,24*u),(66*u,50*u),(86*u,32*u),(82*u,70*u)], fill="#fca311")
    d.rectangle([18*u,72*u,82*u,80*u], fill="#fca311")
    for x in (14,50,86): d.ellipse([(x-5)*u,(18 if x==50 else 26)*u,(x+5)*u,(28 if x==50 else 36)*u], fill="#fca311")
    f = ImageFont.truetype(F, int(11*u)); w = d.textlength("SSW", font=f); d.text(((sz-w)/2, 84*u), "SSW", font=f, fill="white")
    im.save(os.path.join(DST, name))
im = Image.open(os.path.join(DST, "icon-192.png")).resize((48, 48)); im.save(os.path.join(DST, "favicon.ico"))
open(os.path.join(DST, ".nojekyll"), "w").close()
print("KING SSW siap di", DST)
