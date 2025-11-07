"""Ventana de inicio de sesión y registro equivalente a ``LoginFrame``."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Dict, Optional

from ..api_client import ApiClient, ApiError
from ..models.auth import LoginResponse
from ..config import Colors, Fonts
from .widgets import AsyncMixin, setup_styles, styled_button


class LoginWindow(tk.Tk, AsyncMixin):
    LOGIN_VIEW = "login"
    REGISTER_USER_VIEW = "register_user"
    REGISTER_PATIENT_VIEW = "register_patient"

    def __init__(self, api_client: Optional[ApiClient] = None) -> None:
        super().__init__()
        self.title("HeartGuard - Sistema de Monitoreo Cardíaco")
        self.geometry("560x720")
        self.resizable(False, False)
        setup_styles(self)

        self.api_client = api_client or ApiClient()
        self._views: Dict[str, tk.Frame] = {}

        container = ttk.Frame(self, padding=24)
        container.pack(fill="both", expand=True)

        for view_cls in (_LoginFrame, _RegisterUserFrame, _RegisterPatientFrame):
            view = view_cls(container, self.api_client, self)
            view.grid(row=0, column=0, sticky="nsew")
            self._views[view.name] = view

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.show_view(self.LOGIN_VIEW)

    # AsyncMixin requiere after -> Tk lo provee

    def show_view(self, name: str) -> None:
        self._views[name].tkraise()

    # Navegación a dashboards -------------------------------------------------
    def open_dashboard(self, response: LoginResponse) -> None:
        if response.account_type == "patient":
            from .patient_dashboard import PatientDashboardWindow

            dashboard = PatientDashboardWindow(self.api_client, response)
            dashboard.focus_force()
        else:
            from .user_dashboard import UserDashboardWindow

            dashboard = UserDashboardWindow(self.api_client, response)
            dashboard.focus_force()
        self.withdraw()


class _BaseView(ttk.Frame, AsyncMixin):
    name: str

    def __init__(self, master: tk.Widget, api_client: ApiClient, controller: LoginWindow) -> None:
        super().__init__(master)
        self.api_client = api_client
        self.controller = controller
        self.configure(style="Card.TFrame")

    def after(self, delay_ms: int, callback: Callable, *args):  # type: ignore[override]
        return self.controller.after(delay_ms, callback, *args)

    def show_login(self) -> None:
        self.controller.show_view(LoginWindow.LOGIN_VIEW)


class _LoginFrame(_BaseView):
    name = LoginWindow.LOGIN_VIEW

    def __init__(self, master: tk.Widget, api_client: ApiClient, controller: LoginWindow) -> None:
        super().__init__(master, api_client, controller)
        self._status = tk.StringVar(value=" ")
        self._account_type = tk.StringVar(value="user")

        title = ttk.Label(self, text="HeartGuard", font=("Arial", 28, "bold"), foreground=Colors.PRIMARY)
        subtitle = ttk.Label(self, text="Sistema de Monitoreo Cardíaco", font=Fonts.SUBTITLE, foreground=Colors.TEXT_SECONDARY)
        title.pack(pady=(10, 4))
        subtitle.pack(pady=(0, 24))

        form = ttk.Frame(self)
        form.pack(fill="x", padx=8)

        type_label = ttk.Label(form, text="Tipo de cuenta:", font=Fonts.BODY_BOLD)
        type_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 4))

        ttk.Radiobutton(form, text="Usuario (Staff)", variable=self._account_type, value="user").grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(form, text="Paciente", variable=self._account_type, value="patient").grid(row=1, column=1, sticky="w")

        ttk.Label(form, text="Email:").grid(row=2, column=0, sticky="w", pady=(12, 0))
        self._email_entry = ttk.Entry(form, width=30)
        self._email_entry.grid(row=2, column=1, sticky="ew", pady=(12, 0))

        ttk.Label(form, text="Contraseña:").grid(row=3, column=0, sticky="w", pady=(12, 0))
        self._password_entry = ttk.Entry(form, width=30, show="*")
        self._password_entry.grid(row=3, column=1, sticky="ew", pady=(12, 0))

        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(self)
        buttons.pack(pady=20)

        login_button = styled_button(buttons, "Iniciar Sesión", self._on_login)
        register_button = styled_button(buttons, "Registrarse", self._on_register, primary=False)
        login_button.grid(row=0, column=0, padx=6)
        register_button.grid(row=0, column=1, padx=6)

        self._status_label = ttk.Label(self, textvariable=self._status, foreground=Colors.DANGER, anchor="center")
        self._status_label.pack(fill="x")

        self.bind("<Return>", lambda _e: self._on_login())

    def _set_status(self, text: str, *, error: bool = False) -> None:
        self._status.set(text)
        self._status_label.configure(foreground=Colors.DANGER if error else Colors.PRIMARY)

    def _on_register(self) -> None:
        if self._account_type.get() == "user":
            self.controller.show_view(LoginWindow.REGISTER_USER_VIEW)
        else:
            self.controller.show_view(LoginWindow.REGISTER_PATIENT_VIEW)

    def _on_login(self) -> None:
        email = self._email_entry.get().strip()
        password = self._password_entry.get().strip()

        if not email or not password:
            self._set_status("Por favor complete todos los campos", error=True)
            return

        self._set_status("Iniciando sesión...", error=False)

        def handle_success(response: LoginResponse) -> None:
            self._set_status("¡Inicio de sesión exitoso!", error=False)
            self.controller.open_dashboard(response)

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self._set_status(f"Error: {exc}", error=True)
            else:
                messagebox.showerror("Error", str(exc))
                self._set_status("Error de conexión", error=True)

        account_type = self._account_type.get()
        func = self.api_client.login_user if account_type == "user" else self.api_client.login_patient
        self.run_async(func, handle_success, handle_error, email, password)


class _RegisterUserFrame(_BaseView):
    name = LoginWindow.REGISTER_USER_VIEW

    def __init__(self, master: tk.Widget, api_client: ApiClient, controller: LoginWindow) -> None:
        super().__init__(master, api_client, controller)
        self._status = tk.StringVar(value=" ")

        title = ttk.Label(self, text="Registro de Usuario (Staff)", font=Fonts.TITLE)
        title.pack(pady=(0, 16))

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16)

        self._email = ttk.Entry(form, width=30)
        self._password = ttk.Entry(form, width=30, show="*")
        self._confirm = ttk.Entry(form, width=30, show="*")
        self._name = ttk.Entry(form, width=30)
        self._name.insert(0, "Ej: Dr. Juan Pérez López")

        self._add_field(form, 0, "*Email:", self._email)
        self._add_field(form, 1, "*Contraseña:", self._password)
        self._add_field(form, 2, "*Confirmar Contraseña:", self._confirm)
        self._add_field(form, 3, "*Nombre Completo:", self._name)

        ttk.Label(form, text="Nota: Se unirá a organizaciones mediante invitaciones", foreground=Colors.TEXT_SECONDARY).grid(row=4, column=0, columnspan=2, pady=(12, 0), sticky="w")

        buttons = ttk.Frame(self)
        buttons.pack(pady=24)

        styled_button(buttons, "Registrar", self._on_register).grid(row=0, column=0, padx=6)
        styled_button(buttons, "Volver", self.show_login, primary=False).grid(row=0, column=1, padx=6)

        ttk.Label(self, textvariable=self._status, foreground=Colors.DANGER).pack(fill="x")

    def _add_field(self, form: ttk.Frame, row: int, label: str, entry: ttk.Entry) -> None:
        ttk.Label(form, text=label).grid(row=row, column=0, sticky="w", pady=6)
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        form.columnconfigure(1, weight=1)

    def _on_register(self) -> None:
        email = self._email.get().strip()
        password = self._password.get().strip()
        confirm = self._confirm.get().strip()
        name = self._name.get().strip()

        if not email or not password or not name:
            self._status.set("Por favor complete todos los campos obligatorios (*)")
            return
        if password != confirm:
            self._status.set("Las contraseñas no coinciden")
            return
        if len(password) < 8:
            self._status.set("La contraseña debe tener al menos 8 caracteres")
            return

        self._status.set("Registrando usuario...")

        def handle_success(_payload: Dict[str, Any]) -> None:
            messagebox.showinfo(
                "Registro Exitoso",
                "Usuario registrado exitosamente!\n\n"
                f"Email: {email}\nNombre: {name}\n\nAhora puedes iniciar sesión.",
            )
            self._email.delete(0, tk.END)
            self._password.delete(0, tk.END)
            self._confirm.delete(0, tk.END)
            self._name.delete(0, tk.END)
            self._status.set("¡Registro exitoso!")
            self.show_login()

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self._status.set(f"Error: {exc}")
            else:
                self._status.set("Error de conexión: {}".format(exc))

        self.run_async(self.api_client.register_user, handle_success, handle_error, email, password, name)


class _RegisterPatientFrame(_BaseView):
    name = LoginWindow.REGISTER_PATIENT_VIEW

    def __init__(self, master: tk.Widget, api_client: ApiClient, controller: LoginWindow) -> None:
        super().__init__(master, api_client, controller)
        self._status = tk.StringVar(value=" ")

        title = ttk.Label(self, text="Registro de Paciente", font=Fonts.TITLE)
        title.pack(pady=(0, 12))

        note = ttk.Label(
            self,
            text="Ingrese el código o ID de la organización. Se detectará automáticamente el formato.",
            wraplength=460,
            foreground=Colors.TEXT_SECONDARY,
        )
        note.pack(pady=(0, 12))

        form = ttk.Frame(self)
        form.pack(fill="x", padx=16)

        self._fields: Dict[str, ttk.Entry] = {
            "email": ttk.Entry(form, width=30),
            "password": ttk.Entry(form, width=30, show="*"),
            "confirm": ttk.Entry(form, width=30, show="*"),
            "name": ttk.Entry(form, width=30),
            "org": ttk.Entry(form, width=30),
            "birthdate": ttk.Entry(form, width=30),
            "sex": ttk.Entry(form, width=30),
            "risk": ttk.Entry(form, width=30),
        }

        labels = [
            "*Email:",
            "*Contraseña:",
            "*Confirmar Contraseña:",
            "*Nombre Completo:",
            "*Código o ID de Organización:",
            "*Fecha de Nacimiento (YYYY-MM-DD):",
            "*Sexo (M/F/O):",
            "Nivel de Riesgo (opcional):",
        ]

        for idx, (key, entry) in enumerate(self._fields.items()):
            ttk.Label(form, text=labels[idx]).grid(row=idx, column=0, sticky="w", pady=5)
            entry.grid(row=idx, column=1, sticky="ew", pady=5)
        form.columnconfigure(1, weight=1)

        buttons = ttk.Frame(self)
        buttons.pack(pady=24)

        styled_button(buttons, "Registrar Paciente", self._on_register).grid(row=0, column=0, padx=6)
        styled_button(buttons, "Volver", self.show_login, primary=False).grid(row=0, column=1, padx=6)

        ttk.Label(self, textvariable=self._status, foreground=Colors.DANGER).pack(fill="x")

    def _on_register(self) -> None:
        email = self._fields["email"].get().strip()
        password = self._fields["password"].get().strip()
        confirm = self._fields["confirm"].get().strip()
        name = self._fields["name"].get().strip()
        org = self._fields["org"].get().strip()
        birthdate = self._fields["birthdate"].get().strip()
        sex = self._fields["sex"].get().strip()
        risk = self._fields["risk"].get().strip()

        if not all([email, password, name, org, birthdate, sex]):
            self._status.set("Por favor complete todos los campos obligatorios (*)")
            return
        if password != confirm:
            self._status.set("Las contraseñas no coinciden")
            return
        if len(password) < 8:
            self._status.set("La contraseña debe tener al menos 8 caracteres")
            return

        self._status.set("Registrando paciente...")

        def handle_success(_payload: Dict[str, Any]) -> None:
            messagebox.showinfo(
                "Registro Exitoso",
                "Paciente registrado exitosamente. Ahora puedes iniciar sesión.",
            )
            for entry in self._fields.values():
                entry.delete(0, tk.END)
            self._status.set("¡Registro exitoso!")
            self.show_login()

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self._status.set(f"Error: {exc}")
            else:
                self._status.set(f"Error de conexión: {exc}")

        self.run_async(
            self.api_client.register_patient,
            handle_success,
            handle_error,
            email,
            password,
            name,
            org,
            birthdate,
            sex,
            risk or None,
        )
