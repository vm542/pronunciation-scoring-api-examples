"""Mandarin: initial, final and tone of every syllable, expected vs heard, with the engine's decision.

    python mandarin_tones.py ../samples/zh-CN.ogg 我想买书
"""
import sys

from client import assess, word_units


def main(path, text):
    result = assess(path, text, "zh-CN")
    if not result.get("assessable"):
        sys.exit(f"Not assessable: {result.get('reason')}")
    s = result["scores"]
    print(f"Overall {s['overall']:.0f} · initials {s['initial']:.0f} · finals {s['final']:.0f} · tones {s['tone']:.0f}")
    for word in result["words"]:
        print(f"{word['word']} ({word.get('pinyin')})  score {word['score']:.0f}")
        for unit in word_units(word):
            part = unit.get("dimension")
            expected, heard = unit.get("expected"), unit.get("heard")
            if part == "tone":
                expected, heard = f"tone {expected}", f"tone {heard}"
            note = ""
            if unit.get("decision") == "review":
                note = "  <- fix this"
            elif str(expected) != str(heard):
                # Heard estimates are evidence; only "review" asks for a correction (tone sandhi is a common reason).
                note = "  (heard differently, not flagged)"
            print(f"    {part:<8} expected {expected:<8} heard {heard:<8} {unit.get('score'):>5}{note}")
    # Advice text per component is in result["syllables"][i]["components"][part]["advice"].


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(*sys.argv[1:])
