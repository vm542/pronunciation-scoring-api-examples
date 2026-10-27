"""Error handling: check text first (free /v1/lint), then handle 422 and transient errors.

    python errors.py
With a tp_test_ key the script also rehearses error responses via TonePerfect-Test-Outcome.
"""
import os
import sys

from client import ApiError, assess, lint

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


def check_text(text, language):
    report = lint(text, language)
    for issue in report.get("issues", []):
        print(f"  lint {issue['severity']}: {issue['code']} - {issue['message']}")
    return report.get("ok", False)


def try_assess(path, text, language, **kw):
    try:
        result = assess(path, text, language, **kw)
        print("  ok, overall", result["scores"]["overall"])
    except ApiError as error:
        if error.status == 422:
            # Bad input: fix the request, do not retry as-is. Nothing was charged.
            print(f"  422 {error.code}: {error.message}")
        elif error.status == 402:
            print(f"  402 {error.code}: out of credits or no plan - show an upgrade message, keep the take")
        elif error.status == 401:
            print("  401: the API key is missing, unknown or revoked")
        else:
            print(f"  {error.status} {error.code}: gave up after retries ({error.message})")


def main():
    print("1. Lint a Mandarin text with digits (warning, still accepted):")
    check_text("我有3个苹果", "zh-CN")
    print("2. Lint pinyin without characters (refused before you spend a credit):")
    print("  ok =", check_text("ni3 hao3", "zh-CN"))
    print("3. Assess with an unsupported locale -> 422 unsupported_language:")
    try_assess(os.path.join(SAMPLES, "en-US.ogg"), "Hello", "xx-XX")
    print("4. Assess Mandarin with pinyin only -> 422:")
    try_assess(os.path.join(SAMPLES, "zh-CN.ogg"), "ni3 hao3", "zh-CN")
    if os.environ.get("TONEPERFECT_API_KEY", "").startswith("tp_test_"):
        for outcome in ("invalid_assessment", "insufficient_credits", "engine_unavailable"):
            print(f"5. Rehearse {outcome} with the test key:")
            try_assess(os.path.join(SAMPLES, "zh-CN.ogg"), "我想买书", "zh-CN", test_outcome=outcome, attempts=2)


if __name__ == "__main__":
    sys.exit(main())
