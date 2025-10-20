#!/bin/bash
set -o errexit
set -o pipefail
set -o nounset

exec daphne \
    --bind 0.0.0.0 \
    --port 8001 \
    --access-log - \
    --proxy-headers \
    --verbosity 2 \
    core.asgi:application