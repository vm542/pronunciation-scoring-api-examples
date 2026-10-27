#!/bin/sh
# Live list of languages, dimensions and limits (free, no key).
curl -sS "${TONEPERFECT_BASE_URL:-https://api.toneperfect.app}/v1/capabilities"
echo
