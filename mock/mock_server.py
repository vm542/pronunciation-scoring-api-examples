"""Offline stand-in for the TonePerfect API, so the examples run without a key or network.

    python mock/mock_server.py            # http://localhost:8787
    export TONEPERFECT_BASE_URL=http://localhost:8787 TONEPERFECT_API_KEY=tp_test_mock

It answers like the real API's test keys: one fixed result per language (the files in
mock/fixtures/ are real engine responses to synthetic speech, captured 2026-10-28), the
documented 4xx errors for bad input, and TonePerfect-Test-Outcome rehearsals. It does NOT
listen to your audio. Standard library only.
"""
import json
import os
import re
import sys
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
LOCALES = ["zh-CN", "en-US", "fr-FR", "es-419", "de-DE", "it-IT", "pt-BR", "ru-RU", "ko-KR", "ja-JP"]
HAN = re.compile(r"[㐀-鿿]")
ERRORS = json.load(open(os.path.join(FIXTURES, "errors.json"), encoding="utf-8"))
seen = {}  # Idempotency-Key -> (fields, response)


def fixture(locale, text):
    path = os.path.join(FIXTURES, locale + ".json")
    if os.path.exists(path):
        body = json.load(open(path, encoding="utf-8"))
    else:  # generic result for languages without a captured fixture
        words = [w for w in re.split(r"\s+", text) if w] if locale != "ja-JP" else [text]
        body = {
            "id": "req_mock_generic", "status": "completed", "assessable": True, "reason": None,
            "language": locale.split("-")[0], "locale": locale, "task": "general",
            "model_version": f"mock-{locale}", "engine_route": {"engine": "primary", "fallback": False},
            "scores": {"overall": 84.0, "pronunciation": 83.0, "integrity": 100.0, "fluency": None, "rhythm": None, "tone": None},
            "words": [{"index": i, "word": w.strip(".,!?¿¡。、"), "expected_ipa": "", "score": 80.0 + i, "start_ms": 200 + 400 * i,
                       "end_ms": 560 + 400 * i, "decision": "no_correction", "omission_suspected": False, "phonemes": []}
                      for i, w in enumerate(words)],
            "warnings": [], "billing": {"credits": 1, "source": "free", "balance_credits": 0, "free_credits": 49},
        }
    body["test"] = True
    return body


DECISIONS = {"review", "uncertain", "no_correction", "content_mismatch_suspected"}


def compact(body):
    """The documented TonePerfect-Response: compact mapping (toneperfect.compact.v1)."""
    scores = body.get("scores") or {}
    zh = body.get("locale") == "zh-CN"
    words = []
    for w in body.get("words") or []:
        units = [{"dimension": u.get("dimension") or "phoneme", "expected": u.get("expected"), "heard": u.get("heard"),
                  "score": u.get("score"), "decision": u.get("decision") if u.get("decision") in DECISIONS else None}
                 for u in (w.get("phones") or w.get("phonemes") or [])]
        word = {"text": w.get("word") or w.get("text"), "score": w.get("score"), "start_ms": w.get("start_ms"),
                "end_ms": w.get("end_ms"), "decision": None if zh or w.get("decision") not in DECISIONS else w["decision"], "units": units}
        word["pinyin" if zh else "expected_ipa"] = w.get("pinyin") if zh else w.get("expected_ipa")
        words.append(word)
    return {"schema": "toneperfect.compact.v1", "id": body.get("id"), "assessable": body.get("assessable"),
            "reason": body.get("reason"), "locale": body.get("locale"), "task": body.get("task"),
            "model_version": body.get("model_version"), "engine_route": body.get("engine_route"),
            "scores": {k: scores.get(k) for k in ("overall", "pronunciation", "initial", "final", "tone", "fluency", "rhythm")}
            | {"completeness": scores.get("completeness", scores.get("integrity"))},
            "words": words, "warnings": body.get("warnings") or [], "billing": body.get("billing") or {}}


def error(status, code, message):
    return status, {"error": {"code": code, "message": message}}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stderr.write("mock: " + fmt % args + "\n")

    def send(self, status, body, extra=None):
        data = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.startswith("/v1/capabilities"):
            return self.send(200, {"model_version": "mock", "languages": [{"locale": l, "available": True, "status": "experimental"} for l in LOCALES]})
        self.send(*error(404, "not_found", "Unknown route."))

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length)
        if self.path.startswith("/v1/lint"):
            payload = json.loads(raw or b"{}")
            text, lang = payload.get("text", ""), payload.get("language", "zh-CN")
            issues = []
            if lang == "zh-CN" and not HAN.search(text):
                issues.append({"code": "no_reference", "message": "Provide Mandarin characters (汉字).", "field": "text", "severity": "error"})
            elif re.search(r"\d", text):
                issues.append({"code": "digits", "message": "Digits are spelled out before scoring.", "field": "text", "severity": "warning"})
            return self.send(200, {"ok": not any(i["severity"] == "error" for i in issues), "language": lang, "issues": issues})
        if not self.path.startswith("/v1/assess"):
            return self.send(*error(404, "not_found", "Unknown route."))
        auth = self.headers.get("Authorization", "") or ("Bearer " + self.headers.get("X-Api-Key", ""))
        if not re.match(r"Bearer tp_(test|live)_\S+", auth):
            return self.send(*error(401, "invalid_api_key", "The key is missing, unknown or revoked."))
        idem = self.headers.get("Idempotency-Key", "")
        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", idem):
            return self.send(*error(422, "invalid_idempotency_key", "The Idempotency-Key header is missing or malformed."))
        message = BytesParser(policy=HTTP).parsebytes(b"Content-Type: " + self.headers.get("Content-Type", "").encode() + b"\r\n\r\n" + raw)
        if not message.is_multipart():
            return self.send(*error(400, "invalid_multipart", "The body is not readable multipart/form-data."))
        fields, audio = {}, None
        for part in message.iter_parts():
            name = part.get_param("name", header="content-disposition")
            if part.get_filename() is not None:
                audio = part.get_payload(decode=True)
            else:
                fields[name] = part.get_payload(decode=True).decode("utf-8")
        text, lang = fields.get("text", ""), fields.get("language", "zh-CN")
        if not audio:
            return self.send(*error(422, "missing_audio", "No file in the audio field."))
        if lang not in LOCALES:
            return self.send(*error(422, "unsupported_language", "The locale is not available."))
        if not text.strip():
            return self.send(*error(422, "invalid_reference", "No text or pinyin, or a field is too long."))
        if lang == "zh-CN" and not HAN.search(text):
            return self.send(*error(422, "invalid_assessment", "The engine could not assess this reference: Mandarin text needs Chinese characters."))
        outcome = self.headers.get("TonePerfect-Test-Outcome")
        if outcome:
            if outcome not in ERRORS:
                return self.send(*error(422, "invalid_test_outcome", "Unknown test outcome."))
            return self.send(ERRORS[outcome]["status"], ERRORS[outcome]["body"], {"Retry-After": "1"})
        key = (idem, lang, text, len(audio))
        if idem in seen and seen[idem][0] != key:
            return self.send(*error(409, "idempotency_conflict", "This Idempotency-Key was used with different audio or fields."))
        if idem not in seen:
            seen[idem] = (key, fixture(lang, text))
        result = seen[idem][1]
        if self.headers.get("TonePerfect-Response", "").lower() == "compact":
            result = compact(result)
        self.send(200, result, {"X-TonePerfect-Test": "true"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8787"))
    print(f"mock TonePerfect API on http://localhost:{port}")
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
