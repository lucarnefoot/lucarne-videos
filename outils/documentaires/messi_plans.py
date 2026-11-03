# Génère outils/documentaires/messi.json (le découpage du documentaire Messi).
# Chaque plan démarre sur une phrase de la voix : P(n, ...) = phrase n (voir la liste des phrases
# avec : python3 outils/documentaires/messi_plans.py --phrases).
import json, os, re, sys

ICI = os.path.dirname(os.path.abspath(__file__))
D = "medias/documentaires/messi"
textes = json.load(open(os.path.join(ICI, "messi_textes.json")))
meta = json.load(open(os.path.join(ICI, "messi_photos.json")))

def credit(nom):
    m = meta[nom]
    lic = m["licence"]
    if lic in ("Public domain", "CC0"): return f"Photo : {m['auteur']}, domaine public" if lic != "CC0" else f"Photo : {m['auteur']}, CC0"
    return f"Photo : {m['auteur']}, {lic}"

# mouvements : [x0, y0, zoom0, x1, y1, zoom1] (x, y = centre du cadrage entre 0 et 1)
def zin(x=0.5, y=0.5, a=1.0, b=1.15): return [x, y, a, x, y, b]
def zout(x=0.5, y=0.5, a=1.18, b=1.02): return [x, y, a, x, y, b]
def pan(x0, x1, y=0.5, z=1.12): return [x0, y, z, x1, y, z]

def P(n, img=None, k="img", o=0.0, **kw):
    d = {"p": n, "o": o}
    if img: d["img"] = img
    if k != "img": d["k"] = k
    d.update(kw); return d

def voix(i): return f"{D}/voix/{i:02d}.mp3"

def carton(num, titre, annees, fond, mv=None):
    return {"duree": 4.2, "plans": [{"k": "carton", "num": num, "titre": titre, "annees": annees, "fond": fond, "lum": 0.28,
                                     "mv": mv or zin(0.5, 0.5, 1.05, 1.18)}]}

blocs = []
# 0 · PROLOGUE
blocs.append({"voix": voix(0), "texte": textes[0], "avant": 2.0, "apres": 0.6, "plans": [
    P(0, "rosario_nuit", mv=pan(0.35, 0.6, 0.5, 1.15), legende="ROSARIO · ARGENTINE"),
    P(1, "ia_rue", mv=zin(0.5, 0.55)),
    P(2, "ia_chambre", mv=zin(0.5, 0.5, 1.0, 1.2)),
    P(3, "ia_seringue", mv=zin(0.5, 0.5, 1.05, 1.3)),
    P(6, "ia_seringue", mv=pan(0.35, 0.6, 0.5, 1.35), noir_blanc=True),
    P(8, "ia_toise", mv=zin(0.5, 0.45, 1.0, 1.2)),
    P(9, "ia_terrain_terre", mv=zout(0.5, 0.5)),
    P(10, "finale_070", mv=zin(0.58, 0.42, 1.0, 1.25)),
    P(11, "egypte_178", mv=zin(0.5, 0.45, 1.05, 1.2)),
    P(12, "barca_2011_poty", mv=zin(0.5, 0.4, 1.0, 1.3)),
]})
# 1 · TITRE
blocs.append({"duree": 6.5, "plans": [{"k": "titre", "titre": "MESSI", "sous": "Le garçon qui ne devait pas grandir",
                                       "fond": "finale_070", "lum": 0.3, "mv": zin(0.58, 0.45, 1.1, 1.3)}]})
# 2-3 · ROSARIO
blocs.append(carton("CHAPITRE 1", "ROSARIO", "1987 – 2000", "rosario_coucher"))
blocs.append({"voix": voix(1), "texte": textes[1], "plans": [
    P(0, "rosario_parana", mv=pan(0.3, 0.6), legende="ROSARIO · 24 JUIN 1987"),
    P(1, "ia_acierie", mv=zin(0.5, 0.5)),
    P(3, "ia_rue", mv=pan(0.6, 0.4, 0.5, 1.12)),
    P(4, "ia_grandmere", mv=zin(0.5, 0.55, 1.0, 1.18)),
    P(6, "ia_terrain_terre", mv=pan(0.35, 0.6, 0.55, 1.15)),
    P(8, "ia_terrain_terre", mv=zin(0.6, 0.6, 1.25, 1.5)),
    P(10, "predio_03", mv=pan(0.4, 0.6), legende="NEWELL'S OLD BOYS"),
    P(12, k="chiffre", valeur="87", libelle="« LA MACHINE DE 87 »", sous="l'équipe de jeunes de Newell's", fond="predio_09", taille=360, compte=0.1),
    P(13, "ia_ciel", mv=zin(0.5, 0.45, 1.0, 1.15)),
    P(14, "barca_2015_cf", mv=zin(0.5, 0.4, 1.05, 1.25)),
    P(16, "ia_toise", mv=pan(0.4, 0.55, 0.5, 1.25)),
    P(18, k="citation", texte="Déficit en hormone\nde croissance", qui="LE DIAGNOSTIC", fond="ia_toise", lum=0.3),
    P(20, k="chiffre", valeur=1000, suffixe=" $", libelle="PAR MOIS", sous="le coût du traitement", fond="ia_seringue", lum=0.25),
    P(22, "rosario_1914", mv=zin(0.5, 0.5, 1.0, 1.15), noir_blanc=True),
]})
# 4-5 · LA SERVIETTE
blocs.append(carton("CHAPITRE 2", "LA SERVIETTE EN PAPIER", "2000 – 2004", "ia_serviette"))
blocs.append({"voix": voix(2), "texte": textes[2], "plans": [
    P(0, "ia_avion", mv=zin(0.5, 0.5, 1.0, 1.15), legende="SEPTEMBRE 2000"),
    P(1, k="carte", points=[{"nom": "ROSARIO", "sous": "Argentine", "ll": [-60.65, -32.95]},
                            {"nom": "BARCELONE", "sous": "Espagne", "ll": [2.17, 41.39], "dx": -260}],
      vue0=[-58, -28, 70], vue1=[-30, 8, 125], courbe=0.1),
    P(2, "masia_canplanas", mv=pan(0.35, 0.6)),
    P(3, "ia_terrain_masia", mv=zin(0.5, 0.6, 1.0, 1.2)),
    P(5, "campnou_2005", mv=zin(0.5, 0.5, 1.0, 1.15), noir_blanc=True),
    P(8, "ia_serviette", mv=pan(0.4, 0.6), legende="BARCELONE · 14 DÉCEMBRE 2000"),
    P(9, "ia_serviette", mv=zin(0.5, 0.5, 1.0, 1.35)),
    P(12, k="citation", texte="« Ce bout de papier\nva changer l'histoire\ndu football. »", fond="ia_serviette", lum=0.22),
    P(13, "masia_2012", mv=pan(0.6, 0.4), legende="LA MASIA · FÉVRIER 2001"),
    P(15, "ia_avion", mv=zout(0.5, 0.5)),
    P(17, "ia_terrain_masia", mv=pan(0.6, 0.4, 0.5, 1.2)),
    P(18, "ia_dortoir", mv=zin(0.5, 0.5, 1.0, 1.2)),
    P(19, "ia_seringue", mv=zin(0.5, 0.5, 1.15, 1.35)),
    P(21, "ia_dortoir", mv=zout(0.5, 0.5, 1.25, 1.0)),
]})
# 6-7 · L'ENVOL
blocs.append(carton("CHAPITRE 3", "L'ENVOL", "2004 – 2008", "campnou_2014_03"))
blocs.append({"voix": voix(3), "texte": textes[3], "plans": [
    P(0, "masia_2012", mv=zin(0.5, 0.5)),
    P(1, k="chiffre", valeur=30, suffixe=" CM", libelle="GAGNÉS À LA MASIA", fond="masia_canplanas", lum=0.25),
    P(2, "ia_terrain_masia", mv=pan(0.35, 0.6)),
    P(3, "campnou_pano", mv=pan(0.2, 0.8, 0.5, 1.6), legende="16 OCTOBRE 2004 · 17 ANS"),
    P(5, "barca_2007_gol", mv=zin(0.5, 0.45, 1.0, 1.2), legende="1er MAI 2005 · PREMIER BUT"),
    P(8, "campnou_2017", mv=zout(0.5, 0.5)),
    P(9, "barca_2007_gol", mv=pan(0.35, 0.6, 0.45, 1.3), legende="18 AVRIL 2007 · CONTRE GETAFE"),
    P(10, k="chiffre", valeur=5, libelle="ADVERSAIRES ÉLIMINÉS, GARDIEN COMPRIS", fond="campnou_aerien", lum=0.25, compte=2.2),
    P(12, "campnou_2014_03", mv=zin(0.5, 0.4, 1.0, 1.2)),
    P(13, k="citation", texte="« C'est le but\nde Maradona en 1986. »", fond="campnou_nuit", lum=0.25),
    P(14, "arg_2010b", mv=zin(0.5, 0.4), legende="PÉKIN 2008 · CHAMPION OLYMPIQUE"),
    P(15, "barca_2009_gamper", mv=zin(0.5, 0.4, 1.0, 1.25)),
]})
# 8-9 · LE ROI DE BARCELONE
blocs.append(carton("CHAPITRE 4", "LE ROI DE BARCELONE", "2008 – 2021", "campnou_nuit"))
blocs.append({"voix": voix(4), "texte": textes[4], "plans": [
    P(0, "barca_2009_takasu", mv=zin(0.5, 0.45)),
    P(2, "barca_2009_carrera", mv=pan(0.35, 0.6, 0.5, 1.15), legende="BERNABÉU · 2 MAI 2009"),
    P(3, k="chiffre", valeur="6 – 2", libelle="REAL MADRID – BARÇA", sous="Messi joue en « faux 9 »", fond="barca_2009_carrera", lum=0.22, compte=0.1, taille=300),
    P(6, k="chiffre", valeur=6, suffixe=" / 6", libelle="TROPHÉES EN 2009", fond="barca_2011_trio", lum=0.25),
    P(9, k="ballons", titre="{n} BALLONS D'OR", annees=[2009, 2010, 2011, 2012], fond="barca_2011_poty", lum=0.2, p_items=[9, 10, 11, 12]),
    P(13, k="chiffre", valeur=91, libelle="BUTS EN UNE ANNÉE CIVILE (2012)", sous="record du monde", fond="barca_2011_arsenal", lum=0.25, compte=2.0),
    P(15, "barca_2014_a", mv=pan(0.4, 0.6)),
    P(15, "barca_2011_mallorca", o=2.8, mv=zin(0.5, 0.45)),
    P(16, k="chiffre", valeur=672, libelle="BUTS AVEC LE BARÇA", sous="record du club", fond="campnou_2017", lum=0.25, compte=2.2),
    P(17, "arg_2010", mv=zin(0.5, 0.4, 1.0, 1.25)),
    P(19, "arg_suisse_2012", mv=zin(0.5, 0.45, 1.05, 1.3)),
]})
# 10-11 · LA MALÉDICTION
blocs.append(carton("CHAPITRE 5", "LA MALÉDICTION", "2007 – 2016", "arg_xhaka_2012"))
blocs.append({"voix": voix(5), "texte": textes[5], "plans": [
    P(0, "arg_2010", mv=pan(0.4, 0.6, 0.45, 1.15)),
    P(1, "ia_journaux", mv=zin(0.5, 0.5, 1.0, 1.2)),
    P(3, "arg_xhaka_2012", k="cadre", mv=zin(0.5, 0.4, 1.0, 1.08)),
    P(4, k="finales", items=[["2007", "Copa América", "X"], ["2014", "Coupe du monde", "X"], ["2015", "Copa América", "X"], ["2016", "Copa América", "X"]],
      fond="ia_vestiaire", lum=0.18, p_items=[5, 6, 11, 12]),
    P(14, "ia_vestiaire", mv=zin(0.5, 0.5, 1.0, 1.25)),
    P(15, k="citation", texte="« Pour moi,\nla sélection, c'est fini. »", qui="LIONEL MESSI · 26 JUIN 2016", fond="ia_vestiaire", lum=0.2),
    P(16, k="chiffre", valeur="4", libelle="FINALES · 4 DÉFAITES", fond="arg_suisse_2012", lum=0.2, compte=0.1),
    P(18, "ia_vestiaire", mv=zout(0.5, 0.5), noir_blanc=True),
    P(19, "arg_2022_supporters", mv=pan(0.35, 0.6)),
    P(21, "arg_2018_penalty", mv=zin(0.5, 0.45, 1.0, 1.2)),
]})
# 12-13 · LA RÉDEMPTION
blocs.append(carton("CHAPITRE 6", "LA RÉDEMPTION", "2021 – 2022", "arg_2022_mexique"))
blocs.append({"voix": voix(6), "texte": textes[6], "plans": [
    P(0, "arg_2018_penalty", mv=zout(0.5, 0.45), noir_blanc=True),
    P(1, k="chiffre", valeur="1 – 0", libelle="ARGENTINE – BRÉSIL", sous="finale de la Copa América · Maracanã · 10 juillet 2021", fond="arg_2022_supporters", lum=0.25, compte=0.1, taille=300),
    P(2, "ia_genoux", mv=zin(0.5, 0.55, 1.0, 1.2)),
    P(6, "campnou_nuit", mv=zin(0.5, 0.5, 1.0, 1.2), noir_blanc=True, legende="AOÛT 2021"),
    P(8, "ia_conference", mv=zin(0.5, 0.5, 1.0, 1.15)),
    P(9, "psg_trio_2021", mv=pan(0.4, 0.6), legende="PARIS SAINT-GERMAIN · 2021 – 2023"),
    P(10, "psg_trio_2022", mv=zin(0.5, 0.45)),
    P(11, "arg_2022_mexique", mv=zin(0.5, 0.4, 1.0, 1.2), legende="QATAR · NOVEMBRE 2022"),
    P(13, k="chiffre", valeur="1 – 2", libelle="ARGENTINE – ARABIE SAOUDITE", sous="premier match, 22 novembre 2022", fond="arg_2022_mexique", lum=0.2, compte=0.1, taille=300),
    P(15, "arg_2022_mexique", mv=pan(0.35, 0.6, 0.4, 1.3)),
    P(17, k="chiffre", valeur="3 – 3", libelle="ARGENTINE – FRANCE", sous="finale de la Coupe du monde · 18 décembre 2022", fond="arg_2022_supporters", lum=0.22, compte=0.1, taille=300),
    P(21, "ia_penalty", mv=zin(0.5, 0.55, 1.0, 1.3)),
    P(24, "arg_2022_supporters", mv=zin(0.5, 0.5, 1.15, 1.0), flash=True),
    P(25, "ia_trophee", mv=zin(0.5, 0.5, 1.0, 1.2)),
    P(27, "finale_222", mv=zin(0.5, 0.45, 1.0, 1.2)),
]})
# 14-15 · LE DERNIER ACTE
blocs.append(carton("CHAPITRE 7", "LE DERNIER ACTE", "2023 – 2026", "miami_ne_143"))
blocs.append({"voix": voix(7), "texte": textes[7], "plans": [
    P(0, k="ballons", titre="{n} BALLONS D'OR", annees=[2009, 2010, 2011, 2012, 2015, 2019, 2021, 2023], lum=0.2, pas=0.3),
    P(2, "miami_ne_143", mv=pan(0.4, 0.6), legende="INTER MIAMI · DEPUIS 2023"),
    P(3, "miami_nycfc_051", mv=zin(0.5, 0.45)),
    P(4, "miami_nycfc_081", mv=zin(0.5, 0.45, 1.05, 1.25), legende="CHAMPION DE MLS · DÉCEMBRE 2025"),
    P(5, "miami_2025", k="cadre", mv=zin(0.5, 0.3, 1.0, 1.08)),
    P(6, "egypte_105", k="cadre", mv=zin(0.5, 0.3, 1.0, 1.08), legende="COUPE DU MONDE 2026"),
    P(8, "ronaldo_messi_2011", k="cadre", mv=zin(0.5, 0.35, 1.0, 1.1)),
    P(9, k="chiffre", valeur="3 + 2", libelle="BUTS CONTRE L'ALGÉRIE PUIS L'AUTRICHE", fond="egypte_226", lum=0.22, compte=0.1, taille=300),
    P(11, "egypte_312", mv=zin(0.5, 0.45, 1.0, 1.2), legende="MEILLEUR BUTEUR DE L'HISTOIRE DE LA COUPE DU MONDE"),
    P(12, "egypte_lautaro", mv=pan(0.4, 0.6)),
    P(13, "finale_046", mv=zin(0.5, 0.45), legende="NEW JERSEY · 19 JUILLET 2026"),
    P(14, "finale_090", mv=pan(0.4, 0.6, 0.45, 1.15)),
    P(15, k="chiffre", valeur="0 – 1", libelle="ARGENTINE – ESPAGNE", sous="Ferran Torres, 106e minute, en prolongation", fond="finale_093", lum=0.22, compte=0.1, taille=300),
    P(17, "finale_070", mv=zin(0.6, 0.42, 1.0, 1.3)),
    P(18, "finale_305", mv=zin(0.5, 0.45, 1.0, 1.15), noir_blanc=True, legende="31 AOÛT 2026 · RETRAITE INTERNATIONALE"),
    P(20, k="chiffre", valeur=126, libelle="BUTS AVEC L'ARGENTINE", sous="record de la sélection", fond="finale_076", lum=0.22, compte=2.0),
]})
# 16 · ÉPILOGUE (+ appel)
blocs.append({"voix": voix(8), "texte": textes[8], "apres": 0.4, "plans": [
    P(0, "ia_toise", mv=zin(0.5, 0.45, 1.0, 1.15)),
    P(1, "barca_2011_poty", mv=zin(0.5, 0.4, 1.0, 1.15)),
    P(2, "arg_2010", mv=zin(0.5, 0.4)),
    P(3, "ia_trophee", mv=zin(0.5, 0.5, 1.1, 1.25)),
    P(4, "arg_2018_penalty", mv=zin(0.5, 0.45)),
    P(5, "arg_2022_supporters", mv=pan(0.4, 0.6)),
    P(6, "finale_070", mv=zin(0.6, 0.42, 1.0, 1.2), noir_blanc=True),
    P(8, "mural_barcelone", k="cadre", mv=zin(0.5, 0.4, 1.0, 1.1)),
    P(9, "ia_terrain_terre", mv=zin(0.5, 0.55, 1.0, 1.2)),
    P(10, "ia_serviette", mv=zin(0.5, 0.5, 1.1, 1.4)),
    P(11, k="fin", l1="Demain : l'histoire de Cristiano Ronaldo", l2="@lucarnefoot333", fondu=0.8),
]})
# 17 · ÉCRAN DE FIN (20 s : place pour les éléments d'écran de fin YouTube)
blocs.append({"duree": 16.0, "plans": [{"k": "fin", "l1": "Demain : l'histoire de Cristiano Ronaldo", "l2": "@lucarnefoot333", "fondu": 0}]})

credits = {n: credit(n) for n in meta}
cfg = {"titre": "MESSI — Le garçon qui ne devait pas grandir", "images": D, "sortie": "documentaires/lucarne_doc_messi.mp4",
       "credits": credits, "blocs": blocs, "ducking": 0.65,
       "musiques": [], "bruitages": []}
json.dump(cfg, open(os.path.join(ICI, "messi.json"), "w"), ensure_ascii=False, indent=1)
print("ok", len(blocs), "blocs")
