'use strict';

const fs   = require('fs');
const path = require('path');

const ROOT       = path.resolve(__dirname, '..');
const DATA_FILE  = path.join(ROOT, 'data', 'videos-data.json');
const TEMPLATE   = path.join(ROOT, 'engine', 'template.html');
const OUTPUT_DIR = path.join(ROOT, 'output', 'html');
const ENGINE_DIR = path.join(ROOT, 'engine');

// ── Helpers ──────────────────────────────────────────────────────────────────

function toFileUrl(relativePath) {
  if (!relativePath || relativePath.startsWith('http')) return relativePath;
  return 'file:///' + path.resolve(ROOT, relativePath).replace(/\\/g, '/');
}

function resolveSettings(s) {
  return {
    ...s,
    site: {
      ...s.site,
      logo:      toFileUrl(s.site.logo),
      watermark: toFileUrl(s.site.watermark),
    },
    sounds: Object.fromEntries(
      Object.entries(s.sounds).map(([k, v]) => [k, typeof v === 'string' ? toFileUrl(v) : v])
    ),
  };
}

function resolveVideo(v) {
  return {
    ...v,
    question:   { ...v.question,   media: toFileUrl(v.question.media),   audio: toFileUrl(v.question.audio) },
    explication: { ...v.explication, media: toFileUrl(v.explication.media), audio: toFileUrl(v.explication.audio) },
  };
}

function slugify(str) {
  return str.toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
}

// ── Main ─────────────────────────────────────────────────────────────────────

const { settings, videos } = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
const templateHtml = fs.readFileSync(TEMPLATE, 'utf8');

if (!fs.existsSync(OUTPUT_DIR)) fs.mkdirSync(OUTPUT_DIR, { recursive: true });

const engineCss = 'file:///' + path.join(ENGINE_DIR, 'style.css').replace(/\\/g, '/');
const engineJs  = 'file:///' + path.join(ENGINE_DIR, 'script.js').replace(/\\/g, '/');
const resolvedSettings = resolveSettings(settings);

// Filtrer par --id si fourni
const idArg = process.argv.indexOf('--id');
const targetId = idArg !== -1 ? parseInt(process.argv[idArg + 1]) : null;
const targets = targetId ? videos.filter(v => v.id === targetId) : videos;

if (targets.length === 0) {
  console.error(`Aucune vidéo trouvée${targetId ? ` avec id=${targetId}` : ''}.`);
  process.exit(1);
}

targets.forEach(video => {
  const videoData = {
    settings: resolvedSettings,
    video: resolveVideo(video),
  };

  const slug = slugify(video.sujet);
  const filename = `video-${video.id}-${slug}.html`;
  const outputPath = path.join(OUTPUT_DIR, filename);

  const html = templateHtml
    .replace('href="style.css"',   `href="${engineCss}"`)
    .replace('<script src="script.js"></script>', '')
    .replace('</body>',
      `<script>window.__VIDEO_DATA = ${JSON.stringify(videoData)};</script>\n` +
      `<script src="${engineJs}"></script>\n</body>`
    );

  fs.writeFileSync(outputPath, html, 'utf8');
  console.log(`✅  output/html/${filename}`);
});

console.log(`\n🎬  ${targets.length} vidéo(s) générée(s) dans output/html/`);
console.log(`\nCommandes utiles :`);
console.log(`  node scripts/generate-all.js           → toutes les vidéos`);
console.log(`  node scripts/generate-all.js --id 2   → vidéo 2 uniquement`);
console.log(`  node scripts/record-video.js           → exporter en MP4 (Puppeteer)`);
