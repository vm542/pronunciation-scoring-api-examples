"""Score every sample in ../samples (10 languages) and print one line each.

The samples are synthetic eSpeak NG speech: robot voices, so the scores say little
about real learners. Record yourself to see meaningful results.
"""
import json
import os

from client import ApiError, assess

SAMPLES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples")

for sample in json.load(open(os.path.join(SAMPLES, "samples.json"), encoding="utf-8")):
    try:
        result = assess(os.path.join(SAMPLES, sample["file"]), sample["text"], sample["language"])
        overall = result["scores"]["overall"] if result.get("assessable") else None
        words = " ".join(f"{w.get('word')}:{'—' if w.get('score') is None else round(w['score'])}" for w in result.get("words", []))
        print(f"{sample['language']:<7} overall {overall if overall is None else round(overall):>4}  {words}")
    except ApiError as error:
        print(f"{sample['language']:<7} {error.status} {error.code}: {error.message}")
