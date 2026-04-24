/**
 * TestPermis.fr — Convertisseur HTML → MP4
 * Utilise Puppeteer pour enregistrer l'animation HTML en vidéo
 * 
 * Installation : npm install puppeteer
 * Usage : node record-video.js
 */

const puppeteer = require('puppeteer');
const path = require('path');

const CONFIG = {
  htmlFile: path.join(__dirname, 'video-panneau-stop.html'),
  outputFile: path.join(__dirname, 'output', 'panneau-stop.webm'),
  width: 1080,
  height: 1920,
  duration: 37000, // 37 secondes (durée totale de l'animation)
};

async function recordVideo() {
  console.log('🎬 Lancement du navigateur...');

  const browser = await puppeteer.launch({
    headless: 'new',
    args: [
      `--window-size=${CONFIG.width},${CONFIG.height}`,
      '--autoplay-policy=no-user-gesture-required',
    ],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: CONFIG.width, height: CONFIG.height });

  // Activer l'enregistrement vidéo via Chrome DevTools Protocol
  const client = await page.createCDPSession();

  // Créer le dossier output s'il n'existe pas
  const fs = require('fs');
  const outputDir = path.join(__dirname, 'output');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  console.log('📂 Chargement du fichier HTML...');
  await page.goto(`file:///${CONFIG.htmlFile.replace(/\\/g, '/')}`, {
    waitUntil: 'networkidle0',
  });

  // Méthode : Capture de screenshots séquentiels → assemblage avec FFmpeg
  console.log('📸 Capture des frames...');

  const framesDir = path.join(__dirname, 'output', 'frames');
  if (!fs.existsSync(framesDir)) {
    fs.mkdirSync(framesDir, { recursive: true });
  }

  const FPS = 30;
  const totalFrames = Math.ceil((CONFIG.duration / 1000) * FPS);

  for (let i = 0; i < totalFrames; i++) {
    const frameFile = path.join(framesDir, `frame_${String(i).padStart(5, '0')}.png`);
    await page.screenshot({ path: frameFile, type: 'png' });

    // Avancer le temps de l'animation
    await page.evaluate((ms) => {
      // On force un petit délai pour laisser les animations CSS avancer
    }, 1000 / FPS);

    await new Promise(resolve => setTimeout(resolve, 1000 / FPS));

    if (i % 30 === 0) {
      console.log(`  📸 Frame ${i}/${totalFrames} (${Math.round(i/totalFrames*100)}%)`);
    }
  }

  console.log('✅ Capture terminée !');
  await browser.close();

  console.log('');
  console.log('🎬 Pour assembler en MP4, lancez :');
  console.log(`ffmpeg -framerate 30 -i "${framesDir}/frame_%05d.png" -c:v libx264 -pix_fmt yuv420p -r 30 "${path.join(outputDir, 'panneau-stop.mp4')}"`);
  console.log('');
  console.log('🎵 Pour ajouter l\'audio (voix off GPT) :');
  console.log(`ffmpeg -i "${path.join(outputDir, 'panneau-stop.mp4')}" -i "voix-off.mp3" -c:v copy -c:a aac -shortest "${path.join(outputDir, 'panneau-stop-final.mp4')}"`);
}

recordVideo().catch(console.error);
