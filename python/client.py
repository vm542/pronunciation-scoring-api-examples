"""Minimal TonePerfect API client used by the examples (only dependency: requests).

Environment:
  TONEPERFECT_API_KEY   your key: tp_test_... (free, fixed example result) or tp_live_...
  TONEPERFECT_BASE_URL  optional, defaults to https://api.toneperfect.app
"""
import os
import time
import uuid

import requests

BASE_URL = os.environ.get("TONEPERFECT_BASE_URL", "https://api.toneperfect.app").rstrip("/")

# Errors worth retrying with the SAME Idempotency-Key (you are never charged twice).
RETRYABLE = {408, 409, 429, 503, 504}
NOT_RETRYABLE_CODES = {"idempotency_conflict", "idempotency_expired", "free_capacity"}


class ApiError(Exception):
    def __init__(self, status, code, message, body=None):
        super().__init__(f"{status} {code}: {message}")
        self.status, self.code, self.message, self.body = status, code, message, body or {}

    @property
    def retryable(self):
        return self.status in RETRYABLE and self.code not in NOT_RETRYABLE_CODES


def api_key():
    key = os.environ.get("TONEPERFECT_API_KEY")
    if not key:
        raise SystemExit("Set TONEPERFECT_API_KEY (create a free test key at https://api.toneperfect.app/signup).")
    return key


def _raise_for(response):
    try:
        body = response.json()
    except ValueError:
        body = {}
    err = body.get("error") or {}
    raise ApiError(response.status_code, err.get("code", "http_%d" % response.status_code),
                   err.get("message", response.text[:200]), body)


def assess(audio_path, text, language, *, compact=False, test_outcome=None, attempts=4, timeout=60):
    """POST /v1/assess. Retries transient errors with the same Idempotency-Key."""
    idem = str(uuid.uuid4())  # one key per logical attempt; reused on retries
    headers = {"Authorization": "Bearer " + api_key(), "Idempotency-Key": idem}
    if compact:
        headers["TonePerfect-Response"] = "compact"
    if test_outcome:  # test keys only: rehearse an error path
        headers["TonePerfect-Test-Outcome"] = test_outcome
    for attempt in range(1, attempts + 1):
        with open(audio_path, "rb") as audio:
            response = requests.post(
                BASE_URL + "/v1/assess", headers=headers, timeout=timeout,
                files={"audio": (os.path.basename(audio_path), audio)},
                data={"text": text, "language": language},
            )
        if response.ok:
            return response.json()
        try:
            _raise_for(response)
        except ApiError as error:
            if not error.retryable or attempt == attempts:
                raise
            wait = float(response.headers.get("Retry-After") or 2 ** attempt)
            print(f"  {error.code}: retrying in {wait:.0f}s with the same Idempotency-Key")
            time.sleep(min(wait, 30))


def lint(text, language):
    """POST /v1/lint: free reference-text check, no key needed."""
    response = requests.post(BASE_URL + "/v1/lint", json={"text": text, "language": language}, timeout=20)
    if not response.ok:
        _raise_for(response)
    return response.json()


def capabilities():
    """GET /v1/capabilities: live language list, no key needed."""
    response = requests.get(BASE_URL + "/v1/capabilities", timeout=20)
    if not response.ok:
        _raise_for(response)
    return response.json()


def word_units(word):
    """Sound-level rows of a word. The full response uses phones[] or phonemes[]; compact uses units[]."""
    return word.get("units") or word.get("phones") or word.get("phonemes") or []


def needs_review(word):
    """A word (or one of its Mandarin initial/final/tone parts) the engine says to correct."""
    if word.get("decision") in ("review", "content_mismatch_suspected"):
        return True
    return any(u.get("decision") == "review" for u in word_units(word))
