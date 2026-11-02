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
lulu=Image.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","medias","mascotte_lulu.png"))
import sys, json
S,TAG,NAME=json.load(open(sys.argv[1]))
S=[(a,b,[tuple(x[:2])+(tuple(x[2]),x[3]) for x in L],e) for a,b,L,e in S]
TOT=S[-1][1]
def ease(t): t=max(0,min(1,t)); return 1-(1-t)**3
frames=sys.argv[2]; os.makedirs(frames,exist_ok=True)
n=int(TOT*FPS)
for i in range(n):
    t=i/FPS
    sc=next(s for s in S if s[0]<=t<s[1])
    im=base.copy(); d=ImageDraw.Draw(im)
    lt=t-sc[0]
    lines=sc[2]; gap=30
    hs=[F(sz).getbbox("ÉÀgy")[3] for _,sz,_,_ in lines]
    total=sum(hs)+gap*(len(lines)-1)
    y=(HH-total)//2 - (150 if sc[3]=='lulu' else (420 if isinstance(sc[3],str) else 0))
    for (txt,sz,col,dl),h in zip(lines,hs):
        p=ease((lt-dl)/0.35)
        if p>0:
            f=F(sz); tw=d.textlength(txt,font=f)
            while tw>WW-100: sz-=4; f=F(sz); tw=d.textlength(txt,font=f)
            layer=Image.new("RGBA",(WW,HH),(0,0,0,0)); ld=ImageDraw.Draw(layer)
            ld.text(((WW-tw)/2,y+(1-p)*60),txt,font=f,fill=col+(int(255*p),),stroke_width=3,stroke_fill=(5,20,14,int(255*p)))
            im.paste(layer,(0,0),layer)
        y+=h+gap
    if isinstance(sc[3],str) and sc[3].startswith("countdown"):
        n0=int(sc[3].split(":")[1]); k=max(1,n0-int(lt))
        frac=lt-int(lt); s=int(420*(1.15-0.15*ease(frac/0.3)))
        f=F(s); txt=str(k); tw=d.textlength(txt,font=f)
        d.ellipse((540-300,1180-300,540+300,1180+300),outline=Y,width=16)
        d.arc((540-300,1180-300,540+300,1180+300),-90,-90+360*(lt/n0),fill=R,width=16)
        d.text(((WW-tw)/2,1180-s*0.62),txt,font=f,fill=Y)
    if sc[3]=="lulu":
        p=ease((lt-0.4)/0.5); s=int(380*p)
        if s>10:
            bob=int(12*math.sin(lt*6))
            l=lulu.resize((s,s)); im.paste(l,((WW-s)//2,1350+bob),l)
    # header band + progress bar
    d=ImageDraw.Draw(im)
    d.rectangle((0,0,WW,130),fill=Y); d.text((50,32),"LUCARNE",font=F(66),fill=BG)
    d.text((WW-d.textlength(TAG,font=F(40))-50,48),TAG,font=F(40),fill=BG)
    d.rectangle((0,HH-24,WW,HH),fill=(20,55,40)); d.rectangle((0,HH-24,int(WW*t/TOT),HH),fill=Y)
    im.save(f"{frames}/f{i:05d}.png")
# soundtrack: simple beat (kick + hat) synthesized
subprocess.run(["ffmpeg","-y","-loglevel","error","-f","lavfi","-i",
 f"aevalsrc='0.6*sin(2*PI*(55+80*exp(-30*mod(t,0.5)))*t)*exp(-12*mod(t,0.5))+0.08*(random(0)*2-1)*exp(-60*mod(t+0.25,0.5))':s=44100:d={TOT}",
 "-af","afade=t=in:d=0.5,afade=t=out:st=%s:d=1.5,volume=0.7"%(TOT-1.5),frames+"/beat.wav"],check=True)
subprocess.run(["ffmpeg","-y","-loglevel","error","-framerate",str(FPS),"-i",f"{frames}/f%05d.png","-i",frames+"/beat.wav",
 "-c:v","libx264","-pix_fmt","yuv420p","-crf","20","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",
 NAME if NAME.startswith("/") else OUT+NAME],check=True)
print("done")
