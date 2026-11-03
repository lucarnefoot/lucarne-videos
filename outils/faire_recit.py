# Format « Lucarne Récit » : histoire de foot racontée, images IA plein écran qui bougent,
# sous-titres mot à mot, nappe sonore + bruitages. Inspiré des vidéos « histoire » type MARA!.
# Usage : python3 outils/faire_recit.py outils/recits/drogba_2005.json
# Le JSON donne : voix (mp3), mots (horodatage Scribe [texte, début, fin]), dossier d'images,
# plans [début_s, image, x_départ, x_arrivée, zoom_départ, zoom_arrivée] (x = centre du cadrage, 0..1).
import json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WW, HH, FPS, SR = 1080, 1920, 30, 44100
Y = (215, 255, 58); W = (255, 255, 255); BG = (14, 42, 31)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_F = {}
def F(s):
    if s not in _F: _F[s] = ImageFont.truetype(BOLD, s)
    return _F[s]

cfg = json.load(open(sys.argv[1]))
P = lambda p: os.path.join(RACINE, p)
mots = json.load(open(P(cfg["mots"])))
voix = P(cfg["voix"])
out = P(cfg["sortie"]); os.makedirs(os.path.dirname(out), exist_ok=True)
dur_voix = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", voix]).decode())
TOT = round(dur_voix + 1.2, 2)
plans = cfg["plans"]
fin = cfg.get("fin")

# ---------- sous-titres : groupes de 1 à 3 mots ----------
PONCT = set(".,!?:;…»")
toks = []
for txt, a, b in mots:
    if txt in ("«", "»", ":", "!", "?", "…", ";"):
        if toks: toks[-1][3] = True   # coupure après
        continue
    toks.append([txt.strip("«»"), a, b, txt[-1] in PONCT])
chunks, cur = [], []
for tk in toks:
    cur.append(tk)
    if tk[3] or len(cur) == 3 or sum(len(x[0]) for x in cur) > 13:
        chunks.append(cur); cur = []
if cur: chunks.append(cur)
spans = []
for i, ch in enumerate(chunks):
    a = ch[0][1]; b = ch[-1][2] + 0.35
    if i + 1 < len(chunks): b = min(b, chunks[i + 1][0][1])
    spans.append((a, b, ch))

def draw_caption(im, t):
    sp = next((s for s in spans if s[0] <= t < s[1]), None)
    if not sp: return
    a, b, ch = sp
    words = [(w[0].upper().rstrip(".,;"), w[1], w[2]) for w in ch]
    size = 92
    d = ImageDraw.Draw(im)
    gap = 26
    while True:
        ws = [d.textlength(w[0], font=F(size)) for w in words]
        if sum(ws) + gap * (len(ws) - 1) <= WW - 120 or size <= 60: break
        size -= 4
    tw = sum(ws) + gap * (len(ws) - 1)
    pop = min(1, (t - a) / 0.12)
    s2 = int(size * (0.85 + 0.15 * pop))
    x = (WW - tw) / 2; yc = 1330
    for (txt, ws0, we0), wdt in zip(words, ws):
        if t >= ws0 - 0.02:
            col = Y if t < we0 + 0.08 else W
            d.text((x, yc - s2 / 2), txt, font=F(s2), fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
        x += wdt + gap

# ---------- habillage ----------
yy, xx = np.mgrid[0:HH, 0:WW]
r = np.sqrt(((xx - WW / 2) / (WW * 0.62)) ** 2 + ((yy - HH * 0.48) / (HH * 0.55)) ** 2)
vign = np.clip(1.15 - 0.55 * r ** 2, 0.35, 1.0)[..., None].astype(np.float32)
# bas plus sombre pour lire les sous-titres
grad = np.clip((yy - HH * 0.55) / (HH * 0.45), 0, 1)[..., None] * 0.35
vign = (vign * (1 - grad)).astype(np.float32)
rng = np.random.default_rng(7)
grains = [rng.normal(0, 4, (HH // 2, WW // 2, 1)).repeat(2, 0).repeat(2, 1).astype(np.float32) for _ in range(6)]

cache = {}
def source(nom):
    if nom not in cache:
        if len(cache) > 3: cache.pop(next(iter(cache)))
        im = Image.open(os.path.join(P(cfg["images"]), nom + ".jpg")).convert("RGB")
        k = 2160 / im.height
        cache[nom] = im.resize((round(im.width * k), 2160), Image.LANCZOS)
    return cache[nom]

def ease(u): u = max(0, min(1, u)); return u * u * (3 - 2 * u)

def plan_frame(i, t):
    st, nom, x0, x1, z0, z1 = plans[i]
    en = plans[i + 1][0] if i + 1 < len(plans) else TOT
    u = ease((t - st) / max(en - st, 0.1))
    src = source(nom)
    z = z0 + (z1 - z0) * u; cx = (x0 + (x1 - x0) * u) * src.width
    ch = src.height / z; cw = ch * WW / HH
    cx = min(max(cx, cw / 2), src.width - cw / 2)
    cy = src.height / 2
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return src.resize((WW, HH), Image.BILINEAR, box=box)

impacts = [t for t, k in cfg.get("temps_forts", []) if k == "impact"]
logo_w = None

def frame(n):
    t = n / FPS
    i = max(k for k, p in enumerate(plans) if p[0] <= t)
    im = plan_frame(i, t)
    # secousse sur les temps forts
    for ti in impacts:
        if 0 <= t - ti < 0.35:
            a = (1 - (t - ti) / 0.35) * 18
            im = im.transform(im.size, Image.AFFINE, (1, 0, a * math.sin(t * 90), 0, 1, a * math.cos(t * 77)))
    arr = np.asarray(im).astype(np.float32)
    # étalonnage léger : contraste + teinte chaude
    arr = (arr - 128) * 1.08 + 128
    arr *= vign
    arr += grains[(n // 3) % len(grains)]
    for ti in impacts:
        if 0 <= t - ti < 0.18: arr += 255 * (1 - (t - ti) / 0.18) * 0.8
    if fin and t >= fin["debut"]:
        k = min(1, (t - fin["debut"]) / 0.5); arr *= (1 - 0.55 * k)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    # marque
    d.rounded_rectangle((40, 70, 300, 140), 18, fill=Y); d.text((62, 80), "LUCARNE", font=F(46), fill=BG)
    if t < 4.2 and cfg.get("chapitre"):
        k = min(1, t / 0.3, (4.2 - t) / 0.3)
        lay = Image.new("RGBA", im.size, (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.text((40, 165), cfg["chapitre"], font=F(44), fill=W + (int(255 * k),), stroke_width=4, stroke_fill=(0, 0, 0, int(255 * k)))
        im.paste(lay, (0, 0), lay); d = ImageDraw.Draw(im)
    if fin and t >= fin["debut"]:
        k = ease((t - fin["debut"]) / 0.4)
        g = fin["gros"]; s = int(130 * (0.8 + 0.2 * k))
        tw = d.textlength(g, font=F(s))
        d.text(((WW - tw) / 2, 640), g, font=F(s), fill=Y, stroke_width=8, stroke_fill=(0, 0, 0))
        p = fin["petit"]; tw = d.textlength(p, font=F(44))
        d.text(((WW - tw) / 2, 820), p, font=F(44), fill=W, stroke_width=4, stroke_fill=(0, 0, 0))
    draw_caption(im, t)
    # crédit photo (licences libres type CC BY / CC BY-SA : obligatoire quand la photo est à l'écran)
    cr = cfg.get("credits", {}).get(plans[i][1])
    if cr:
        tw = d.textlength(cr, font=F(26))
        d.text((WW - tw - 30, HH - 60), cr, font=F(26), fill=W, stroke_width=3, stroke_fill=(0, 0, 0))
    # barre de progression fine
    d.rectangle((0, HH - 12, int(WW * t / TOT), HH), fill=Y)
    return im

# ---------- son : nappe + battements + bruitages ----------
N = int(TOT * SR); tt = np.arange(N) / SR
def env_fade(x, a, b, f=0.6):
    return np.clip(np.minimum((x - a) / f, (b - x) / f), 0, 1)
musique = np.zeros(N)
majeur = [(a, TOT if b is None else b) for a, b in cfg.get("majeur", [[24.5, 29.6], [52.6, None]])]
is_maj = np.zeros(N, bool)
for a, b in majeur: is_maj |= (tt >= a) & (tt < b)
lfo = 0.7 + 0.3 * np.sin(2 * np.pi * 0.12 * tt)
for f in (55.0, 110.0, 164.81):
    musique += np.sin(2 * np.pi * f * tt) * 0.16
mineur = np.sin(2 * np.pi * 130.81 * tt) * 0.12 + np.sin(2 * np.pi * 261.63 * tt) * 0.05
maj = np.sin(2 * np.pi * 138.59 * tt) * 0.12 + np.sin(2 * np.pi * 277.18 * tt) * 0.05 + np.sin(2 * np.pi * 329.63 * tt) * 0.05
musique += np.where(is_maj, maj, mineur)
musique *= lfo * np.clip(tt / 1.5, 0, 1) * np.clip((TOT - tt) / 1.5, 0, 1)
# battements de cœur pendant le penalty
for a, b in cfg.get("coeur", [[16.8, 24.4]]):
    k = a
    while k < b:
        for dt, amp in ((0, 1), (0.22, 0.6)):
            s = int((k + dt) * SR); L = int(0.25 * SR)
            if s + L < N:
                x = np.arange(L) / SR
                musique[s:s + L] += amp * 0.9 * np.sin(2 * np.pi * (45 + 40 * np.exp(-25 * x)) * x) * np.exp(-14 * x)
        k += 0.82
sfx = np.zeros(N)
# souffle à chaque coupe
for p in plans[1:]:
    s = int((p[0] - 0.12) * SR); L = int(0.3 * SR)
    if 0 <= s and s + L < N:
        x = np.arange(L) / SR
        nz = rng.normal(0, 1, L); nz = np.convolve(nz, np.ones(12) / 12, "same")
        sfx[s:s + L] += nz * np.sin(np.pi * x / x[-1]) ** 2 * 0.12
for ti, kind in cfg.get("temps_forts", []):
    s = int(ti * SR)
    if kind == "impact":
        L = int(1.6 * SR); x = np.arange(L) / SR
        boom = np.sin(2 * np.pi * (40 + 60 * np.exp(-20 * x)) * x) * np.exp(-3.5 * x) * 1.2
        ting = sum(np.sin(2 * np.pi * f * x) * np.exp(-dk * x) * a for f, dk, a in
                   ((1250, 4, 0.35), (2730, 5, 0.25), (4150, 7, 0.15)))
        seg = boom + ting
        sfx[s:s + L] += seg[:max(0, min(L, N - s))]
    if kind == "sifflet":
        L = int(0.35 * SR); x = np.arange(L) / SR
        seg = np.sin(2 * np.pi * (2900 + 120 * np.sin(2 * np.pi * 32 * x)) * x) * np.minimum(1, np.minimum(x / 0.02, (x[-1] - x) / 0.05)) * 0.12
        sfx[s:s + L] += seg
fond = (musique * 0.10 + sfx * 0.5)
tmpw = out + ".fond.wav"
with wave.open(tmpw, "w") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(SR)
    wf.writeframes((np.clip(fond, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------- rendu ----------
ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WW}x{HH}",
                       "-r", str(FPS), "-i", "-", "-i", tmpw, "-i", voix, "-filter_complex",
                       "[2:a]adelay=0|0,volume=1.0[v];[1:a][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
                       "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "slow", "-crf", "24", "-maxrate", "3M", "-bufsize", "6M",
                       "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out],
                      stdin=subprocess.PIPE)
n_frames = int(TOT * FPS)
for n in range(n_frames):
    ff.stdin.write(frame(n).tobytes())
    if n % 300 == 0: print(f"{n}/{n_frames}", flush=True)
ff.stdin.close(); ff.wait()
os.remove(tmpw)
print("ok", out, TOT, "s")
