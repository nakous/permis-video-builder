 // ══════════════════════════════════════════════════
    //  MOTEUR DE RENDU DYNAMIQUE v3 — TestPermis.fr
    //  - Format responsive (ratio-based)
    //  - Countdown intégré dans l'écran question avec tick-tack
    //  - Timing basé sur les durées audio
    // ══════════════════════════════════════════════════

    // ─── Presets de résolution par plateforme ───
    const FORMAT_PRESETS = {
      'tiktok':    { ratio: '9:16', width: 1080, height: 1920 },
      'reels':     { ratio: '9:16', width: 1080, height: 1920 },
      'shorts':    { ratio: '9:16', width: 1080, height: 1920 },
      'youtube':   { ratio: '16:9', width: 1920, height: 1080 },
      'facebook':  { ratio: '1:1',  width: 1080, height: 1080 },
      'linkedin':  { ratio: '1:1',  width: 1080, height: 1080 },
      'story':     { ratio: '9:16', width: 1080, height: 1920 },
      'twitter':   { ratio: '16:9', width: 1280, height: 720 },
    };

    function getResolution(format) {
      // Si une plateforme est précisée, utiliser le preset
      if (format.platform && FORMAT_PRESETS[format.platform]) {
        return FORMAT_PRESETS[format.platform];
      }
      // Sinon calculer à partir du ratio
      const [rw, rh] = (format.ratio || '9:16').split(':').map(Number);
      if (rw > rh) return { width: 1920, height: Math.round(1920 * rh / rw) };
      if (rw < rh) return { width: 1080, height: Math.round(1080 * rh / rw) };
      return { width: 1080, height: 1080 };
    }

    function loadData() {
      if (window.__VIDEO_DATA) return window.__VIDEO_DATA;
      const params = new URLSearchParams(window.location.search);
      const d = params.get('data');
      if (d) try { return JSON.parse(decodeURIComponent(d)); } catch(e) {}

      return {
        settings: {
          site: { name: "TestPermis.fr", url: "https://testpermis.fr", logo: "", logoAnimation: "zoom-bounce", watermark: "", callToAction: "Testez vos connaissances !" },
          sounds: { intro: "", suspense: "", correct: "", wrong: "", outro: "", backgroundMusic: "", backgroundMusicVolume: 0.15 },
          theme: { primaryColor: "#4facfe", secondaryColor: "#f5576c", backgroundColor: "#0a0a2e", accentGradient: ["#4facfe","#00f2fe"], fontFamily: "Montserrat" },
          socials: { tiktok: "@testpermis.fr", instagram: "@testpermis.fr", youtube: "TestPermis.fr", facebook: "", website: "testpermis.fr" },
          format: { ratio: "9:16", platform: "tiktok", fps: 30 }
        },
        video: {
          id: 1, sujet: "Panneau STOP", categorie: "Signalisation", emoji: "🛑", difficulty: "facile",
          question: { texte: "« Au panneau STOP, je peux ralentir sans m'arrêter. »", media: "", mediaType: "image", audio: "", audioDuration: 5 },
          reponse: "FAUX",
          explication: { titre: "L'arrêt est OBLIGATOIRE", media: "", mediaType: "image", audio: "", audioDuration: 13,
            points: [
              { icon: "🛑", texte: "L'arrêt complet est obligatoire" },
              { icon: "📍", texte: "Arrêtez-vous à la ligne blanche" },
              { icon: "💰", texte: "-4 points + 135€ d'amende" },
              { icon: "✅", texte: "Cédez le passage après l'arrêt" }
            ],
            badge: { texte: "⚠️ -4 pts + 135€", type: "danger" }
          },
          timing: { introDuration: 3, questionDuration: 10, countdownDuration: 3, answerDuration: 4, explanationDuration: 17, outroDuration: 4 },
          source: "", tags: [], description: ""
        }
      };
    }

    // ─── Calcule et applique le scale viewport → video-stage ───
    function applyScale() {
      const stage = document.getElementById('videoStage');
      const res = window.__RESOLUTION || { width: 1080, height: 1920 };
      const scaleX = window.innerWidth  / res.width;
      const scaleY = window.innerHeight / res.height;
      const s = Math.min(scaleX, scaleY);
      // Centrer horizontalement en tenant compte du scale
      const offsetX = (window.innerWidth - res.width * s) / 2;
      stage.style.transform = `translateX(${offsetX}px) scale(${s})`;
    }

    // ─── Appliquer le format responsive ───
    function applyFormat(format) {
      const res = getResolution(format);
      const r = document.documentElement.style;
      r.setProperty('--vw', res.width + 'px');
      r.setProperty('--vh', res.height + 'px');

      // Adapter les tailles de police selon le format (portrait/paysage/carré)
      const isLandscape = res.width > res.height;
      const isSquare    = res.width === res.height;
      const fontScale   = isLandscape ? 0.7 : isSquare ? 0.85 : 1;
      document.getElementById('videoStage').style.fontSize = (fontScale * 100) + '%';

      // Stocker la résolution puis calculer le scale viewport
      window.__RESOLUTION = res;
      applyScale();
      window.addEventListener('resize', applyScale);

      console.log(`📐 Format: ${format.ratio || format.platform} → ${res.width}x${res.height}`);
    }

    function applyTheme(theme) {
      const r = document.documentElement.style;
      if (theme.primaryColor) r.setProperty('--primary', theme.primaryColor);
      if (theme.secondaryColor) r.setProperty('--secondary', theme.secondaryColor);
      if (theme.backgroundColor) { r.setProperty('--bg', theme.backgroundColor); document.getElementById('videoStage').style.background = theme.backgroundColor; }
      if (theme.accentGradient) { r.setProperty('--primary', theme.accentGradient[0]); r.setProperty('--primary2', theme.accentGradient[1]); }
      if (theme.fontFamily) { r.setProperty('--font', `'${theme.fontFamily}', sans-serif`); document.body.style.fontFamily = `'${theme.fontFamily}', sans-serif`; }
    }

    function setupSounds(sounds) {
      if (sounds.intro) document.getElementById('audioIntro').src = sounds.intro;
      if (sounds.suspense) document.getElementById('audioSuspense').src = sounds.suspense;
      if (sounds.outro) document.getElementById('audioOutro').src = sounds.outro;
      if (sounds.backgroundMusic) {
        const bg = document.getElementById('audioBgMusic');
        bg.src = sounds.backgroundMusic;
        bg.volume = sounds.backgroundMusicVolume || 0.15;
      }
    }

    function playAudio(id) {
      const a = document.getElementById(id);
      if (a && a.src && a.src !== window.location.href) a.play().catch(() => {});
    }

    // ─── Timing intelligent basé sur les durées audio ───
    function calculateTiming(video) {
      const t = video.timing;
      const qAudio = video.question.audioDuration || 0;
      const eAudio = video.explication.audioDuration || 0;

      // questionDuration = max(temps configuré, audioDuration + countdown + 2s buffer)
      const minQuestionTime = qAudio + t.countdownDuration + 2;
      const questionDuration = Math.max(t.questionDuration, minQuestionTime);

      // explanationDuration = max(temps configuré, audioDuration + 3s buffer)
      const minExplanationTime = eAudio + 3;
      const explanationDuration = Math.max(t.explanationDuration, minExplanationTime);

      return {
        introDuration: t.introDuration,
        questionDuration,
        countdownDuration: t.countdownDuration,
        answerDuration: t.answerDuration,
        explanationDuration,
        outroDuration: t.outroDuration
      };
    }

    // ─── Helpers séquenceur ───
    const wait = ms => new Promise(r => setTimeout(r, ms));

    // Attend la fin réelle de l'audio, avec fallback timeout pour Puppeteer (headless, pas d'audio)
    function waitForAudio(audioEl, fallbackDuration) {
      return new Promise(resolve => {
        if (!audioEl.src || audioEl.src === window.location.href) {
          return setTimeout(resolve, (fallbackDuration || 0) * 1000);
        }
        let done = false;
        const finish = () => { if (done) return; done = true; audioEl.removeEventListener('ended', finish); audioEl.removeEventListener('error', finish); resolve(); };
        audioEl.addEventListener('ended', finish, { once: true });
        audioEl.addEventListener('error', finish, { once: true });
        // Fallback Puppeteer : si l'audio ne joue pas, continuer après fallbackDuration + 2s
        setTimeout(finish, ((fallbackDuration || 5) + 2) * 1000);
      });
    }

    function showSeq(el) {
      el.style.pointerEvents = 'auto';
      el.style.animation = 'fadeIn 0.5s ease forwards';
    }

    function hideSeq(el) {
      el.style.pointerEvents = 'none';
      el.style.animation = 'fadeOut 0.5s ease forwards';
    }

    // ─── Séquenceur événementiel ───
    async function runSequencer(video, estimatedTiming) {
      const t = estimatedTiming;
      const startTime = performance.now();

      // Progress bar basée sur la durée estimée
      const estimatedTotal = t.introDuration + t.questionDuration + t.answerDuration + t.explanationDuration + t.outroDuration;
      const pbStyle = document.createElement('style');
      pbStyle.textContent = `@keyframes progress { from{width:0} to{width:100%} }`;
      document.head.appendChild(pbStyle);
      document.getElementById('progressBar').style.animation = `progress ${estimatedTotal}s linear forwards`;
      window.__TOTAL_DURATION = estimatedTotal;

      // ══ INTRO ══
      const introEl = document.getElementById('intro');
      showSeq(introEl);
      introEl.querySelector('.logo-container').style.animation = `logoAnim ${t.introDuration - 0.5}s ease forwards`;
      playAudio('audioBgMusic');
      playAudio('audioIntro');

      // Transition après la fin RÉELLE de l'audio intro (pas de timer fixe)
      await waitForAudio(document.getElementById('audioIntro'), t.introDuration);
      hideSeq(introEl);

      // ══ QUESTION ══
      const questionEl = document.getElementById('question');
      showSeq(questionEl);

      // Animer les éléments de la question avec des décalages
      questionEl.querySelector('.question-icon').style.animation = 'bounceIn 0.6s ease forwards';
      setTimeout(() => { questionEl.querySelector('.vrai-faux-badge').style.animation = 'bounceIn 0.8s ease forwards'; }, 300);
      const qMedia = document.getElementById('questionMedia');
      const qVid   = document.getElementById('questionVideo');
      if (qMedia.style.display !== 'none') setTimeout(() => { qMedia.style.animation = 'bounceIn 0.8s ease forwards'; }, 600);
      if (qVid.style.display   !== 'none') setTimeout(() => { qVid.style.animation   = 'bounceIn 0.8s ease forwards'; }, 600);
      setTimeout(() => { questionEl.querySelector('.question-text').style.animation = 'slideUp 1s ease forwards'; }, 1200);

      // Jouer l'audio après l'apparition du texte
      await wait(1700);
      playAudio('audioQuestion');

      // ── Countdown : attend la fin RÉELLE de l'audio question ──
      await waitForAudio(document.getElementById('audioQuestion'), video.question.audioDuration || 5);
      await wait(400); // léger buffer

      const cdOverlay   = document.getElementById('countdownOverlay');
      const cdValue     = document.getElementById('countdownValue');
      const ringProgress = document.getElementById('ringProgress');
      const circumference = 2 * Math.PI * 65;
      ringProgress.style.strokeDasharray  = circumference;
      ringProgress.style.strokeDashoffset = '0';
      const dot3 = document.getElementById('dot3');
      const dot2 = document.getElementById('dot2');
      const dot1 = document.getElementById('dot1');
      [dot3, dot2, dot1].forEach(d => { d.className = 'countdown-dot'; });

      // 3
      cdOverlay.classList.add('visible');
      cdValue.textContent = '3'; cdValue.classList.add('pop');
      dot3.classList.add('active');
      ringProgress.style.strokeDashoffset = '0';
      playAudio('audioSuspense');
      setTimeout(() => cdValue.classList.remove('pop'), 400);
      await wait(1000);

      // 2
      cdValue.textContent = '2'; cdValue.classList.add('pop');
      dot3.classList.remove('active'); dot3.classList.add('done');
      dot2.classList.add('active');
      ringProgress.style.strokeDashoffset = `${circumference / 3}`;
      playAudio('audioSuspense');
      setTimeout(() => cdValue.classList.remove('pop'), 400);
      await wait(1000);

      // 1
      cdValue.textContent = '1'; cdValue.classList.add('pop');
      dot2.classList.remove('active'); dot2.classList.add('done');
      dot1.classList.add('active');
      ringProgress.style.strokeDashoffset = `${(circumference / 3) * 2}`;
      playAudio('audioSuspense');
      setTimeout(() => cdValue.classList.remove('pop'), 400);
      await wait(1000);

      cdOverlay.classList.remove('visible');
      hideSeq(questionEl);

      // ══ RÉPONSE — déclenchée dynamiquement après le dernier tick ══
      const answerEl = document.getElementById('answer');
      showSeq(answerEl);
      await wait(200);
      document.getElementById('answerEmoji').style.animation = 'shakeIn 0.8s ease forwards';
      await wait(500);
      document.getElementById('answerText').style.animation = 'shakeIn 0.6s ease forwards';
      playAudio('audioAnswer');

      await wait(t.answerDuration * 1000);
      hideSeq(answerEl);

      // ══ EXPLICATION ══
      const explanationEl = document.getElementById('explanation');
      showSeq(explanationEl);
      setTimeout(() => { document.getElementById('explanationTitle').style.animation = 'slideDown 0.8s ease forwards'; }, 300);

      const expMedia = document.getElementById('explanationMedia');
      const mainIcon = document.getElementById('mainIcon');
      if (expMedia.style.display !== 'none') setTimeout(() => { expMedia.style.animation = 'bounceIn 0.8s ease forwards'; }, 600);
      if (mainIcon.style.display !== 'none') setTimeout(() => { mainIcon.style.animation = 'bounceIn 0.8s ease forwards'; }, 600);

      await wait(800);
      playAudio('audioExplication');

      // Points animés progressivement pendant l'audio explication
      const points = document.querySelectorAll('#explanationPoints .point');
      const eAudioDur = video.explication.audioDuration || 12;
      const pointInterval = (eAudioDur - 1) / Math.max(points.length, 1);
      points.forEach((p, i) => {
        setTimeout(() => { p.style.animation = 'slideRight 0.8s ease forwards'; }, i * pointInterval * 1000);
      });

      // ── Outro : attend la fin RÉELLE de l'audio explication ──
      await waitForAudio(document.getElementById('audioExplication'), eAudioDur);

      // Badge et source après l'audio
      document.getElementById('infoBadge').style.animation = 'bounceIn 0.6s ease forwards';
      setTimeout(() => { document.getElementById('sourceText').style.animation = 'fadeIn 0.5s ease forwards'; }, 600);

      await wait(1500);
      hideSeq(explanationEl);

      // ══ OUTRO ══
      const outroEl = document.getElementById('outro');
      showSeq(outroEl);
      playAudio('audioOutro');

      const outroLogo    = outroEl.querySelector('.outro-logo');
      const outroLogoImg = document.getElementById('outroLogoImage');
      if (outroLogo)                              { outroLogo.style.opacity    = '0'; setTimeout(() => { outroLogo.style.animation    = 'logoPulse 1s ease forwards'; }, 400); }
      if (outroLogoImg.style.display !== 'none')  { outroLogoImg.style.opacity = '0'; setTimeout(() => { outroLogoImg.style.animation = 'logoPulse 1s ease forwards'; }, 400); }

      document.querySelectorAll('.social-item').forEach((s, i) => {
        setTimeout(() => { s.style.animation = 'slideRight 0.6s ease forwards'; }, 800 + i * 300);
      });
      setTimeout(() => { outroEl.querySelector('.subscribe-btn').style.animation = 'bounceIn 0.8s ease forwards'; }, 1800);
      setTimeout(() => { document.getElementById('ctaText').style.animation = 'fadeIn 0.5s ease forwards'; }, 2300);

      await wait(t.outroDuration * 1000);

      // Durée réelle mesurée
      const elapsed = (performance.now() - startTime) / 1000;
      window.__TOTAL_DURATION = elapsed;
      window.__VIDEO_DONE = true;
      console.log(`✅ Vidéo terminée en ${elapsed.toFixed(1)}s (estimé: ${estimatedTotal}s)`);
    }

    // ─── SVG Icons ───
    const SVG_ICONS = {
      // Social
      tiktok: `<svg viewBox="0 0 24 24" fill="white" width="28" height="28"><path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-2.88 2.5 2.89 2.89 0 01-2.89-2.89 2.89 2.89 0 012.89-2.89c.28 0 .54.04.79.1v-3.5a6.37 6.37 0 00-.79-.05A6.34 6.34 0 003.15 15.2a6.34 6.34 0 006.34 6.34 6.34 6.34 0 006.34-6.34V8.69a8.2 8.2 0 004.76 1.52V6.76a4.79 4.79 0 01-1-.07z"/></svg>`,
      instagram: `<svg viewBox="0 0 24 24" fill="white" width="28" height="28"><path d="M12 2.16c3.2 0 3.58.01 4.85.07 1.17.05 1.97.24 2.44.41.61.24 1.05.52 1.51.98.46.46.74.9.98 1.51.17.47.36 1.27.41 2.44.06 1.27.07 1.65.07 4.85s-.01 3.58-.07 4.85c-.05 1.17-.24 1.97-.41 2.44a4.08 4.08 0 01-.98 1.51c-.46.46-.9.74-1.51.98-.47.17-1.27.36-2.44.41-1.27.06-1.65.07-4.85.07s-3.58-.01-4.85-.07c-1.17-.05-1.97-.24-2.44-.41a4.08 4.08 0 01-1.51-.98 4.08 4.08 0 01-.98-1.51c-.17-.47-.36-1.27-.41-2.44C2.17 15.58 2.16 15.2 2.16 12s.01-3.58.07-4.85c.05-1.17.24-1.97.41-2.44.24-.61.52-1.05.98-1.51a4.08 4.08 0 011.51-.98c.47-.17 1.27-.36 2.44-.41C8.42 2.17 8.8 2.16 12 2.16zM12 0C8.74 0 8.33.01 7.05.07 5.78.13 4.9.33 4.14.63c-.78.3-1.44.71-2.1 1.37A5.88 5.88 0 00.63 4.14C.33 4.9.13 5.78.07 7.05.01 8.33 0 8.74 0 12s.01 3.67.07 4.95c.06 1.27.26 2.15.56 2.91.3.78.71 1.44 1.37 2.1a5.88 5.88 0 002.14 1.37c.76.3 1.64.5 2.91.56C8.33 23.99 8.74 24 12 24s3.67-.01 4.95-.07c1.27-.06 2.15-.26 2.91-.56a5.88 5.88 0 002.14-1.37 5.88 5.88 0 001.37-2.1c.3-.76.5-1.64.56-2.91.06-1.28.07-1.69.07-4.95s-.01-3.67-.07-4.95c-.06-1.27-.26-2.15-.56-2.91a5.88 5.88 0 00-1.37-2.14A5.88 5.88 0 0019.86.63C19.1.33 18.22.13 16.95.07 15.67.01 15.26 0 12 0zm0 5.84a6.16 6.16 0 100 12.32 6.16 6.16 0 000-12.32zM12 16a4 4 0 110-8 4 4 0 010 8zm7.85-10.4a1.44 1.44 0 11-2.88 0 1.44 1.44 0 012.88 0z"/></svg>`,
      youtube: `<svg viewBox="0 0 24 24" fill="white" width="28" height="28"><path d="M23.5 6.19a3.02 3.02 0 00-2.12-2.14C19.5 3.5 12 3.5 12 3.5s-7.5 0-9.38.55A3.02 3.02 0 00.5 6.19 31.6 31.6 0 000 12a31.6 31.6 0 00.5 5.81 3.02 3.02 0 002.12 2.14c1.88.55 9.38.55 9.38.55s7.5 0 9.38-.55a3.02 3.02 0 002.12-2.14A31.6 31.6 0 0024 12a31.6 31.6 0 00-.5-5.81zM9.55 15.57V8.43L15.82 12l-6.27 3.57z"/></svg>`,
      facebook: `<svg viewBox="0 0 24 24" fill="white" width="28" height="28"><path d="M24 12.07C24 5.41 18.63 0 12 0S0 5.4 0 12.07c0 6.03 4.39 11.02 10.13 11.93v-8.44H7.08v-3.49h3.04V9.41c0-3.02 1.79-4.7 4.53-4.7 1.31 0 2.68.24 2.68.24v2.97h-1.51c-1.49 0-1.95.93-1.95 1.89v2.26h3.33l-.53 3.49h-2.8v8.44C19.61 23.09 24 18.1 24 12.07z"/></svg>`,
      // Answer
      check: `<svg viewBox="0 0 24 24" width="1em" height="1em"><circle cx="12" cy="12" r="11" fill="none" stroke="#44ff44" stroke-width="2"/><path d="M7 12.5l3 3 7-7" fill="none" stroke="#44ff44" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
      cross: `<svg viewBox="0 0 24 24" width="1em" height="1em"><circle cx="12" cy="12" r="11" fill="none" stroke="#ff4444" stroke-width="2"/><path d="M8 8l8 8M16 8l-8 8" fill="none" stroke="#ff4444" stroke-width="2.5" stroke-linecap="round"/></svg>`,
      // Bell
      bell: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M12 22c1.1 0 2-.9 2-2h-4a2 2 0 002 2zm6-6V10c0-3.07-1.63-5.64-4.5-6.32V3a1.5 1.5 0 00-3 0v.68C7.64 4.36 6 6.92 6 10v6l-2 2v1h16v-1l-2-2z"/></svg>`,
      // Car (logo fallback)
      car: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.85 7h10.29l1.08 3.11H5.77L6.85 7zM19 17H5v-5h14v5z"/><circle cx="7.5" cy="14.5" r="1.5" fill="white"/><circle cx="16.5" cy="14.5" r="1.5" fill="white"/></svg>`,
      // Common point icons
      stop: `<svg viewBox="0 0 24 24" width="1em" height="1em"><polygon points="7.86,2 16.14,2 22,7.86 22,16.14 16.14,22 7.86,22 2,16.14 2,7.86" fill="#ff4444"/><text x="12" y="16" text-anchor="middle" fill="white" font-size="10" font-weight="bold">STOP</text></svg>`,
      pin: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5a2.5 2.5 0 010-5 2.5 2.5 0 010 5z"/></svg>`,
      money: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M11.8 10.9c-2.27-.59-3-1.2-3-2.15 0-1.09 1.01-1.85 2.7-1.85 1.78 0 2.44.85 2.5 2.1h2.21c-.07-1.72-1.12-3.3-3.21-3.81V3h-3v2.16c-1.94.42-3.5 1.68-3.5 3.61 0 2.31 1.91 3.46 4.7 4.13 2.5.6 3 1.48 3 2.41 0 .69-.49 1.79-2.7 1.79-2.06 0-2.87-.92-2.98-2.1h-2.2c.12 2.19 1.76 3.42 3.68 3.83V21h3v-2.15c1.95-.37 3.5-1.5 3.5-3.55 0-2.84-2.43-3.81-4.7-4.4z"/></svg>`,
      valid: `<svg viewBox="0 0 24 24" width="1em" height="1em"><circle cx="12" cy="12" r="10" fill="none" stroke="#2ed573" stroke-width="2"/><path d="M7 12.5l3.5 3.5 6.5-7" fill="none" stroke="#2ed573" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
      warning: `<svg viewBox="0 0 24 24" fill="#ffa502" width="1em" height="1em"><path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/></svg>`,
      info: `<svg viewBox="0 0 24 24" fill="#4facfe" width="1em" height="1em"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>`,
      shield: `<svg viewBox="0 0 24 24" fill="#4facfe" width="1em" height="1em"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4z"/></svg>`,
      eye: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/></svg>`,
      helmet: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M12 2C6.48 2 2 6.48 2 12c0 2.76 1.12 5.26 2.93 7.07l1.41-1.41A7.95 7.95 0 014 12c0-4.42 3.58-8 8-8s8 3.58 8 8a7.95 7.95 0 01-2.34 5.66l1.41 1.41A9.97 9.97 0 0022 12c0-5.52-4.48-10-10-10zm0 4a6 6 0 00-6 6h2a4 4 0 018 0h2a6 6 0 00-6-6z"/></svg>`,
      speed: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M20.38 8.57l-1.23 1.85a8 8 0 01-.22 7.58H5.07A8 8 0 0115.58 6.85l1.85-1.23A10 10 0 003.35 19a2 2 0 001.72 1h13.85a2 2 0 001.74-1 10 10 0 00-.27-10.44z"/><path d="M10.59 15.41a2 2 0 002.83 0l5.66-8.49-8.49 5.66a2 2 0 000 2.83z"/></svg>`,
      road: `<svg viewBox="0 0 24 24" fill="white" width="1em" height="1em"><path d="M11 4h2v3h-2V4zm0 4h2v3h-2V8zm0 4h2v3h-2v-3zm0 4h2v5h-2v-5zM4 2l3 18h2L6.5 2H4zm14 0h-2.5L13 20h2l3-18z"/></svg>`,
    };

    // Emoji → SVG mapping
    const EMOJI_TO_SVG = {
      '🛑': 'stop', '📍': 'pin', '💰': 'money', '✅': 'valid', '⚠️': 'warning',
      'ℹ️': 'info', '🛡️': 'shield', '👁️': 'eye', '🪖': 'helmet', '⏱️': 'speed',
      '🏍️': 'speed', '🚗': 'car', '🔔': 'bell', '🎵': 'tiktok', '📸': 'instagram',
      '▶️': 'youtube', '👤': 'facebook', '❌': 'cross', '🚧': 'warning',
      '📏': 'road', '🛣️': 'road', '🔒': 'shield', '💡': 'info', '🔺': 'warning',
      '🔴': 'stop', '🟢': 'valid', '🏁': 'road',
    };

    function emojiToSvg(emoji, fallbackSize) {
      const key = EMOJI_TO_SVG[emoji];
      if (key && SVG_ICONS[key]) return SVG_ICONS[key];
      // Fallback: return emoji as text
      return emoji;
    }

    // ─── Remplir le contenu et lancer le séquenceur ───
    function renderVideo(data) {
      const settings = data.settings;
      const video = data.video;
      const isVrai = video.reponse.toUpperCase() === "VRAI";

      // ── Watermark ──
      const wm = document.getElementById('watermark');
      if (settings.site.watermark) wm.innerHTML = `<img src="${settings.site.watermark}" alt="watermark">`;
      else wm.textContent = settings.site.name;

      // ── Difficulty ──
      if (video.difficulty) {
        const db = document.getElementById('difficultyBadge');
        db.style.display = 'block';
        db.textContent = video.difficulty;
        db.className = `difficulty-badge ${video.difficulty}`;
      }

      // ── Intro ──
      if (settings.site.logo) {
        document.getElementById('logoImage').src = settings.site.logo;
        document.getElementById('logoImage').style.display = 'block';
        document.getElementById('logoEmoji').style.display = 'none';
      } else {
        document.getElementById('logoEmoji').style.display = 'flex';
        document.getElementById('logoEmoji').innerHTML = emojiToSvg(video.emoji || '🚗');
      }
      document.getElementById('siteName').textContent = settings.site.name;
      document.getElementById('subtitle').textContent = video.categorie;
      document.getElementById('siteUrl').textContent = settings.site.url.replace('https://', '');

      // ── Question ──
      document.getElementById('questionEmoji').innerHTML = emojiToSvg(video.emoji || '❓');
      document.getElementById('questionText').textContent = video.question.texte;
      if (video.question.media && video.question.mediaType === 'image') {
        document.getElementById('questionMedia').src = video.question.media;
        document.getElementById('questionMedia').style.display = 'block';
      } else if (video.question.media && video.question.mediaType === 'video') {
        const qv = document.getElementById('questionVideo');
        qv.src = video.question.media; qv.style.display = 'block';
      }

      // ── Réponse ──
      const answerDiv = document.getElementById('answer');
      answerDiv.className = `sequence ${isVrai ? 'answer-vrai' : 'answer-faux'}`;
      document.getElementById('answerEmoji').innerHTML = isVrai ? SVG_ICONS.check : SVG_ICONS.cross;
      const answerText = document.getElementById('answerText');
      answerText.textContent = `${video.reponse.toUpperCase()} !`;
      answerText.className = `answer-text ${isVrai ? 'vrai' : 'faux'}`;

      // ── Explication ──
      document.getElementById('explanationTitle').textContent = video.explication.titre;
      if (video.explication.media && video.explication.mediaType === 'image') {
        document.getElementById('explanationMedia').src = video.explication.media;
        document.getElementById('explanationMedia').style.display = 'block';
        document.getElementById('mainIcon').style.display = 'none';
      } else {
        document.getElementById('mainIcon').innerHTML = emojiToSvg(video.emoji);
      }

      // Points dynamiques
      const pointsContainer = document.getElementById('explanationPoints');
      pointsContainer.innerHTML = '';
      video.explication.points.forEach(p => {
        const div = document.createElement('div');
        div.className = 'point';
        div.innerHTML = `<div class="point-icon">${emojiToSvg(p.icon)}</div><span>${p.texte}</span>`;
        pointsContainer.appendChild(div);
      });

      const badge = document.getElementById('infoBadge');
      badge.textContent = video.explication.badge.texte;
      badge.className = `info-badge ${video.explication.badge.type}`;

      if (video.source) document.getElementById('sourceText').textContent = `Source : ${video.source}`;

      // ── Outro ──
      if (settings.site.logo) {
        document.getElementById('outroLogoImage').src = settings.site.logo;
        document.getElementById('outroLogoImage').style.display = 'block';
      }
      document.getElementById('outroSiteName').textContent = settings.site.name;
      document.getElementById('outroUrl').textContent = settings.site.url.replace('https://', '');

      const socialContainer = document.getElementById('socialLinks');
      socialContainer.innerHTML = '';
      const socials = settings.socials;
      if (socials.tiktok) socialContainer.innerHTML += `<div class="social-item"><div class="social-icon tiktok">${SVG_ICONS.tiktok}</div><span>${socials.tiktok}</span></div>`;
      if (socials.instagram) socialContainer.innerHTML += `<div class="social-item"><div class="social-icon instagram">${SVG_ICONS.instagram}</div><span>${socials.instagram}</span></div>`;
      if (socials.youtube) socialContainer.innerHTML += `<div class="social-item"><div class="social-icon youtube">${SVG_ICONS.youtube}</div><span>${socials.youtube}</span></div>`;
      if (socials.facebook) socialContainer.innerHTML += `<div class="social-item"><div class="social-icon facebook">${SVG_ICONS.facebook}</div><span>${socials.facebook}</span></div>`;

      if (settings.site.callToAction) document.getElementById('ctaText').textContent = settings.site.callToAction;

      // ── Calculer timing estimé (pour progress bar) + lancer le séquenceur ──
      const estimatedTiming = calculateTiming(video);
      runSequencer(video, estimatedTiming).catch(console.error);
    }

    // ─── Lancement ───
    const rawData = loadData();

    // Initialiser le DOM (format, thème, contenu) sans démarrer le séquenceur
    // Le séquenceur démarre après le clic (politique autoplay Chrome)
    function setupDOM(data) {
      const settings = data.settings;
      const video    = data.video;
      applyFormat(settings.format);
      applyTheme(settings.theme);
      setupSounds(settings.sounds);
      if (settings.sounds.correct && video.reponse.toUpperCase() === 'VRAI') document.getElementById('audioAnswer').src = settings.sounds.correct;
      if (settings.sounds.wrong   && video.reponse.toUpperCase() !== 'VRAI') document.getElementById('audioAnswer').src = settings.sounds.wrong;
      if (video.question.audio)    document.getElementById('audioQuestion').src    = video.question.audio;
      if (video.explication.audio) document.getElementById('audioExplication').src = video.explication.audio;
    }
    setupDOM(rawData);

    document.getElementById('startOverlay').addEventListener('click', function () {
      this.style.display = 'none';

      // Pré-déverrouiller tous les éléments audio en un seul geste utilisateur
      // (sans ça Chrome bloque .play() appelé en dehors du handler)
      ['audioIntro','audioBgMusic','audioQuestion','audioAnswer',
       'audioExplication','audioOutro','audioSuspense'].forEach(id => {
        const a = document.getElementById(id);
        if (a && a.src && a.src !== window.location.href) {
          a.play().then(() => { a.pause(); a.currentTime = 0; }).catch(() => {});
        }
      });

      renderVideo(rawData);
    }, { once: true });