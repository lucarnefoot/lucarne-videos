# Remplace la vidéo d'un post Buffer programmé par sa version avec vignette, sans toucher au reste.
# Usage : BUFFER_API_KEY=... python3 outils/buffer_vignette.py <post_id> <url_video>
# Buffer refuse les images de vignette perso (thumbnailUrl) : la vignette est donc collée sur les
# 2 premières images de la vidéo. TikTok : couverture forcée au temps 0 (thumbnailOffset).
# YouTube : pas de réglage de couverture par l'API, on choisit la vignette dans l'appli YouTube.
import json, os, sys, urllib.request

API = "https://api.buffer.com"
def gql(q, v=None):
    req = urllib.request.Request(API, json.dumps({"query": q, "variables": v or {}}).encode(),
                                 {"Authorization": "Bearer " + os.environ["BUFFER_API_KEY"], "Content-Type": "application/json"})
    d = json.load(urllib.request.urlopen(req, timeout=60))
    if d.get("errors"): raise SystemExit(json.dumps(d["errors"], ensure_ascii=False))
    return d["data"]

LIRE = """query($id: PostId!){ post(input:{id:$id}){ id status dueAt channelService text
  assets{ ... on VideoAsset{ source thumbnail video{ title thumbnailOffset } } }
  metadata{ __typename ... on YoutubePostMetadata{ title category{ categoryId } privacy madeForKids isAiGenerated notifySubscribers embeddable license }
            ... on TiktokPostMetadata{ title isAiGenerated } } } }"""

def lire(pid): return gql(LIRE, {"id": pid})["post"]

pid, url = sys.argv[1:3]
p = lire(pid)
assert p["status"] == "scheduled", p["status"]
m = p["metadata"]; svc = p["channelService"]
video = {"url": url}
if svc == "tiktok":
    video["metadata"] = {"thumbnailOffset": 0}
    meta = {"tiktok": {"title": m.get("title"), "isAiGenerated": m["isAiGenerated"]}}
else:
    meta = {"youtube": {"title": m["title"], "categoryId": (m.get("category") or {}).get("categoryId"),
                        "privacy": m["privacy"], "madeForKids": m["madeForKids"], "isAiGenerated": m["isAiGenerated"],
                        "notifySubscribers": m["notifySubscribers"], "embeddable": m["embeddable"], "license": m["license"]}}
inp = {"id": pid, "text": p["text"], "dueAt": p["dueAt"], "assets": [{"video": video}], "metadata": meta}
r = gql("""mutation($i: EditPostInput!){ editPost(input:$i){ __typename ... on PostActionSuccess{ post{ id } }
  ... on InvalidInputError{ message } ... on UnexpectedError{ message } ... on RestProxyError{ message }
  ... on NotFoundError{ message } ... on UnauthorizedError{ message } ... on LimitReachedError{ message } } }""", {"i": inp})
print(json.dumps(r, ensure_ascii=False))
q = lire(pid)
print(q["status"], q["dueAt"], q["assets"][0].get("source"), q["assets"][0].get("thumbnail"), q["assets"][0].get("video"),
      json.dumps(q["metadata"], ensure_ascii=False))
