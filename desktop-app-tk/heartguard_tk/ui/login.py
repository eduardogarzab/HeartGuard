"""Modern login view with professional HealthTech design."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import TYPE_CHECKING

from ..api import ApiError
from ..models import LoginResponse
from .base import BaseView
from .theme import ModernTheme, COLORS, FONTS, SPACING, SIZES

if TYPE_CHECKING:
    from ..app import HeartGuardApp


class LoginView(BaseView):
    """Vista de inicio de sesión con diseño moderno."""

    def __init__(self, master: tk.Misc, controller, **kwargs):
        super().__init__(master, controller, **kwargs)
        self.configure(bg=COLORS["bg_secondary"])
        
        self.account_var = tk.StringVar(value="user")
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.status_var = tk.StringVar()
        
        self._build()

    def _build(self) -> None:
        """Construye la interfaz de login moderna."""
        # Contenedor principal centrado
        main_container = tk.Frame(self, bg=COLORS["bg_secondary"])
        main_container.place(relx=0.5, rely=0.5, anchor="center")
        
        # Tarjeta de login
        login_card = ModernTheme.create_card(main_container, 
                                            padding=SPACING["xxl"] + 8)
        login_card.pack()
        
        # Header con logo y título
        header = ttk.Frame(login_card, style="Card.TFrame")
        header.pack(fill="x", pady=(0, SPACING["xl"]))
        
        # Logo/Icono
        logo = ttk.Label(header, text="❤️", font=("Segoe UI", 48),
                        background=COLORS["bg_card"])
        logo.pack(pady=(0, SPACING["sm"]))
        
        # Título
        title = ttk.Label(header, text="HeartGuard",
                         style="Heading1.TLabel")
        title.pack()
        
        subtitle = ttk.Label(header, text="Sistema de Monitoreo Cardíaco",
                           style="Secondary.TLabel")
        subtitle.pack(pady=(SPACING["xs"], 0))
        
        # Formulario
        form = ttk.Frame(login_card, style="Card.TFrame")
        form.pack(fill="both", expand=True, pady=SPACING["lg"])
        
        # Tipo de cuenta
        account_frame = ttk.Frame(form, style="Card.TFrame")
        account_frame.pack(fill="x", pady=(0, SPACING["lg"]))
        
        ttk.Label(account_frame, text="Tipo de cuenta:",
                 font=FONTS["label"], foreground=COLORS["text_secondary"],
                 background=COLORS["bg_card"]).pack(anchor="w", 
                                                    pady=(0, SPACING["sm"]))
        
        radio_container = ttk.Frame(account_frame, style="Card.TFrame")
        radio_container.pack(fill="x")
        
        user_radio = ttk.Radiobutton(radio_container, text="👨‍⚕️ Usuario (Staff)",
                                    value="user", variable=self.account_var)
        user_radio.pack(side="left", padx=(0, SPACING["lg"]))
        
        patient_radio = ttk.Radiobutton(radio_container, text="🩺 Paciente",
                                       value="patient", variable=self.account_var)
        patient_radio.pack(side="left")
        
        # Email
        email_frame = ttk.Frame(form, style="Card.TFrame")
        email_frame.pack(fill="x", pady=(0, SPACING["md"]))
        
        ttk.Label(email_frame, text="Correo electrónico",
                 font=FONTS["label"], foreground=COLORS["text_secondary"],
                 background=COLORS["bg_card"]).pack(anchor="w", 
                                                    pady=(0, SPACING["xs"]))
        
        email_entry = ttk.Entry(email_frame, textvariable=self.email_var,
                               font=FONTS["body"], width=40)
        email_entry.pack(fill="x", ipady=8)
        email_entry.bind("<Return>", lambda e: self._on_login())
        
        # Password
        password_frame = ttk.Frame(form, style="Card.TFrame")
        password_frame.pack(fill="x", pady=(0, SPACING["lg"]))
        
        ttk.Label(password_frame, text="Contraseña",
                 font=FONTS["label"], foreground=COLORS["text_secondary"],
                 background=COLORS["bg_card"]).pack(anchor="w",
                                                    pady=(0, SPACING["xs"]))
        
        password_entry = ttk.Entry(password_frame, textvariable=self.password_var,
                                  font=FONTS["body"], show="●", width=40)
        password_entry.pack(fill="x", ipady=8)
        password_entry.bind("<Return>", lambda e: self._on_login())
        
        # Mensaje de error
        error_label = ttk.Label(form, textvariable=self.status_var,
                               foreground=COLORS["danger"],
                               font=FONTS["body_small"],
                               background=COLORS["bg_card"],
                               wraplength=450)
        error_label.pack(fill="x", pady=(0, SPACING["md"]))
        
        # Botones
        button_frame = ttk.Frame(form, style="Card.TFrame")
        button_frame.pack(fill="x")
        
        button_container = ttk.Frame(button_frame, style="Card.TFrame")
        button_container.pack()
        
        self.login_button = ModernTheme.create_button(button_container, 
                                                     text="Iniciar Sesión",
                                                     command=self._on_login,
                                                     style="Primary.TButton")
        self.login_button.pack(side="left", padx=(0, SPACING["sm"]), ipady=4, ipadx=10)
        
        self.register_button = ModernTheme.create_button(button_container,
                                                        text="Registrarse",
                                                        command=self._open_register,
                                                        style="Secondary.TButton")
        self.register_button.pack(side="left", ipady=4, ipadx=10)
        
        # Footer
        footer = ttk.Label(login_card, 
                          text="© 2025 HeartGuard. Tecnología para el cuidado cardíaco.",
                          style="Caption.TLabel")
        footer.pack(pady=(SPACING["xl"], 0))
        
        # Focus inicial
        email_entry.focus_set()

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------
    def _on_login(self) -> None:
        email = self.email_var.get().strip()
        password = self.password_var.get()
        account_type = self.account_var.get()

        if not email or not password:
            self.status_var.set("Por favor complete todos los campos")
            return

        self.status_var.set("Iniciando sesión...")
        self.login_button.configure(state="disabled")
        self.register_button.configure(state="disabled")

        def task() -> LoginResponse:
            if account_type == "patient":
                return self.controller.api.login_patient(email, password)
            else:
                return self.controller.api.login_user(email, password)

        def on_success(response: LoginResponse) -> None:
            self.status_var.set("")
            self.login_button.configure(state="normal")
            self.register_button.configure(state="normal")
            # Determinar tipo de dashboard según el tipo de cuenta
            if account_type == "patient":
                self.controller.open_patient_dashboard(response)
            else:
                self.controller.open_user_dashboard(response)

        def on_error(error: Exception) -> None:
            self.login_button.configure(state="normal")
            self.register_button.configure(state="normal")
            if isinstance(error, ApiError):
                self.status_var.set(error.message)
            else:
                self.status_var.set(str(error))

        self.run_async(task, on_success=on_success, on_error=on_error)

    def _open_register(self) -> None:
        account_type = self.account_var.get()
        if account_type == "patient":
            self.controller.show_register_patient()
        else:
            self.controller.show_register_user()
