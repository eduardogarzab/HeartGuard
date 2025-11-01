from __future__ import annotations

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from common.app_factory import create_app
import routes
from middleware import validate_api_key_middleware


SERVICE_NAME = "gateway"
DEFAULT_PORT = 5000


app = create_app(SERVICE_NAME, routes.register_blueprint)

# Agregar middleware de validación de API Key
validate_api_key_middleware(app)


if __name__ == "__main__":
    port = int(os.getenv("PORT", os.getenv("SERVICE_PORT", DEFAULT_PORT)))
    app.run(host="0.0.0.0", port=port)
