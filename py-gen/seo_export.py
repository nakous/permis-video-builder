"""
seo_export.py — génère output/seo.csv pour publier les vidéos.

    python3 seo_export.py

Colonnes : id, categorie, difficulty, sujet, titre_seo, description, hashtags
  • id / categorie / difficulty / sujet : lus depuis data/videos-data.json
  • titre_seo   : rédigé à la main, ≤ 40 caractères
  • description : rédigée à la main, ≤ 100 caractères
  • hashtags    : 3 tags pertinents par vidéo

Le contenu SEO est curé dans SEO_COPY ci-dessous (clé = id de la vidéo).
Le script valide les longueurs et signale tout dépassement.
"""

import os
import sys
import csv
import json

sys.path.insert(0, os.path.dirname(__file__))
from config import DATA_FILE, OUTPUT_DIR

TITRE_MAX = 40
DESC_MAX  = 100
N_TAGS    = 3

# ── Contenu SEO rédigé à la main (lu depuis sujet / énoncé / réponse) ────────
SEO_COPY = {
    1:  {"titre": "Quelle vitesse en délai probatoire ?",
         "desc":  "Jeune permis : connais-tu ta vitesse max sur route ? Réponds vite ⏱️",
         "tags":  ["permisprobatoire", "codedelaroute", "vitesse"]},
    2:  {"titre": "Piéton sur le passage : on fait quoi ?",
         "desc":  "Klaxonner, accélérer ou s'arrêter ? La priorité piéton n'attend pas 🚶",
         "tags":  ["pieton", "priorite", "codedelaroute"]},
    3:  {"titre": "Feu tricolore éteint : qui passe ?",
         "desc":  "Le feu est en panne : qui a la priorité au carrefour ? 🚦",
         "tags":  ["feutricolore", "prioriteadroite", "codedelaroute"]},
    4:  {"titre": "Virages dangereux : à droite ou gauche ?",
         "desc":  "Le panneau annonce des virages : le premier part de quel côté ? ↩️",
         "tags":  ["panneau", "virages", "codedelaroute"]},
    5:  {"titre": "Sortie d'autoroute : on dépasse ?",
         "desc":  "Tu sors à la prochaine sortie : le dépassement est-il permis ? 🛣️",
         "tags":  ["autoroute", "depassement", "codedelaroute"]},
    6:  {"titre": "Poids lourd devant : quelle distance ?",
         "desc":  "Aucune visibilité devant le camion : faut-il allonger les distances ? 🚛",
         "tags":  ["poidslourd", "securite", "distancesecurite"]},
    7:  {"titre": "Zone de danger : quelle réaction ?",
         "desc":  "Freiner, dépasser ou klaxonner ? La bonne réaction face au danger 🚧",
         "tags":  ["zonedanger", "securiteroutiere", "codedelaroute"]},
    8:  {"titre": "Doubler une caravane par grand vent ?",
         "desc":  "Vent fort + dépassement de caravane : risque d'écart de trajectoire ? 💨",
         "tags":  ["depassement", "vent", "caravane"]},
    9:  {"titre": "Quels feux la nuit en ville ?",
         "desc":  "De nuit en agglomération : feux de position ou de croisement ? 💡",
         "tags":  ["eclairage", "feux", "conduitenuit"]},
    10: {"titre": "Pluie : risque d'aquaplanage ?",
         "desc":  "Chaussée trempée : ta voiture peut-elle perdre l'adhérence ? 🌧️",
         "tags":  ["aquaplanage", "pluie", "securiteroutiere"]},
    11: {"titre": "Véhicule arrêté sur la BAU : danger ?",
         "desc":  "Intervention sur la bande d'arrêt d'urgence : des piétons possibles ? ⚠️",
         "tags":  ["bau", "corridordesecurite", "autoroute"]},
    12: {"titre": "À quelle distance poser le triangle ?",
         "desc":  "Accident sur la route : à quelle distance placer le triangle ? 🔺",
         "tags":  ["triangle", "securite", "accident"]},
    13: {"titre": "Changer un pneu : quelles règles ?",
         "desc":  "Remplacement de pneu : faut-il suivre les préconisations constructeur ? 🛞",
         "tags":  ["pneu", "mecanique", "entretienauto"]},
    14: {"titre": "À quoi sert vraiment l'ABS ?",
         "desc":  "L'ABS réduit-il la distance de freinage ou garde-t-il la direction ? 🛑",
         "tags":  ["abs", "freinage", "mecanique"]},
    15: {"titre": "Feux de brouillard AR sous la pluie ?",
         "desc":  "Pluie forte : as-tu le droit d'allumer les feux de brouillard arrière ? 🌧️",
         "tags":  ["feuxbrouillard", "pluie", "codedelaroute"]},
    16: {"titre": "Tunnel : les feux diurnes suffisent ?",
         "desc":  "En tunnel : feux de jour suffisants ou feux de croisement obligatoires ? 🚇",
         "tags":  ["tunnel", "feux", "codedelaroute"]},
    17: {"titre": "Désembuage arrière : quelle commande ?",
         "desc":  "Recyclage d'air, désembuage ou essuie-glaces ? Reconnais le bon picto 🚗",
         "tags":  ["desembuage", "mecanique", "tableaudebord"]},
    18: {"titre": "Que signale cette balise ?",
         "desc":  "Travaux, passage à niveau ou obstacle ? Décode la balise routière 🚧",
         "tags":  ["balise", "signalisation", "codedelaroute"]},
    19: {"titre": "Voiture d'un ami : que vérifier ?",
         "desc":  "Tu reprends la voiture d'un proche : quels réglages vérifier avant ? 🪑",
         "tags":  ["reglages", "securite", "conduite"]},
    20: {"titre": "Ligne discontinue : quand s'arrêter ?",
         "desc":  "S'arrêter à la ligne, ou seulement si un piéton s'engage ? 🚶",
         "tags":  ["passagepieton", "priorite", "codedelaroute"]},
    21: {"titre": "Feu jaune clignotant : on passe ?",
         "desc":  "Le feu jaune clignote : tu passes ou tu t'arrêtes ? Gare à la règle 🟡",
         "tags":  ["feujaune", "prioriteadroite", "codedelaroute"]},
    22: {"titre": "Chargement : quel dépassement autorisé ?",
         "desc":  "De combien le chargement peut-il dépasser à l'arrière du véhicule ? 📦",
         "tags":  ["chargement", "securite", "codedelaroute"]},
    23: {"titre": "Ambulance au feu rouge : que faire ?",
         "desc":  "Une ambulance arrive et ton feu est rouge : tu avances ou tu attends ? 🚑",
         "tags":  ["ambulance", "feurouge", "priorite"]},
    24: {"titre": "Vélo plus rapide que la voiture ?",
         "desc":  "Sur de courts trajets en ville, le vélo peut-il battre la voiture ? 🚲",
         "tags":  ["velo", "mobilite", "ville"]},
}

COLUMNS = ["id", "categorie", "difficulty", "sujet",
           "titre_seo", "description", "hashtags"]


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)
    videos = data["videos"]

    rows = []
    warnings = []
    for v in videos:
        vid  = v["id"]
        copy = SEO_COPY.get(vid)
        if not copy:
            warnings.append(f"#{vid} : pas de contenu SEO dans SEO_COPY")
            continue

        titre = copy["titre"].strip()
        desc  = copy["desc"].strip()
        tags  = copy["tags"]

        if len(titre) > TITRE_MAX:
            warnings.append(f"#{vid} titre {len(titre)}>{TITRE_MAX} : {titre!r}")
        if len(desc) > DESC_MAX:
            warnings.append(f"#{vid} description {len(desc)}>{DESC_MAX} : {desc!r}")
        if len(tags) != N_TAGS:
            warnings.append(f"#{vid} {len(tags)} tags (attendu {N_TAGS})")

        rows.append({
            "id":          vid,
            "categorie":   v.get("categorie", ""),
            "difficulty":  v.get("difficulty", ""),
            "sujet":       v.get("sujet", ""),
            "titre_seo":   titre,
            "description": desc,
            "hashtags":    " ".join("#" + t for t in tags),
        })

    out_path = os.path.join(OUTPUT_DIR, "seo.csv")
    # utf-8-sig : BOM pour un affichage correct des accents dans Excel
    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  ✓ CSV écrit -> {out_path}  ({len(rows)} lignes)")
    longest_t = max(len(r["titre_seo"])   for r in rows)
    longest_d = max(len(r["description"]) for r in rows)
    print(f"    titre_seo   : max {longest_t}/{TITRE_MAX} car.")
    print(f"    description : max {longest_d}/{DESC_MAX} car.")
    if warnings:
        print("  ⚠️  Avertissements :")
        for w in warnings:
            print("     -", w)
    else:
        print("    Toutes les longueurs sont OK ✓")


if __name__ == "__main__":
    main()
