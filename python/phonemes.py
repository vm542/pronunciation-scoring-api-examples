"""Show expected vs heard sounds for each word (all languages except Mandarin; see mandarin_tones.py).

    python phonemes.py ../samples/en-US.ogg "I like sunny days." en-US
"""
import sys

from client import assess, word_units


def main(path, text, language):
    result = assess(path, text, language)
    if not result.get("assessable"):
        sys.exit(f"Not assessable: {result.get('reason')}")
    for word in result["words"]:
        print(f"{word.get('word')}  /{word.get('expected_ipa', '')}/  score {word.get('score')}  decision {word.get('decision')}")
        for unit in word_units(word):
            expected, heard = unit.get("expected"), unit.get("heard")
            mark = "" if heard == expected else ("  (missing)" if heard is None else "  (heard differently)")
            print(f"    {expected:>4} -> {heard or '—':<4} {unit.get('score')}{mark}")
    # Phoneme rows are experimental evidence; act on the word-level decision.


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    main(*sys.argv[1:])
