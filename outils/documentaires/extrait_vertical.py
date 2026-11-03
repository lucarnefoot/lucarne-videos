# Extrait vertical 9:16 (TikTok, Reels, Shorts) tiré du documentaire 16:9 déjà rendu.
# Mise en page : accroche en haut, film au milieu (pleine largeur), sous-titres en dessous, fond flouté.
# Usage : python3 outils/documentaires/extrait_vertical.py outils/documentaires/messi.json documentaires/lucarne_doc_messi.mp4 sortie.mp4
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda p: p if os.path.isabs(p) else os.path.join(RACINE, p)
cfg_path, source, sortie = sys.argv[1:4]

# timings des phrases : on réutilise le calage du moteur
src = open(os.path.join(RACINE, "outils/faire_documentaire.py")).read()
src = src.split("# ---------- son ----------")[0]
sys.argv = ["x", cfg_path]
ns = {"__name__": "moteur", "__file__": os.path.join(RACINE, "outils/faire_documentaire.py")}; exec(compile(src, "faire_documentaire.py", "exec"), ns)
blocs, phrases = ns["blocs"], ns["phrases"]

# --- découpage : (début, fin) dans le film 16:9 ---
SEGMENTS = [(97.0, 114.54), (118.44, 179.75)]  # fin du chap. 1 (le traitement) + chap. 2 (la serviette), sans le carton
ACCROCHE = ("ON LE DISAIT", "TROP PETIT", "pour devenir footballeur")
FIN = 3.6  # carte de fin (s)
W, H, FPS = 1080, 1920, 30
VH = 608; VY = 640  # film au milieu

def vers_sortie(t):
    acc = 0.0
    for a, b in SEGMENTS:
        if a <= t <= b: return acc + t - a
        acc += b - a
    return None

# sous-titres : chaque phrase coupée en morceaux de 7 mots max, durée au prorata des caractères
subs = []
for b in blocs:
    if not b.get("voix"): continue
    ph = phrases(b["texte"]); deb = [b["_t0"] + b["_av"] + x for x in b["_ph"]]
    fins = deb[1:] + [b["_t0"] + b["_av"] + b["_dvoix"]]
    for txt, t0, t1 in zip(ph, deb, fins):
        mots = txt.split(); n = max(1, round(len(mots) / 7 + 0.49)); k = -(-len(mots) // n)
        morceaux = [" ".join(mots[i:i + k]) for i in range(0, len(mots), k)]
        tot = sum(len(m) for m in morceaux); t = t0
        for m in morceaux:
            d = (t1 - t0 - 0.15) * len(m) / tot
            a, z = vers_sortie(t), vers_sortie(min(t + d, t1 - 0.05))
            if a is not None and z is not None and z > a: subs.append((a, z, m))
            t += d
DUREE = sum(b - a for a, b in SEGMENTS)

# --- polices et calques fixes ---
BEBAS = P("medias/polices/BebasNeue-Regular.ttf"); INTER = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
JAUNE = (215, 255, 58)
def police(f, s): return ImageFont.truetype(f, s)

def calque_haut():
    c = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((60, 120, 300, 186), 14, fill=JAUNE)
    d.text((80, 122), "LUCARNE", font=police(BEBAS, 62), fill=(14, 42, 31))
    y = 250
    for i, (txt, f, col) in enumerate([(ACCROCHE[0], police(INTER, 52), (255, 255, 255)),
                                        (ACCROCHE[1], police(BEBAS, 190), JAUNE),
                                        (ACCROCHE[2], police(INTER, 46), (255, 255, 255))]):
        tw = d.textlength(txt, font=f); d.text(((W - tw) / 2, y), txt, font=f, fill=col, stroke_width=3, stroke_fill=(0, 0, 0))
        y += [64, 186, 0][i]
    f = police(INTER, 36); txt = "L'histoire complète : Lucarne Foot sur YouTube"
    tw = d.textlength(txt, font=f); d.text(((W - tw) / 2, 1740), txt, font=f, fill=(230, 230, 230), stroke_width=2, stroke_fill=(0, 0, 0))
    return c
HAUT = calque_haut()

def calque_sub(txt):
    c = Image.new("RGBA", (W, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(c); f = police(INTER, 62)
    mots, lignes, cur = txt.split(), [], ""
    for m in mots:
        essai = (cur + " " + m).strip()
        if d.textlength(essai, font=f) > 960 and cur: lignes.append(cur); cur = m
        else: cur = essai
    lignes.append(cur)
    y = 10
    for l in lignes[:3]:
        tw = d.textlength(l, font=f); d.text(((W - tw) / 2, y), l, font=f, fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0)); y += 78
    return c
SUBS = [(a, z, calque_sub(t)) for a, z, t in subs]

def carte_fin(fond):
    im = fond.copy(); d = ImageDraw.Draw(im)
    for txt, f, col, y in [("L'HISTOIRE COMPLÈTE", police(BEBAS, 120), (255, 255, 255), 760),
                           ("DE LIONEL MESSI", police(BEBAS, 120), JAUNE, 880),
                           ("9 minutes · sur YouTube", police(INTER, 52), (255, 255, 255), 1040),
                           ("Lucarne Foot", police(INTER, 64), JAUNE, 1120)]:
        tw = d.textlength(txt, font=f); d.text(((W - tw) / 2, y), txt, font=f, fill=col, stroke_width=4, stroke_fill=(0, 0, 0))
    return im

# --- 1) découpe de l'image et du son du film ---
tmp = sortie + ".seg.mp4"
fc, n = [], len(SEGMENTS)
for i, (a, b) in enumerate(SEGMENTS):
    fc.append(f"[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}]")
    fc.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.12,afade=t=out:st={b - a - 0.15}:d=0.15[a{i}]")
fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", P(source), "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]",
                       "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-c:a", "pcm_s16le", tmp.replace(".mp4", ".mkv")])
tmp = tmp.replace(".mp4", ".mkv")

# son final : extrait + queue musicale sous la carte de fin
wav = sortie + ".wav"
musique = P("medias/documentaires/messi/musique/m5_dernier.mp3")
subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ss", "128", "-t", str(FIN + 0.5), "-i", musique, "-filter_complex",
                       f"[1:a]volume=0.55,afade=t=in:d=0.4,afade=t=out:st={FIN - 1.2}:d=1.2,adelay={int((DUREE - 0.2) * 1000)}|{int((DUREE - 0.2) * 1000)}[m];"
                       f"[0:a][m]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", wav])

# --- 2) composition verticale image par image ---
lec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", tmp, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
ecr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", P(sortie)], stdin=subprocess.PIPE)
taille = 1920 * 1080 * 3; k = 0; dernier = None
def composer(fr, t, sous_titres=True):
    fond = fr.resize((192, 108)).resize((int(H * 16 / 9), H), Image.BILINEAR)
    x0 = (fond.width - W) // 2; fond = fond.crop((x0, 0, x0 + W, H)).filter(ImageFilter.GaussianBlur(18))
    fond = Image.fromarray((np.asarray(fond) * 0.35).astype(np.uint8))
    fond.paste(fr.resize((W, VH), Image.LANCZOS), (0, VY))
    im = fond.convert("RGBA"); im.alpha_composite(HAUT)
    if sous_titres:
        for a, z, c in SUBS:
            if a <= t < z: im.alpha_composite(c, (0, VY + VH + 60)); break
    return im.convert("RGB")
while True:
    raw = lec.stdout.read(taille)
    if len(raw) < taille: break
    fr = Image.frombytes("RGB", (1920, 1080), raw); t = k / FPS
    im = composer(fr, t); ecr.stdin.write(im.tobytes()); dernier = fr; k += 1
# carte de fin : dernière image figée et assombrie
base = composer(Image.fromarray((np.asarray(dernier) * 0.45).astype(np.uint8)), 0, False)
fin = carte_fin(base)
for j in range(int(FIN * FPS)):
    u = min(1, j / 8); ecr.stdin.write(Image.blend(base, fin, u).tobytes())
ecr.stdin.close(); ecr.wait(); lec.wait()
for f in (tmp, wav): os.remove(f)
print("ok", sortie, f"{DUREE + FIN:.1f} s", len(subs), "sous-titres")
