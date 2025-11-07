"""Login and registration window."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..utils.notifications import show_snackbar


class LoginView(ttk.Frame):
    def __init__(self, master: tk.Widget, *, on_login, on_register_user, on_register_patient) -> None:
        super().__init__(master)
        self.on_login = on_login
        self.on_register_user = on_register_user
        self.on_register_patient = on_register_patient
        self._build_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.configure(padding=40)

        title = ttk.Label(
            self,
            text="HeartGuard Command Center",
            font=("Segoe UI", 24, "bold"),
        )
        title.grid(row=0, column=0, pady=(0, 20))

        self.role_var = tk.StringVar(value="user")
        toggle = ttk.Checkbutton(
            self,
            text="Ingresar como paciente",
            variable=self.role_var,
            onvalue="patient",
            offvalue="user",
        )
        toggle.grid(row=1, column=0, pady=(0, 20))

        form = ttk.Frame(self)
        form.grid(row=2, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Email").grid(row=0, column=0, sticky="w", pady=4)
        self.email_entry = ttk.Entry(form)
        self.email_entry.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(form, text="Contraseña").grid(row=1, column=0, sticky="w", pady=4)
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=1, column=1, sticky="ew", pady=4)

        login_btn = ttk.Button(self, text="Iniciar sesión", command=self._handle_login)
        login_btn.grid(row=3, column=0, pady=20, sticky="ew")

        register_frame = ttk.LabelFrame(self, text="Registro rápido")
        register_frame.grid(row=4, column=0, pady=10, sticky="ew")

        ttk.Button(register_frame, text="Registrar usuario", command=self._handle_register_user).pack(
            fill="x", pady=4
        )
        ttk.Button(
            register_frame,
            text="Registrar paciente",
            command=self._handle_register_patient,
        ).pack(fill="x", pady=4)

    def _handle_login(self) -> None:
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        role = self.role_var.get()
        if not email or not password:
            show_snackbar(self, "Completa email y contraseña", bg="#c53030")
            return
        self.on_login(email, password, role == "patient")

    def _handle_register_user(self) -> None:
        self.on_register_user()

    def _handle_register_patient(self) -> None:
        self.on_register_patient()
