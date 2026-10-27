// Mandarin: initial, final and tone of each syllable, expected vs heard, with the engine's decision.
//   node mandarin-tones.mjs ../samples/zh-CN.ogg 我想买书
import { assess, wordUnits } from './client.mjs';

const [path, text] = process.argv.slice(2);
if (!text) { console.error('usage: node mandarin-tones.mjs <audio> <characters>'); process.exit(1); }
const result = await assess(path, text, 'zh-CN');
if (!result.assessable) { console.log('Not assessable:', result.reason); process.exit(0); }
const s = result.scores;
console.log(`Overall ${Math.round(s.overall)} · initials ${Math.round(s.initial)} · finals ${Math.round(s.final)} · tones ${Math.round(s.tone)}`);
for (const word of result.words) {
  console.log(`${word.word} (${word.pinyin})  score ${Math.round(word.score)}`);
  for (const u of wordUnits(word)) {
    const fmt = v => (u.dimension === 'tone' ? `tone ${v}` : String(v));
    const note = u.decision === 'review' ? '  <- fix this' : String(u.expected) !== String(u.heard) ? '  (heard differently, not flagged)' : '';
    // Heard estimates are evidence; only "review" asks for a correction (tone sandhi is a common reason).
    console.log(`    ${u.dimension.padEnd(8)} expected ${fmt(u.expected).padEnd(8)} heard ${fmt(u.heard).padEnd(8)} ${u.score}${note}`);
  }
}
