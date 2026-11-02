# Vignettes (photos de couverture) Lucarne Foot, 1080x1920.
# Usage : python3 outils/faire_vignette.py outils/vignettes.json [nom ...]
# Pour chaque entrée : crée medias/vignettes/<nom>.jpg, puis colle la vignette sur les 2 premières
# images de la vidéo (0,07 s) pour que TikTok et YouTube l'utilisent comme couverture (cover au temps 0).
# Le texte important reste dans la zone centrale 1080x1440 (ce que la grille TikTok affiche).
import json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WW, HH = 1080, 1920
Y = (215, 255, 58); W = (255, 255, 255); BG = (14, 42, 31); R = (255, 59, 59)
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
COUL = {"Y": Y, "W": W, "R": R}
def F(s): return ImageFont.truetype(BOLD, s)

def fond(chemin, x=0.5):
    im = Image.open(os.path.join(RACINE, chemin)).convert("RGB")
    k = HH / im.height
    im = im.resize((round(im.width * k), HH), Image.LANCZOS)
    cx = int(x * im.width); cw = WW
    l = min(max(cx - cw // 2, 0), im.width - cw)
    im = im.crop((l, 0, l + cw, HH))
    im = ImageEnhance.Brightness(im).enhance(0.55)
    im = ImageEnhance.Contrast(im).enhance(1.15)
    return im

def vignette(v):
    im = fond(v["fond"], v.get("x", 0.5)) if v.get("fond") else Image.new("RGB", (WW, HH), BG)
    # dégradé sombre derrière le texte
    ov = Image.new("L", (WW, HH), 0); d = ImageDraw.Draw(ov)
    for y in range(HH):
        a = 0
        if 300 < y < 1650: a = int(150 * min(1, (y - 300) / 250, (1650 - y) / 250))
        d.line((0, y, WW, y), fill=a)
    im = Image.composite(Image.new("RGB", (WW, HH), (0, 0, 0)), im, ov)
    d = ImageDraw.Draw(im)
    # bandeau marque
    d.rounded_rectangle((60, 270, 400, 360), 22, fill=Y)
    d.text((88, 282), "LUCARNE", font=F(60), fill=BG)
    # accroche du haut (date / contexte)
    y = 430
    if v.get("haut"):
        t = v["haut"]; f = F(64)
        tw = d.textlength(t, font=f)
        d.rounded_rectangle(((WW - tw) / 2 - 30, y - 10, (WW + tw) / 2 + 30, y + 86), 16, fill=(0, 0, 0))
        d.text(((WW - tw) / 2, y), t, font=f, fill=W)
        y += 150
    # gros texte, une ligne = [texte, couleur]
    for txt, c in v["gros"]:
        s = 230
        while d.textlength(txt, font=F(s)) > WW - 90 and s > 60: s -= 6
        tw = d.textlength(txt, font=F(s))
        d.text(((WW - tw) / 2, y), txt, font=F(s), fill=COUL[c], stroke_width=10, stroke_fill=(0, 0, 0))
        y += int(s * 1.08)
    y += 30
    for txt, c in v.get("bas", []):
        s = 82
        while d.textlength(txt, font=F(s)) > WW - 100 and s > 40: s -= 4
        tw = d.textlength(txt, font=F(s))
        d.text(((WW - tw) / 2, y), txt, font=F(s), fill=COUL[c], stroke_width=6, stroke_fill=(0, 0, 0))
        y += int(s * 1.2)
    if v.get("lulu"):
        lulu = Image.open(os.path.join(RACINE, "medias/mascotte_lulu.png")).resize((330, 330))
        im.paste(lulu, (WW - 360, 1330), lulu)
    return im

cfg = json.load(open(sys.argv[1]))
noms = sys.argv[2:] or list(cfg)
os.makedirs(os.path.join(RACINE, "medias/vignettes"), exist_ok=True)
for nom in noms:
    v = cfg[nom]
    jpg = os.path.join(RACINE, "medias/vignettes", nom + ".jpg")
    vignette(v).save(jpg, quality=92)
    if v.get("video"):
        src = os.path.join(RACINE, v["video"])
        tmp = src + ".tmp.mp4"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", jpg, "-filter_complex",
                        "[1:v]scale=1080:1920,format=yuv420p[c];[0:v][c]overlay=0:0:enable='lt(n,2)'[v]",
                        "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "slow", "-crf", "21",
                        "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, src)
    print("ok", nom)
