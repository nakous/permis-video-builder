# SEO & Publication — TestPermis.fr

Workflow de production et de diffusion des vidéos quiz « Code de la route ».

> Source de vérité du contenu : [`data/videos-data.json`](data/videos-data.json)
> Générateur : [`py-gen/generate.py`](py-gen/generate.py)

---

## Vue d'ensemble

| Étape | Action | Outil |
|-------|--------|-------|
| 1 | Générer les vidéos (9:16 + 16:9) | `generate.py` |
| 2 | Préparer titres / descriptions / hashtags par plateforme | tableau ci-dessous |
| 3 | Pousser vidéos + textes SEO sur Google Drive (accès mobile) | Drive |
| 4 | Planifier la publication — 3 vidéos / semaine | calendrier / alertes |

---

## Étape 1 — Génération des vidéos

```bash
cd py-gen

# une vidéo, les 2 formats d'un coup
python3 generate.py --id 1 --format both

# toutes les vidéos, les 2 formats
python3 generate.py --format both

# reprendre à partir d'une vidéo (ex : la 7)
python3 generate.py --from-id 7 --format both

# sauter celles déjà rendues
python3 generate.py --skip-existing --format both
```

Sorties dans `output/` :
- `video-{id}-{slug}.mp4` → **9:16** (1080×1920)
- `video-{id}-{slug}-landscape.mp4` → **16:9** (1920×1080)

---

## Étape 2 — Métadonnées & textes SEO

### 2.1 — Métadonnées embarquées dans le MP4 (automatique)

`generate.py` écrit ces tags dans chaque fichier (voir `_build_metadata`) :

| Tag | Valeur | Source |
|-----|--------|--------|
| `title` | `{sujet} — Code de la route \| testpermis.fr` | dynamique |
| `artist` / `author` | `testpermis.fr` | **fixe** |
| `album` | `Quiz Code de la route — {catégorie}` | dynamique |
| `date` | **échelonnée** (≈ 3 vidéos/semaine, pas toutes la même date) | calculée |
| `genre` | catégorie (Signalisation, Conduite…) | dynamique |
| `comment` | titre de l'explication | dynamique |
| `description` / `synopsis` | énoncé de la question + points clés | dynamique |

> Date de départ de campagne : constante `SEO_BASE_DATE` dans `generate.py`.
> Cadence : `SEO_CADENCE_PER_WEEK` (défaut 3).

⚠️ Les métadonnées embarquées sont **peu exploitées** par TikTok / Instagram / YouTube — ces plateformes se basent sur les **champs du formulaire d'upload**. D'où le tableau 2.2.

### 2.2 — Textes par plateforme (à coller dans le formulaire d'upload)

Pour chaque vidéo, préparer :

| Champ | Règle |
|-------|-------|
| **Titre** | court, accrocheur, question implicite. Ex : « Quelle vitesse en délai probatoire ? 🚗 » |
| **Description** | reformuler l'énoncé + CTA « Réponds en commentaire avant la fin du timer 👇 » + lien testpermis.fr |
| **Hashtags** | `#permisdeconduire #codedelaroute #{catégorie} #{thème}` + tags plateforme |
| **CTA** | renvoyer vers `testpermis.fr` |

Modèle de ligne (à remplir par vidéo) :

| ID | Plateforme | Format | Titre | Description | Hashtags |
|----|-----------|--------|-------|-------------|----------|
| 1 | TikTok | 9:16 | … | … | … |
| 1 | Instagram Reels | 9:16 | … | … | … |
| 1 | YouTube Shorts | 9:16 | … | … | … |
| 1 | YouTube | 16:9 | … | … | … |
| 1 | X | 9:16 | … | … | … |
| 1 | LinkedIn | 16:9 | … | … | … |

---

## Étape 3 — Partage via Google Drive

- Un dossier par lot de publication (ex : `Semaine-01/`).
- Dans chaque dossier : les MP4 (9:16 + 16:9) + un fichier texte des titres/descriptions/hashtags.
- Drive accessible depuis le téléphone → publication faite depuis le mobile.

---

## Étape 4 — Planification

- **Cadence : 3 vidéos / semaine** (≈ lun / mer / ven).
- Alterner les catégories (ne pas enchaîner 8 « Signalisation »).
- Alertes calendrier pour rappeler chaque publication.
- Suivre quelles catégories performent → ajuster le mix.

---

## Annexe — Contraintes par plateforme

| Plateforme | Format | Durée max | Notes |
|------------|--------|-----------|-------|
| **TikTok** | 9:16 | 10 min | Cœur de cible. ~60 s idéal. |
| **Instagram Reels** | 9:16 | 90 s | OK tant que < 90 s. |
| **YouTube Shorts** | 9:16 | **60 s** | ⚠️ > 60 s = traité comme vidéo longue, pas Short. Garder les vidéos sous 60 s. |
| **YouTube (classique)** | 16:9 | — | Version paysage. Bon pour le référencement durable + playlists par catégorie. |
| **X (Twitter)** | 9:16 | 2 min 20 | Le format vertical passe bien. |
| **LinkedIn (page)** | 16:9 | 10 min | Plutôt 16:9, ton plus « pro ». |

### Point d'attention durée
Les timings sont dans `videos-data.json` → `timing` (`introDuration`, `countdownDuration`, `outroDuration`).
Pour rester **sous 60 s** (YouTube Shorts), ajuster `introDuration` / `outroDuration` si une vidéo dépasse.
