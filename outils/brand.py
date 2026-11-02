from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, os
OUT="/mnt/project-files/lucarne/"
os.makedirs(OUT, exist_ok=True)
BG=(14,42,31); Y=(215,255,58); W=(255,255,255); G=(46,139,87); R=(255,59,59)
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def F(s): return ImageFont.truetype(BOLD, s)

def glow_bg(w,h):
    im=Image.new("RGB",(w,h),BG)
    ov=Image.new("RGB",(w,h),(0,0,0)); d=ImageDraw.Draw(ov)
    d.ellipse((w*0.55,-h*0.3,w*1.3,h*0.6),fill=(40,90,60))
    ov=ov.filter(ImageFilter.GaussianBlur(min(w,h)//6))
    return Image.blend(im, Image.eval(ov,lambda v:v), 0.0) if False else Image.composite(ov,im,Image.new("L",(w,h),90))

def ball(d,cx,cy,r,fill=Y,line=BG):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=fill)
    # pentagon center
    pts=[(cx+r*0.38*math.cos(math.radians(-90+72*i)), cy+r*0.38*math.sin(math.radians(-90+72*i))) for i in range(5)]
    d.polygon(pts,fill=line)
    for (px,py) in pts:
        ang=math.atan2(py-cy,px-cx)
        d.line((px,py,cx+r*math.cos(ang),cy+r*math.sin(ang)),fill=line,width=max(2,r//14))

def goal_logo(d,x,y,s,with_text=True):
    # goal frame (posts + bar) with ball in top-right corner
    lw=max(4,s//18)
    d.line((x,y+s*0.75,x,y-lw//2),fill=W,width=lw)
    d.line((x-lw//2,y,x+s*1.2+lw//2,y),fill=W,width=lw)
    d.line((x+s*1.2,y-lw//2,x+s*1.2,y+s*0.75),fill=W,width=lw)
    ball(d,int(x+s*1.2-s*0.2),int(y+s*0.2),int(s*0.16))

# Avatar 800x800
im=glow_bg(800,800); d=ImageDraw.Draw(im)
goal_logo(d,160,170,330)
f=F(118); t="LUCARNE"; tw=d.textlength(t,font=f)
d.text(((800-tw)/2,500),t,font=f,fill=W)
f2=F(40); t2="FOOT EN 45 SECONDES"; d.text(((800-d.textlength(t2,font=f2))/2,650),t2,font=f2,fill=Y)
im.save(OUT+"avatar_800.png")

# Banner 2560x1440 (safe area 1546x423 centered)
im=glow_bg(2560,1440); d=ImageDraw.Draw(im)
# pitch lines
d.ellipse((1280-520,720-520,1280+520,720+520),outline=(30,70,50),width=10)
d.line((1280,0,1280,1440),fill=(30,70,50),width=10)
goal_logo(d,540,560,260)
f=F(190); d.text((940,555),"LUCARNE",font=f,fill=W)
f2=F(64); d.text((950,775),"Le foot raconté en 45 secondes",font=f2,fill=Y)
f3=F(44); d.text((950,860),"Debriefs · Stats folles · Légendes · Pronos de Lulu",font=f3,fill=W)
im.save(OUT+"banniere_youtube_2560x1440.png")

# Mascotte Lulu 1080x1080
im=Image.new("RGBA",(1080,1080),(0,0,0,0)); d=ImageDraw.Draw(im)
cx,cy,r=540,560,400
d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=Y,outline=BG,width=18)
# patches
for ang in (200,340):
    px=cx+r*0.78*math.cos(math.radians(ang)); py=cy+r*0.78*math.sin(math.radians(ang))
    pts=[(px+70*math.cos(math.radians(a)),py+70*math.sin(math.radians(a))) for a in range(0,360,72)]
    d.polygon(pts,fill=BG)
# eyes
for ex in (cx-140,cx+140):
    d.ellipse((ex-85,cy-170,ex+85,cy+20),fill=W,outline=BG,width=10)
    d.ellipse((ex-30,cy-90,ex+40,cy-10),fill=BG)
    d.ellipse((ex,cy-80,ex+18,cy-62),fill=W)
# eyebrow (cheeky)
d.line((cx-220,cy-215,cx-70,cy-190),fill=BG,width=22)
d.line((cx+70,cy-200,cx+220,cy-240),fill=BG,width=22)
# grin
d.chord((cx-170,cy+20,cx+170,cy+250),0,180,fill=BG)
d.chord((cx-120,cy+120,cx+120,cy+250),20,160,fill=R)
im.save(OUT+"mascotte_lulu.png")

# Thumbnail template vertical 1080x1920
im=glow_bg(1080,1920); d=ImageDraw.Draw(im)
d.rectangle((0,0,1080,150),fill=Y); d.text((60,38),"LUCARNE",font=F(76),fill=BG)
d.text((60,560),"SÉNÉGAL",font=F(150),fill=W); d.text((60,740),"1 - 0",font=F(230),fill=Y); d.text((60,1000),"FRANCE",font=F(150),fill=W)
d.text((60,1220),"LE JOUR OÙ LE MONDE",font=F(70),fill=W); d.text((60,1310),"A ÉTÉ CHOQUÉ",font=F(70),fill=R)
lulu=Image.open(OUT+"mascotte_lulu.png").resize((420,420)); im.paste(lulu,(620,1420),lulu)
im.save(OUT+"vignette_exemple_1080x1920.png")
print("ok")
