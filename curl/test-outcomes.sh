#!/bin/sh
# Rehearse error responses with a tp_test_ key (never charged).   ./test-outcomes.sh
set -eu
BASE=${TONEPERFECT_BASE_URL:-https://api.toneperfect.app}
for outcome in invalid_assessment insufficient_credits subscription_required engine_unavailable account_busy rate_limit; do
  printf '%s -> ' "$outcome"
  curl -sS -o /dev/null -w '%{http_code}\n' "$BASE/v1/assess" \
    -H "Authorization: Bearer $TONEPERFECT_API_KEY" \
    -H "Idempotency-Key: $(uuidgen 2>/dev/null || cat /proc/sys/kernel/random/uuid)" \
    -H "TonePerfect-Test-Outcome: $outcome" \
    -F "audio=@$(dirname "$0")/../samples/zh-CN.ogg" -F "text=我想买书" -F "language=zh-CN"
done
