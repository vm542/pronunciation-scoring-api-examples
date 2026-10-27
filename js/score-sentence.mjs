// Score a sentence (or one word) in any of the 10 languages.
//   node score-sentence.mjs ../samples/es-419.ogg "Buenos días, ¿cómo estás?" es-419
import { assess, needsReview } from './client.mjs';

const [path, text, language] = process.argv.slice(2);
if (!language) { console.error('usage: node score-sentence.mjs <audio> <text> <locale>'); process.exit(1); }

const result = await assess(path, text, language);
if (!result.assessable) {
  console.log(`Could not assess this take (${result.reason}). Ask for another recording; nothing was charged.`);
} else {
  const s = result.scores;
  console.log(`Overall ${Math.round(s.overall)}/100 · pronunciation ${Math.round(s.pronunciation ?? 0)}${s.integrity != null ? ` · completeness ${Math.round(s.integrity)}` : ''}`);
  for (const word of result.words) {
    console.log(`  ${(word.word ?? word.text).padEnd(14)} ${word.score == null ? '—' : String(Math.round(word.score)).padStart(3)}${needsReview(word) ? '  <- review' : ''}`);
  }
  console.log(`credits charged: ${result.billing?.credits} · model ${result.model_version}`);
}
