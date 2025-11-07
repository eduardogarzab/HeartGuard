"""Ventana Tkinter que replica ``PatientDashboardPanel`` de Swing."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, List, Optional

from ..api_client import ApiClient
from ..models import auth as auth_models
from ..config import Colors, Fonts
from .widgets import AsyncMixin, ScrollableFrame, setup_styles, styled_button


class PatientDashboardWindow(tk.Toplevel, AsyncMixin):
    def __init__(self, api_client: ApiClient, login_response: auth_models.LoginResponse) -> None:
        super().__init__()
        self.api_client = api_client
        self.login_response = login_response
        self.title("HeartGuard - Mi Portal de Salud")
        self.geometry("1100x780")
        self.configure(background=Colors.BACKGROUND)
        setup_styles(self)

        header = ttk.Frame(self, padding=24)
        header.pack(fill="x")
        ttk.Label(header, text="Mi Portal de Salud", font=("Segoe UI", 24, "bold"), foreground=Colors.PRIMARY).pack(anchor="w")
        ttk.Label(
            header,
            text="Resumen personalizado de tu bienestar y seguimiento clínico",
            font=Fonts.SUBTITLE,
            foreground=Colors.TEXT_SECONDARY,
        ).pack(anchor="w")

        body = ScrollableFrame(self)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.profile_section = _ProfileSection(body.content)
        self.profile_section.frame.pack(fill="x", pady=8)

        self.stats_section = _StatsSection(body.content)
        self.stats_section.frame.pack(fill="x", pady=8)

        self.alerts_section = _AlertsSection(body.content)
        self.alerts_section.frame.pack(fill="x", pady=8)

        self.care_team_section = _CareTeamSection(body.content)
        self.care_team_section.frame.pack(fill="x", pady=8)

        self.caregivers_section = _CaregiversSection(body.content)
        self.caregivers_section.frame.pack(fill="x", pady=8)

        self.locations_section = _LocationsSection(body.content)
        self.locations_section.frame.pack(fill="x", pady=8)

        actions = ttk.Frame(self, padding=(24, 0, 24, 24))
        actions.pack(fill="x")
        styled_button(actions, "Actualizar", self.refresh).pack(side="left")
        styled_button(actions, "Cerrar Sesión", self.logout, primary=False).pack(side="right")

        self.refresh()

    # AsyncMixin -> after provisto por Tk

    def refresh(self) -> None:
        token = self.login_response.access_token

        def on_success(payloads: Dict[str, Dict[str, Any]]) -> None:
            dashboard = payloads["dashboard"]
            self.profile_section.update(dashboard.get("profile") or {})
            self.stats_section.update(dashboard.get("metrics") or {}, payloads.get("devices"))
            self.alerts_section.update(payloads.get("alerts") or {})
            self.care_team_section.update(payloads.get("care_team") or {})
            self.caregivers_section.update(payloads.get("caregivers") or {})
            self.locations_section.update(payloads.get("locations") or {})

        def on_error(exc: Exception) -> None:
            messagebox.showerror("Error", f"No se pudo actualizar el dashboard: {exc}")

        def fetch_all() -> Dict[str, Dict[str, Any]]:
            return {
                "dashboard": self.api_client.get_patient_dashboard(token),
                "alerts": self.api_client.get_patient_alerts(token=token, limit=6),
                "devices": self.api_client.get_patient_devices(token=token),
                "care_team": self.api_client.get_patient_care_team(token=token),
                "caregivers": self.api_client.get_patient_caregivers(token=token),
                "locations": self.api_client.get_patient_locations(token=token, limit=6),
            }

        self.run_async(fetch_all, on_success, on_error)

    def logout(self) -> None:
        self.destroy()


class _Section:
    def __init__(self, master: tk.Widget, title: str) -> None:
        self.frame = ttk.LabelFrame(master, text=title, padding=16)
        self.frame.configure(labelanchor="n")


class _ProfileSection(_Section):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Información Personal")
        self.labels: Dict[str, tk.StringVar] = {
            "name": tk.StringVar(value="--"),
            "email": tk.StringVar(value="--"),
            "birthdate": tk.StringVar(value="--"),
            "risk": tk.StringVar(value="--"),
            "org": tk.StringVar(value="--"),
        }
        grid = ttk.Frame(self.frame)
        grid.pack(fill="x")
        for row, (label, var) in enumerate(self.labels.items()):
            ttk.Label(grid, text={
                "name": "Nombre",
                "email": "Email",
                "birthdate": "Fecha de Nacimiento",
                "risk": "Nivel de Riesgo",
                "org": "Organización",
            }[label]).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Label(grid, textvariable=var, font=Fonts.BODY_BOLD).grid(row=row, column=1, sticky="w", pady=4)

    def update(self, profile: Dict[str, Any]) -> None:
        self.labels["name"].set(profile.get("name") or "--")
        self.labels["email"].set(profile.get("email") or "--")
        self.labels["birthdate"].set(profile.get("birthdate") or "--")
        risk = profile.get("risk_level") or profile.get("risk") or "--"
        self.labels["risk"].set(risk)
        org = profile.get("org_name") or profile.get("organization") or "--"
        self.labels["org"].set(org)


class _StatsSection(_Section):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Métricas de Salud")
        self.metrics = {
            "alerts": tk.StringVar(value="0"),
            "pending": tk.StringVar(value="0"),
            "devices": tk.StringVar(value="0"),
            "last_reading": tk.StringVar(value="--"),
        }
        grid = ttk.Frame(self.frame)
        grid.pack(fill="x")
        labels = {
            "alerts": "Alertas totales",
            "pending": "Alertas pendientes",
            "devices": "Dispositivos activos",
            "last_reading": "Última lectura",
        }
        for col, key in enumerate(labels):
            card = ttk.Frame(grid, padding=12, borderwidth=1, relief="ridge")
            card.grid(row=0, column=col, padx=6, sticky="nsew")
            ttk.Label(card, text=labels[key], font=Fonts.SUBTITLE).pack()
            ttk.Label(card, textvariable=self.metrics[key], font=("Segoe UI", 16, "bold"), foreground=Colors.PRIMARY).pack()
        for col in range(len(labels)):
            grid.columnconfigure(col, weight=1)

    def update(self, metrics: Dict[str, Any], devices_payload: Optional[Dict[str, Any]]) -> None:
        data = metrics.get("data") if isinstance(metrics.get("data"), dict) else metrics
        alerts = data.get("alerts") if isinstance(data, dict) else {}
        self.metrics["alerts"].set(str(alerts.get("total") or data.get("alerts_total") or "0"))
        self.metrics["pending"].set(str(alerts.get("pending") or data.get("alerts_pending") or "0"))
        if devices_payload:
            devices_data = devices_payload.get("data") or {}
            self.metrics["devices"].set(str(devices_data.get("count") or len(devices_data.get("devices") or [])))
        last_reading = data.get("last_reading") or "--"
        if isinstance(last_reading, dict):
            last_reading = last_reading.get("measured_at") or last_reading.get("value")
        self.metrics["last_reading"].set(str(last_reading or "--"))


class _AlertsSection(_Section):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Alertas Recientes")
        self.listbox = tk.Listbox(self.frame, height=6)
        self.listbox.pack(fill="both", expand=True)

    def update(self, payload: Dict[str, Any]) -> None:
        self.listbox.delete(0, tk.END)
        alerts = payload.get("data", {}).get("alerts") or payload.get("alerts") or []
        for alert in alerts:
            if isinstance(alert, dict):
                item = f"[{alert.get('status', 'N/A')}] {alert.get('message') or alert.get('description', '')}"
                self.listbox.insert(tk.END, item)
        if not alerts:
            self.listbox.insert(tk.END, "No hay alertas recientes")


class _CareTeamSection(_Section):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Equipo de Cuidado")
        self.tree = ttk.Treeview(self.frame, columns=("rol", "contacto"), show="headings")
        self.tree.heading("rol", text="Rol")
        self.tree.heading("contacto", text="Contacto")
        self.tree.pack(fill="both", expand=True)

    def update(self, payload: Dict[str, Any]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        members = payload.get("data", {}).get("members") or payload.get("members") or []
        for member in members:
            if isinstance(member, dict):
                role = member.get("role_label") or member.get("role")
                contact = member.get("email") or member.get("phone")
                self.tree.insert("", tk.END, values=(role, contact))
        if not members:
            self.tree.insert("", tk.END, values=("--", "No hay equipo asignado"))


class _CaregiversSection(_Section):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Cuidadores")
        self.listbox = tk.Listbox(self.frame, height=5)
        self.listbox.pack(fill="both", expand=True)

    def update(self, payload: Dict[str, Any]) -> None:
        self.listbox.delete(0, tk.END)
        caregivers = payload.get("data", {}).get("caregivers") or payload.get("caregivers") or []
        for caregiver in caregivers:
            if isinstance(caregiver, dict):
                name = caregiver.get("name") or caregiver.get("full_name")
                role = caregiver.get("relationship") or caregiver.get("role")
                self.listbox.insert(tk.END, f"{name} - {role}")
        if not caregivers:
            self.listbox.insert(tk.END, "No hay cuidadores registrados")


class _LocationsSection(_Section):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master, "Ubicaciones Recientes")
        ttk.Label(
            self.frame,
            text="Por limitaciones de Tkinter, mostramos la lista de ubicaciones en lugar del mapa embebido de JavaFX.",
            wraplength=720,
            foreground=Colors.TEXT_SECONDARY,
        ).pack(fill="x", pady=(0, 8))
        self.listbox = tk.Listbox(self.frame, height=6)
        self.listbox.pack(fill="both", expand=True)

    def update(self, payload: Dict[str, Any]) -> None:
        self.listbox.delete(0, tk.END)
        locations = payload.get("data", {}).get("locations") or payload.get("locations") or []
        for item in locations:
            if isinstance(item, dict):
                coord = item.get("latitude"), item.get("longitude")
                timestamp = item.get("recorded_at") or item.get("created_at")
                self.listbox.insert(tk.END, f"{timestamp} - {coord[0]}, {coord[1]}")
        if not locations:
            self.listbox.insert(tk.END, "No hay ubicaciones registradas")
