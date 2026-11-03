# Miniature YouTube 1280x720 du documentaire Messi.
# Usage : python3 outils/documentaires/vignette_messi.py [photo] [x_centre]
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = lambda p: os.path.join(RACINE, p)
W, H = 1280, 720
JAUNE = (215, 255, 58); BLANC = (255, 255, 255); VERT = (14, 42, 31)
TITRE = P("medias/polices/BebasNeue-Regular.ttf"); SANS = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
photo = sys.argv[1] if len(sys.argv) > 1 else "finale_070"
xc = float(sys.argv[2]) if len(sys.argv) > 2 else 0.58

im = Image.open(P(f"medias/documentaires/messi/{photo}.jpg")).convert("RGB")
k = H * 1.25 / im.height; im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
cx = int(xc * im.width); left = max(0, min(cx - int(W * 0.68), im.width - W)); top = int((im.height - H) * 0.3)
im = im.crop((left, top, left + W, top + H))
im = ImageEnhance.Contrast(im).enhance(1.12); im = ImageEnhance.Color(im).enhance(1.1)
# dégradé sombre à gauche pour le texte
g = Image.new("L", (W, H), 0); d = ImageDraw.Draw(g)
for x in range(W):
    d.line((x, 0, x, H), fill=int(235 * max(0, min(1, (0.62 - x / W) / 0.35))))
im = Image.composite(Image.new("RGB", (W, H), (6, 14, 12)), im, g)
d = ImageDraw.Draw(im)
f1 = ImageFont.truetype(SANS, 44); f2 = ImageFont.truetype(TITRE, 190); f3 = ImageFont.truetype(TITRE, 92)
d.text((56, 150), "ON LE DISAIT", font=f1, fill=BLANC)
d.text((50, 196), "TROP", font=f2, fill=JAUNE, stroke_width=4, stroke_fill=(0, 0, 0))
d.text((50, 360), "PETIT", font=f2, fill=JAUNE, stroke_width=4, stroke_fill=(0, 0, 0))
d.text((56, 545), "MESSI · LE DOCUMENTAIRE", font=ImageFont.truetype(SANS, 34), fill=BLANC)
# toise (règle de taille) le long du bord gauche du texte
for i in range(0, 13):
    y = 196 + i * 28; L = 26 if i % 4 == 0 else 14
    d.line((22, y, 22 + L, y), fill=BLANC, width=3)
d.line((22, 196, 22, 196 + 12 * 28), fill=BLANC, width=3)
# pastille marque
d.rounded_rectangle((50, 48, 280, 108), 14, fill=JAUNE)
d.text((70, 52), "LUCARNE", font=ImageFont.truetype(TITRE, 58), fill=VERT)
out = P("medias/documentaires/messi/vignette_messi.jpg")
im.save(out, quality=92); print(out)
