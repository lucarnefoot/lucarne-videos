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

def fond(chemin, x=0.5, lum=0.55):
    im = Image.open(os.path.join(RACINE, chemin)).convert("RGB")
    k = HH / im.height
    im = im.resize((round(im.width * k), HH), Image.LANCZOS)
    cx = int(x * im.width); cw = WW
    l = min(max(cx - cw // 2, 0), im.width - cw)
    im = im.crop((l, 0, l + cw, HH))
    im = ImageEnhance.Brightness(im).enhance(lum)
    im = ImageEnhance.Contrast(im).enhance(1.15)
    return im

def vignette(v):
    im = fond(v["fond"], v.get("x", 0.5), v.get("lum", 0.55)) if v.get("fond") else Image.new("RGB", (WW, HH), BG)
    # dégradé sombre derrière le texte (texte_y : le texte commence plus bas, pour laisser voir un visage)
    ty = v.get("texte_y", 430)
    ov = Image.new("L", (WW, HH), 0); d = ImageDraw.Draw(ov)
    for y in range(HH):
        a = 0
        h0 = ty - 130
        if h0 < y < 1650: a = int((150 if ty == 430 else 200) * min(1, (y - h0) / 250, (1650 - y) / 250))
        d.line((0, y, WW, y), fill=a)
    im = Image.composite(Image.new("RGB", (WW, HH), (0, 0, 0)), im, ov)
    d = ImageDraw.Draw(im)
    # bandeau marque
    d.rounded_rectangle((60, 270, 400, 360), 22, fill=Y)
    d.text((88, 282), "LUCARNE", font=F(60), fill=BG)
    # accroche du haut (date / contexte)
    y = ty
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
    if v.get("credit"):
        tw = d.textlength(v["credit"], font=F(28))
        d.text((WW - tw - 30, HH - 70), v["credit"], font=F(28), fill=W, stroke_width=3, stroke_fill=(0, 0, 0))
    if v.get("lulu"):
        lulu = Image.open(os.path.join(RACINE, "medias/mascotte_lulu.png")).resize((300, 300))
        im.paste(lulu, (WW - 330, 1540), lulu)
    return im

def ecran_fin():
    # écran de fin : logo + « Abonne-toi », pour qu'on retienne la marque
    im = Image.new("RGB", (WW, HH), BG); d = ImageDraw.Draw(im)
    logo = Image.open(os.path.join(RACINE, "medias/avatar_800.png")).convert("RGB").resize((640, 640))
    m = Image.new("L", (640, 640), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 639, 639), 60, fill=255)
    im.paste(logo, ((WW - 640) // 2, 470), m)
    for t, s, c, y in (("ABONNE-TOI", 130, Y, 1180), ("@lucarnefoot333", 58, W, 1360), ("1 vidéo foot folle chaque jour", 44, W, 1450)):
        tw = d.textlength(t, font=F(s)); d.text(((WW - tw) / 2, y), t, font=F(s), fill=c)
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
        fin = os.path.join(RACINE, "medias/vignettes/_fin_abonne.png")
        ecran_fin().save(fin)
        # vignette sur les 2 premières images + écran logo « Abonne-toi » de 1,5 s à la fin
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", src, "-i", jpg,
                        "-loop", "1", "-framerate", "30", "-t", "1.5", "-i", fin,
                        "-f", "lavfi", "-t", "1.5", "-i", "anullsrc=r=44100:cl=mono", "-filter_complex",
                        "[1:v]scale=1080:1920,format=yuv420p[c];[0:v][c]overlay=0:0:enable='lt(n,2)',setsar=1,format=yuv420p[v0];"
                        "[2:v]scale=1080:1920,setsar=1,format=yuv420p,fade=t=in:st=0:d=0.2[v1];"
                        "[0:a]aformat=sample_rates=44100:channel_layouts=mono[a0];[3:a]aformat=sample_rates=44100:channel_layouts=mono[a1];"
                        "[v0][a0][v1][a1]concat=n=2:v=1:a=1[v][a]",
                        "-map", "[v]", "-map", "[a]", "-r", "30", "-c:v", "libx264", "-preset", "slow", "-crf", str(v.get("crf", 21))]
                       + (["-maxrate", v["maxrate"], "-bufsize", "6M"] if v.get("maxrate") else [])
                       + ["-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", tmp], check=True)
        os.replace(tmp, src)
    print("ok", nom)
