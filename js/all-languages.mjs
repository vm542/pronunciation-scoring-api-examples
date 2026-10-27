// Score every sample in ../samples (10 languages). Synthetic robot speech: scores say little about learners.
import { readFile } from 'node:fs/promises';
import { ApiError, assess } from './client.mjs';

const dir = new URL('../samples/', import.meta.url);
const samples = JSON.parse(await readFile(new URL('samples.json', dir), 'utf8'));
for (const s of samples) {
  try {
    const r = await assess(new URL(s.file, dir).pathname, s.text, s.language);
    const words = (r.words || []).map(w => `${w.word}:${w.score == null ? '—' : Math.round(w.score)}`).join(' ');
    console.log(`${s.language.padEnd(7)} overall ${r.assessable ? Math.round(r.scores.overall) : '—'}  ${words}`);
  } catch (e) {
    if (!(e instanceof ApiError)) throw e;
    console.log(`${s.language.padEnd(7)} ${e.status} ${e.code}`);
  }
}
