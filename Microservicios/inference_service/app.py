from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from common.app_factory import create_app
from .routes import register_blueprint


SERVICE_NAME = "inference"
DEFAULT_PORT = 5007


app = create_app(SERVICE_NAME, register_blueprint)


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("SERVICE_PORT", DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port)
