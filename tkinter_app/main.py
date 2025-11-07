"""Punto de entrada para la aplicación HeartGuard en Tkinter."""

from __future__ import annotations

from .api_client import ApiClient
from .ui.login import LoginWindow


def main() -> None:
    root = LoginWindow(ApiClient())
    root.mainloop()


if __name__ == "__main__":
    main()
