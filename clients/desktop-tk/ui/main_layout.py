"""Main layout for the Tkinter application."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial
from typing import Callable

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from ..api.gateway_client import ApiError
from ..controllers.auth_controller import AuthSession
from ..controllers.user_controller import UserController
from ..controllers.patient_controller import PatientController
from ..utils import config
from ..utils.notifications import show_snackbar


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Widget) -> None:
        super().__init__(master)
        canvas = tk.Canvas(self, background=config.BACKGROUND_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas = canvas


class MainLayout(ttk.Frame):
    def __init__(
        self,
        master: tk.Widget,
        *,
        session: AuthSession,
        on_logout: Callable[[], None],
        user_controller: UserController,
        patient_controller: PatientController,
    ) -> None:
        super().__init__(master)
        self.session = session
        self.on_logout = on_logout
        self.user_controller = user_controller
        self.patient_controller = patient_controller
        self.current_org_id: str | None = None
        self.current_view: str | None = None

        self.configure(style="Main.TFrame")
        self._setup_styles()
        self._build_layout()
        self._populate_sidebar()
        default_view = "dashboard" if self.session.account_type in {"user", "staff", "caregiver"} else "patient_dashboard"
        self.show_view(default_view)

    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.configure(
            "Main.TFrame",
            background=config.BACKGROUND_COLOR,
        )
        style.configure(
            "Sidebar.TFrame",
            background="#1f2933",
        )
        style.configure(
            "Sidebar.TButton",
            background="#1f2933",
            foreground="#e2e8f0",
            font=(config.FONT_FAMILY, 12),
            anchor="w",
            padding=12,
        )
        style.map(
            "Sidebar.TButton",
            background=[("active", "#2d3748"), ("selected", config.PRIMARY_COLOR)],
        )
        style.configure(
            "Card.TFrame",
            background=config.CARD_BACKGROUND,
            relief="flat",
        )
        style.configure("Card.TLabel", background=config.CARD_BACKGROUND, font=(config.FONT_FAMILY, 12))
        style.configure("Title.TLabel", background=config.BACKGROUND_COLOR, font=(config.FONT_FAMILY, 18, "bold"))

    def _build_layout(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # Top bar
        topbar = ttk.Frame(self, padding=(20, 12), style="Main.TFrame")
        topbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        topbar.columnconfigure(0, weight=1)

        title = ttk.Label(
            topbar,
            text="HeartGuard Command Center",
            font=(config.FONT_FAMILY, 20, "bold"),
        )
        title.grid(row=0, column=0, sticky="w")

        user_name = self.session.user.get("name") or self.session.user.get("email", "Usuario")
        self.user_label = ttk.Label(topbar, text=user_name, font=(config.FONT_FAMILY, 12))
        self.user_label.grid(row=0, column=1, padx=(20, 10))

        options_btn = ttk.Menubutton(topbar, text="⚙️")
        menu = tk.Menu(options_btn, tearoff=False)
        menu.add_command(label="Mi perfil", command=self._show_profile)
        menu.add_command(label="Mis invitaciones", command=self._show_invitations)
        menu.add_separator()
        menu.add_command(label="Cerrar sesión", command=self.on_logout)
        options_btn["menu"] = menu
        options_btn.grid(row=0, column=2)

        # Sidebar
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", padding=(0, 20))
        self.sidebar.grid(row=1, column=0, sticky="nsw")
        self.sidebar_buttons: dict[str, ttk.Button] = {}

        # Content area
        content_wrapper = ttk.Frame(self, style="Main.TFrame")
        content_wrapper.grid(row=1, column=1, sticky="nsew")
        content_wrapper.rowconfigure(0, weight=1)
        content_wrapper.columnconfigure(0, weight=1)

        self.content = ScrollableFrame(content_wrapper)
        self.content.grid(row=0, column=0, sticky="nsew")

    def _populate_sidebar(self) -> None:
        for widget in self.sidebar.winfo_children():
            widget.destroy()
        options = []
        if self.session.account_type in {"user", "staff", "caregiver"}:
            options = [
                ("Dashboard", "dashboard"),
                ("Pacientes", "patients"),
                ("Care-teams", "care_teams"),
                ("Dispositivos", "devices"),
                ("Alertas", "alerts"),
                ("Mapa", "map"),
            ]
        else:
            options = [
                ("Dashboard", "patient_dashboard"),
                ("Perfil", "patient_profile"),
                ("Alertas", "patient_alerts"),
                ("Dispositivos", "patient_devices"),
                ("Cuidadores", "patient_caregivers"),
                ("Lecturas", "patient_readings"),
                ("Equipo de cuidado", "patient_care_team"),
                ("Ubicaciones", "patient_locations"),
            ]
        for idx, (label, key) in enumerate(options):
            btn = ttk.Button(
                self.sidebar,
                text=label,
                style="Sidebar.TButton",
                command=partial(self.show_view, key),
            )
            btn.grid(row=idx, column=0, sticky="ew", padx=20, pady=5)
            self.sidebar_buttons[key] = btn

    def show_view(self, key: str) -> None:
        if self.current_view == key:
            return
        for child in self.content.scrollable_frame.winfo_children():
            child.destroy()
        self.current_view = key
        if self.session.account_type in {"user", "staff", "caregiver"}:
            self._render_staff_view(key)
        else:
            self._render_patient_view(key)

    # ------------------------------------------------------------------
    # Staff views
    # ------------------------------------------------------------------
    def _render_staff_view(self, key: str) -> None:
        if key == "dashboard":
            self._render_dashboard()
        elif key == "patients":
            self._render_patients()
        elif key == "alerts":
            self._render_alerts()
        elif key == "devices":
            self._render_devices()
        elif key == "map":
            self._render_map()
        elif key == "care_teams":
            self._render_care_teams()
        else:
            self._render_empty_state("Vista no disponible")

    def _render_dashboard(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Dashboard organizacional", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )

        memberships = self._api_call(self.user_controller.get_memberships, [])
        if not memberships:
            self._render_empty_state("No perteneces a ninguna organización")
            return
        org = memberships[0]
        org_id = org.get("org", {}).get("org_id") or org.get("org_id")
        self.current_org_id = org_id

        dashboard = self._api_call(lambda: self.user_controller.get_dashboard(org_id), {})
        metrics = self._api_call(lambda: self.user_controller.get_metrics(org_id), {})

        cards = ttk.Frame(frame, style="Main.TFrame")
        cards.grid(row=1, column=0, sticky="ew")
        for idx, (label, key, color) in enumerate(
            [
                ("Pacientes activos", "active_patients", config.PRIMARY_COLOR),
                ("Alertas abiertas", "open_alerts", "#e53e3e"),
                ("Dispositivos activos", "active_devices", config.ACCENT_COLOR),
                ("Caregivers activos", "active_caregivers", "#805ad5"),
            ]
        ):
            value = dashboard.get("data", {}).get(key, "-") if isinstance(dashboard, dict) else "-"
            card = ttk.Frame(cards, style="Card.TFrame", padding=20)
            card.grid(row=0, column=idx, padx=10, sticky="nsew")
            ttk.Label(card, text=label, style="Card.TLabel").pack(anchor="w")
            value_label = ttk.Label(
                card,
                text=str(value),
                style="Card.TLabel",
                font=(config.FONT_FAMILY, 24, "bold"),
                foreground=color,
            )
            value_label.pack(anchor="w")

        figure = Figure(figsize=(5, 2.5), dpi=100)
        chart = figure.add_subplot(111)
        if isinstance(metrics, dict):
            metric_values = metrics.get("data", {})
            if isinstance(metric_values, dict):
                names = list(metric_values.keys())
                values = [metric_values[name] for name in names]
                chart.bar(names, values, color=config.PRIMARY_COLOR)
                chart.set_ylabel("Valor")
                chart.set_xticklabels(names, rotation=25, ha="right")
        chart.set_title("Métricas organizacionales")
        chart.figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=2, column=0, pady=20, sticky="ew")

    def _render_patients(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Pacientes asignados", style="Title.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 16)
        )
        data = self._api_call(self.user_controller.get_patients, {})
        patients = data.get("data", {}).get("patients", []) if isinstance(data, dict) else []
        if not patients:
            self._render_empty_state("No tienes pacientes asignados")
            return
        for idx, patient in enumerate(patients):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=patient.get("name", "Paciente"), style="Card.TLabel", font=(config.FONT_FAMILY, 14, "bold")).pack(anchor="w")
            ttk.Label(card, text=patient.get("email", ""), style="Card.TLabel").pack(anchor="w")
            ttk.Label(card, text=f"Estado: {patient.get('status', 'Desconocido')}", style="Card.TLabel").pack(anchor="w")

    def _render_alerts(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Alertas recientes", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 16))
        data = self._api_call(self.user_controller.get_patients, {})
        patients = data.get("data", {}).get("patients", []) if isinstance(data, dict) else []
        if not patients:
            self._render_empty_state("Sin pacientes")
            return
        for idx, patient in enumerate(patients[:5]):
            alerts = self._api_call(lambda pid=patient.get("patient_id", ""): self.user_controller.get_patient_alerts(pid), {})
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=patient.get("name", "Paciente"), font=(config.FONT_FAMILY, 14, "bold"), style="Card.TLabel").pack(anchor="w")
            patient_alerts = alerts.get("data", {}).get("alerts", []) if isinstance(alerts, dict) else []
            if not patient_alerts:
                ttk.Label(card, text="Sin alertas", style="Card.TLabel").pack(anchor="w")
                continue
            for alert in patient_alerts:
                ttk.Label(
                    card,
                    text=f"• {alert.get('type', 'Alerta')} - {alert.get('status', 'Abierta')}",
                    style="Card.TLabel",
                ).pack(anchor="w")

    def _render_devices(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Dispositivos de los equipos", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        if not self.current_org_id:
            self._render_empty_state("Selecciona una organización")
            return
        teams = self._api_call(lambda: self.user_controller.get_care_team_patients(self.current_org_id), {})
        teams_list = teams.get("data", {}).get("teams", []) if isinstance(teams, dict) else []
        if not teams_list:
            self._render_empty_state("Sin equipos registrados")
            return
        for idx, team in enumerate(teams_list):
            team_id = team.get("team_id")
            devices = self._api_call(lambda tid=team_id: self.user_controller.get_care_team_devices(self.current_org_id, tid), {})
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=team.get("name", "Equipo"), style="Card.TLabel", font=(config.FONT_FAMILY, 14, "bold")).pack(anchor="w")
            device_list = devices.get("data", {}).get("devices", []) if isinstance(devices, dict) else []
            if not device_list:
                ttk.Label(card, text="Sin dispositivos", style="Card.TLabel").pack(anchor="w")
                continue
            for device in device_list:
                ttk.Label(
                    card,
                    text=f"• {device.get('device_type', 'Dispositivo')} - {device.get('status', 'Desconocido')}",
                    style="Card.TLabel",
                ).pack(anchor="w")

    def _render_map(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Mapa de ubicaciones", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 16))
        try:
            from tkhtmlview import HTMLLabel
            import folium
            from folium.plugins import MarkerCluster
        except Exception as exc:  # pragma: no cover - optional dependency runtime check
            self._render_empty_state(f"tkhtmlview/folium no disponibles: {exc}")
            return
        patients_locations = self._api_call(self.user_controller.get_patient_locations, {})
        care_team_locations = self._api_call(self.user_controller.get_care_team_locations, {})
        patient_points = patients_locations.get("data", {}).get("locations", []) if isinstance(patients_locations, dict) else []
        care_points = care_team_locations.get("data", {}).get("locations", []) if isinstance(care_team_locations, dict) else []
        if not patient_points and not care_points:
            self._render_empty_state("Sin datos de ubicación disponibles")
            return

        map_obj = folium.Map(location=[0, 0], zoom_start=2)
        patient_cluster = MarkerCluster(name="Pacientes").add_to(map_obj)
        for point in patient_points:
            coords = point.get("coordinates", {})
            lat = coords.get("lat") or coords.get("latitude")
            lon = coords.get("lon") or coords.get("longitude")
            if lat is None or lon is None:
                continue
            folium.Marker(
                [lat, lon],
                tooltip=point.get("name", "Paciente"),
                icon=folium.Icon(color="blue", icon="heartbeat", prefix="fa"),
            ).add_to(patient_cluster)
        care_cluster = MarkerCluster(name="Care-teams").add_to(map_obj)
        for team in care_points:
            coords = team.get("coordinates", {})
            lat = coords.get("lat") or coords.get("latitude")
            lon = coords.get("lon") or coords.get("longitude")
            if lat is None or lon is None:
                continue
            folium.Marker(
                [lat, lon],
                tooltip=team.get("name", "Equipo"),
                icon=folium.Icon(color="green", icon="plus", prefix="fa"),
            ).add_to(care_cluster)
        folium.LayerControl().add_to(map_obj)
        html = map_obj._repr_html_()
        label = HTMLLabel(frame, html=html)
        label.grid(row=1, column=0, sticky="nsew")

    def _render_care_teams(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Care-teams", style="Title.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 16))
        if not self.current_org_id:
            self._render_empty_state("Sin organización seleccionada")
            return
        teams = self._api_call(lambda: self.user_controller.get_care_team_patients(self.current_org_id), {})
        teams_list = teams.get("data", {}).get("teams", []) if isinstance(teams, dict) else []
        if not teams_list:
            self._render_empty_state("Sin equipos")
            return
        for idx, team in enumerate(teams_list):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=team.get("name", "Equipo"), font=(config.FONT_FAMILY, 14, "bold"), style="Card.TLabel").pack(anchor="w")
            members = team.get("members", [])
            for member in members:
                ttk.Label(
                    card,
                    text=f"• {member.get('name', 'Miembro')} ({member.get('role', 'Rol')})",
                    style="Card.TLabel",
                ).pack(anchor="w")

    # ------------------------------------------------------------------
    # Patient views
    # ------------------------------------------------------------------
    def _render_patient_view(self, key: str) -> None:
        mapping = {
            "patient_dashboard": self._render_patient_dashboard,
            "patient_profile": self._render_patient_profile,
            "patient_alerts": self._render_patient_alerts,
            "patient_devices": self._render_patient_devices,
            "patient_caregivers": self._render_patient_caregivers,
            "patient_readings": self._render_patient_readings,
            "patient_care_team": self._render_patient_care_team,
            "patient_locations": self._render_patient_locations,
        }
        render = mapping.get(key)
        if render:
            render()
        else:
            self._render_empty_state("Vista no disponible")

    def _render_patient_dashboard(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Dashboard del paciente", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        dashboard = self._api_call(self.patient_controller.get_dashboard, {})
        if not isinstance(dashboard, dict):
            self._render_empty_state("Sin datos disponibles")
            return
        cards = ttk.Frame(frame, style="Main.TFrame")
        cards.grid(row=1, column=0, sticky="ew")
        summary = dashboard.get("data", {})
        for idx, (label, key, color) in enumerate(
            [
                ("Lecturas recientes", "recent_readings", config.PRIMARY_COLOR),
                ("Alertas activas", "active_alerts", "#e53e3e"),
                ("Cuidadores", "caregivers", config.ACCENT_COLOR),
                ("Dispositivos", "devices", "#3182ce"),
            ]
        ):
            value = summary.get(key, "-") if isinstance(summary, dict) else "-"
            card = ttk.Frame(cards, style="Card.TFrame", padding=16)
            card.grid(row=0, column=idx, padx=10, sticky="nsew")
            ttk.Label(card, text=label, style="Card.TLabel").pack(anchor="w")
            ttk.Label(card, text=str(value), font=(config.FONT_FAMILY, 20, "bold"), foreground=color, style="Card.TLabel").pack(anchor="w")

    def _render_patient_profile(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Mi perfil", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        profile = self._api_call(self.patient_controller.get_profile, {})
        data = profile.get("data", {}) if isinstance(profile, dict) else {}
        if not data:
            self._render_empty_state("Sin datos de perfil")
            return
        card = ttk.Frame(frame, style="Card.TFrame", padding=16)
        card.grid(row=1, column=0, sticky="ew")
        for key, value in data.items():
            ttk.Label(card, text=f"{key}: {value}", style="Card.TLabel").pack(anchor="w")

    def _render_patient_alerts(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Mis alertas", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        alerts = self._api_call(self.patient_controller.get_alerts, {})
        data = alerts.get("data", {}).get("alerts", []) if isinstance(alerts, dict) else []
        if not data:
            self._render_empty_state("Sin alertas")
            return
        for idx, alert in enumerate(data):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=f"Tipo: {alert.get('type', 'N/A')}", style="Card.TLabel").pack(anchor="w")
            ttk.Label(card, text=f"Estado: {alert.get('status', 'Desconocido')}", style="Card.TLabel").pack(anchor="w")

    def _render_patient_devices(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Mis dispositivos", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        devices = self._api_call(self.patient_controller.get_devices, {})
        data = devices.get("data", {}).get("devices", []) if isinstance(devices, dict) else []
        if not data:
            self._render_empty_state("Sin dispositivos asignados")
            return
        for idx, device in enumerate(data):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=device.get("device_type", "Dispositivo"), style="Card.TLabel", font=(config.FONT_FAMILY, 14, "bold")).pack(anchor="w")
            ttk.Label(card, text=f"Estado: {device.get('status', 'Desconocido')}", style="Card.TLabel").pack(anchor="w")

    def _render_patient_caregivers(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Mi equipo de cuidadores", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        caregivers = self._api_call(self.patient_controller.get_caregivers, {})
        data = caregivers.get("data", {}).get("caregivers", []) if isinstance(caregivers, dict) else []
        if not data:
            self._render_empty_state("Sin cuidadores")
            return
        for idx, caregiver in enumerate(data):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=caregiver.get("name", "Cuidador"), style="Card.TLabel").pack(anchor="w")
            ttk.Label(card, text=caregiver.get("role", "Rol"), style="Card.TLabel").pack(anchor="w")

    def _render_patient_readings(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Lecturas recientes", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        readings = self._api_call(self.patient_controller.get_readings, {})
        data = readings.get("data", {}).get("readings", []) if isinstance(readings, dict) else []
        if not data:
            self._render_empty_state("Sin lecturas disponibles")
            return
        for idx, reading in enumerate(data):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            for key, value in reading.items():
                ttk.Label(card, text=f"{key}: {value}", style="Card.TLabel").pack(anchor="w")

    def _render_patient_care_team(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Mi equipo de cuidado", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        team = self._api_call(self.patient_controller.get_care_team, {})
        data = team.get("data", {}).get("care_team", []) if isinstance(team, dict) else []
        if not data:
            self._render_empty_state("Sin equipo de cuidado")
            return
        for idx, member in enumerate(data):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx + 1, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=member.get("name", "Miembro"), style="Card.TLabel").pack(anchor="w")
            ttk.Label(card, text=member.get("role", "Rol"), style="Card.TLabel").pack(anchor="w")

    def _render_patient_locations(self) -> None:
        frame = self.content.scrollable_frame
        ttk.Label(frame, text="Mis ubicaciones", style="Title.TLabel").grid(row=0, column=0, pady=(0, 16), sticky="w")
        latest = self._api_call(self.patient_controller.get_latest_location, {})
        locations = self._api_call(self.patient_controller.get_locations, {})
        latest_data = latest.get("data", {}) if isinstance(latest, dict) else {}
        history = locations.get("data", {}).get("locations", []) if isinstance(locations, dict) else []
        if latest_data:
            latest_card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            latest_card.grid(row=1, column=0, sticky="ew", pady=8)
            ttk.Label(latest_card, text="Última ubicación", font=(config.FONT_FAMILY, 14, "bold"), style="Card.TLabel").pack(anchor="w")
            for key, value in latest_data.items():
                ttk.Label(latest_card, text=f"{key}: {value}", style="Card.TLabel").pack(anchor="w")
        if history:
            for idx, point in enumerate(history):
                card = ttk.Frame(frame, style="Card.TFrame", padding=16)
                card.grid(row=idx + 2, column=0, sticky="ew", pady=8)
                ttk.Label(card, text=f"Registro #{idx + 1}", font=(config.FONT_FAMILY, 12, "bold"), style="Card.TLabel").pack(anchor="w")
                for key, value in point.items():
                    ttk.Label(card, text=f"{key}: {value}", style="Card.TLabel").pack(anchor="w")
        if not latest_data and not history:
            self._render_empty_state("Sin ubicaciones registradas")

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------
    def _render_profile_summary(self, frame: ttk.Frame) -> None:
        profile = self._api_call(self.user_controller.get_profile, {})
        data = profile.get("data", {}) if isinstance(profile, dict) else {}
        if not data:
            self._render_empty_state("Sin datos de perfil")
            return
        card = ttk.Frame(frame, style="Card.TFrame", padding=16)
        card.grid(row=0, column=0, sticky="ew")
        for key, value in data.items():
            ttk.Label(card, text=f"{key}: {value}", style="Card.TLabel").pack(anchor="w")

    def _show_profile(self) -> None:
        popup = tk.Toplevel(self)
        popup.title("Mi perfil")
        popup.resizable(False, False)
        frame = ttk.Frame(popup, padding=20, style="Main.TFrame")
        frame.grid(sticky="nsew")
        self._render_profile_summary(frame)

    def _show_invitations(self) -> None:
        if self.session.account_type not in {"user", "staff", "caregiver"}:
            show_snackbar(self, "Invitaciones solo para staff", bg="#c53030")
            return
        popup = tk.Toplevel(self)
        popup.title("Mis invitaciones")
        popup.resizable(False, False)
        frame = ttk.Frame(popup, padding=20, style="Main.TFrame")
        frame.grid(sticky="nsew")
        invitations = self._api_call(self.user_controller.get_invitations, [])
        if not invitations:
            ttk.Label(frame, text="Sin invitaciones pendientes", style="Title.TLabel").grid(row=0, column=0)
            return
        for idx, invitation in enumerate(invitations):
            card = ttk.Frame(frame, style="Card.TFrame", padding=16)
            card.grid(row=idx, column=0, sticky="ew", pady=8)
            ttk.Label(card, text=invitation.get("org_name", "Organización"), style="Card.TLabel", font=(config.FONT_FAMILY, 12, "bold")).pack(anchor="w")
            ttk.Label(card, text=invitation.get("status", "Pendiente"), style="Card.TLabel").pack(anchor="w")
            actions = ttk.Frame(card, style="Card.TFrame")
            actions.pack(anchor="e", pady=(8, 0))
            ttk.Button(
                actions,
                text="Aceptar",
                command=lambda inv=invitation: self._handle_invitation(inv.get("invitation_id"), True),
            ).pack(side="left", padx=4)
            ttk.Button(
                actions,
                text="Rechazar",
                command=lambda inv=invitation: self._handle_invitation(inv.get("invitation_id"), False),
            ).pack(side="left", padx=4)

    def _handle_invitation(self, invitation_id: str, accept: bool) -> None:
        try:
            if accept:
                self.user_controller.accept_invitation(invitation_id)
                show_snackbar(self, "Invitación aceptada", bg=config.ACCENT_COLOR)
            else:
                self.user_controller.reject_invitation(invitation_id)
                show_snackbar(self, "Invitación rechazada", bg="#c53030")
            self.show_view("dashboard")
        except Exception as exc:  # pragma: no cover - runtime network errors
            messagebox.showerror("Error", str(exc))

    def _api_call(self, func, default):
        try:
            return func()
        except ApiError as exc:
            show_snackbar(self, f"Error al obtener datos: {exc}", bg="#c53030")
            return default

    def _render_empty_state(self, message: str) -> None:
        frame = self.content.scrollable_frame
        for child in frame.winfo_children():
            child.destroy()
        container = ttk.Frame(frame, style="Main.TFrame", padding=40)
        container.grid(row=0, column=0, sticky="nsew")
        ttk.Label(container, text="ℹ️", font=(config.FONT_FAMILY, 48)).pack()
        ttk.Label(container, text=message, font=(config.FONT_FAMILY, 14)).pack(pady=10)
