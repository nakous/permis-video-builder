# 🎬 TestPermis.fr — Générateur Automatique de Vidéos Quiz

Génère des vidéos quiz **Vrai/Faux** pour permis moto/voiture à partir d'un fichier JSON.
Les vidéos sont créées en HTML/CSS animé, puis exportables en MP4 via Puppeteer + FFmpeg.

---

## 🚀 Comment ça marche

```
videos-data.json        →  generate-all.js  →  output/*.html  →  (--record)  →  MP4
   (questions +              (injecte dans       (vidéos           Puppeteer
    settings)                 template.html)      animées)          + FFmpeg
```

1. Tu remplis `videos-data.json` avec tes questions, réponses, explications
2. `node generate-all.js` génère un fichier HTML animé par vidéo
3. Ouvre le HTML dans Chrome pour voir le résultat
4. (Optionnel) `node generate-all.js --record` pour exporter en MP4

---

## 📁 Structure du projet

```
testpermis-video-workflow/
├── template.html              ← Template maître (CSS animations + JS dynamique)
├── videos-data.json           ← Données : settings globaux + tableau de vidéos
├── generate-all.js            ← Script Node.js : JSON → HTML (+ MP4 optionnel)
├── generate-placeholders.js   ← Génère les fichiers assets placeholder
├── README.md
├── assets/
│   ├── logo.png               ← Logo du site (500x500px, fond transparent)
│   ├── watermark.png          ← Watermark (130x130px, semi-opaque)
│   ├── sounds/
│   │   ├── intro.mp3          ← Jingle d'intro (2-3s)
│   │   ├── tick.mp3           ← Son tick countdown (0.5-1s)
│   │   ├── correct.mp3        ← Son bonne réponse (1-2s)
│   │   ├── wrong.mp3          ← Son mauvaise réponse (1-2s)
│   │   ├── outro.mp3          ← Jingle de fin (2-3s)
│   │   └── bg-music.mp3       ← Musique de fond en boucle (30-60s)
│   ├── audio/
│   │   ├── q1-question.mp3    ← Voix-off question 1
│   │   ├── q1-explication.mp3 ← Voix-off explication 1
│   │   ├── q2-question.mp3    ← ...
│   │   └── ...
│   └── media/
│       ├── q1-panneau-stop.png       ← Image question 1
│       ├── q1-explication-stop.png   ← Image explication 1
│       └── ...
└── output/
    ├── video-1-panneau-stop.html     ← Vidéo générée
    ├── video-2-angle-mort-moto.html
    └── ...
```

---

## 🎥 Structure d'une vidéo (~40s)

| # | Séquence | Durée | Contenu |
|---|----------|-------|---------|
| 1 | **Intro** | 3s | Logo animé + nom du site + catégorie |
| 2 | **Question** | 10s | Emoji + badge "VRAI ou FAUX ?" + texte + image + voix-off |
| 3 | **Countdown** | 3s | Timer circulaire 3-2-1 (apparaît après la voix-off) |
| 4 | **Réponse** | 4s | ✅ VRAI ou ❌ FAUX en grand avec animation |
| 5 | **Explication** | 17s | Titre + image + 3-5 points animés + badge info + voix-off |
| 6 | **Outro** | 4s | Logo + réseaux sociaux (TikTok, Insta, YouTube) + CTA |

Le timing s'adapte automatiquement à la durée des audios voix-off.

---

## 📝 Format de `videos-data.json`

```jsonc
{
  "settings": {
    "site": { "name": "...", "url": "...", "logo": "./assets/logo.png", "watermark": "...", "callToAction": "..." },
    "sounds": { "intro": "...", "tick": "...", "correct": "...", "wrong": "...", "outro": "...", "backgroundMusic": "..." },
    "theme": { "primaryColor": "#4facfe", "secondaryColor": "#f5576c", "backgroundColor": "#0a0a2e", ... },
    "socials": { "tiktok": "@...", "instagram": "@...", "youtube": "..." },
    "format": { "ratio": "9:16", "platform": "tiktok", "fps": 30 }
  },
  "videos": [
    {
      "id": 1,
      "sujet": "Panneau STOP",
      "categorie": "Signalisation",
      "emoji": "🛑",
      "difficulty": "facile",              // facile | moyen | difficile
      "question": {
        "texte": "« Au panneau STOP, je peux ralentir sans m'arrêter. »",
        "media": "./assets/media/q1-panneau-stop.png",
        "audio": "./assets/audio/q1-question.mp3",
        "audioDuration": 5                 // secondes (pour sync timing)
      },
      "reponse": "FAUX",
      "explication": {
        "titre": "L'arrêt est OBLIGATOIRE",
        "media": "./assets/media/q1-explication-stop.png",
        "audio": "./assets/audio/q1-explication.mp3",
        "audioDuration": 13,
        "points": [
          { "icon": "🛑", "texte": "L'arrêt complet est obligatoire" },
          { "icon": "📍", "texte": "Arrêtez-vous à la ligne blanche" }
        ],
        "badge": { "texte": "⚠️ -4 pts + 135€", "type": "danger" }
      },
      "timing": {
        "introDuration": 3,
        "questionDuration": 10,
        "countdownDuration": 3,
        "answerDuration": 4,
        "explanationDuration": 17,
        "outroDuration": 4
      }
    }
  ]
}
```

---

## ⚡ Commandes

```bash
# Générer les fichiers assets placeholder
node generate-placeholders.js

# Générer toutes les vidéos en HTML
node generate-all.js

# Générer + exporter en MP4 (nécessite Puppeteer + FFmpeg)
node generate-all.js --record

# Générer une seule vidéo en MP4
node generate-all.js --record --id 1
```

### Prérequis pour l'export MP4
```bash
npm install puppeteer
# + installer FFmpeg : https://ffmpeg.org/download.html
```

---

## 🎨 Formats supportés

| Plateforme | Ratio | Résolution |
|-----------|-------|------------|
| TikTok / Reels / Shorts | 9:16 | 1080×1920 |
| YouTube | 16:9 | 1920×1080 |
| Facebook / LinkedIn | 1:1 | 1080×1080 |
| Twitter | 16:9 | 1280×720 |

Change `settings.format.platform` dans `videos-data.json` pour switcher.

---

## 🔊 Où trouver les assets

| Type | Sites gratuits |
|------|---------------|
| **Sons/Jingles** | [Pixabay](https://pixabay.com/sound-effects/) · [Mixkit](https://mixkit.co/free-sound-effects/) · [Freesound](https://freesound.org/) |
| **Voix-off (TTS)** | [OpenAI TTS API](https://platform.openai.com/docs/guides/text-to-speech) (voix "nova" recommandée) |
| **Images** | [OpenAI DALL-E](https://platform.openai.com/docs/guides/images) · [Unsplash](https://unsplash.com/) |

---

## 🔄 Pipeline n8n (à venir)

```
GPT-5 → génère question/réponse/explication
  ↓
GPT TTS → génère audio voix-off (question + explication)
  ↓
GPT Image → génère illustrations
  ↓
Remplit videos-data.json
  ↓
node generate-all.js --record → MP4
  ↓
Upload TikTok / YouTube / Instagram
```
