# Écrit le titre, la description YouTube (chapitres + crédits photo) et les tags du documentaire Messi.
# Usage : python3 outils/documentaires/description_messi.py <plans.json de la vidéo rendue> <sortie.md>
import json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(ICI, "messi.json")))
meta = json.load(open(os.path.join(ICI, "messi_photos.json")))
plans = json.load(open(sys.argv[1]))

def mmss(t): t = int(t); return f"{t // 60}:{t % 60:02d}"

# chapitres : début de chaque carton (et de l'épilogue)
noms = ["Rosario", "La serviette en papier", "L'envol", "Le roi de Barcelone", "La malédiction", "La rédemption", "Le dernier acte"]
cartons = [p["t"] for p in plans if p["k"] == "carton"]
epilogue = next(p["t"] for p in plans if p["t"] > cartons[-1] and p.get("img") == "ia_toise")
chap = [("0:00", "Prologue : l'enfant qui se piquait la jambe")]
chap += [(mmss(t), f"Chapitre {i + 1} · {n}") for i, (t, n) in enumerate(zip(cartons, noms))]
chap.append((mmss(epilogue), "Épilogue"))

# photos réellement utilisées
utilisees = []
for b in cfg["blocs"]:
    for p in b["plans"]:
        for k in ("img", "fond"):
            n = p.get(k)
            if n and n in meta and n not in utilisees: utilisees.append(n)

def ligne(n):
    m = meta[n]
    lic = {"Public domain": "domaine public"}.get(m["licence"], m["licence"])
    return f"• {m['auteur']} ({m.get('date', '')[:4] or 's. d.'}), {lic} : {m['page']}"

def groupes():
    g = {}
    for n in utilisees:
        m = meta[n]; lic = {"Public domain": "domaine public"}.get(m["licence"], m["licence"])
        g.setdefault((m["auteur"], lic), 0); g[(m["auteur"], lic)] += 1
    return [f"• {a}, {l}" + (f" ({k} photos)" if k > 1 else "") for (a, l), k in g.items()]

titre = "MESSI : le garçon qu'on disait trop petit (le documentaire)"
desc = f"""On lui a dit qu'il était trop petit. Pas assez argentin. Incapable de gagner avec son pays. Toute sa vie, Lionel Messi a répondu sur le terrain.

De Rosario à Barcelone, de la serviette en papier au toit du monde au Qatar, jusqu'à sa dernière finale perdue en 2026 : voici l'histoire complète de Lionel Messi, de sa naissance à aujourd'hui.

Demain sur Lucarne Foot : l'histoire de Cristiano Ronaldo. Abonne-toi pour ne pas la rater.

CHAPITRES
""" + "\n".join(f"{a} {b}" for a, b in chap) + """

SOURCES ET CRÉDITS
Photos sous licence libre, Wikimedia Commons (auteur et licence ; chaque photo est aussi créditée à l'écran, liens complets en commentaire épinglé) :
""" + "\n".join(groupes()) + """

Les licences CC BY et CC BY-SA demandent de citer l'auteur et la licence : https://creativecommons.org/licenses/
Les scènes d'ambiance (chambre, aciérie, serviette, vestiaire…) sont des reconstitutions générées par IA. Aucune ne montre le visage d'une personne réelle.
Voix off, musique originale et bruitages créés avec ElevenLabs.

#Messi #LionelMessi #Football #Documentaire #LucarneFoot
"""
tags = ["Messi", "Lionel Messi", "documentaire Messi", "histoire de Messi", "Messi Barcelone", "Messi Coupe du monde 2022",
        "Messi Argentine", "Messi Inter Miami", "Messi 2026", "Ballon d'Or", "football", "Lucarne Foot"]
out = f"""# Documentaire Messi : publication YouTube

## Titre
{titre}

## Description
```
{desc.strip()}
```

## Commentaire à épingler (liens des photos)
```
""" + "Sources des photos (Wikimedia Commons) :\n" + "\n".join(ligne(n) for n in utilisees) + """
```

## Tags
{", ".join(tags)}

## Réglages à cocher dans YouTube Studio
- **Contenu modifié ou synthétique : Oui.** La voix et les scènes d'ambiance sont générées par IA, il faut le déclarer.
- Catégorie : Sport. Langue : français. Public : « Non, cette vidéo n'est pas conçue pour les enfants ».
- Écran de fin : les 16 dernières secondes sont prévues pour ça (abonnement + vidéo suivante).
- Miniature : `vignette_messi.jpg`.
"""
open(sys.argv[2], "w").write(out); print(sys.argv[2])
