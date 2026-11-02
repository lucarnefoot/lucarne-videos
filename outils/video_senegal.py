from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, subprocess, os
OUT="/mnt/project-files/lucarne/"
BG=(14,42,31); Y=(215,255,58); W=(255,255,255); R=(255,59,59)
BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FC={}
def F(s):
    if s not in FC: FC[s]=ImageFont.truetype(BOLD,s)
    return FC[s]
WW,HH,FPS=1080,1920,30
base=Image.new("RGB",(WW,HH),BG)
ov=Image.new("RGB",(WW,HH),(0,0,0)); d=ImageDraw.Draw(ov)
d.ellipse((500,-500,1500,900),fill=(40,95,62)); ov=ov.filter(ImageFilter.GaussianBlur(220))
base=Image.composite(ov,base,Image.new("L",(WW,HH),110))
dd=ImageDraw.Draw(base)
dd.ellipse((540-330,1100-330,540+330,1100+330),outline=(26,62,44),width=8); dd.line((0,1100,WW,1100),fill=(26,62,44),width=8)
lulu=Image.open(OUT+"mascotte_lulu.png")
# scenes: (start,end,[(text,size,color,delay)], extra)
S=[(0,3.5,[("LE JOUR OÙ",110,W,0),("LE SÉNÉGAL",120,Y,0.25),("A CHOQUÉ",110,W,0.5),("LE MONDE",110,R,0.75)],None),
 (3.5,8,[("31 MAI 2002",110,Y,0),("SÉOUL",90,W,0.3),("Match d'ouverture",60,W,0.8),("de la Coupe du monde",60,W,1.0)],None),
 (8,14,[("EN FACE :",80,W,0),("LA FRANCE",120,Y,0.3),("Championne du monde",58,W,1.0),("en titre (1998)",58,W,1.2),("Championne d'Europe",58,W,2.0),("en titre (2000)",58,W,2.2)],None),
 (14,19,[("LE SÉNÉGAL ?",110,Y,0),("Sa toute première",64,W,0.6),("Coupe du monde.",64,W,0.8),("Personne n'y croit.",64,R,1.8)],None),
 (19,27,[("30e MINUTE",120,Y,0),("Diouf déborde à gauche…",54,W,0.8),("centre…",54,W,1.8),("PAPA BOUBA",110,W,3.0),("DIOP !",150,Y,3.3)],None),
 (27,31.5,[("SÉNÉGAL",110,W,0),("1 - 0",260,Y,0.3),("FRANCE",110,W,0.6)],None),
 (31.5,37,[("La France :",64,W,0),("éliminée au 1er tour,",64,R,0.3),("sans marquer un but.",64,R,0.6),("Le Sénégal :",64,W,2.0),("quart de finale.",64,Y,2.3)],None),
 (37,42,[("Tu étais devant",80,W,0),("ce match ?",80,W,0.2),("Dis-le en commentaire",58,Y,0.8),("ABONNE-TOI",90,Y,1.6)],"lulu")]
TOT=S[-1][1]
def ease(t): t=max(0,min(1,t)); return 1-(1-t)**3
frames="/tmp/lframes"; os.makedirs(frames,exist_ok=True)
n=int(TOT*FPS)
for i in range(n):
    t=i/FPS
    sc=next(s for s in S if s[0]<=t<s[1])
    im=base.copy(); d=ImageDraw.Draw(im)
    lt=t-sc[0]
    lines=sc[2]; gap=30
    hs=[F(sz).getbbox("ÉÀgy")[3] for _,sz,_,_ in lines]
    total=sum(hs)+gap*(len(lines)-1)
    y=(HH-total)//2 - (150 if sc[3] else 0)
    for (txt,sz,col,dl),h in zip(lines,hs):
        p=ease((lt-dl)/0.35)
        if p>0:
            f=F(sz); tw=d.textlength(txt,font=f)
            while tw>WW-100: sz-=4; f=F(sz); tw=d.textlength(txt,font=f)
            layer=Image.new("RGBA",(WW,HH),(0,0,0,0)); ld=ImageDraw.Draw(layer)
            ld.text(((WW-tw)/2,y+(1-p)*60),txt,font=f,fill=col+(int(255*p),),stroke_width=3,stroke_fill=(5,20,14,int(255*p)))
            im.paste(layer,(0,0),layer)
        y+=h+gap
    if sc[3]=="lulu":
        p=ease((lt-0.4)/0.5); s=int(380*p)
        if s>10:
            bob=int(12*math.sin(lt*6))
            l=lulu.resize((s,s)); im.paste(l,((WW-s)//2,1350+bob),l)
    # header band + progress bar
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,WW,130),fill=Y); d.text((50,32),"LUCARNE",font=F(66),fill=BG)
    d.text((WW-d.textlength("IL Y A X ANS",font=F(40))-50,48),"IL Y A X ANS",font=F(40),fill=BG)
    d.rectangle((0,HH-24,WW,HH),fill=(20,55,40)); d.rectangle((0,HH-24,int(WW*t/TOT),HH),fill=Y)
    im.save(f"{frames}/f{i:05d}.png")
# soundtrack: simple beat (kick + hat) synthesized
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",
 f"aevalsrc='0.6*sin(2*PI*(55+80*exp(-30*mod(t,0.5)))*t)*exp(-12*mod(t,0.5))+0.08*(random(0)*2-1)*exp(-60*mod(t+0.25,0.5))':s=44100:d={TOT}",
 "-af","afade=t=in:d=0.5,afade=t=out:st=%s:d=1.5,volume=0.7"%(TOT-1.5),"/tmp/beat.wav"],check=True)
subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",f"{frames}/f%05d.png","-i","/tmp/beat.wav",
 "-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",
 OUT+"video_test_senegal_france_2002.mp4"],check=True)
print("done")
