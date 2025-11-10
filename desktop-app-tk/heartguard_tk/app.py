"""Entry point for the Tkinter version of HeartGuard desktop."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Optional, Type

from .api import ApiClient
from .models import LoginResponse
from .ui.base import AppController, BaseView
from .ui.login import LoginView
from .ui.patient_dashboard import PatientDashboardView
from .ui.register_patient import RegisterPatientView
from .ui.register_user import RegisterUserView
from .ui.user_dashboard import UserDashboardView
from .ui.theme import ModernTheme, COLORS


class HeartGuardApp(tk.Tk, AppController):
    def __init__(self) -> None:
        super().__init__()
        self.title("HeartGuard - Sistema de Monitoreo Cardíaco")
        
        # Hacer la ventana pantalla completa
        self.state('zoomed')  # Windows maximizado
        # Alternativamente: self.attributes('-fullscreen', True)
        
        # Aplicar tema moderno
        self.configure(bg=COLORS["bg_secondary"])
        self.style = ModernTheme.configure_style(self)
        
        self._api = ApiClient()
        self.current_view: Optional[BaseView] = None
        self.current_login: Optional[LoginResponse] = None

        self.show_login()

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def call_soon(self, callback) -> None:
        self.after(0, callback)

    @property
    def api(self) -> ApiClient:
        return self._api

    def _swap_view(self, view_cls: Type[BaseView], **kwargs) -> BaseView:
        if self.current_view is not None:
            self.current_view.destroy()
        frame = view_cls(self, self, **kwargs)
        frame.pack(fill="both", expand=True)
        self.current_view = frame
        return frame

    def show_login(self, prefill_email: Optional[str] = None) -> None:
        view = self._swap_view(LoginView)
        if prefill_email:
            view.populate_from_registration(prefill_email)
        self.current_login = None
        self._api.set_access_token(None)

    def show_register_user(self) -> None:
        self._swap_view(RegisterUserView)

    def show_register_patient(self) -> None:
        self._swap_view(RegisterPatientView)

    def open_patient_dashboard(self, login: LoginResponse) -> None:
        self.current_login = login
        self._api.set_access_token(login.access_token)
        self._swap_view(PatientDashboardView, login=login)

    def open_user_dashboard(self, login: LoginResponse) -> None:
        self.current_login = login
        self._api.set_access_token(login.access_token)
        self._swap_view(UserDashboardView, login=login)

    def logout(self) -> None:
        self.show_login()

    # ------------------------------------------------------------------
    # Run loop
    # ------------------------------------------------------------------
    def run(self) -> None:
        self.mainloop()


def main() -> None:
    app = HeartGuardApp()
    app.run()


if __name__ == "__main__":
    main()
