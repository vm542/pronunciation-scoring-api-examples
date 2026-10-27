#!/bin/sh
# Score a recording.   ./assess.sh ../samples/de-DE.ogg "Guten Morgen, wie geht es dir?" de-DE
# Needs TONEPERFECT_API_KEY. Add -H "TonePerfect-Response: compact" for the stable compact schema.
set -eu
BASE=${TONEPERFECT_BASE_URL:-https://api.toneperfect.app}
curl -sS "$BASE/v1/assess" \
  -H "Authorization: Bearer $TONEPERFECT_API_KEY" \
  -H "Idempotency-Key: $(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)" \
  -F "audio=@$1" \
  -F "text=$2" \
  -F "language=$3"
echo
