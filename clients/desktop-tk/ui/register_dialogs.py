"""Registration dialogs for users and patients."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..utils.notifications import show_snackbar


class BaseDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, title: str) -> None:
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.result = None
        self.columnconfigure(0, weight=1)
        ttk.Frame(self, padding=20).grid(sticky="nsew")


class UserRegisterDialog(BaseDialog):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Registrar usuario")
        frame = ttk.Frame(self, padding=20)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="Nombre").grid(row=0, column=0, sticky="w", pady=4)
        self.name_entry = ttk.Entry(frame)
        self.name_entry.grid(row=0, column=1, pady=4, sticky="ew")

        ttk.Label(frame, text="Email").grid(row=1, column=0, sticky="w", pady=4)
        self.email_entry = ttk.Entry(frame)
        self.email_entry.grid(row=1, column=1, pady=4, sticky="ew")

        ttk.Label(frame, text="Contraseña").grid(row=2, column=0, sticky="w", pady=4)
        self.password_entry = ttk.Entry(frame, show="*")
        self.password_entry.grid(row=2, column=1, pady=4, sticky="ew")

        ttk.Button(frame, text="Registrar", command=self._submit).grid(
            row=3, column=0, columnspan=2, pady=(12, 0), sticky="ew"
        )

    def _submit(self) -> None:
        name = self.name_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()
        if not all([name, email, password]):
            show_snackbar(self, "Completa todos los campos", bg="#c53030")
            return
        self.result = {"name": name, "email": email, "password": password}
        self.destroy()


class PatientRegisterDialog(BaseDialog):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Registrar paciente")
        frame = ttk.Frame(self, padding=20)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)

        fields = [
            ("Nombre", "name"),
            ("Email", "email"),
            ("Contraseña", "password"),
            ("Org ID o Código", "org"),
            ("Fecha de nacimiento (YYYY-MM-DD)", "birthdate"),
            ("Sexo (M/F/O)", "sex"),
            ("Nivel de riesgo (opcional)", "risk"),
        ]
        self.entries: dict[str, ttk.Entry] = {}
        for row, (label, key) in enumerate(fields):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frame, show="*" if key == "password" else None)
            entry.grid(row=row, column=1, sticky="ew", pady=4)
            self.entries[key] = entry

        ttk.Button(frame, text="Registrar", command=self._submit).grid(
            row=len(fields), column=0, columnspan=2, pady=(12, 0), sticky="ew"
        )

    def _submit(self) -> None:
        name = self.entries["name"].get().strip()
        email = self.entries["email"].get().strip()
        password = self.entries["password"].get().strip()
        org = self.entries["org"].get().strip()
        birthdate = self.entries["birthdate"].get().strip()
        sex = self.entries["sex"].get().strip()
        risk = self.entries["risk"].get().strip()

        if not all([name, email, password, org, birthdate, sex]):
            show_snackbar(self, "Completa todos los campos obligatorios", bg="#c53030")
            return
        self.result = {
            "name": name,
            "email": email,
            "password": password,
            "org": org,
            "birthdate": birthdate,
            "sex": sex,
            "risk": risk or None,
        }
        self.destroy()
