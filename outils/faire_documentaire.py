# Format « Lucarne Doc » : documentaire long 16:9 (8 à 12 min) pour YouTube.
# Photos réelles sous licence libre (crédit à l'écran), images d'ambiance IA sans visage,
# animations (carte, chiffres, frises), cartons de chapitre, musique par chapitre avec
# ducking sous la voix, bruitages, écran de fin « Abonne-toi ».
#
# Usage : python3 outils/faire_documentaire.py outils/documentaires/messi.json [--apercu] [--de S --a S]
#   --apercu : 640x360 à 12 i/s pour vérifier le montage vite
#   --de/--a : ne rend qu'un extrait (en secondes)
#
# Le JSON décrit des « blocs » joués dans l'ordre. Un bloc a une durée fixe (carton) ou celle de sa
# voix (chapitre). Dans un bloc à voix, chaque plan démarre sur une phrase du texte : "p": n (index de
# phrase, à partir de 0) + "o": décalage en s. Les débuts de phrase viennent des silences de la voix.
import json, math, os, re, subprocess, sys, wave
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda p: p if os.path.isabs(p) else os.path.join(RACINE, p)
SR = 44100
JAUNE = (215, 255, 58); BLANC = (255, 255, 255); VERT = (14, 42, 31); ROUGE = (230, 57, 70); OR = (226, 185, 92)
POL = {"titre": P("medias/polices/BebasNeue-Regular.ttf"), "serif": P("medias/polices/PlayfairDisplay.ttf"),
       "serif_i": P("medias/polices/PlayfairDisplay-Italic.ttf"), "sans": "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
       "sans_r": "/usr/share/fonts/opentype/inter/Inter-Medium.otf"}
_F = {}
def F(nom, s, poids=None):
    k = (nom, s, poids)
    if k not in _F:
        f = ImageFont.truetype(POL[nom], s)
        if poids:
            try: f.set_variation_by_name(poids)
            except Exception: pass
        _F[k] = f
    return _F[k]

args = sys.argv[1:]
cfg = json.load(open(P(args[0])))
APERCU = "--apercu" in args
def arg(n, d=None):
    return float(args[args.index(n) + 1]) if n in args else d
WW, HH, FPS = (640, 360, 12) if APERCU else (1920, 1080, 30)
K = WW / 1920  # échelle des tailles (aperçu)
IMG = P(cfg["images"])

def ease(u): u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)
def ease_out(u): u = max(0.0, min(1.0, u)); return 1 - (1 - u) ** 3

def duree(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())

def lire_audio(f):
    raw = subprocess.check_output(["ffmpeg", "-v", "error", "-i", f, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"])
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()

# ---------- phrases et calage sur la voix ----------
def phrases(txt):
    txt = re.sub(r"\[[^\]]+\]", "", txt)
    morceaux = re.split(r"(?<=[\.\!\?…])\s+|\n+", txt)
    return [m.strip() for m in morceaux if len(re.sub(r"[\W_]", "", m)) > 0]

def silences(f):
    out = subprocess.run(["ffmpeg", "-i", f, "-af", "silencedetect=noise=-38dB:d=0.22", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    a = [float(x) for x in re.findall(r"silence_start: ([\d\.]+)", out)]
    b = [float(x) for x in re.findall(r"silence_end: ([\d\.]+)", out)]
    return list(zip(a, b))

def caler(bloc):
    """Renvoie la liste des débuts de phrase (s) dans la voix du bloc."""
    if bloc.get("calage"): return bloc["calage"]
    ph = phrases(bloc["texte"]); d = duree(P(bloc["voix"]))
    sil = [(a, b) for a, b in silences(P(bloc["voix"])) if a > 0.3 and b < d - 0.2]
    n = [len(x) for x in ph]; tot = sum(n)
    debut_voix = 0.0
    s0 = silences(P(bloc["voix"]))
    if s0 and s0[0][0] < 0.05: debut_voix = s0[0][1]
    t, est = debut_voix, []
    for x in n:
        est.append(t); t += x / tot * (d - debut_voix)
    res = [debut_voix]; libres = sorted(sil, key=lambda s: s[0])
    for e in est[1:]:
        cand = [s for s in libres if abs(s[1] - e) < 2.5 and s[1] > res[-1] + 0.4]
        if cand:
            best = min(cand, key=lambda s: abs(s[1] - e) - 0.6 * (s[1] - s[0]))
            res.append(max(best[1] - 0.05, res[-1] + 0.4))
        else:
            res.append(max(e, res[-1] + 0.4))
    return res

# ---------- construction de la frise ----------
blocs = cfg["blocs"]; frise = []; t = 0.0
for b in blocs:
    if b.get("voix"):
        b["_dvoix"] = duree(P(b["voix"]))
        b["_ph"] = caler(b)
        b["_t0"] = t; b["_av"] = b.get("avant", 0.6)
        b["_dur"] = b["_av"] + b["_dvoix"] + b.get("apres", 0.9)
    else:
        b["_t0"] = t; b["_dur"] = b["duree"]
    # plans absolus
    pl = []
    for p in b.get("plans", []):
        if "p" in p: st = b["_av"] + b["_ph"][p["p"]] + p.get("o", 0)
        else: st = p.get("t", 0)
        q = dict(p, _st=t + max(0, st))
        if "p_items" in p: q["_items"] = [b["_av"] + b["_ph"][j] for j in p["p_items"]]
        pl.append(q)
    for q in pl:
        if "_items" in q: q["_items"] = [t + x - q["_st"] for x in q["_items"]]
    pl.sort(key=lambda p: p["_st"])
    if pl: pl[0]["_st"] = t
    for i, p in enumerate(pl):
        p["_en"] = pl[i + 1]["_st"] if i + 1 < len(pl) else t + b["_dur"]
    b["_plans"] = pl; frise += pl
    t += b["_dur"]
TOT = t

# ---------- sources images ----------
_cache = {}
def source(nom, h=None):
    h = h or int(HH * 1.35)
    k = (nom, h)
    if k not in _cache:
        if len(_cache) > 10: _cache.pop(next(iter(_cache)))
        f = os.path.join(IMG, nom)
        if not os.path.splitext(f)[1]: f += ".jpg"
        im = Image.open(f).convert("RGB")
        r = max(h / im.height, (h * WW / HH) / im.width)
        _cache[k] = im.resize((max(1, round(im.width * r)), max(1, round(im.height * r))), Image.LANCZOS)
    return _cache[k]

_flou = {}
def fond_flou(nom):
    if nom not in _flou:
        if len(_flou) > 6: _flou.pop(next(iter(_flou)))
        im = source(nom).copy()
        im = im.resize((WW // 8, HH // 8), Image.BILINEAR, box=centre_box(im, 0.5, 0.5, 1.0))
        im = im.filter(ImageFilter.GaussianBlur(4)).resize((WW, HH), Image.BILINEAR)
        _flou[nom] = ImageEnhance.Brightness(im).enhance(0.45)
    return _flou[nom]

def centre_box(src, x, y, z):
    ch = src.height / z; cw = ch * WW / HH
    if cw > src.width: cw = src.width / z; ch = cw * HH / WW
    cx = min(max(x * src.width, cw / 2), src.width - cw / 2)
    cy = min(max(y * src.height, ch / 2), src.height - ch / 2)
    return (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)

def kenburns(nom, u, mv):
    x0, y0, z0, x1, y1, z1 = mv
    u = ease(u)
    src = source(nom)
    return src.resize((WW, HH), Image.BILINEAR, box=centre_box(src, x0 + (x1 - x0) * u, y0 + (y1 - y0) * u, z0 + (z1 - z0) * u))

def photo_cadre(nom, u, mv):
    """Photo verticale ou carrée : posée au centre sur un fond flou, qui zoome doucement."""
    x0, y0, z0, x1, y1, z1 = mv
    u = ease(u); z = z0 + (z1 - z0) * u
    f = os.path.join(IMG, nom if os.path.splitext(nom)[1] else nom + ".jpg")
    src = source(nom, int(HH * 1.3))
    h = int(HH * 0.9 * z); w = int(src.width * h / src.height)
    im = fond_flou(nom).copy()
    ph = src.resize((w, h), Image.BILINEAR)
    # recadrage vertical si plus haut que l'écran
    cy = y0 + (y1 - y0) * u
    top = int((h - HH * 0.9) * cy) if h > HH * 0.9 else 0
    ph = ph.crop((0, top, w, top + min(h, int(HH * 0.9))))
    x = int((WW - w) / 2 + (x1 - x0) * u * WW * 0.1)
    y = int((HH - ph.height) / 2)
    ombre = Image.new("L", (ph.width + 60, ph.height + 60), 0)
    ImageDraw.Draw(ombre).rectangle((30, 30, ph.width + 30, ph.height + 30), fill=170)
    ombre = ombre.filter(ImageFilter.GaussianBlur(int(18 * K) + 1))
    im.paste((0, 0, 0), (x - 30, y - 22), ombre)
    im.paste(ph, (x, y))
    return im

# ---------- textes ----------
def texte_centre(d, y, txt, font, fill, a=255, stroke=0, sf=(0, 0, 0)):
    tw = d.textlength(txt, font=font)
    d.text(((WW - tw) / 2, y), txt, font=font, fill=fill + (a,), stroke_width=stroke, stroke_fill=sf + (a,))
    return tw

def calque(): return Image.new("RGBA", (WW, HH), (0, 0, 0, 0))

def legende(im, txt, age, dur):
    """Légende façon documentaire en bas à gauche : trait jaune + texte qui se dévoile."""
    a = min(1, age / 0.5, max(0, (dur - age) / 0.5))
    if a <= 0: return im
    L = calque(); d = ImageDraw.Draw(L)
    x, y = int(90 * K), int(HH - 170 * K)
    w = int(70 * K * ease_out(age / 0.6))
    d.rectangle((x, y, x + w, y + max(1, int(5 * K))), fill=JAUNE + (int(255 * a),))
    n = int(len(txt) * min(1, age / 0.9))
    d.text((x, y + int(18 * K)), txt[:n], font=F("sans", int(38 * K)), fill=BLANC + (int(255 * a),))
    im.paste(L, (0, 0), L); return im

# ---------- plans spéciaux (animations) ----------
_land = None
def terres():
    global _land
    if _land is None:
        g = json.load(open(P("medias/carte/ne_50m_land.geojson")))
        polys = []
        for ft in g["features"]:
            gm = ft["geometry"]
            cs = gm["coordinates"] if gm["type"] == "MultiPolygon" else [gm["coordinates"]]
            for poly in cs: polys.append(np.array(poly[0]))
        _land = polys
    return _land

def carte(pl, age):
    """Carte animée : vue qui suit un trajet (liste de points lon/lat), arc lumineux, villes."""
    pts = pl["points"]; dur = pl["_en"] - pl["_st"]
    u = ease((age - 0.4) / max(dur - 1.6, 0.5))
    v0, v1 = pl.get("vue0"), pl.get("vue1")  # [lon_centre, lat_centre, largeur_en_degrés]
    v = [v0[i] + (v1[i] - v0[i]) * ease(age / max(dur, 0.1)) for i in range(3)]
    sc = WW / v[2]
    def pr(lon, lat):
        y = math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))
        yc = math.degrees(math.log(math.tan(math.pi / 4 + math.radians(v[1]) / 2)))
        return (WW / 2 + (lon - v[0]) * sc, HH / 2 - (y - yc) * sc)
    im = Image.new("RGB", (WW, HH), (8, 20, 18)); d = ImageDraw.Draw(im)
    # quadrillage
    for lo in range(-180, 181, 15):
        x, _ = pr(lo, 0); d.line((x, 0, x, HH), fill=(16, 38, 33), width=1)
    for la in range(-75, 76, 15):
        _, y = pr(0, la); d.line((0, y, WW, y), fill=(16, 38, 33), width=1)
    for poly in terres():
        if poly[:, 0].max() < v[0] - v[2] or poly[:, 0].min() > v[0] + v[2]: continue
        xy = [pr(lo, max(-85, min(85, la))) for lo, la in poly[::1]]
        d.polygon(xy, fill=(28, 66, 54), outline=(60, 120, 98))
    # arc (grand cercle approximé par une courbe de Bézier relevée)
    L = calque(); dl = ImageDraw.Draw(L)
    for i in range(len(pts) - 1):
        a = pr(*pts[i]["ll"]); b = pr(*pts[i + 1]["ll"])
        seg_u = max(0, min(1, u * (len(pts) - 1) - i))
        if seg_u <= 0: continue
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - math.dist(a, b) * pl.get("courbe", 0.12)
        N = 120; m = int(N * seg_u)
        c = [((1 - s) ** 2 * a[0] + 2 * (1 - s) * s * mx + s * s * b[0], (1 - s) ** 2 * a[1] + 2 * (1 - s) * s * my + s * s * b[1])
             for s in [k / N for k in range(m + 1)]]
        if len(c) > 1:
            dl.line(c, fill=JAUNE + (90,), width=max(2, int(14 * K)))
            dl.line(c, fill=JAUNE + (255,), width=max(1, int(5 * K)))
            hx, hy = c[-1]; r = 9 * K
            dl.ellipse((hx - r, hy - r, hx + r, hy + r), fill=BLANC + (255,))
    L2 = L.filter(ImageFilter.GaussianBlur(6 * K + 0.5))
    im.paste(L2, (0, 0), L2); im.paste(L, (0, 0), L)
    d = ImageDraw.Draw(im)
    for i, p in enumerate(pts):
        apparait = 0.4 + i * (dur - 1.6) / max(1, len(pts) - 1)
        a = min(1, (age - apparait + 0.4) / 0.4)
        if a <= 0: continue
        x, y = pr(*p["ll"]); r = (10 + 6 * math.sin(age * 4)) * K
        d.ellipse((x - r, y - r, x + r, y + r), outline=JAUNE, width=max(1, int(3 * K)))
        d.ellipse((x - 5 * K, y - 5 * K, x + 5 * K, y + 5 * K), fill=JAUNE)
        f = F("titre", int(64 * K)); f2 = F("sans_r", int(28 * K))
        dx = p.get("dx", 24) * K
        d.text((x + dx, y - 70 * K), p["nom"], font=f, fill=BLANC, stroke_width=max(1, int(3 * K)), stroke_fill=(0, 0, 0))
        if p.get("sous"): d.text((x + dx, y - 6 * K), p["sous"], font=f2, fill=JAUNE)
    return im

def fond_sombre(pl, age):
    if pl.get("fond"):
        im = kenburns(pl["fond"], age / max(pl["_en"] - pl["_st"], 0.1), pl.get("mv", [0.5, 0.5, 1.05, 0.5, 0.5, 1.15]))
        im = ImageEnhance.Brightness(im).enhance(pl.get("lum", 0.32))
        return im.filter(ImageFilter.GaussianBlur(pl.get("flou", 0) * K)) if pl.get("flou") else im
    im = Image.new("RGB", (WW, HH), (10, 16, 15))
    return im

def chiffre(pl, age):
    """Grand chiffre qui défile + libellé."""
    im = fond_sombre(pl, age); L = calque(); d = ImageDraw.Draw(L)
    val = pl["valeur"]; u = ease_out((age - 0.2) / pl.get("compte", 1.6))
    s = str(int(round(val * u))) if isinstance(val, int) else val
    a = int(255 * min(1, age / 0.3))
    f = F("titre", int(pl.get("taille", 340) * K))
    texte_centre(d, HH * 0.5 - f.size * 0.62, s + pl.get("suffixe", ""), f, pl.get("couleur") and tuple(pl["couleur"]) or JAUNE, a)
    la = int(255 * min(1, max(0, (age - 0.8) / 0.4)))
    texte_centre(d, HH * 0.5 + f.size * 0.42, pl["libelle"], F("sans", int(46 * K)), BLANC, la)
    if pl.get("sous"):
        texte_centre(d, HH * 0.5 + f.size * 0.42 + 70 * K, pl["sous"], F("sans_r", int(32 * K)), (200, 200, 200), la)
    im.paste(L, (0, 0), L); return im

def frise_finales(pl, age):
    """Une ligne par finale ; chaque ligne arrive, puis une croix rouge (ou une coupe dorée)."""
    im = fond_sombre(pl, age); L = calque(); d = ImageDraw.Draw(L)
    items = pl["items"]; n = len(items); dur = pl["_en"] - pl["_st"]
    pas = pl.get("pas", (dur - 1.0) / n)
    for i, (annee, quoi, res) in enumerate(items):
        t0 = pl["_items"][i] if "_items" in pl else 0.3 + i * pas; a = ease_out((age - t0) / 0.5)
        if a <= 0: continue
        y = HH / 2 - (n * 120 * K) / 2 + i * 120 * K
        x = WW * 0.27 - (1 - a) * 60 * K
        d.text((x, y), annee, font=F("titre", int(96 * K)), fill=JAUNE + (int(255 * a),))
        d.text((x + 230 * K, y + 22 * K), quoi, font=F("sans", int(48 * K)), fill=BLANC + (int(255 * a),))
        b = ease_out((age - t0 - 0.45) / 0.3)
        if b > 0:
            cx, cy, r = WW * 0.73, y + 50 * K, 34 * K * (0.6 + 0.4 * b)
            if res == "X":
                w = max(2, int(12 * K))
                d.line((cx - r, cy - r, cx + r, cy + r), fill=ROUGE + (int(255 * b),), width=w)
                d.line((cx - r, cy + r, cx + r, cy - r), fill=ROUGE + (int(255 * b),), width=w)
            else:
                d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=OR + (int(255 * b),))
                d.text((cx - 14 * K, cy - 30 * K), "★", font=F("sans", int(44 * K)), fill=VERT + (int(255 * b),))
    im.paste(L, (0, 0), L); return im

def ballons(pl, age):
    """Ballons d'Or : disques dorés qui s'allument un par un, avec l'année."""
    im = fond_sombre(pl, age); L = calque(); d = ImageDraw.Draw(L)
    ans = pl["annees"]; n = len(ans); dur = pl["_en"] - pl["_st"]
    pas = pl.get("pas", min(0.55, (dur - 1.5) / n))
    allume = 0
    for i, an in enumerate(ans):
        t0 = pl["_items"][i] if "_items" in pl else 0.4 + i * pas; a = ease_out((age - t0) / 0.35)
        cx = WW / 2 + (i - (n - 1) / 2) * 190 * K; cy = HH * 0.47; r = 70 * K
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(90, 80, 60, 255), width=max(1, int(3 * K)))
        if a > 0:
            allume += 1; rr = r * (0.5 + 0.5 * a)
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=OR + (int(255 * a),))
            f = F("titre", int(46 * K)); tw = d.textlength(str(an), font=f)
            d.text((cx - tw / 2, cy + r + 18 * K), str(an), font=f, fill=BLANC + (int(255 * a),))
    f = F("titre", int(120 * K))
    if pl.get("titre"):
        texte_centre(d, HH * 0.13, pl["titre"].replace("{n}", str(allume)), f, BLANC, 255)
    G = L.filter(ImageFilter.GaussianBlur(12 * K + 0.5))
    im.paste(G, (0, 0), G); im.paste(L, (0, 0), L); return im

def carton(pl, age):
    """Carton de chapitre : numéro, titre, années, sur image assombrie."""
    im = fond_sombre(pl, age); dur = pl["_en"] - pl["_st"]
    a = min(1, age / 0.6, max(0, (dur - age) / 0.5))
    L = calque(); d = ImageDraw.Draw(L)
    if pl.get("num"):
        texte_centre(d, HH * 0.30, pl["num"], F("sans", int(34 * K)), JAUNE, int(255 * a))
    sp = 1 + 0.03 * age
    f = F("titre", int(190 * K * sp))
    texte_centre(d, HH * 0.37, pl["titre"], f, BLANC, int(255 * a))
    w = int(220 * K * ease_out(age / 1.0))
    d.rectangle((WW / 2 - w / 2, HH * 0.37 + f.size * 1.02, WW / 2 + w / 2, HH * 0.37 + f.size * 1.02 + max(2, 5 * K)), fill=JAUNE + (int(255 * a),))
    if pl.get("annees"):
        texte_centre(d, HH * 0.37 + f.size * 1.12, pl["annees"], F("serif_i", int(46 * K)), BLANC, int(230 * a))
    im.paste(L, (0, 0), L); return im

def titre_film(pl, age):
    im = fond_sombre(pl, age); dur = pl["_en"] - pl["_st"]
    a = min(1, age / 1.2, max(0, (dur - age) / 0.8))
    L = calque(); d = ImageDraw.Draw(L)
    texte_centre(d, HH * 0.255, "LUCARNE FOOT PRÉSENTE", F("sans", int(30 * K)), JAUNE, int(255 * min(1, age / 0.6) * a))
    f = F("titre", int(300 * K * (1 + 0.025 * age)))
    texte_centre(d, HH * 0.32, pl["titre"], f, BLANC, int(255 * ease((age - 0.5) / 1.0) * a))
    texte_centre(d, HH * 0.32 + f.size * 0.98, pl["sous"], F("serif_i", int(64 * K)), BLANC, int(255 * ease((age - 1.4) / 1.0) * a))
    im.paste(L, (0, 0), L); return im

def citation(pl, age):
    im = fond_sombre(pl, age); dur = pl["_en"] - pl["_st"]
    a = min(1, age / 0.6, max(0, (dur - age) / 0.5))
    L = calque(); d = ImageDraw.Draw(L)
    f = F("serif_i", int(84 * K))
    lignes = pl["texte"].split("\n"); y = HH / 2 - len(lignes) * f.size * 0.65
    for ln in lignes:
        texte_centre(d, y, ln, f, BLANC, int(255 * a)); y += f.size * 1.3
    if pl.get("qui"):
        texte_centre(d, y + 20 * K, pl["qui"], F("sans", int(34 * K)), JAUNE, int(255 * a))
    im.paste(L, (0, 0), L); return im

LOGO = None
def ecran_fin(pl, age):
    global LOGO
    im = Image.new("RGB", (WW, HH), VERT); d = ImageDraw.Draw(im)
    # halo
    g = Image.new("L", (WW, HH), 0); ImageDraw.Draw(g).ellipse((WW * 0.15, -HH * 0.3, WW * 0.85, HH * 0.9), fill=110)
    g = g.filter(ImageFilter.GaussianBlur(160 * K + 1)); im.paste((40, 95, 64), (0, 0), g)
    if LOGO is None: LOGO = Image.open(P("medias/avatar_800.png")).convert("RGB")
    s = int(300 * K); lg = LOGO.resize((s, s), Image.LANCZOS)
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, s - 1, s - 1), int(40 * K), fill=255)
    a = ease_out(age / 0.6)
    im.paste(lg, (int(WW / 2 - s / 2), int(HH * 0.12 + (1 - a) * 40 * K)), m)
    d = ImageDraw.Draw(im)
    b = ease_out((age - 0.4) / 0.5)
    bw, bh = 560 * K * (0.8 + 0.2 * b), 120 * K * (0.8 + 0.2 * b)
    cx, cy = WW / 2, HH * 0.62
    pul = 1 + 0.03 * math.sin(age * 5)
    d.rounded_rectangle((cx - bw / 2 * pul, cy - bh / 2 * pul, cx + bw / 2 * pul, cy + bh / 2 * pul), int(24 * K), fill=ROUGE)
    f = F("titre", int(92 * K)); tw = d.textlength("ABONNE-TOI", font=f)
    d.text((cx - tw / 2, cy - f.size * 0.52), "ABONNE-TOI", font=f, fill=BLANC)
    for txt, y, fnt, c in ((pl.get("l1", ""), 0.75, F("sans", int(40 * K)), BLANC), (pl.get("l2", ""), 0.81, F("sans_r", int(30 * K)), JAUNE)):
        if txt: texte_centre(d, HH * y, txt, fnt, c)
    # zones vides à gauche/droite : emplacements des éléments d'écran de fin YouTube
    return im

SPECIAUX = {"carte": carte, "chiffre": chiffre, "finales": frise_finales, "ballons": ballons, "carton": carton,
            "titre": titre_film, "citation": citation, "fin": ecran_fin}

def plan_image(pl, t):
    age = t - pl["_st"]; dur = pl["_en"] - pl["_st"] + 0.6
    k = pl.get("k", "img")
    if k in SPECIAUX: return SPECIAUX[k](pl, age)
    mv = pl.get("mv", [0.5, 0.5, 1.0, 0.5, 0.5, 1.12])
    im = photo_cadre(pl["img"], age / dur, mv) if k == "cadre" else kenburns(pl["img"], age / dur, mv)
    if pl.get("noir_blanc"): im = ImageEnhance.Color(im).enhance(0.0)
    if pl.get("lum"): im = ImageEnhance.Brightness(im).enhance(pl["lum"])
    return im

# ---------- habillage global ----------
yy, xx = np.mgrid[0:HH, 0:WW]
_r = np.sqrt(((xx - WW / 2) / (WW * 0.62)) ** 2 + ((yy - HH / 2) / (HH * 0.62)) ** 2)
VIGN = np.clip(1.12 - 0.42 * _r ** 2, 0.45, 1.0)[..., None].astype(np.float32)
del yy, xx, _r
_rng = np.random.default_rng(3)
GRAINS = [_rng.normal(0, 5, (HH // 2, WW // 2, 1)).repeat(2, 0).repeat(2, 1).astype(np.float32) for _ in range(5)]
# étalonnage : ombres sarcelle, hautes lumières chaudes
LUT = np.zeros((256, 3), np.float32)
for i in range(256):
    x = i / 255; s = x * x * (3 - 2 * x)
    c = 0.85 * x + 0.15 * s
    LUT[i] = [c + 0.025 * (x - 0.5), c + 0.008 * (0.5 - abs(x - 0.5)), c - 0.03 * (x - 0.5)]
LUT = np.clip(LUT * 255, 0, 255)

def credit_de(pl):
    return pl.get("credit") or cfg.get("credits", {}).get(pl.get("img") or pl.get("fond") or "")

def frame(n):
    t = n / FPS
    i = 0
    for k, p in enumerate(frise):
        if p["_st"] <= t: i = k
    pl = frise[i]
    im = plan_image(pl, t)
    fondu = pl.get("fondu", 0.45)
    if i > 0 and fondu and t - pl["_st"] < fondu:
        prev = plan_image(frise[i - 1], t)
        im = Image.blend(prev, im, ease((t - pl["_st"]) / fondu))
    if pl.get("legende"):
        im = legende(im, pl["legende"], t - pl["_st"], pl["_en"] - pl["_st"])
    arr = np.asarray(im)
    if pl.get("k", "img") != "fin":
        arr = LUT[arr, [0, 1, 2]] if False else np.stack([LUT[arr[..., c], c] for c in range(3)], -1)
        arr = arr * VIGN + GRAINS[n % len(GRAINS)]
    else:
        arr = arr.astype(np.float32)
    # flash blanc / noir d'ouverture et de fin
    for tf in cfg.get("flashs", []):
        if 0 <= t - tf < 0.25: arr = arr + 255 * (1 - (t - tf) / 0.25) * 0.7
    if t < 0.8: arr = arr * (t / 0.8)
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    cr = credit_de(pl)
    if cr and pl.get("k", "img") in ("img", "cadre", "chiffre", "carton", "finales", "ballons", "citation"):
        f = F("sans_r", int(22 * K)); tw = d.textlength(cr, font=f)
        d.text((WW - tw - 28 * K, HH - 44 * K), cr, font=f, fill=(235, 235, 235), stroke_width=max(1, int(2 * K)), stroke_fill=(0, 0, 0))
    if pl.get("k", "img") not in ("fin", "titre"):
        f = F("titre", int(34 * K)); d.text((34 * K, 26 * K), "LUCARNE", font=f, fill=(255, 255, 255, 150))
    return im

# ---------- son ----------
def mixer(sortie_wav):
    N = int(TOT * SR) + SR
    voix = np.zeros((N, 2), np.float32); mus = np.zeros((N, 2), np.float32); sfx = np.zeros((N, 2), np.float32)
    def poser(buf, a, t0, gain=1.0, fi=0.0, fo=0.0, longueur=None):
        s = int(t0 * SR)
        if s >= N: return
        if longueur: a = a[:int(longueur * SR)]
        a = a[:N - s].copy()
        if fi > 0: a[:int(fi * SR)] *= np.linspace(0, 1, min(len(a), int(fi * SR)))[:, None]
        if fo > 0:
            m = min(len(a), int(fo * SR)); a[len(a) - m:] *= np.linspace(1, 0, m)[:, None]
        buf[s:s + len(a)] += a * gain
    for b in blocs:
        if b.get("voix"):
            poser(voix, lire_audio(P(b["voix"])), b["_t0"] + b["_av"], b.get("gain_voix", 1.0))
    # musiques : [fichier, début_s (absolu ou "bloc:index"), durée, gain, fondu_entrée, fondu_sortie, décalage_dans_le_fichier]
    def tabs(x):
        if isinstance(x, str) and x.startswith("bloc:"):
            j, *o = x[5:].split("+"); return blocs[int(j)]["_t0"] + (float(o[0]) if o else 0)
        return float(x)
    for m in cfg.get("musiques", []):
        f = P(m["fichier"])
        if not os.path.exists(f): continue
        a = lire_audio(f)[int(m.get("depuis", 0) * SR):]
        t0 = tabs(m["debut"]); fin = tabs(m["fin"]) if "fin" in m else t0 + len(a) / SR
        poser(mus, a, t0, m.get("gain", 0.5), m.get("fi", 1.5), m.get("fo", 2.5), longueur=fin - t0)
    for s in cfg.get("bruitages", []):
        f = P(s["fichier"])
        if not os.path.exists(f): continue
        poser(sfx, lire_audio(f), tabs(s["t"]), s.get("gain", 0.6), s.get("fi", 0.02), s.get("fo", 0.3), s.get("duree"))
    # ducking : la musique baisse quand la voix parle (enveloppe lissée)
    env = np.abs(voix).max(1)
    w = int(0.05 * SR); env = np.convolve(env, np.ones(w) / w, "same")
    parle = (env > 0.01).astype(np.float32)
    w2 = int(0.35 * SR); parle = np.convolve(parle, np.ones(w2) / w2, "same")
    duck = 1 - cfg.get("ducking", 0.62) * np.clip(parle * 1.5, 0, 1)
    mix = voix + mus * duck[:, None] + sfx
    pic = np.abs(mix).max()
    if pic > 0.98: mix *= 0.98 / pic
    with wave.open(sortie_wav, "w") as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes((np.clip(mix, -1, 1) * 32767).astype(np.int16).tobytes())

# ---------- rendu ----------
def rendre(job):
    a, b, f = job
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{WW}x{HH}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "19" if not APERCU else "28",
                           "-pix_fmt", "yuv420p", f], stdin=subprocess.PIPE)
    for n in range(a, b):
        ff.stdin.write(frame(n).tobytes())
        if (n - a) % 600 == 0: print(f"  {f[-12:]} {n - a}/{b - a}", flush=True)
    ff.stdin.close(); ff.wait()
    return f

if __name__ == "__main__":
    out = P(cfg["sortie"]) if not APERCU else P(cfg["sortie"]).replace(".mp4", "_apercu.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    t_de, t_a = arg("--de", 0.0), arg("--a", TOT)
    print(f"durée totale {TOT:.1f} s ({TOT / 60:.2f} min), rendu {t_de:.1f} → {t_a:.1f}")
    json.dump([{"t": round(p["_st"], 2), "k": p.get("k", "img"), "img": p.get("img", p.get("fond", ""))} for p in frise],
              open(out + ".plans.json", "w"), ensure_ascii=False, indent=0)
    wav = out + ".mix.wav"; mixer(wav)
    n0, n1 = int(t_de * FPS), int(t_a * FPS)
    NP = 4; pas = math.ceil((n1 - n0) / NP)
    jobs = [(n0 + k * pas, min(n1, n0 + (k + 1) * pas), out + f".part{k}.mp4") for k in range(NP) if n0 + k * pas < n1]
    with Pool(len(jobs)) as pool: parts = pool.map(rendre, jobs)
    lst = out + ".liste.txt"
    open(lst, "w").write("".join(f"file '{p}'\n" for p in parts))
    subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-ss", str(t_de), "-t", str(t_a - t_de),
                           "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-shortest",
                           "-movflags", "+faststart", out])
    for p in parts + [lst, wav]: os.remove(p)
    print("ok", out)
