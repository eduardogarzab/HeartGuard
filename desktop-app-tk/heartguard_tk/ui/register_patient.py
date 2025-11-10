"""Patient registration view."""

from __future__ import annotations

import datetime as dt
import tkinter as tk
from tkinter import ttk

from ..api import ApiError
from .base import BaseView


class RegisterPatientView(BaseView):
    def __init__(self, master: tk.Misc, controller, **kwargs):
        super().__init__(master, controller, **kwargs)
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.org_var = tk.StringVar()
        self.birthdate_var = tk.StringVar()
        self.sex_var = tk.StringVar(value="M")
        self.risk_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self._build()

    def _build(self) -> None:
        wrapper = ttk.Frame(self, padding=20)
        wrapper.pack(expand=True)

        ttk.Label(wrapper, text="Registro de Paciente", font=("Segoe UI", 20, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(10, 20)
        )

        self._add_field(wrapper, "Email:", self.email_var, row=1)
        self._add_field(wrapper, "Contraseña:", self.password_var, row=2, show="*")
        self._add_field(wrapper, "Confirmar contraseña:", self.confirm_var, row=3, show="*")
        self._add_field(wrapper, "Nombre completo:", self.name_var, row=4)
        self._add_field(wrapper, "Org ID o código:", self.org_var, row=5)
        self._add_field(wrapper, "Fecha de nacimiento (YYYY-MM-DD):", self.birthdate_var, row=6)

        ttk.Label(wrapper, text="Sexo (M/F/O):").grid(row=7, column=0, sticky="e", padx=10, pady=6)
        sex_entry = ttk.Combobox(wrapper, textvariable=self.sex_var, values=("M", "F", "O"), state="readonly")
        sex_entry.grid(row=7, column=1, sticky="we", padx=10, pady=6)

        self._add_field(wrapper, "Nivel de riesgo (opcional):", self.risk_var, row=8)

        ttk.Label(
            wrapper,
            text="Puedes usar un UUID de organización o su código como CLIN-001",
            foreground="#555",
        ).grid(row=9, column=0, columnspan=2, pady=(10, 15))

        button_frame = ttk.Frame(wrapper)
        button_frame.grid(row=10, column=0, columnspan=2, pady=10)
        ttk.Button(button_frame, text="Registrar", command=self._on_submit).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Volver", command=self.controller.show_login).pack(side="left", padx=10)

        ttk.Label(wrapper, textvariable=self.status_var, foreground="#c91e1e").grid(
            row=11, column=0, columnspan=2, pady=(5, 0)
        )

    def _add_field(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        *,
        row: int,
        show: str | None = None,
    ) -> None:
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="e", padx=10, pady=6)
        entry = ttk.Entry(parent, textvariable=variable, width=32)
        if show:
            entry.configure(show=show)
        entry.grid(row=row, column=1, sticky="we", padx=10, pady=6)

    def _on_submit(self) -> None:
        email = self.email_var.get().strip()
        password = self.password_var.get()
        confirm = self.confirm_var.get()
        name = self.name_var.get().strip()
        org = self.org_var.get().strip()
        birthdate = self.birthdate_var.get().strip()
        sex = self.sex_var.get().strip().upper()
        risk = self.risk_var.get().strip() or None

        if not all([email, password, name, org, birthdate, sex]):
            self.status_var.set("Completa los campos obligatorios")
            return
        if password != confirm:
            self.status_var.set("Las contraseñas no coinciden")
            return
        if len(password) < 8:
            self.status_var.set("La contraseña debe tener al menos 8 caracteres")
            return
        try:
            dt.date.fromisoformat(birthdate)
        except ValueError:
            self.status_var.set("Formato de fecha inválido")
            return
        if sex not in {"M", "F", "O"}:
            self.status_var.set("Sexo inválido (usa M/F/O)")
            return

        self.status_var.set("Registrando paciente...")
        self._set_enabled(False)

        def task():
            return self.controller.api.register_patient(
                email,
                password,
                name,
                org,
                birthdate,
                sex,
                risk,
            )

        def handle_success(_response) -> None:
            self._set_enabled(True)
            self.status_var.set("")
            self.controller.show_login(prefill_email=email)

        def handle_error(exc: Exception) -> None:
            self._set_enabled(True)
            if isinstance(exc, ApiError):
                self.status_var.set(exc.message)
            else:
                self.status_var.set(str(exc))

        self.run_async(task, on_success=handle_success, on_error=handle_error)

    def _set_enabled(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        for child in self.winfo_children():
            _set_state_recursive(child, state)


def _set_state_recursive(widget: tk.Widget, state: str) -> None:
    try:
        widget.configure(state=state)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        _set_state_recursive(child, state)
