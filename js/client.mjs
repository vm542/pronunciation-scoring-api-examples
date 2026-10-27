// Minimal TonePerfect API client for Node 18+ (built-in fetch, FormData, Blob). Server-side only:
// never ship a tp_live_ key to a browser or app. Env: TONEPERFECT_API_KEY, optional TONEPERFECT_BASE_URL.
import { readFile } from 'node:fs/promises';
import { basename } from 'node:path';
import { randomUUID } from 'node:crypto';

export const BASE_URL = (process.env.TONEPERFECT_BASE_URL || 'https://api.toneperfect.app').replace(/\/$/, '');
const RETRYABLE = new Set([408, 409, 429, 503, 504]);
const NOT_RETRYABLE_CODES = new Set(['idempotency_conflict', 'idempotency_expired', 'free_capacity']);

export class ApiError extends Error {
  constructor(status, code, message, body) {
    super(`${status} ${code}: ${message}`);
    Object.assign(this, { status, code, body });
  }
  get retryable() { return RETRYABLE.has(this.status) && !NOT_RETRYABLE_CODES.has(this.code); }
}

function apiKey() {
  const key = process.env.TONEPERFECT_API_KEY;
  if (!key) { console.error('Set TONEPERFECT_API_KEY (free test key: https://api.toneperfect.app/signup).'); process.exit(1); }
  return key;
}

async function toError(response) {
  const body = await response.json().catch(() => ({}));
  return new ApiError(response.status, body.error?.code || `http_${response.status}`, body.error?.message || response.statusText, body);
}

/** POST /v1/assess. Retries transient errors with the same Idempotency-Key, so you pay at most once. */
export async function assess(audioPath, text, language, { compact = false, testOutcome, attempts = 4 } = {}) {
  const audio = new Blob([await readFile(audioPath)]);
  const headers = { Authorization: `Bearer ${apiKey()}`, 'Idempotency-Key': randomUUID() };
  if (compact) headers['TonePerfect-Response'] = 'compact';
  if (testOutcome) headers['TonePerfect-Test-Outcome'] = testOutcome; // test keys only
  for (let attempt = 1; ; attempt++) {
    const form = new FormData();
    form.set('audio', audio, basename(audioPath));
    form.set('text', text);
    form.set('language', language);
    const response = await fetch(`${BASE_URL}/v1/assess`, { method: 'POST', headers, body: form });
    if (response.ok) return response.json();
    const error = await toError(response);
    if (!error.retryable || attempt >= attempts) throw error;
    const wait = Number(response.headers.get('retry-after')) || 2 ** attempt;
    console.log(`  ${error.code}: retrying in ${wait}s with the same Idempotency-Key`);
    await new Promise(r => setTimeout(r, Math.min(wait, 30) * 1000));
  }
}

/** POST /v1/lint: free reference-text check, no key needed. */
export async function lint(text, language) {
  const response = await fetch(`${BASE_URL}/v1/lint`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ text, language }) });
  if (!response.ok) throw await toError(response);
  return response.json();
}

/** GET /v1/capabilities: live language list, no key needed. */
export async function capabilities() {
  const response = await fetch(`${BASE_URL}/v1/capabilities`);
  if (!response.ok) throw await toError(response);
  return response.json();
}

/** Sound-level rows: phones[] or phonemes[] in the full response, units[] in the compact one. */
export const wordUnits = word => word.units || word.phones || word.phonemes || [];

/** The engine says to correct this word (or one of its Mandarin initial/final/tone parts). */
export const needsReview = word =>
  ['review', 'content_mismatch_suspected'].includes(word.decision) || wordUnits(word).some(u => u.decision === 'review');
