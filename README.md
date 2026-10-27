# Pronunciation scoring API examples

Copy-paste examples for the [TonePerfect pronunciation assessment API](https://api.toneperfect.app/):
send a recording and the text the speaker read, get back a 0–100 score for the sentence and every word,
plus what was expected and what was heard, sound by sound. Mandarin is scored per syllable as
**initial, final and tone**.

Python, JavaScript (Node 18+), TypeScript and curl. Ten languages:

| Locale | Language | Sample | Sound-level detail |
| --- | --- | --- | --- |
| `zh-CN` | Mandarin Chinese | 我想买书 | initial · final · tone |
| `en-US` | English (US) | I like sunny days. | phonemes |
| `es-419` | Spanish (Latin America) | Buenos días, ¿cómo estás? | phonemes |
| `fr-FR` | French | Je voudrais un café. | phonemes |
| `de-DE` | German | Guten Morgen, wie geht es dir? | phonemes |
| `it-IT` | Italian | Buongiorno, come stai? | phonemes |
| `pt-BR` | Portuguese (Brazil) | Obrigado pela ajuda. | phonemes |
| `ru-RU` | Russian | Спасибо за помощь. | phonemes |
| `ko-KR` | Korean | 커피 한 잔 주세요. | phonemes |
| `ja-JP` | Japanese | ありがとうございます。 | phonemes |

Every pack is labelled *experimental*; each language page on the site
([Italian](https://api.toneperfect.app/languages/italian/), [Mandarin](https://api.toneperfect.app/languages/mandarin-chinese/), …)
says what it scores and where its limits are. Call `GET /v1/capabilities` for the live list.

## 1. Get a key

Create an account at [api.toneperfect.app/signup](https://api.toneperfect.app/signup). Every account gets
**50 free credits** (one credit per started 15 s of audio). In the dashboard you can also create a
**test key** (`tp_test_…`): it runs the whole request path but returns a fixed example result, is never
charged, and can rehearse errors. Use it while you wire things up.

```sh
cp .env.example .env        # then put your key in .env
export $(grep -v '^#' .env | xargs)
```

Keep `tp_live_` keys on your server. Never put one in a browser bundle, a mobile app or a public repo.

## 2. Run an example

```sh
# curl
./curl/assess.sh samples/de-DE.ogg "Guten Morgen, wie geht es dir?" de-DE

# Python 3.9+
cd python && pip install -r requirements.txt
python score_sentence.py ../samples/es-419.ogg "Buenos días, ¿cómo estás?" es-419
python phonemes.py ../samples/en-US.ogg "I like sunny days." en-US
python mandarin_tones.py ../samples/zh-CN.ogg 我想买书
python errors.py
python all_languages.py

# Node 18+ (no dependencies)
cd js
node score-sentence.mjs ../samples/pt-BR.ogg "Obrigado pela ajuda." pt-BR
node mandarin-tones.mjs ../samples/zh-CN.ogg 我想买书
node errors.mjs

# TypeScript, stable compact schema
cd ts && npm install && npx tsx score-compact.ts ../samples/fr-FR.ogg "Je voudrais un café." fr-FR
```

| Example | What it shows |
| --- | --- |
| `score_sentence` | Sentence and word scores, words flagged for review, unassessable takes (HTTP 200, `assessable: false`, not charged) |
| `phonemes` | Expected vs heard phoneme rows under each word (`phones[]`/`phonemes[]`) |
| `mandarin_tones` | Initial, final and tone per syllable: expected, heard, score and `decision` |
| `errors` | Free `/v1/lint` text check, 422 handling, 401/402, retries that reuse the `Idempotency-Key` |
| `all_languages` | One request per sample in all ten languages |
| `ts/score-compact.ts` | Typed client for `TonePerfect-Response: compact` (`toneperfect.compact.v1`) |

The samples in `samples/` are **synthetic eSpeak NG speech** (no person's voice; regenerate with
`samples/make-samples.sh`). A robot voice is not a learner, so its scores mean little. Record yourself:
any WAV, MP3, M4A, Ogg or WebM between 0.15 and 30 seconds works.

## 3. Read the result

```jsonc
{
  "assessable": true,
  "scores": { "overall": 78.4, "pronunciation": 86.1, "initial": 49.4, "final": 76.1, "tone": 79.4 },
  "words": [
    { "word": "世", "pinyin": "shi4", "score": 88.3,
      "phones": [ { "dimension": "initial", "expected": "sh", "heard": "ch", "score": 12.6, "decision": "no_correction" }, … ] }
  ],
  "billing": { "credits": 1 }
}
```

- **Act on decisions, not on every mismatch.** A word (Mandarin: an initial, final or tone) with
  `decision: "review"` is what to correct. Heard values are acoustic estimates; a different heard tone can be
  right in context (tone sandhi). Outside Mandarin the decision sits on the word and phoneme rows are evidence.
- **`assessable: false`** (HTTP 200) means nothing could be scored: ask for another take. It is not charged.
- **Wrong sentence.** Outside Mandarin a recording of different words is not always refused. Check
  `warnings`, `scores.integrity` and the word scores if your app needs to catch it.
- Field reference: [docs → response structure](https://api.toneperfect.app/docs#response).

## 4. Errors

| Status | Typical code | What to do |
| --- | --- | --- |
| 401 | `invalid_api_key` | Check the key. |
| 402 | `subscription_required`, `insufficient_credits` | Free credits used up or plan balance too low. |
| 422 | `invalid_assessment`, `invalid_reference`, `unsupported_language`, `invalid_audio` | Fix the input; nothing was charged. Run `/v1/lint` on lesson text when you author it. |
| 408, 409 `request_pending`, 429, 503, 504 | `rate_limit`, `account_busy`, `engine_unavailable`, … | Retry with the **same** `Idempotency-Key` (honour `Retry-After`). You are charged at most once. |

Full list: [docs → errors](https://api.toneperfect.app/docs#errors). With a test key, send
`TonePerfect-Test-Outcome: insufficient_credits` (or `invalid_assessment`, `engine_unavailable`, `rate_limit`, …)
to rehearse each path; `curl/test-outcomes.sh` runs them all.

## Run offline

`mock/mock_server.py` (standard library only) imitates the API with fixed results (real engine output for
synthetic speech, captured October 2026) and the documented errors. It does not listen to your audio.

```sh
python3 mock/mock_server.py &
TONEPERFECT_BASE_URL=http://localhost:8787 TONEPERFECT_API_KEY=tp_test_mock python3 python/score_sentence.py samples/it-IT.ogg "Buongiorno, come stai?" it-IT
./scripts/smoke.sh   # runs every example against the mock
```

## Links

- API site and live demo: https://api.toneperfect.app/
- Docs: https://api.toneperfect.app/docs · Quickstart: https://api.toneperfect.app/quickstart/
- Pricing (from $10/month, 50 free credits): https://api.toneperfect.app/pricing/
- Questions: nik@toneperfect.app

MIT licensed. The examples are independent of any SDK so you can copy them into your own code.
