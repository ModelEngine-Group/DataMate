#!/usr/bin/env bash
set -euo pipefail

PORT="${QWEN_SERVER_PORT:-18080}"

# qwen_vl_server.py binds 127.0.0.1 in __main__ by default.
# Start the Flask app explicitly so the container listens on 0.0.0.0.
exec python -c "import qwen_vl_server as s; s.app.run(host='0.0.0.0', port=int('${PORT}'), debug=False)"
