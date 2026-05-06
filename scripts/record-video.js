'use strict';

// Enregistre les vidéos HTML en MP4 via Puppeteer + FFmpeg.
// Prérequis : npm install puppeteer  +  FFmpeg dans le PATH
//
// Usage :
//   node scripts/record-video.js              → toutes les vidéos
//   node scripts/record-video.js --id 2       → vidéo 2 uniquement

const fs      = require('fs');
const path    = require('path');
const { execSync, spawn } = require('child_process');

const ROOT      = path.resolve(__dirname, '..');
const HTML_DIR  = path.join(ROOT, 'output', 'html');
const MP4_DIR   = path.join(ROOT, 'output', 'mp4');

if (!fs.existsSync(MP4_DIR)) fs.mkdirSync(MP4_DIR, { recursive: true });

// ── Vérifier les dépendances ──────────────────────────────────────────────────

let puppeteer;
try {
  puppeteer = require('puppeteer');
} catch {
  console.error('Puppeteer non installé. Lancez : npm install puppeteer');
  process.exit(1);
}

try {
  execSync('ffmpeg -version', { stdio: 'ignore' });
} catch {
  console.error('FFmpeg introuvable. Installez-le : https://ffmpeg.org/download.html');
  process.exit(1);
}

// ── Filtrer les HTML à enregistrer ───────────────────────────────────────────

const idArg    = process.argv.indexOf('--id');
const targetId = idArg !== -1 ? process.argv[idArg + 1] : null;

const htmlFiles = fs.readdirSync(HTML_DIR)
  .filter(f => f.endsWith('.html'))
  .filter(f => !targetId || f.includes(`video-${targetId}-`));

if (htmlFiles.length === 0) {
  console.error('Aucun fichier HTML trouvé dans output/html/. Lancez d\'abord generate-all.js.');
  process.exit(1);
}

// ── Enregistrement ───────────────────────────────────────────────────────────

async function recordVideo(htmlFile) {
  const htmlPath  = path.join(HTML_DIR, htmlFile);
  const mp4Name   = htmlFile.replace('.html', '.mp4');
  const mp4Path   = path.join(MP4_DIR, mp4Name);
  const frameDir  = path.join(MP4_DIR, htmlFile.replace('.html', '-frames'));
  const fileUrl   = 'file:///' + htmlPath.replace(/\\/g, '/');

  console.log(`\n🎬  ${htmlFile}`);

  if (!fs.existsSync(frameDir)) fs.mkdirSync(frameDir, { recursive: true });

  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--autoplay-policy=no-user-gesture-required'],
  });

  const page = await browser.newPage();

  // Lire la résolution depuis __RESOLUTION après chargement
  await page.goto(fileUrl, { waitUntil: 'networkidle0' });

  // Supprimer l'overlay "Tap to play" et démarrer la vidéo automatiquement
  await page.evaluate(() => {
    const overlay = document.getElementById('startOverlay');
    if (overlay) overlay.click();
  });

  const { width, height } = await page.evaluate(() => window.__RESOLUTION || { width: 1080, height: 1920 });
  await page.setViewport({ width, height });

  // Capturer les frames jusqu'à la fin (window.__VIDEO_DONE = true)
  const fps = 30;
  const frameInterval = 1000 / fps;
  let frameIndex = 0;

  console.log(`  Résolution : ${width}x${height} @ ${fps}fps`);
  process.stdout.write('  Capture frames : ');

  while (true) {
    const done = await page.evaluate(() => window.__VIDEO_DONE);
    if (done) break;

    const framePath = path.join(frameDir, `frame-${String(frameIndex).padStart(6, '0')}.png`);
    await page.screenshot({ path: framePath });
    frameIndex++;

    if (frameIndex % fps === 0) process.stdout.write(`${frameIndex / fps}s `);

    await new Promise(r => setTimeout(r, frameInterval));
  }

  console.log(`\n  Total : ${frameIndex} frames`);
  await browser.close();

  // Assembler les frames en MP4 avec FFmpeg
  console.log('  Assemblage MP4...');
  execSync(
    `ffmpeg -y -framerate ${fps} -i "${path.join(frameDir, 'frame-%06d.png')}" -c:v libx264 -pix_fmt yuv420p "${mp4Path}"`,
    { stdio: 'inherit' }
  );

  // Nettoyage des frames temporaires
  fs.rmSync(frameDir, { recursive: true, force: true });

  console.log(`  ✅  output/mp4/${mp4Name}`);
}

(async () => {
  for (const htmlFile of htmlFiles) {
    await recordVideo(htmlFile);
  }
  console.log(`\n🏁  ${htmlFiles.length} vidéo(s) exportée(s) dans output/mp4/`);
})().catch(err => { console.error(err); process.exit(1); });
