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
const { execSync } = require('child_process');

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
  durationSec: 37,
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
    const payloadStr = JSON.stringify({ settings, video }, null, 2)
      .replace(/\.\/assets\//g, '../assets/');
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

// ─── Étape 2 : Enregistrer en MP4 (Puppeteer + FFmpeg) ───
async function recordVideo(htmlFile, outputMp4, videoId, settings) {
  const puppeteer = require('puppeteer');
  const res = getResolution(settings.format);

  console.log(`\n🎥 Enregistrement vidéo #${videoId} (${res.width}x${res.height})...`);

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [`--window-size=${res.width},${res.height}`],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: res.width, height: res.height });

  // Dossier frames temporaire pour cette vidéo
  const videoFramesDir = path.join(CONFIG.framesDir, `video-${videoId}`);
  if (fs.existsSync(videoFramesDir)) {
    fs.rmSync(videoFramesDir, { recursive: true });
  }
  fs.mkdirSync(videoFramesDir, { recursive: true });

  // Charger le HTML
  const htmlPath = `file:///${htmlFile.replace(/\\/g, '/')}`;
  await page.goto(htmlPath, { waitUntil: 'networkidle0' });

  // Capturer les frames
  const totalFrames = CONFIG.durationSec * CONFIG.fps;
  const frameDelay = 1000 / CONFIG.fps;

  for (let i = 0; i < totalFrames; i++) {
    const frameFile = path.join(videoFramesDir, `frame_${String(i).padStart(5, '0')}.png`);
    await page.screenshot({ path: frameFile, type: 'png' });
    await new Promise(r => setTimeout(r, frameDelay));

    if (i % CONFIG.fps === 0) {
      const sec = Math.floor(i / CONFIG.fps);
      console.log(`  📸 ${sec}s / ${CONFIG.durationSec}s (${Math.round(i/totalFrames*100)}%)`);
    }
  }

  await browser.close();

  // Assembler avec FFmpeg
  console.log(`  🔧 Assemblage FFmpeg...`);
  const ffmpegCmd = `ffmpeg -y -framerate ${CONFIG.fps} -i "${videoFramesDir}/frame_%05d.png" -c:v libx264 -pix_fmt yuv420p -r ${CONFIG.fps} "${outputMp4}"`;

  try {
    execSync(ffmpegCmd, { stdio: 'pipe' });
    console.log(`  ✅ Vidéo créée : ${outputMp4}`);
  } catch (err) {
    console.error(`  ❌ Erreur FFmpeg. Commande manuelle :`);
    console.log(`  ${ffmpegCmd}`);
  }

  // Nettoyer les frames
  fs.rmSync(videoFramesDir, { recursive: true });
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

    await recordVideo(htmlFile, mp4File, video.id, rawData.settings);
  }
}

// ─── Main ───
async function main() {
  const args = process.argv.slice(2);
  const shouldRecord = args.includes('--record');
  const idIndex = args.indexOf('--id');
  const filterId = idIndex !== -1 ? parseInt(args[idIndex + 1]) : null;

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
