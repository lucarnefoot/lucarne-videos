# Rend un quiz Lucarne calé sur sa voix off (pauses <break> détectées par silencedetect).
# Usage : python3 faire_quiz.py quiz/<nom>.json <voix.mp3> <sortie.mp4>
# Chaque scène a "at": ["parole", i] (début du i-ème segment parlé) ou ["pause", j] (début de la j-ième pause, pour un compte à rebours).
import json, re, subprocess, sys, os, shutil
G=os.path.dirname(os.path.abspath(__file__))
spec=json.load(open(sys.argv[1])); mp3=sys.argv[2]; out=sys.argv[3]
D=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",mp3]))
err=subprocess.run(["ffmpeg","-hide_banner","-nostats","-i",mp3,"-af","silencedetect=noise=-35dB:d=0.7","-f","null","-"],capture_output=True,text=True).stderr
st=[float(x) for x in re.findall(r"silence_start: ([0-9.]+)",err)]; en=[float(x) for x in re.findall(r"silence_end: ([0-9.]+)",err)]
# ignore un silence initial / final
pairs=[(a,b) for a,b in zip(st,en) if a>0.2 and b<D-0.2]
# "ignorer_pauses" : indices (dans les pauses détectées) de silences naturels qui ne sont pas des <break>
pairs=[p for k,p in enumerate(pairs) if k not in spec.get("ignorer_pauses",[])]
assert len(pairs)==spec["pauses"], f"pauses détectées {len(pairs)} != attendues {spec['pauses']} : {pairs}"
def t(at):
    kind,i=at
    if kind=="parole": return 0.0 if i==0 else pairs[i-1][1]-0.1
    return pairs[i][0]+0.05
starts=[t(s["at"]) for s in spec["scenes"]]; TOT=round(D+1.5,2)
S=[[round(starts[k],2),round(starts[k+1] if k+1<len(starts) else TOT,2),s["lignes"],s.get("extra")] for k,s in enumerate(spec["scenes"])]
jf="/tmp/quiz_scenes.json"; json.dump([S,spec["bandeau"],os.path.join(os.path.dirname(os.path.abspath(out)),"_tmp_quiz.mp4")],open(jf,"w"),ensure_ascii=False)
frames="/tmp/qframes"; subprocess.run(["python3",os.path.join(G,"make_quiz.py"),jf,frames],check=True)
tmp=os.path.join(os.path.dirname(os.path.abspath(out)),"_tmp_quiz.mp4")
subprocess.run(["ffmpeg","-y","-loglevel","error","-i",tmp,"-i",mp3,"-filter_complex",
 "[0:a]volume=-18dB[b];[1:a]volume=1.0[v];[b][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
 "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-movflags","+faststart",out],check=True)
os.remove(tmp); shutil.rmtree(frames,ignore_errors=True); print("ok",out,TOT,"s")
