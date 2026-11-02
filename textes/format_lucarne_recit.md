# Format « Lucarne Récit » (inspiré de MARA! / @maratrium)

## 1. Ce qu'on sait du format MARA!

TikTok et YouTube ne sont pas accessibles depuis l'environnement de travail : l'analyse vient de recherches web (descriptions de chaîne, titres de vidéos), pas du visionnage des vidéos.

- **Compte** : MARA! (@maratrium), créateur français, environ 1,5 M d'abonnés TikTok et 231 k sur Instagram. Bio YouTube : « Je raconte des trucs ».
- **Promesse** : des histoires 100 % réelles (faits divers, mystères, histoire, parcours de célébrités), « racontées à travers des animations visuelles immersives et une voix captivante ».
- **Sujets** : très larges, et le foot y marche déjà (« La main de Dieu, Diego Maradona »). Il y a aussi des séries en plusieurs parties (« L'histoire de Gims – Partie 1 », environ 400 k likes).
- **Signature** : un son d'ouverture reconnaissable (« MARA! 🔔 »). Le format est assez connu pour qu'il existe des tutos « faire des vidéos comme MARA avec l'IA ».

Ce qui fait marcher ce type de vidéo :
1. **Accroche en une phrase** qui pose un mystère ou un paradoxe, sans contexte avant.
2. **Récit chronologique tendu** : date, lieu, enjeu, obstacle, retournement, chute.
3. **Une image différente toutes les 2 à 3 secondes**, toujours en mouvement (zoom, panoramique), qui illustre la phrase en cours.
4. **Sous-titres mot à mot**, gros, au centre, le mot prononcé en couleur (beaucoup regardent sans le son).
5. **Voix de conteur** qui ralentit, chuchote, puis explose sur le retournement.
6. **Fin ouverte** : question en commentaire, « partie 2 », ou « la prochaine est encore plus folle ».
7. **Plus d'une minute** : c'est ce qui rend la vidéo éligible à la rémunération TikTok (voir § 4).

## 2. Adaptation Lucarne Foot

| Élément | Lucarne Récit |
|---|---|
| Durée | 61 à 75 s (au-dessus d'1 min pour le programme de rémunération TikTok) |
| Images | images IA « peinture cinéma », palette sarcelle/orange, **joueurs de dos ou en silhouette, jamais de visage reconnaissable**, pas de logo de club |
| Mouvement | chaque image est recadrée en 9:16 et bouge (panoramique + zoom lent) ; coupe sèche toutes les 1,5 à 3 s |
| Sous-titres | 1 à 3 mots, majuscules, mot en cours en jaune Lucarne |
| Voix | Oscar Doré (ElevenLabs, modèle v4) avec balises d'émotion : `[softly]`, `[nervous]`, `[whispers]`, `[excited]` |
| Son | nappe sombre qui passe en majeur au retournement, battements de cœur pendant le suspense, souffle à chaque coupe, impact + flash blanc sur le moment clé |
| Signature | coup de sifflet très court à 0 s (notre « 🔔 ») + pastille LUCARNE en haut à gauche |
| Fin | carte « LUCARNE FOOT – 1 histoire de foot folle chaque jour » + question en commentaire |

Structure type du script (environ 170 à 190 mots) :
1. **Accroche** (0–6 s) : le paradoxe en une phrase. « Un footballeur s'est mis à genoux… et tout un pays en guerre l'a écouté. »
2. **Contexte** (6–16 s) : date, lieu, enjeu.
3. **Montée** (16–24 s) : suspense, phrases courtes.
4. **Retournement** (24–30 s) : impact, flash.
5. **Le vrai sujet** (30–46 s) : ce que l'histoire raconte au-delà du score.
6. **Chute** (46–62 s) : conséquence surprenante, dernier détail qui claque.
7. **Appel** (62 s et après) : question et abonnement.

## 3. Fabrication (outil `outils/faire_recit.py`)

1. Écrire le script (structure ci-dessus) et générer la voix : Oscar Doré, modèle `eleven_v4`.
2. Transcrire la voix avec Scribe pour avoir l'horodatage mot à mot, à enregistrer dans `outils/recits/<nom>_mots.json`.
3. Générer 10 à 12 images IA (une par moment du récit). **Demander du 9:16 dans les réglages du nœud**, pas seulement dans le texte : le prototype est sorti en 16:9 et a dû être recadré.
4. Écrire `outils/recits/<nom>.json` : liste des plans `[début_s, image, x_départ, x_arrivée, zoom_départ, zoom_arrivée]` calés sur les mots, plus les temps forts (impact, sifflet).
5. `python3 outils/faire_recit.py outils/recits/<nom>.json`. Le rendu prend environ 4 min et produit environ 25 Mo.

Coût ElevenLabs du prototype : voix 2 × 1 285 crédits (2 prises), 44 images × 190 crédits, transcription 365 crédits, soit environ 11 300 crédits. En production, 1 prise de voix et 2 variantes d'image par plan suffisent, soit environ 5 800 crédits par vidéo.

## 4. Monétisation (chiffres publics à vérifier dans les applis, ils changent)

- **TikTok, programme de récompenses des créateurs** : 18 ans ou plus, 10 000 abonnés, 100 000 vues sur 30 jours, et seules les vidéos **de plus d'1 minute** rapportent. D'où la durée du format.
- **YouTube, Programme Partenaire** : 1 000 abonnés et 10 M de vues de Shorts sur 90 jours (ou 4 000 h de visionnage en vidéos longues).
- Les vidéos faites avec l'IA doivent être signalées comme telles (case « contenu généré par l'IA » sur TikTok, « contenu modifié ou synthétique » sur YouTube).

## 5. Prochaines histoires possibles (vérifier chaque fait avant d'écrire)

1. Le penalty raté de Baggio en 1994, et la phrase qu'il a dite des années plus tard
2. Le Danemark champion d'Europe 1992, appelé en remplacement deux semaines avant le tournoi
3. Le « miracle d'Istanbul » 2005 : 3-0 à la mi-temps, et le vestiaire de Liverpool
4. La Grèce championne d'Europe 2004
5. Le Leicester champion 2016 (cote 5000 contre 1)
6. Le but de Roger Milla à 42 ans, et sa danse au poteau de corner
7. Le Maroc demi-finaliste en 2022 : le premier pays africain à y arriver
8. Le match Sénégal–France 2002, raconté au format récit (à refaire avec ce format)
9. L'arbitre qui a donné trois cartons jaunes au même joueur (Coupe du monde 2006)
10. La Zambie championne d'Afrique 2012, à quelques kilomètres de la plage où son équipe avait péri en 1993
