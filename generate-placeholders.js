// Génère des fichiers MP3 silencieux comme placeholders
// Les fichiers seront des WAV minimaux (compatibles navigateur)
const fs = require('fs');
const path = require('path');

const soundsDir = path.join(__dirname, 'assets', 'sounds');

// Minimal WAV header (silence) - renommé en .mp3 pour compatibilité chemin
// En vrai il faudra remplacer par de vrais MP3
function createSilentWav(duration = 1) {
  const sampleRate = 44100;
  const numSamples = sampleRate * duration;
  const dataSize = numSamples * 2; // 16-bit mono
  const buffer = Buffer.alloc(44 + dataSize);
  
  // RIFF header
  buffer.write('RIFF', 0);
  buffer.writeUInt32LE(36 + dataSize, 4);
  buffer.write('WAVE', 8);
  
  // fmt chunk
  buffer.write('fmt ', 12);
  buffer.writeUInt32LE(16, 16);       // chunk size
  buffer.writeUInt16LE(1, 20);        // PCM
  buffer.writeUInt16LE(1, 22);        // mono
  buffer.writeUInt32LE(sampleRate, 24);
  buffer.writeUInt32LE(sampleRate * 2, 28); // byte rate
  buffer.writeUInt16LE(2, 32);        // block align
  buffer.writeUInt16LE(16, 34);       // bits per sample
  
  // data chunk
  buffer.write('data', 36);
  buffer.writeUInt32LE(dataSize, 40);
  // rest is silence (zeros)
  
  return buffer;
}

const files = [
  { name: 'intro.mp3',    duration: 3,  desc: 'Jingle intro' },
  { name: 'tick.mp3',     duration: 1,  desc: 'Tick countdown' },
  { name: 'correct.mp3',  duration: 2,  desc: 'Son correct' },
  { name: 'wrong.mp3',    duration: 2,  desc: 'Son faux' },
  { name: 'outro.mp3',    duration: 3,  desc: 'Jingle outro' },
  { name: 'bg-music.mp3', duration: 30, desc: 'Musique de fond' },
];

files.forEach(f => {
  const filePath = path.join(soundsDir, f.name);
  fs.writeFileSync(filePath, createSilentWav(f.duration));
  console.log(`  ✅ sounds/${f.name} (${f.duration}s) — ${f.desc}`);
});

// ── Audio voiceover par question (question + explication) ──
const audioDir = path.join(__dirname, 'assets', 'audio');
if (!fs.existsSync(audioDir)) fs.mkdirSync(audioDir, { recursive: true });

const audioFiles = [
  { name: 'q1-question.mp3',     duration: 5,  desc: 'Voix Q1: "Au panneau STOP, je peux ralentir sans m\'arrêter"' },
  { name: 'q1-explication.mp3',  duration: 13, desc: 'Voix explication Q1: Arrêt obligatoire au STOP' },
  { name: 'q2-question.mp3',     duration: 4,  desc: 'Voix Q2: "Les angles morts n\'existent pas en moto"' },
  { name: 'q2-explication.mp3',  duration: 14, desc: 'Voix explication Q2: Angles morts moto' },
  { name: 'q3-question.mp3',     duration: 5,  desc: 'Voix Q3: "La priorité à droite s\'applique toujours"' },
  { name: 'q3-explication.mp3',  duration: 14, desc: 'Voix explication Q3: Priorité à droite' },
  { name: 'q4-question.mp3',     duration: 4,  desc: 'Voix Q4: "Le casque est obligatoire uniquement sur autoroute"' },
  { name: 'q4-explication.mp3',  duration: 13, desc: 'Voix explication Q4: Casque obligatoire' },
  { name: 'q5-question.mp3',     duration: 5,  desc: 'Voix Q5: "À 50 km/h la distance de freinage est de 5m"' },
  { name: 'q5-explication.mp3',  duration: 14, desc: 'Voix explication Q5: Distance de freinage' },
];

console.log('');
audioFiles.forEach(f => {
  const filePath = path.join(audioDir, f.name);
  fs.writeFileSync(filePath, createSilentWav(f.duration));
  console.log(`  ✅ audio/${f.name} (${f.duration}s) — ${f.desc}`);
});

console.log('\n🔊 Tous les fichiers audio placeholder créés !');
console.log('');
console.log('💡 Pour générer les voix-off avec GPT TTS :');
console.log('   curl https://api.openai.com/v1/audio/speech \\');
console.log('     -H "Authorization: Bearer $OPENAI_API_KEY" \\');
console.log('     -H "Content-Type: application/json" \\');
console.log('     -d \'{"model":"tts-1","input":"Votre texte ici","voice":"nova"}\'');
console.log('     --output assets/audio/q1-question.mp3');
console.log('');
console.log('💡 Sons/musique gratuits :');
console.log('   - https://pixabay.com/sound-effects/');
console.log('   - https://mixkit.co/free-sound-effects/');
