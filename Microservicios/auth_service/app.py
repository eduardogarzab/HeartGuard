from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure parent directory is in path for common imports
BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from common.app_factory import create_app

# Use absolute import instead of relative import to avoid package resolution issues
import routes

SERVICE_NAME = "auth"
DEFAULT_PORT = 5001


app = create_app(SERVICE_NAME, routes.register_blueprint)


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("SERVICE_PORT", DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port)
