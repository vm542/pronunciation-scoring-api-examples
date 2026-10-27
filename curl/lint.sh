#!/bin/sh
# Check a reference text before recording (free, no key).   ./lint.sh "我有3个苹果" zh-CN
set -eu
BASE=${TONEPERFECT_BASE_URL:-https://api.toneperfect.app}
curl -sS "$BASE/v1/lint" -H "Content-Type: application/json" \
  -d "{\"text\": \"$1\", \"language\": \"$2\"}"
echo
