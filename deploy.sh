#!/bin/bash
# Token stored in ~/.butterfly-effect-env (not committed)
# Format: export CLOUDFLARE_API_TOKEN=cfut_...
source ~/.butterfly-effect-env 2>/dev/null

CLOUDFLARE_ACCOUNT_ID=7a9ccd036a8d7855cc8c2edff6bffd7c \
wrangler deploy
