# Cale les scènes d'une vidéo Lucarne sur sa voix off, rend la vidéo et mixe voix + beat (-18 dB).
# Usage : python3 caler_voix.py <nom>   (nom = senegal | messi | remontada | onze_secondes | zidane)
import json, re, subprocess, sys, os, shutil
G = os.path.dirname(os.path.abspath(__file__))
L = os.path.dirname(G)
V = os.path.join(L, "voix")
FIN = os.path.join(L, "final")
os.makedirs(FIN, exist_ok=True)

# scène source, décalage de la voix (s), instants (dans le MP3) où commencent les scènes 1..n.
# Instants tirés de la transcription ElevenLabs Scribe (horodatage mot à mot).
CFG = {
 "senegal": ("senegal", 1.5, [0.0, 4.76, 9.056, 13.92, 20.445, 21.641, 27.574]),
 "messi": ("messi_91", 0, [1.196, 6.989, 14.791, 19.052, 24.393]),
 "remontada": ("remontada", 1.5, [0.0, 11.018, 19.18, 23.684, 25.809, 29.814]),
 "onze_secondes": ("11_secondes", 0, [2.67, 3.843, 8.882, 13.468, 17.241]),
 "zidane": ("zidane_2006", 0, [3.332, 8.742, 15.639, 19.725, 25.855, 31.602]),
}

def senegal_scenes():
    src = open(os.path.join(G, "video_senegal.py")).read()
    W, Y, R = [255, 255, 255], [215, 255, 58], [255, 59, 59]
    m = re.search(r"^S=\[(.*?)\]\nTOT", src, re.S | re.M)
    S = eval("[" + m.group(1) + "]", {"W": W, "Y": Y, "R": R, "None": None})
    return [[a, b, [[t, s, list(c), d] for t, s, c, d in lines], e] for a, b, lines, e in S], "IL Y A X ANS", "x.mp4"

def script_text(nom):
    md = open(os.path.join(L, "voix_off_5_scripts.md")).read()
    m = re.search(r"## \d\. " + nom + r"\.mp3\n(.*?)(?:\n## |\Z)", md, re.S)
    return m.group(1).strip()

def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", f]).decode())

def silence_ends(f):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af",
                          "silencedetect=noise=-35dB:d=0.15", "-f", "null", "-"], capture_output=True, text=True).stderr
    return [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", out)]

nom = sys.argv[1]
scene_name, off, anchors = CFG[nom]
if nom == "senegal":
    S, TAG, _ = senegal_scenes()
else:
    S, TAG, _ = json.load(open(os.path.join(G, "scenes", scene_name + ".json")))
assert len(anchors) == len(S) - 1, (len(anchors), len(S))
mp3 = os.path.join(V, nom + ".mp3")
D = dur(mp3)
starts = [0.0] + [max(t - 0.1, 0) + off for t in anchors]
TOT = round(off + D + 1.5, 2)
starts[0] = 0.0
# la scène d'accroche dure au moins 1 s
for k in range(1, len(starts)):
    starts[k] = max(starts[k], starts[k - 1] + 1.0)
newS = [[round(starts[k], 2), round(starts[k + 1] if k + 1 < len(S) else TOT, 2), S[k][2], S[k][3]]
        for k in range(len(S))]
tmpname = "final/_tmp_" + nom + ".mp4"
jf = os.path.join(G, "scenes", "voix_" + nom + ".json")
json.dump([newS, TAG, tmpname], open(jf, "w"), ensure_ascii=False)
print(nom, "voix", round(D, 2), "s → vidéo", TOT, "s ; débuts", [s[0] for s in newS])

frames = "/tmp/lframes_" + nom
subprocess.run(["python3", os.path.join(G, "make_short.py"), jf, frames], check=True)
tmp = os.path.join(L, tmpname)
out = os.path.join(FIN, "lucarne_" + nom + ".mp4")
ms = int(off * 1000)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", mp3, "-filter_complex",
                f"[0:a]volume=-18dB[b];[1:a]adelay={ms}|{ms},volume=1.0[v];[b][v]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.95[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out],
               check=True)
os.remove(tmp)
shutil.rmtree(frames, ignore_errors=True)
print("ok", out)
