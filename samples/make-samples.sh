#!/bin/sh
# Regenerates the synthetic sample recordings in this folder with eSpeak NG + ffmpeg.
# The audio is machine-generated (no person's voice). Robot speech is NOT a good
# learner: expect odd scores. Record yourself for meaningful results.
set -eu
cd "$(dirname "$0")"
tmp=$(mktemp -d)
python3 - <<'PY' > "$tmp/list.tsv"
import json
for s in json.load(open("samples.json")):
    print("\t".join([s["file"], s["voice"], s["text"]]))
PY
while IFS="$(printf '\t')" read -r file voice text; do
  espeak-ng -v "$voice" -s 140 -w "$tmp/x.wav" "$text"
  ffmpeg -hide_banner -loglevel error -y -i "$tmp/x.wav" -ac 1 -ar 16000 -c:a libopus -b:a 24k "$file"
done < "$tmp/list.tsv"
rm -rf "$tmp"
espeak-ng --version
