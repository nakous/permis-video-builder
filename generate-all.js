/**
 * TestPermis.fr — Générateur de vidéos en masse
 * 
 * Ce script :
 * 1. Lit videos-data.json (liste de sujets)
 * 2. Génère un fichier HTML par vidéo (à partir du template)
 * 3. Enregistre chaque HTML en MP4 avec Puppeteer + FFmpeg
 * 
 * Installation :
 *   npm install puppeteer
 *   + FFmpeg installé sur le système (https://ffmpeg.org/download.html)
 * 
 * Usage :
 *   node generate-all.js              → Génère tous les HTML
 *   node generate-all.js --record     → Génère HTML + enregistre en MP4
 *   node generate-all.js --record --id 3  → Enregistre seulement la vidéo #3
 */

const fs = require('fs');
const path = require('path');
const { execSync, execFileSync } = require('child_process');

// ─── Configuration ───
const FORMAT_PRESETS = {
  'tiktok':   { width: 1080, height: 1920 },
  'reels':    { width: 1080, height: 1920 },
  'shorts':   { width: 1080, height: 1920 },
  'youtube':  { width: 1920, height: 1080 },
  'facebook': { width: 1080, height: 1080 },
  'linkedin': { width: 1080, height: 1080 },
  'story':    { width: 1080, height: 1920 },
  'twitter':  { width: 1280, height: 720 },
};

function getResolution(format) {
  if (format.platform && FORMAT_PRESETS[format.platform]) return FORMAT_PRESETS[format.platform];
  const [rw, rh] = (format.ratio || '9:16').split(':').map(Number);
  if (rw > rh) return { width: 1920, height: Math.round(1920 * rh / rw) };
  if (rw < rh) return { width: 1080, height: Math.round(1080 * rh / rw) };
  return { width: 1080, height: 1080 };
}

const CONFIG = {
  templateFile: path.join(__dirname, 'template.html'),
  dataFile: path.join(__dirname, 'videos-data.json'),
  outputDir: path.join(__dirname, 'output'),
  framesDir: path.join(__dirname, 'output', 'frames'),
  width: 1080,
  height: 1920,
  fps: 30,
};

// ─── Étape 1 : Générer les fichiers HTML ───
function generateHTML() {
  const template = fs.readFileSync(CONFIG.templateFile, 'utf-8');
  const rawData = JSON.parse(fs.readFileSync(CONFIG.dataFile, 'utf-8'));
  const settings = rawData.settings;
  const videos = rawData.videos;

  if (!fs.existsSync(CONFIG.outputDir)) {
    fs.mkdirSync(CONFIG.outputDir, { recursive: true });
  }

  console.log(`\n🎬 Génération de ${videos.length} vidéos HTML...\n`);

  for (const video of videos) {
    const slug = video.sujet
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');

    const filename = `video-${video.id}-${slug}.html`;
    const filepath = path.join(CONFIG.outputDir, filename);

    // Injecter settings + video dans le template
    // Corriger les chemins relatifs: output/ → ../assets/ au lieu de ./assets/
    // Échapper </script> pour éviter la fermeture prématurée du tag
    const payloadStr = JSON.stringify({ settings, video }, null, 2)
      .replace(/\.\/assets\//g, '../assets/')
      .replace(/<\/script>/gi, '<\\/script>');
    const dataScript = `<script>window.__VIDEO_DATA = ${payloadStr};</script>`;
    const html = template.replace('</head>', `${dataScript}\n</head>`);

    fs.writeFileSync(filepath, html, 'utf-8');

    const totalDuration = Object.values(video.timing).reduce((a, b) => a + b, 0);
    const res = getResolution(settings.format);
    console.log(`  ✅ ${filename} — "${video.sujet}" (${totalDuration}s, ${video.difficulty}, ${settings.format.platform || settings.format.ratio} ${res.width}x${res.height})`);
  }

  console.log(`\n📁 Fichiers générés dans : ${CONFIG.outputDir}`);
  return videos;
}

// ─── Assemblage MP4 avec audio — approche 3 passes ───
// Passe 1 : frames → vidéo muette
// Passe 2 : toutes les pistes audio → fichier WAV mixé
// Passe 3 : mux vidéo + audio → MP4 final
function buildAudioMix(videoFramesDir, outputMp4, video, settings, totalDuration) {
  const sounds = settings.sounds;
  const timing = video.timing;

  const framesPattern = path.join(videoFramesDir, 'frame_%05d.png').replace(/\\/g, '/');
  const outputPath    = outputMp4.replace(/\\/g, '/');
  const silentMp4     = outputPath.replace(/\.mp4$/, '-silent.mp4');
  const mixedWav      = outputPath.replace(/\.mp4$/, '-audio.wav');

  // ── Résolution des chemins assets ──
  const resolveAsset = (p) => {
    if (!p) return null;
    const full = path.resolve(__dirname, p.replace(/^\.\.\//, './').replace(/^\.\//, './'));
    return fs.existsSync(full) ? full : null;
  };

  // ── Offsets temporels (ms) ──
  const tQuestion    = timing.introDuration * 1000;
  const qAudioMs     = (video.question.audioDuration || 0) * 1000;
  const tCountdown   = tQuestion + qAudioMs + 1000;
  const tAnswer      = tQuestion + timing.questionDuration * 1000;
  const tExplanation = tAnswer + timing.answerDuration * 1000;
  const tOutro       = tExplanation + timing.explanationDuration * 1000;

  // ── Liste des pistes : { file, delayMs, volume, loop } ──
  const tracks = [];
  const bgFile = resolveAsset(sounds.backgroundMusic);
  if (bgFile) tracks.push({ file: bgFile, delayMs: 0, volume: sounds.backgroundMusicVolume || 0.15, loop: true });
  const introFile = resolveAsset(sounds.intro);
  if (introFile) tracks.push({ file: introFile, delayMs: 0, volume: 1 });
  const qAudioFile = resolveAsset(video.question.audio);
  if (qAudioFile) tracks.push({ file: qAudioFile, delayMs: tQuestion, volume: 1 });
  const tickFile = resolveAsset(sounds.suspense);
  if (tickFile) {
    tracks.push({ file: tickFile, delayMs: tCountdown,        volume: 1 });
    tracks.push({ file: tickFile, delayMs: tCountdown + 1000, volume: 1 });
    tracks.push({ file: tickFile, delayMs: tCountdown + 2000, volume: 1 });
  }
  const isCorrect = video.reponse === 'VRAI';
  const answerFile = resolveAsset(isCorrect ? sounds.correct : sounds.wrong);
  if (answerFile) tracks.push({ file: answerFile, delayMs: tAnswer, volume: 1 });
  const explFile = resolveAsset(video.explication.audio);
  if (explFile) tracks.push({ file: explFile, delayMs: tExplanation, volume: 1 });
  const outroFile = resolveAsset(sounds.outro);
  if (outroFile) tracks.push({ file: outroFile, delayMs: tOutro, volume: 1 });

  try {
    // ══ PASSE 1 : frames PNG → vidéo muette H.264 ══
    console.log(`  🔧 Passe 1/3 — encodage vidéo (${totalDuration}s à ${CONFIG.fps}fps)...`);
    execFileSync('ffmpeg', [
      '-y',
      '-framerate', String(CONFIG.fps),
      '-i', framesPattern,
      '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
      '-r', String(CONFIG.fps),
      '-t', String(totalDuration),
      silentMp4,
    ], { stdio: 'pipe' });

    if (tracks.length === 0) {
      // Pas d'audio — renommer la vidéo muette en sortie finale
      fs.renameSync(silentMp4, outputMp4);
      console.log(`  ✅ Vidéo créée (sans audio) : ${outputMp4}`);
      return true;
    }

    // ══ PASSE 2 : mixer toutes les pistes → WAV ══
    console.log(`  🔧 Passe 2/3 — mixage audio (${tracks.length} pistes)...`);
    const audioArgs = ['-y'];
    const filterParts = [];
    const mixLabels   = [];

    tracks.forEach((track, i) => {
      if (track.loop) {
        audioArgs.push('-stream_loop', '-1', '-t', String(totalDuration));
      }
      audioArgs.push('-i', track.file.replace(/\\/g, '/'));

      const label    = `a${i}`;
      const delayStr = `${Math.round(track.delayMs)}|${Math.round(track.delayMs)}`;
      let chain = `[${i}:a]adelay=${delayStr}`;
      if (track.volume !== 1) chain += `,volume=${track.volume}`;
      chain += `[${label}]`;
      filterParts.push(chain);
      mixLabels.push(`[${label}]`);
    });

    // amix en FFmpeg 4.x divise le volume par N — on compense avec volume=N
    filterParts.push(
      `${mixLabels.join('')}amix=inputs=${tracks.length}:duration=longest,volume=${tracks.length}[aout]`
    );

    audioArgs.push(
      '-filter_complex', filterParts.join('; '),
      '-map', '[aout]',
      '-ar', '44100',
      '-t', String(totalDuration),
      mixedWav,
    );
    execFileSync('ffmpeg', audioArgs, { stdio: 'pipe' });

    // ══ PASSE 3 : mux vidéo muette + WAV → MP4 final ══
    console.log(`  🔧 Passe 3/3 — mux vidéo + audio...`);
    execFileSync('ffmpeg', [
      '-y',
      '-i', silentMp4,
      '-i', mixedWav,
      '-c:v', 'copy',
      '-c:a', 'aac', '-b:a', '192k',
      '-shortest',
      outputPath,
    ], { stdio: 'pipe' });

    // Nettoyer les fichiers temporaires
    fs.unlinkSync(silentMp4);
    fs.unlinkSync(mixedWav);

    console.log(`  ✅ Vidéo créée (avec audio) : ${outputMp4}`);
    return true;

  } catch (err) {
    const msg = err.stderr?.toString() || err.message || String(err);
    console.error(`  ❌ Erreur FFmpeg :`, msg.split('\n').slice(-5).join('\n'));
    // Nettoyer les fichiers temporaires partiels
    for (const tmp of [silentMp4, mixedWav]) {
      try { if (fs.existsSync(tmp)) fs.unlinkSync(tmp); } catch (_) {}
    }
    return false;
  }
}

// ─── Étape 2 : Enregistrer en MP4 (Puppeteer + FFmpeg) ───
async function recordVideo(htmlFile, outputMp4, videoId, settings, video) {
  const puppeteer = require('puppeteer');
  const res = getResolution(settings.format);

  // Durée calculée dynamiquement depuis le timing de la vidéo
  const totalDuration = Object.values(video.timing).reduce((a, b) => a + b, 0);
  const totalFrames   = totalDuration * CONFIG.fps;
  const frameDelay    = 1000 / CONFIG.fps; // ms par frame

  console.log(`\n🎥 Enregistrement vidéo #${videoId} (${res.width}x${res.height}, ${totalDuration}s, ${totalFrames} frames)...`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      `--window-size=${res.width},${res.height}`,
      '--disable-background-timer-throttling',
      '--disable-renderer-backgrounding',
      '--disable-backgrounding-occluded-windows',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: res.width, height: res.height });

  // Dossier frames temporaire
  const videoFramesDir = path.join(CONFIG.framesDir, `video-${videoId}`);
  if (fs.existsSync(videoFramesDir)) fs.rmSync(videoFramesDir, { recursive: true });
  fs.mkdirSync(videoFramesDir, { recursive: true });

  // 1. Charger la page normalement (réseau réel) — AVANT d'activer le virtual time
  const htmlPath = `file:///${htmlFile.replace(/\\/g, '/')}`;
  await page.goto(htmlPath, { waitUntil: 'load' });

  // 2. CDP — horloge virtuelle déterministe (activée APRÈS la navigation)
  // Élimine la dérive de framerate causée par le temps de screenshot réel
  // À ce stade la page est chargée, on fige le temps JS/CSS à t=0
  const client = await page.createCDPSession();
  await client.send('Emulation.setVirtualTimePolicy', { policy: 'pause' });

  // Capture frame par frame : screenshot → avancer le temps virtuel d'exactement 1 frame
  for (let i = 0; i < totalFrames; i++) {
    const frameFile = path.join(videoFramesDir, `frame_${String(i).padStart(5, '0')}.png`);
    await page.screenshot({ path: frameFile, type: 'png' });

    // Préparer le listener AVANT d'envoyer la commande (évite la race condition)
    const budgetExpired = new Promise(resolve => {
      client.once('Emulation.virtualTimeBudgetExpired', resolve);
    });
    await client.send('Emulation.setVirtualTimePolicy', {
      policy: 'advance',
      budget: frameDelay,
      maxVirtualTimeTaskStarvationCount: 0,
    });
    await budgetExpired;

    if (i % CONFIG.fps === 0) {
      console.log(`  📸 ${Math.floor(i / CONFIG.fps)}s / ${totalDuration}s (${Math.round(i / totalFrames * 100)}%)`);
    }
  }

  await browser.close();

  // Mixer frames + toutes les pistes audio → MP4
  const success = buildAudioMix(videoFramesDir, outputMp4, video, settings, totalDuration);

  // Nettoyer les frames temporaires seulement si le MP4 a bien été créé
  if (success) {
    fs.rmSync(videoFramesDir, { recursive: true });
  } else {
    console.log(`  ⚠️ Frames conservées dans : ${videoFramesDir}`);
  }
}

// ─── Étape 3 : Enregistrer toutes les vidéos ───
async function recordAll(filterById) {
  const rawData = JSON.parse(fs.readFileSync(CONFIG.dataFile, 'utf-8'));
  const videos = rawData.videos;

  for (const video of videos) {
    if (filterById && video.id !== filterById) continue;

    const slug = video.sujet
      .toLowerCase()
      .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '');

    const htmlFile = path.join(CONFIG.outputDir, `video-${video.id}-${slug}.html`);
    const mp4File = path.join(CONFIG.outputDir, `video-${video.id}-${slug}.mp4`);

    if (!fs.existsSync(htmlFile)) {
      console.log(`  ⚠️ HTML introuvable pour vidéo #${video.id}, lancez d'abord sans --record`);
      continue;
    }

    await recordVideo(htmlFile, mp4File, video.id, rawData.settings, video);
  }
}

// ─── Main ───
async function main() {
  const args = process.argv.slice(2);
  const shouldRecord = args.includes('--record');
  const idIndex = args.indexOf('--id');
  let filterId = null;
  if (idIndex !== -1) {
    filterId = parseInt(args[idIndex + 1]);
    if (Number.isNaN(filterId)) {
      console.error("  ❌ --id doit être suivi d'un nombre. Ex: node generate-all.js --record --id 3");
      process.exit(1);
    }
  }

  // Toujours générer les HTML
  generateHTML();

  // Si --record, enregistrer en MP4
  if (shouldRecord) {
    console.log('\n' + '═'.repeat(50));
    console.log('🎬 MODE ENREGISTREMENT VIDÉO');
    console.log('═'.repeat(50));
    await recordAll(filterId);
  } else {
    console.log('\n💡 Pour enregistrer en MP4 :');
    console.log('   node generate-all.js --record');
    console.log('   node generate-all.js --record --id 1  (une seule vidéo)');
    console.log('\n💡 Ou ouvrez les HTML dans Chrome pour voir les animations !');
  }
}

main().catch(console.error);
