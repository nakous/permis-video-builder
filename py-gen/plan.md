# py-gen — Générateur vidéo Python pour TestPermis.fr

## Objectif

Remplacer le pipeline Puppeteer/Node.js par un générateur Python pur.
Entrée : `data/videos-data.json` — Sortie : `output/*.mp4`

Résultat visé : vidéos TikTok/Reels professionnelles, style cohérent avec testpermis.fr,
sans icônes système, sans emoji, typographie propre, animations fluides.

---

## Liste de corrections — à valider avant implémentation

### C1 — Scène 2 : Image question coupée (cover-fit → contain-fit)

**Problème :** `image_block.py` utilise le mode "cover" : l'image est agrandie pour remplir toute la zone puis rognée au centre. Les images de testpermis.fr sont en 4:3 ou 16:9 — sur un format 9:16 TikTok, les éléments importants (panneaux, intersections) sont coupés en haut ou en bas.

**Correction :** Ajouter un paramètre `fit="cover"|"contain"` à `load_image()`.  
En mode `contain` : l'image est mise à l'échelle pour tenir entière dans le cadre en respectant son ratio, fond `BG_DARK` pour les bandes vides (letterbox haut/bas ou gauche/droite).  
Scènes 2 et 5 passeront en `contain`.

---

### C2 — Scène 2 : Question uniquement VRAI/FAUX → multi-choix dynamique

**Problème :** "VRAI ou FAUX ?" est codé en dur dans `question.py`. Les vraies questions du code de la route sont des QCM (A, B, C...) ou OUI/NON doubles. La carte n'affiche que le texte de la question sans les choix.

**Correction JSON :** Ajouter un champ `choix` dans `question` :
```json
"question": {
  "texte": "Dans cette situation, la vitesse maximale est de :",
  "type": "qcm",          ← "vrai_faux" | "qcm"
  "choix": [
    { "lettre": "A", "texte": "80 km/h" },
    { "lettre": "B", "texte": "90 km/h" }
  ],
  "reponse": "A",         ← lettre de la bonne réponse (ou "VRAI"/"FAUX")
  "media": "...",
  "audio": "..."
}
```
**Correction `question.py` :**  
- Si `type == "vrai_faux"` → badge "VRAI ou FAUX ?" (comportement actuel)  
- Si `type == "qcm"` → badge "QCM" + chaque choix affiché sur sa propre ligne avec sa lettre dans un pill coloré (A en PRIMARY, B/C en BG_CARD2)  
- `reponse` remonte au niveau racine du video_data (ou reste dans `question`)

---

### C3 — Scène 3 : Tick en double + déborde après 3s

**Problème :** Dans `mixer.py`, chaque tick est ajouté comme `_load(tick_path, start=t2+i)` sans limiter sa durée. Si `tick.mp3` dure > 1s, les clips `t2+0` et `t2+1` se chevauchent → son double. De plus, le dernier tick (`t2+2`) peut déborder sur la scène Answer si sa durée est > 1s.

**Correction :** Chaque tick doit être limité à exactement 1.0s :
```python
AudioFileClip(tick_path).subclip(0, min(1.0, duration)).set_start(t2 + i)
```
Vérification : `countdown_dur` doit valoir exactement 3.0s (3 ticks × 1s), le 3ème tick finit à `t2 + 3 = t3` sans déborder.

---

### C4 — Scène 4 : Réponse dynamique + affichage des choix

**Problème :** `answer.py` affiche "VRAI" ou "FAUX" en dur selon `video_data["reponse"]`. Pour un QCM, il faut afficher la lettre de la bonne réponse, le texte du bon choix, et optionnellement barrer les mauvais choix.

**Correction `answer.py` :**  
- Récupérer `type` et `choix` depuis `video_data["question"]`  
- Pour `vrai_faux` : comportement actuel (VRAI/FAUX grand + icône check/cross)  
- Pour `qcm` :  
  - Afficher "Réponse : **A**" en grand  
  - En dessous : texte complet du bon choix  
  - Liste des autres choix barrés (ligne horizontale sur le texte, couleur DANGER)

**Correction JSON :** `reponse` dans `video_data` doit correspondre à la `lettre` du bon choix (`"A"`, `"B"`...) ou rester `"VRAI"`/`"FAUX"` pour les vrai/faux.

---

### C5 — Scène 5 : Image explication coupée

**Problème :** `load_image(path, WIDTH, IMG_H)` en mode cover coupe l'image de correction. Les images `_c.png` de testpermis.fr contiennent la correction annotée — il faut tout voir.

**Correction :** Passer `fit="contain"` dans `explanation.py` (même fix que C1). L'image s'affiche en entier, centrée dans son bloc `IMG_H = HEIGHT * 0.40`, avec fond `BG_DARK` pour les bandes.

---

### C6 — Scène 5 : Texte pixelisé et trop petit

**Problème :**  
1. `PT_FONT = 38` — trop petit pour TikTok mobile (les gens lisent en tenant le téléphone)  
2. Pillow rend le texte sans antialiasing sub-pixel → pixelisé, surtout sur les petites tailles  
3. Roboto extrait via fontTools peut perdre les hints de rendu

**Corrections :**  
- Augmenter `PT_FONT` : `38 → 46`, titre `52 → 58`, badge `38 → 44`  
- Activer le rendu en **supersampling 2×** : générer les frames à `2160×3840` puis downscaler à `1080×1920` avant de retourner le numpy array → antialiasing naturel par réduction  
- Alternative plus simple (si supersampling trop lent) : augmenter encore les tailles de police pour compenser

---

### C7 — JSON `videos-data.json` : structure à mettre à jour

Pour supporter C2 et C4, le JSON doit évoluer :
```json
{
  "question": {
    "type": "qcm",
    "texte": "Dans cette situation, la vitesse maximale est de :",
    "choix": [
      { "lettre": "A", "texte": "80 km/h" },
      { "lettre": "B", "texte": "90 km/h" }
    ],
    "media": "./assets/videos/q1/question.png",
    "audio": "./assets/videos/q1/question.mp3"
  },
  "reponse": "A"
}
```
La clé `reponse` au niveau racine indique la lettre correcte (ou "VRAI"/"FAUX").

---

### Résumé des fichiers à modifier

| Fichier | Corrections |
|---|---|
| `data/videos-data.json` | C7 — ajouter `type`, `choix`, adapter `reponse` |
| `renderer/elements/image_block.py` | C1, C5 — ajouter paramètre `fit="cover"\|"contain"` |
| `renderer/scenes/question.py` | C2 — affichage multi-choix dynamique |
| `audio/mixer.py` | C3 — subclip tick à 1.0s max |
| `renderer/scenes/answer.py` | C4 — réponse dynamique + choix barrés |
| `renderer/scenes/explanation.py` | C5, C6 — contain-fit image + tailles de police |
| `config.py` | C6 — constante supersampling (optionnel) |

---

## Stack technique

| Librairie     | Rôle                                              |
|---------------|---------------------------------------------------|
| `moviepy`     | Assemblage clips, mix audio, export MP4           |
| `Pillow`      | Rendu frames : texte, formes, dégradés, images    |
| `numpy`       | Conversion frames PIL → arrays pour MoviePy       |
| `requests`    | Téléchargement police Nunito si absente           |

```bash
pip install moviepy pillow numpy requests
```

---

## Structure du dossier

```
py-gen/
├── plan.md
├── generate.py              # Point d'entrée — lit JSON, lance le pipeline
├── config.py                # Résolutions, FPS, constantes
├── theme.py                 # Couleurs, polices, espacements brand
│
├── renderer/
│   ├── compositor.py        # Orchestre les scènes → MoviePy clips → MP4
│   ├── animations.py        # Fonctions d'easing + interpolateur de frames
│   │
│   ├── scenes/
│   │   ├── intro.py         # Scène 1 : logo + nom site + catégorie
│   │   ├── question.py      # Scène 2 : image question + texte + badge VRAI/FAUX
│   │   ├── countdown.py     # Scène 3 : décompte 3-2-1 + ring SVG
│   │   ├── answer.py        # Scène 4 : révélation VRAI / FAUX
│   │   ├── explanation.py   # Scène 5 : image + points + badge
│   │   └── outro.py         # Scène 6 : logo + réseaux sociaux + CTA
│   │
│   └── elements/
│       ├── background.py    # Fonds : dégradés, overlay, vignette
│       ├── typography.py    # Rendu texte : wrapping, taille auto, ombre
│       ├── card.py          # Cartes arrondies avec fond semi-transparent
│       ├── progress_bar.py  # Barre de progression animée (bas d'écran)
│       └── image_block.py   # Affichage image avec fondu + border-radius
│
└── audio/
    └── mixer.py             # Charge les MP3, calcule les offsets, mix final
```

---

## Design des scènes — règles visuelles

### Principes généraux
- **Pas d'icônes système, pas d'emoji** dans le rendu final
- Tout le visuel = typographie + images + formes géométriques + couleurs brand
- Police unique : **Nunito** (téléchargée au premier lancement)
- Format : **1080 × 1920px** (9:16 TikTok/Reels), 30fps
- Fond de base : `#0D1B2A` (navy brand)

### Palette de couleurs (variables exactes du site testpermis.fr)

```
# Brand teal
PRIMARY        #2DD4BF   --primary-color      titres, accents, CTA, ring countdown
PRIMARY_DARK   #14B8A6   --primary-dark       ombres teal, borders
PRIMARY_LIGHT  #5EEAD4   --primary-light      highlights, glows
ACCENT         #0D9488   --accent-color       séparateurs, détails fins

# Fonds vidéo (dark pour TikTok — plus sombre que le site web)
BG_DARK        #111827   (secondary-dark -10%)  fond principal vidéo
BG_CARD        #1F2937   --secondary-dark       fond des cartes, overlays
BG_CARD2       #374151   --secondary-color      cartes secondaires, badges neutres

# Texte
TEXT_WHITE     #FFFFFF   --background-white     texte principal sur fond sombre
TEXT_MEDIUM    #9CA3AF   --text-light           texte secondaire, source, labels
TEXT_DARK      #1F2937   --text-dark            texte sur fond clair (ex: bouton CTA)

# États
SUCCESS        #10B981   --success-color        réponse VRAI, points positifs
WARNING        #F59E0B   --warning-color        badges attention, difficultés moyen
DANGER         #EF4444   --error-color          réponse FAUX, pénalités

# Bordures
BORDER         #E5E7EB   --border-color         bords de cards (opacity 0.15 sur fond sombre)
```

### Scène 1 — INTRO (durée fixe : 3s)
```
┌─────────────────────────────┐
│                             │
│      [logo image 220px]     │
│                             │
│    TestPermis.fr            │  ← Nunito 900, couleur PRIMARY
│    CODE MOTO FRANCE         │  ← Nunito 400, TEXT_MUTED, letter-spacing
│                             │
│    testpermis.fr            │  ← Nunito 400, TEXT_MUTED small
│                             │
└─────────────────────────────┘
Animation : logo scale 0→1 ease_out (0.4s) + texte fadeIn décalé
```

### Scène 2 — QUESTION (durée = audio question)
```
┌─────────────────────────────┐
│  [badge difficulté]         │  ← coin haut gauche
│                    [logo]   │  ← coin haut droite (watermark)
│                             │
│  ┌─────────────────────┐    │
│  │  [image question]   │    │  ← image pleine largeur, h=700px, rounded
│  └─────────────────────┘    │
│                             │
│  ┌─────────────────────┐    │
│  │  VRAI ou FAUX ?     │    │  ← card BG_CARD, PRIMARY, Nunito 900
│  │                     │    │
│  │  [texte question]   │    │  ← Nunito 700, 40px, wrapping auto
│  └─────────────────────┘    │
└─────────────────────────────┘
Animation : image slideDown (0.5s) + card slideUp (0.3s décalé)
```

### Scène 3 — COUNTDOWN (3 secondes fixes)
```
┌─────────────────────────────┐
│  [image question — grisée]  │  ← même image, overlay sombre 70%
│                             │
│          ┌──────┐           │
│          │  3   │           │  ← ring SVG dessiné en Pillow, chiffre centré
│          └──────┘           │     Nunito 900, 180px, couleur PRIMARY
│       Répondez !            │  ← Nunito 700, TEXT_MUTED
└─────────────────────────────┘
Animation : ring se vide progressivement (stroke-dashoffset), chiffre pop scale
```

### Scène 4 — RÉPONSE (durée = audio correct/wrong)
```
┌─────────────────────────────┐
│                             │
│     ┌───────────────────┐   │
│     │  ✗  FAUX          │   │  ← card arrondie, fond DANGER ou SUCCESS
│     └───────────────────┘   │     Nunito 900, 140px
│                             │
│  [texte court confirmation] │  ← ex: "L'arrêt est obligatoire !"
│                             │     Nunito 700, 38px, TEXT_MUTED
└─────────────────────────────┘
Fond : dégradé radial depuis DANGER/SUCCESS au centre, BG_DARK sur les bords
Animation : card scale 0→1.05→1 (shakeIn), texte fadeIn décalé 0.3s
Pas de check/cross emoji — utiliser formes géométriques (cercle + trait Pillow)
```

### Scène 5 — EXPLICATION (durée = audio explication)
```
┌─────────────────────────────┐
│  [image explication]        │  ← h=500px, largeur pleine, rounded bas
│                             │
│  Titre explication          │  ← Nunito 900, PRIMARY, 44px
│                             │
│  ├─ Point 1 texte           │  ← barre gauche couleur PRIMARY, pas d'icône
│  ├─ Point 2 texte           │     Nunito 600, 32px
│  ├─ Point 3 texte           │
│  └─ Point 4 texte           │
│                             │
│  [badge ⚠ -4 pts + 135€]   │  ← card DANGER/WARNING arrondie
└─────────────────────────────┘
Animation : titre slideDown, points slideRight décalés (0.3s chacun)
```

### Scène 6 — OUTRO (durée fixe : 4s)
```
┌─────────────────────────────┐
│                             │
│      [logo image 200px]     │
│      TestPermis.fr          │  ← PRIMARY
│      testpermis.fr          │  ← TEXT_MUTED
│                             │
│  ┌──────────────────────┐   │
│  │  Testez vos          │   │  ← card CTA, fond PRIMARY, texte BG_DARK
│  │  connaissances !     │   │     Nunito 900
│  └──────────────────────┘   │
│                             │
│  @testpermis.fr    [TikTok] │  ← réseaux : texte + rectangle coloré
│  @testpermis.fr    [Insta]  │
└─────────────────────────────┘
Animation : logo fadeIn, card slideUp, réseaux slideRight décalés
```

---

## Pipeline audio (mixer.py)

Tous les timings sont calculés dynamiquement à partir des durées réelles des MP3 :

```
t=0                    intro.mp3 + bg-music (vol 0.15, loop)
t=intro_end            question.mp3
t=question_end         tick.mp3 × 3 (1s d'écart)
t=countdown_end        correct.mp3 ou wrong.mp3
t=answer_end           explication.mp3
t=explication_end      outro.mp3
```

`moviepy.CompositeAudioClip` assemble tout en 1 seul appel — pas de passes FFmpeg séparées.

---

## Système d'animation (animations.py)

```python
# Fonctions d'easing disponibles
ease_out(t)         # décélère en fin
ease_in_out(t)      # accélère puis décélère
ease_spring(t)      # overshoot léger (bounceIn)
linear(t)

# Interpolateur générique
interpolate(from_val, to_val, progress, easing)

# Exemple : fadeIn sur 0.5s à partir de t=1.2s dans la scène
opacity = interpolate(0, 1, elapsed, ease_out) if elapsed < 0.5 else 1
```

---

## Tasks

### Phase 1 — Setup
- [ ] `config.py` — résolution, FPS, chemins assets
- [ ] `theme.py` — palette, polices, espacements
- [ ] Télécharger police Nunito (Regular 400, SemiBold 600, Bold 700, ExtraBold 900)
- [ ] `animations.py` — fonctions easing + interpolateur
- [ ] `audio/mixer.py` — lecture durées MP3, calcul offsets, CompositeAudioClip

### Phase 2 — Éléments visuels
- [ ] `elements/background.py` — dégradé linéaire/radial, overlay
- [ ] `elements/typography.py` — rendu texte Pillow, auto word-wrap, ombre portée
- [ ] `elements/card.py` — rectangle arrondi semi-transparent
- [ ] `elements/image_block.py` — load image, resize, border-radius, fadeIn
- [ ] `elements/progress_bar.py` — barre animée bas d'écran

### Phase 3 — Scènes
- [ ] `scenes/intro.py`
- [ ] `scenes/question.py`
- [ ] `scenes/countdown.py` — ring dessiné avec Pillow arcs
- [ ] `scenes/answer.py` — formes géométriques (pas d'emoji)
- [ ] `scenes/explanation.py` — barre latérale colorée au lieu d'icônes
- [ ] `scenes/outro.py`

### Phase 4 — Assemblage
- [ ] `renderer/compositor.py` — enchaîne les scènes, gère les transitions entre clips
- [ ] `generate.py` — lit JSON, boucle sur les vidéos, appelle compositor + mixer

### Phase 5 — Qualité
- [ ] Tester sur les 5 vidéos existantes
- [ ] Vérifier sync audio/vidéo
- [ ] Vérifier rendu sur mobile (ratio 9:16)
- [ ] Optimiser vitesse de rendu si nécessaire

---

## Exemple d'utilisation finale

```bash
# Générer toutes les vidéos
python generate.py

# Générer une seule vidéo
python generate.py --id 1

# Prévisualiser une scène sans générer le MP4
python generate.py --preview question --id 1
```

---

## Ce qui reste côté Node.js

Le générateur HTML (`generate-all.js` + `engine/`) reste disponible pour
prévisualiser les données JSON dans un browser.
Le générateur Python prend en charge exclusivement la production des MP4.
