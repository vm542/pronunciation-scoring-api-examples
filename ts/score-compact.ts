// Typed example using the stable compact schema. Run with: npx tsx score-compact.ts ../samples/fr-FR.ogg "Je voudrais un café." fr-FR
import { readFile } from 'node:fs/promises';
import { basename } from 'node:path';
import { randomUUID } from 'node:crypto';
import type { ApiErrorBody, CompactResult } from './types.js';

const BASE_URL = process.env.TONEPERFECT_BASE_URL ?? 'https://api.toneperfect.app';

export async function assessCompact(audioPath: string, text: string, language: string): Promise<CompactResult> {
  const form = new FormData();
  form.set('audio', new Blob([await readFile(audioPath)]), basename(audioPath));
  form.set('text', text);
  form.set('language', language);
  const response = await fetch(`${BASE_URL}/v1/assess`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${process.env.TONEPERFECT_API_KEY}`,
      'Idempotency-Key': randomUUID(),
      'TonePerfect-Response': 'compact',
    },
    body: form,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as ApiErrorBody | null;
    throw new Error(`${response.status} ${body?.error.code ?? ''}: ${body?.error.message ?? response.statusText}`);
  }
  return (await response.json()) as CompactResult;
}

const [path, text, language] = process.argv.slice(2);
if (path && text && language) {
  const r = await assessCompact(path, text, language);
  console.log(`${r.locale}: overall ${r.scores.overall}`);
  for (const w of r.words) {
    const off = w.units.filter(u => u.heard !== u.expected).map(u => `${u.expected}->${u.heard ?? '∅'}`);
    console.log(`  ${w.text} ${w.score ?? '—'} ${w.decision ?? ''} ${off.join(' ')}`);
  }
}
