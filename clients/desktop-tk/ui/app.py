"""Tkinter root application for HeartGuard."""
from __future__ import annotations

import logging
import tkinter as tk
from tkinter import ttk, messagebox

from ..api.gateway_client import ApiError, GatewayApiClient
from ..controllers.auth_controller import AuthController, AuthSession
from ..controllers.user_controller import UserController
from ..controllers.patient_controller import PatientController
from ..utils.config import APP_CONFIG, BACKGROUND_COLOR, FONT_FAMILY
from ..utils.logging_config import configure_logging
from ..utils.notifications import show_snackbar
from ..utils.token_storage import TokenStorage
from .login_view import LoginView
from .main_layout import MainLayout
from .register_dialogs import PatientRegisterDialog, UserRegisterDialog

LOGGER = logging.getLogger(__name__)


class HeartGuardApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        configure_logging()
        self.title("HeartGuard Command Center")
        self.geometry("1280x800")
        self.configure(bg=BACKGROUND_COLOR)
        self.option_add("*Font", (FONT_FAMILY, 11))

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:  # pragma: no cover - depends on Tk theme availability
            pass
        style.configure("Main.TFrame", background=BACKGROUND_COLOR)
        style.configure("TFrame", background=BACKGROUND_COLOR)
        style.configure("TLabel", background=BACKGROUND_COLOR)
        self.api_client = GatewayApiClient(APP_CONFIG.gateway_url)
        self.token_storage = TokenStorage()
        self.auth_controller = AuthController(self.api_client, self.token_storage)
        self.user_controller = UserController(self.api_client)
        self.patient_controller = PatientController(self.api_client)
        self.active_layout: MainLayout | None = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.container = ttk.Frame(self, style="Main.TFrame")
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.columnconfigure(0, weight=1)
        self.container.rowconfigure(0, weight=1)

        self._show_login()
        self.after(100, self._attempt_restore_session)

    def _show_login(self) -> None:
        for child in self.container.winfo_children():
            child.destroy()
        self.login_view = LoginView(
            self.container,
            on_login=self._handle_login,
            on_register_user=self._handle_register_user,
            on_register_patient=self._handle_register_patient,
        )
        self.login_view.grid(row=0, column=0, sticky="nsew")

    def _handle_login(self, email: str, password: str, as_patient: bool) -> None:
        try:
            session = self.auth_controller.login(email, password, as_patient=as_patient)
        except ApiError as exc:
            LOGGER.error("Login failed: %s", exc)
            messagebox.showerror("Error de autenticación", str(exc))
            return
        show_snackbar(self, "Inicio de sesión exitoso", bg="#38a169")
        self._show_main_layout(session)

    def _handle_register_user(self) -> None:
        dialog = UserRegisterDialog(self)
        self.wait_window(dialog)
        if not dialog.result:
            return
        try:
            self.auth_controller.register_user(**dialog.result)
            show_snackbar(self, "Usuario registrado. Inicia sesión para continuar", bg="#3182ce")
        except ApiError as exc:
            messagebox.showerror("Registro", str(exc))

    def _handle_register_patient(self) -> None:
        dialog = PatientRegisterDialog(self)
        self.wait_window(dialog)
        if not dialog.result:
            return
        try:
            data = dialog.result
            self.auth_controller.register_patient(
                name=data["name"],
                email=data["email"],
                password=data["password"],
                org_id_or_code=data["org"],
                birthdate=data["birthdate"],
                sex_code=data["sex"],
                risk_level_code=data["risk"],
            )
            show_snackbar(self, "Paciente registrado. Inicia sesión", bg="#3182ce")
        except ApiError as exc:
            messagebox.showerror("Registro", str(exc))

    def _show_main_layout(self, session: AuthSession) -> None:
        for child in self.container.winfo_children():
            child.destroy()
        self.active_layout = MainLayout(
            self.container,
            session=session,
            on_logout=self._logout,
            user_controller=self.user_controller,
            patient_controller=self.patient_controller,
        )
        self.active_layout.grid(row=0, column=0, sticky="nsew")

    def _attempt_restore_session(self) -> None:
        session = self.auth_controller.restore_session()
        if session:
            show_snackbar(self, "Sesión restaurada", bg="#38a169")
            self._show_main_layout(session)

    def _logout(self) -> None:
        self.auth_controller.clear_session()
        show_snackbar(self, "Sesión finalizada", bg="#c53030")
        self._show_login()


def run() -> None:
    app = HeartGuardApp()
    app.mainloop()


__all__ = ["HeartGuardApp", "run"]
