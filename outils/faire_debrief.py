# Gabarit « Debrief » Lucarne Foot : short 9:16 en textes animés, calé sur la voix off.
# Usage : python3 outils/faire_debrief.py outils/debriefs/<nom>.json
# Le JSON donne la voix (MP3 dans medias/voix/), la vidéo de sortie et les scènes.
# Chaque scène : [début dans le MP3 (s), [[texte, taille, couleur Y|W|R, délai (s)], ...], "lulu" ou null].
# Les débuts viennent des silences de la voix (ffmpeg silencedetect), un par phrase.
# Ensuite : python3 outils/faire_vignette.py outils/vignettes.json <nom> (couverture + écran ABONNE-TOI).
import json, math, os, shutil, subprocess, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG = (14, 42, 31); COUL = {"Y": (215, 255, 58), "W": (255, 255, 255), "R": (255, 59, 59)}
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
WW, HH, FPS = 1080, 1920, 30
FC = {}
def F(s):
    if s not in FC: FC[s] = ImageFont.truetype(BOLD, s)
    return FC[s]
def ease(t): t = max(0, min(1, t)); return 1 - (1 - t) ** 3
def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).decode())

cfg = json.load(open(sys.argv[1]))
mp3 = os.path.join(RACINE, cfg["voix"]); out = os.path.join(RACINE, cfg["sortie"])
off = cfg.get("decalage", 0.4); tag = cfg.get("tag", "DEBRIEF")
D = dur(mp3); TOT = round(off + D + 1.2, 2)
starts = [0.0] + [max(s[0] - 0.1, 0) + off for s in cfg["scenes"][1:]]
S = [(starts[k], starts[k + 1] if k + 1 < len(starts) else TOT, sc[1], sc[2]) for k, sc in enumerate(cfg["scenes"])]
print(cfg["sortie"], "voix", round(D, 2), "s → vidéo", TOT, "s")

base = Image.new("RGB", (WW, HH), BG)
ov = Image.new("RGB", (WW, HH), (0, 0, 0)); d = ImageDraw.Draw(ov)
d.ellipse((500, -500, 1500, 900), fill=(40, 95, 62)); ov = ov.filter(ImageFilter.GaussianBlur(220))
base = Image.composite(ov, base, Image.new("L", (WW, HH), 110))
dd = ImageDraw.Draw(base)
dd.ellipse((540 - 330, 1100 - 330, 540 + 330, 1100 + 330), outline=(26, 62, 44), width=8)
dd.line((0, 1100, WW, 1100), fill=(26, 62, 44), width=8)
lulu = Image.open(os.path.join(RACINE, "medias/mascotte_lulu.png"))

frames = "/tmp/lframes_debrief"; shutil.rmtree(frames, ignore_errors=True); os.makedirs(frames)
for i in range(int(TOT * FPS)):
    t = i / FPS
    a, b, lines, extra = next(s for s in S if s[0] <= t < s[1]) if t < S[-1][1] else S[-1]
    im = base.copy(); d = ImageDraw.Draw(im); lt = t - a; gap = 30
    hs = [F(sz).getbbox("ÉÀgy")[3] for _, sz, _, _ in lines]
    y = (HH - (sum(hs) + gap * (len(lines) - 1))) // 2 - (150 if extra else 0)
    for (txt, sz, col, dl), h in zip(lines, hs):
        p = ease((lt - dl) / 0.35)
        if p > 0:
            f = F(sz); tw = d.textlength(txt, font=f)
            while tw > WW - 100: sz -= 4; f = F(sz); tw = d.textlength(txt, font=f)
            layer = Image.new("RGBA", (WW, HH), (0, 0, 0, 0)); ld = ImageDraw.Draw(layer)
            ld.text(((WW - tw) / 2, y + (1 - p) * 60), txt, font=f, fill=COUL[col] + (int(255 * p),),
                    stroke_width=3, stroke_fill=(5, 20, 14, int(255 * p)))
            im.paste(layer, (0, 0), layer)
        y += h + gap
    if extra == "lulu":
        p = ease((lt - 0.4) / 0.5); s = int(380 * p)
        if s > 10:
            l = lulu.resize((s, s)); im.paste(l, ((WW - s) // 2, 1350 + int(12 * math.sin(lt * 6))), l)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, WW, 130), fill=COUL["Y"]); d.text((50, 32), "LUCARNE", font=F(66), fill=BG)
    d.text((WW - d.textlength(tag, font=F(40)) - 50, 48), tag, font=F(40), fill=BG)
    d.rectangle((0, HH - 24, WW, HH), fill=(20, 55, 40)); d.rectangle((0, HH - 24, int(WW * t / TOT), HH), fill=COUL["Y"])
    im.save(f"{frames}/f{i:05d}.png")

beat = frames + "/beat.wav"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i",
                f"aevalsrc='0.6*sin(2*PI*(55+80*exp(-30*mod(t,0.5)))*t)*exp(-12*mod(t,0.5))+0.08*(random(0)*2-1)*exp(-60*mod(t+0.25,0.5))':s=44100:d={TOT}",
                "-af", "afade=t=in:d=0.5,afade=t=out:st=%s:d=1.5,volume=0.7" % (TOT - 1.5), beat], check=True)
ms = int(off * 1000)
os.makedirs(os.path.dirname(out), exist_ok=True)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{frames}/f%05d.png", "-i", beat, "-i", mp3,
                "-filter_complex", f"[1:a]volume=-18dB[b];[2:a]adelay={ms}|{ms}[v];[b][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
                "-movflags", "+faststart", out], check=True)
shutil.rmtree(frames, ignore_errors=True)
print("ok", out)
