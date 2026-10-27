// Check text first (free /v1/lint), then handle 422 and transient errors.
// With a tp_test_ key it also rehearses error responses via TonePerfect-Test-Outcome.
import { ApiError, assess, lint } from './client.mjs';

const sample = f => new URL(`../samples/${f}`, import.meta.url).pathname;

async function tryAssess(path, text, language, options) {
  try {
    const result = await assess(path, text, language, options);
    console.log('  ok, overall', result.scores.overall);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    if (error.status === 422) console.log(`  422 ${error.code}: ${error.message.split(': ').slice(1).join(': ')}`); // fix the input; not charged
    else if (error.status === 402) console.log(`  402 ${error.code}: out of credits or no plan`);
    else if (error.status === 401) console.log('  401: the API key is missing, unknown or revoked');
    else console.log(`  ${error.status} ${error.code}: gave up after retries`);
  }
}

console.log('1. Lint a Mandarin text with digits:');
for (const i of (await lint('我有3个苹果', 'zh-CN')).issues) console.log(`  ${i.severity}: ${i.code}`);
console.log('2. Lint pinyin without characters:');
console.log('  ok =', (await lint('ni3 hao3', 'zh-CN')).ok);
console.log('3. Unsupported locale -> 422:');
await tryAssess(sample('en-US.ogg'), 'Hello', 'xx-XX');
console.log('4. Mandarin with pinyin only -> 422:');
await tryAssess(sample('zh-CN.ogg'), 'ni3 hao3', 'zh-CN');
if ((process.env.TONEPERFECT_API_KEY || '').startsWith('tp_test_')) {
  for (const outcome of ['invalid_assessment', 'insufficient_credits', 'engine_unavailable']) {
    console.log(`5. Rehearse ${outcome}:`);
    await tryAssess(sample('zh-CN.ogg'), '我想买书', 'zh-CN', { testOutcome: outcome, attempts: 2 });
  }
}
