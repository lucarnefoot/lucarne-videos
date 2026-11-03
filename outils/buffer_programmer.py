# Programme une vidéo sur YouTube Shorts + TikTok via l'API Buffer, sans doublon.
# Usage : BUFFER_API_KEY=... python3 outils/buffer_programmer.py <dueAt ISO UTC> <url_video> <titre> <fichier_description>
#         BUFFER_API_KEY=... python3 outils/buffer_programmer.py --liste      (posts programmés)
# Couverture : la vignette est collée sur les 2 premières images ; TikTok la prend au temps 0 (thumbnailOffset 0),
# sur YouTube on la choisit dans l'appli. Contenu IA toujours signalé.
import json, os, sys, urllib.request

API = "https://api.buffer.com"
ORG = "6ae877f418a45197780f4921"
CANAUX = {"youtube": "6ae8785ce29c69a171371c85", "tiktok": "6ae8783be29c69a171371bac"}

def gql(q, v=None):
    req = urllib.request.Request(API, json.dumps({"query": q, "variables": v or {}}).encode(),
                                 {"Authorization": "Bearer " + os.environ["BUFFER_API_KEY"], "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get("errors"): raise SystemExit(json.dumps(d["errors"], ensure_ascii=False))
    return d["data"]

def programmes():
    # attention : sans "first", l'API ne renvoie que 10 posts
    out, apres = [], None
    while True:
        d = gql("""query($o: OrganizationId!, $a: String){ posts(first:100, after:$a, input:{organizationId:$o, filter:{status:[scheduled]}}){
          edges{ node{ id dueAt channelService text } } pageInfo{ hasNextPage endCursor } } }""", {"o": ORG, "a": apres})["posts"]
        out += [e["node"] for e in d["edges"]]
        if not d["pageInfo"]["hasNextPage"]: break
        apres = d["pageInfo"]["endCursor"]
    return sorted(out, key=lambda n: n["dueAt"] or "")

if sys.argv[1] == "--liste":
    for n in programmes(): print(n["dueAt"], n["channelService"], n["id"], n["text"][:60].replace("\n", " "))
    raise SystemExit

due, url, titre, fdesc = sys.argv[1:5]
texte = open(fdesc).read().strip()
deja = {n["channelService"] for n in programmes() if n["dueAt"] and n["dueAt"][:16] == due[:16]}
MUT = """mutation($i: CreatePostInput!){ createPost(input:$i){ __typename ... on PostActionSuccess{ post{ id dueAt } }
  ... on InvalidInputError{ message } ... on UnexpectedError{ message } ... on RestProxyError{ message }
  ... on NotFoundError{ message } ... on UnauthorizedError{ message } ... on LimitReachedError{ message } } }"""
for svc, cid in CANAUX.items():
    if svc in deja: print(svc, "déjà programmé à", due, ": rien fait"); continue
    video = {"url": url, "metadata": {"title": titre}}
    if svc == "tiktok":
        video["metadata"]["thumbnailOffset"] = 0
        meta = {"tiktok": {"title": titre, "isAiGenerated": True}}
    else:
        meta = {"youtube": {"title": titre, "categoryId": "17", "privacy": "public", "madeForKids": False, "isAiGenerated": True,
                            "notifySubscribers": True, "embeddable": True, "license": "youtube"}}
    inp = {"channelId": cid, "text": texte, "assets": [{"video": video}], "metadata": meta, "dueAt": due,
           "mode": "customScheduled", "schedulingType": "automatic", "needsApproval": False, "aiAssisted": True}
    print(svc, json.dumps(gql(MUT, {"i": inp})["createPost"], ensure_ascii=False))
