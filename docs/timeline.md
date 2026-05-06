# Timeline du générateur de vidéo — TestPermis.fr

## Vue d'ensemble

```
T=0          T=intro_end   T=+question   T=+answer   T=+explication   T=fin
|───INTRO────|────────QUESTION+COUNTDOWN────|──RÉPONSE──|──EXPLICATION──|──OUTRO──|
     ~3s              ~10s                       ~4s          ~17s          ~4s
                                                               ↑
                                              durée réelle = fin audio + 1.5s
```

---

## 1. INTRO

| Élément         | Début (relatif) | Fin                        | Durée         |
|-----------------|-----------------|----------------------------|---------------|
| Écran intro     | T = 0           | fin de `audioIntro`        | `introDuration` (défaut 3s) |
| Animation logo  | T = 0           | T + `introDuration - 0.5s` | `introDuration - 0.5s` |
| `audioBgMusic`  | T = 0           | fin de la vidéo (loop)     | toute la vidéo |
| `audioIntro`    | T = 0           | fin naturelle              | durée du fichier |

### Conditions

| Condition                          | Comportement                                      |
|------------------------------------|---------------------------------------------------|
| `settings.site.logo` non vide      | Affiche `<img>` avec le logo                      |
| `settings.site.logo` vide          | Affiche l'emoji `video.emoji` (converti en SVG)   |
| `settings.site.watermark` non vide | Affiche l'image watermark en overlay permanent    |
| `settings.site.watermark` vide     | Affiche le texte `settings.site.name` en watermark |
| `video.difficulty` défini          | Affiche le badge difficulté (facile/moyen/difficile) |

### Déclencheur de fin
L'écran INTRO se termine quand `audioIntro` se termine (`ended` event).
Fallback Puppeteer : `introDuration + 2s`.

---

## 2. QUESTION

| Élément              | Début (relatif à début QUESTION) | Fin                                        | Durée     |
|----------------------|----------------------------------|--------------------------------------------|-----------|
| Écran question       | T = 0                            | fin countdown                              | `questionDuration` calculé |
| Emoji (icône)        | T = 0                            | —                                          | animation bounceIn 0.6s |
| Badge "VRAI ou FAUX" | T + 0.3s                         | —                                          | animation bounceIn 0.8s |
| Image/Vidéo media    | T + 0.6s                         | —                                          | animation bounceIn 0.8s |
| Texte question       | T + 1.2s                         | —                                          | animation slideUp 1s |
| `audioQuestion`      | T + 1.7s                         | fin naturelle (`audioDuration`)            | `question.audioDuration` |
| **Countdown**        | fin `audioQuestion` + 0.4s       | + 3s (3 ticks × 1s)                        | `countdownDuration` (3s) |
| Tick "3"             | fin audio + 0.4s                 | + 1s                                       | 1s |
| Tick "2"             | fin audio + 0.4s + 1s            | + 1s                                       | 1s |
| Tick "1"             | fin audio + 0.4s + 2s            | + 1s                                       | 1s |
| `audioSuspense`      | à chaque tick (×3)               | fin naturelle (~0.5-1s)                    | court |

### Calcul de `questionDuration`
```
minQuestionTime   = question.audioDuration + countdownDuration + 2
questionDuration  = max(timing.questionDuration, minQuestionTime)
```
Exemple vidéo 1 : `max(10, 5 + 3 + 2)` = `max(10, 10)` = **10s**

### Conditions

| Condition                                               | Comportement                                 |
|---------------------------------------------------------|----------------------------------------------|
| `question.media` non vide ET `mediaType === 'image'`    | Affiche `<img>` (animation bounceIn à T+0.6s)|
| `question.media` non vide ET `mediaType === 'video'`    | Affiche `<video muted>` (animation bounceIn) |
| `question.media` vide                                   | Aucun media affiché                          |

### Déclencheur de fin
Countdown termne (après le dernier tick "1" + 1s) → fadeOut question.

---

## 3. RÉPONSE

| Élément         | Début (relatif) | Fin                       | Durée          |
|-----------------|-----------------|---------------------------|----------------|
| Écran réponse   | T = 0           | T + `answerDuration`      | `answerDuration` (défaut 4s) |
| Icône ✅/❌      | T + 0.2s        | —                         | animation shakeIn 0.8s |
| Texte réponse   | T + 0.7s        | —                         | animation shakeIn 0.6s |
| `audioAnswer`   | T + 0.7s        | fin naturelle             | durée du fichier |

### Conditions

| Condition                             | Comportement                                 |
|---------------------------------------|----------------------------------------------|
| `video.reponse.toUpperCase() === 'VRAI'` | Fond vert, icône ✅ (SVG check), texte "VRAI !" |
| `video.reponse.toUpperCase() !== 'VRAI'` | Fond rouge, icône ❌ (SVG cross), texte "FAUX !" |
| `sounds.correct` défini ET réponse VRAI | `audioAnswer` → `sounds.correct`            |
| `sounds.wrong` défini ET réponse FAUX  | `audioAnswer` → `sounds.wrong`              |

### Déclencheur de fin
Timer fixe : `answerDuration × 1000ms` → fadeOut réponse.

---

## 4. EXPLICATION

| Élément                | Début (relatif) | Fin                              | Durée              |
|------------------------|-----------------|----------------------------------|--------------------|
| Écran explication      | T = 0           | fin `audioExplication` + 1.5s    | `explanationDuration` calculé |
| Titre explication      | T + 0.3s        | —                                | animation slideDown 0.8s |
| Image/Icône media      | T + 0.6s        | —                                | animation bounceIn 0.8s |
| `audioExplication`     | T + 0.8s        | fin naturelle (`audioDuration`)  | `explication.audioDuration` |
| Point 0                | T + 0.8s        | —                                | animation slideRight 0.8s |
| Point 1                | T + 0.8s + 1×interval | —                          | animation slideRight 0.8s |
| Point N                | T + 0.8s + N×interval | —                          | animation slideRight 0.8s |
| Badge info             | fin audio        | —                                | animation bounceIn 0.6s |
| Source (texte)         | fin audio + 0.6s | —                               | animation fadeIn 0.5s |

### Calcul de l'intervalle entre les points
```
pointInterval = (explication.audioDuration - 1) / nombre_de_points
```
Exemple vidéo 1 : `(13 - 1) / 4` = **3s entre chaque point**

### Calcul de `explanationDuration`
```
minExplanationTime  = explication.audioDuration + 3
explanationDuration = max(timing.explanationDuration, minExplanationTime)
```
Exemple vidéo 1 : `max(17, 13 + 3)` = `max(17, 16)` = **17s**

### Conditions

| Condition                                                 | Comportement                                   |
|-----------------------------------------------------------|------------------------------------------------|
| `explication.media` non vide ET `mediaType === 'image'`   | Affiche `<img>` (bounceIn à T+0.6s), icône cachée |
| `explication.media` vide                                  | Affiche l'icône emoji `video.emoji` en grand   |
| `video.source` non vide                                   | Affiche "Source : …" après l'audio            |
| `explication.badge.type === 'danger'`                     | Badge rouge                                    |
| `explication.badge.type === 'warning'`                    | Badge orange                                   |
| `explication.badge.type === 'success'`                    | Badge vert                                     |

### Déclencheur de fin
Fin réelle de `audioExplication` (`ended` event) → +1.5s → fadeOut explication.
Fallback Puppeteer : `audioDuration + 2s`.

---

## 5. OUTRO

| Élément           | Début (relatif) | Fin                         | Durée            |
|-------------------|-----------------|-----------------------------|------------------|
| Écran outro       | T = 0           | T + `outroDuration`         | `outroDuration` (défaut 4s) |
| `audioOutro`      | T = 0           | fin naturelle               | durée du fichier |
| Logo/texte site   | T + 0.4s        | —                           | animation logoPulse 1s |
| Réseau social 1   | T + 0.8s        | —                           | animation slideRight 0.6s |
| Réseau social 2   | T + 1.1s        | —                           | animation slideRight 0.6s |
| Réseau social 3   | T + 1.4s        | —                           | animation slideRight 0.6s |
| Réseau social 4   | T + 1.7s        | —                           | animation slideRight 0.6s |
| Bouton "Abonnez-vous" | T + 1.8s   | —                           | animation bounceIn 0.8s |
| Texte CTA         | T + 2.3s        | —                           | animation fadeIn 0.5s |

### Conditions

| Condition                       | Comportement                                      |
|---------------------------------|---------------------------------------------------|
| `settings.site.logo` non vide   | Affiche `<img>` logo                              |
| `socials.tiktok` non vide       | Affiche item TikTok                               |
| `socials.instagram` non vide    | Affiche item Instagram                            |
| `socials.youtube` non vide      | Affiche item YouTube                              |
| `socials.facebook` non vide     | Affiche item Facebook                             |
| `settings.site.callToAction`    | Affiche le texte CTA                              |

### Déclencheur de fin
Timer fixe : `outroDuration × 1000ms` → `window.__VIDEO_DONE = true` (signal Puppeteer).

---

## Timeline complète avec valeurs exemple (vidéo 1 — Panneau STOP)

```
T (sec)   Événement
────────  ─────────────────────────────────────────────────────────────
 0.0      ▶ INTRO démarre | audioBgMusic démarre (loop) | audioIntro démarre
 0.0      Animation logo (2.5s)
 3.0      ◀ INTRO se termine (fin audioIntro)

 3.0      ▶ QUESTION démarre
 3.0      Emoji bounceIn
 3.3      Badge "VRAI ou FAUX ?" bounceIn
 3.6      Image question bounceIn
 4.2      Texte question slideUp
 4.7      ▶ audioQuestion démarre (5s)
 9.7      ◀ audioQuestion se termine
10.1      ▶ COUNTDOWN démarre (buffer 0.4s)
10.1      Tick "3" + audioSuspense | ring = 0%
11.1      Tick "2" + audioSuspense | ring = 33%
12.1      Tick "1" + audioSuspense | ring = 66%
13.1      ◀ QUESTION se termine

13.1      ▶ RÉPONSE démarre (fond rouge — FAUX)
13.3      Icône ❌ shakeIn
13.8      Texte "FAUX !" shakeIn | audioAnswer (sounds/wrong.mp3) démarre
17.1      ◀ RÉPONSE se termine

17.1      ▶ EXPLICATION démarre
17.4      Titre slideDown
17.7      Image explication bounceIn
17.9      ▶ audioExplication démarre (13s)
17.9      Point 0 slideRight (interval = 3s)
20.9      Point 1 slideRight
23.9      Point 2 slideRight
26.9      Point 3 slideRight
30.9      ◀ audioExplication se termine | badge bounceIn
31.5      Texte source fadeIn
32.4      ◀ EXPLICATION se termine (+1.5s buffer)

32.4      ▶ OUTRO démarre | audioOutro démarre
32.8      Logo logoPulse
33.2      TikTok item slideRight
33.5      Instagram item slideRight
33.8      YouTube item slideRight
34.2      Bouton "Abonnez-vous" bounceIn
34.7      Texte CTA fadeIn
36.4      ◀ OUTRO se termine | window.__VIDEO_DONE = true

Durée totale estimée : 38s  |  Durée réelle mesurée : ~36.4s
```

---

## Paramètres configurables dans `videos-data.json`

| Paramètre                      | Clé JSON                             | Valeur défaut | Rôle |
|--------------------------------|--------------------------------------|---------------|------|
| Durée intro                    | `timing.introDuration`               | 3s            | Durée écran intro |
| Durée question (minimum)       | `timing.questionDuration`            | 10s           | Plancher de la durée question |
| Durée countdown                | `timing.countdownDuration`           | 3s            | Durée du timer 3-2-1 |
| Durée réponse                  | `timing.answerDuration`              | 4s            | Durée écran réponse |
| Durée explication (minimum)    | `timing.explanationDuration`         | 17s           | Plancher de la durée explication |
| Durée outro                    | `timing.outroDuration`               | 4s            | Durée écran outro |
| Durée audio question           | `question.audioDuration`             | —             | Sync timing question + countdown |
| Durée audio explication        | `explication.audioDuration`          | —             | Sync timing explication + points |

> Les durées `questionDuration` et `explanationDuration` sont des **minimums**.
> Le séquenceur les allonge automatiquement si l'audio est plus long.
