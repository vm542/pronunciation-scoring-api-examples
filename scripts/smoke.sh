#!/bin/sh
# Runs every example against the offline mock (no key, no network). Needs python3 + requests and Node 18+.
set -eu
cd "$(dirname "$0")/.."
PORT=${PORT:-8787}
PORT=$PORT python3 mock/mock_server.py 2>/dev/null &
MOCK=$!
trap 'kill $MOCK' EXIT
sleep 1
export TONEPERFECT_BASE_URL=http://localhost:$PORT TONEPERFECT_API_KEY=tp_test_mock
(cd python
 python3 score_sentence.py ../samples/it-IT.ogg "Buongiorno, come stai?" it-IT
 python3 phonemes.py ../samples/en-US.ogg "I like sunny days." en-US
 python3 mandarin_tones.py ../samples/zh-CN.ogg 你好世界
 python3 errors.py
 python3 all_languages.py)
(cd js
 node score-sentence.mjs ../samples/pt-BR.ogg "Obrigado pela ajuda." pt-BR
 node phonemes.mjs ../samples/en-US.ogg "I like sunny days." en-US
 node mandarin-tones.mjs ../samples/zh-CN.ogg 你好世界
 node errors.mjs
 node all-languages.mjs)
for s in curl/capabilities.sh; do sh $s >/dev/null && echo "curl capabilities ok"; done
sh curl/assess.sh samples/ru-RU.ogg "Спасибо за помощь." ru-RU | head -c 120; echo
sh curl/test-outcomes.sh
echo "smoke: all examples ran"
