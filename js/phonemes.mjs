// Expected vs heard sounds per word (all languages except Mandarin; see mandarin-tones.mjs).
//   node phonemes.mjs ../samples/en-US.ogg "I like sunny days." en-US
import { assess, wordUnits } from './client.mjs';

const [path, text, language] = process.argv.slice(2);
if (!language) { console.error('usage: node phonemes.mjs <audio> <text> <locale>'); process.exit(1); }
const result = await assess(path, text, language);
if (!result.assessable) { console.log('Not assessable:', result.reason); process.exit(0); }
for (const word of result.words) {
  console.log(`${word.word}  /${word.expected_ipa ?? ''}/  score ${word.score}  decision ${word.decision}`);
  for (const u of wordUnits(word)) {
    const note = u.heard === u.expected ? '' : u.heard == null ? '  (missing)' : '  (heard differently)';
    console.log(`    ${String(u.expected).padStart(4)} -> ${String(u.heard ?? '—').padEnd(4)} ${u.score}${note}`);
  }
}
// Phoneme rows are experimental evidence; act on the word-level decision.
