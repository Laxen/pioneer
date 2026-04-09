#!/bin/sh
set -e

# If running inside HA Supervisor, read credentials from options.json.
# Falls back to environment variables (for local dev with a .env file).
if [ -f /data/options.json ]; then
    OPENAI_API_KEY=$(python3 -c "import json; d=json.load(open('/data/options.json')); print(d.get('openai_api_key',''))")
    TELEGRAM_BOT_TOKEN=$(python3 -c "import json; d=json.load(open('/data/options.json')); print(d.get('telegram_bot_token',''))")
    TELEGRAM_CHAT_ID=$(python3 -c "import json; d=json.load(open('/data/options.json')); print(d.get('telegram_chat_id',''))")
    OPENAI_MODEL=$(python3 -c "import json; d=json.load(open('/data/options.json')); print(d.get('openai_model','gpt-4o-mini'))")
    PROMPT=$(python3 -c "import json; d=json.load(open('/data/options.json')); print(d.get('prompt',''))")
    export OPENAI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID OPENAI_MODEL PROMPT
fi

exec python /app/main.py
