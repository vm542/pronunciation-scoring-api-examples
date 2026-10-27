"""Score a recording of a sentence (or a single word) in any of the 10 languages.

    python score_sentence.py ../samples/es-419.ogg "Buenos días, ¿cómo estás?" es-419
"""
import sys

from client import assess, needs_review


def main(path, text, language):
    result = assess(path, text, language)
    if not result.get("assessable"):
        # HTTP 200 but nothing could be scored (silence, noise, wrong language...). Not charged.
        print(f"Could not assess this take: {result.get('reason')}. Ask the learner to record again.")
        return
    scores = result["scores"]
    print(f"Overall {scores['overall']:.0f}/100 · pronunciation {scores.get('pronunciation') or 0:.0f}"
          + (f" · completeness {scores['integrity']:.0f}" if scores.get("integrity") is not None else ""))
    for word in result["words"]:
        label = word.get("word") or word.get("text")
        score = "—" if word.get("score") is None else f"{word['score']:.0f}"
        flag = "  <- review" if needs_review(word) else ""
        print(f"  {label:<14} {score:>4}{flag}")
    for warning in result.get("warnings") or []:
        print("warning:", warning.get("code") if isinstance(warning, dict) else warning)
    print(f"credits charged: {result.get('billing', {}).get('credits')} · model {result.get('model_version')}")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
