"""Dashboard principal para personal clínico - Diseño moderno HealthTech."""

from __future__ import annotations

import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Iterable, List, Optional

from ..api import ApiError
from ..models import LoginResponse
from .base import BaseView
from .theme import ModernTheme, COLORS, FONTS, SPACING, SIZES

try:  # pragma: no cover - optional dependency
    from tkintermapview import TkinterMapView
except ImportError:  # pragma: no cover - optional dependency
    TkinterMapView = None  # type: ignore


class UserDashboardView(BaseView):
    """Dashboard moderno para personal clínico con diseño HealthTech."""

    def __init__(self, master: tk.Misc, controller, login: LoginResponse, **kwargs):
        super().__init__(master, controller, **kwargs)
        self.login = login
        self.token = login.access_token
        self.memberships: List[Dict[str, str]] = []
        self.selected_org: Optional[Dict[str, str]] = None

        # Variables de estado
        self.user_name_var = tk.StringVar(value=login.full_name)
        self.role_var = tk.StringVar(value="")
        self.org_var = tk.StringVar(value="Selecciona una organización")
        self.status_var = tk.StringVar(value="Cargando...")

        # Variables de métricas
        self.patients_var = tk.StringVar(value="0")
        self.alerts_var = tk.StringVar(value="0")
        self.caregivers_var = tk.StringVar(value="0")
        self.teams_var = tk.StringVar(value="0")
        self.extra_alerts_var = tk.StringVar(value="0")
        self.avg_alerts_var = tk.StringVar(value="0.0")
        self.map_status_var = tk.StringVar(value="Mapa no disponible")

        # Widgets principales
        self.org_combo: ttk.Combobox | None = None
        self.alerts_tree: ttk.Treeview | None = None
        self.team_tree: ttk.Treeview | None = None
        self.patients_tree: ttk.Treeview | None = None
        self.map_widget = None
        self._map_markers: List[Any] = []

        self.configure(bg=COLORS["bg_secondary"])
        self._build()
        self._load_profile()

    # ------------------------------------------------------------------
    # UI Construction - Modern Design
    # ------------------------------------------------------------------
    def _build(self) -> None:
        """Construye el dashboard con diseño moderno."""
        # Crear contenedor principal con scroll
        main_container = tk.Frame(self, bg=COLORS["bg_secondary"])
        main_container.pack(fill="both", expand=True)

        # Canvas para scroll
        canvas = tk.Canvas(main_container, bg=COLORS["bg_secondary"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS["bg_secondary"])

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mouse wheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Construir secciones
        self._build_header(scrollable_frame)
        self._build_metrics(scrollable_frame)
        self._build_map_section(scrollable_frame)
        self._build_tabs(scrollable_frame)
        self._build_footer(scrollable_frame)

    def _build_header(self, parent: tk.Frame) -> None:
        """Header moderno con información del usuario y selector de organización."""
        header_card = ModernTheme.create_card(parent)
        header_card.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        # Row 1: Logo y usuario
        top_row = tk.Frame(header_card, bg=COLORS["bg_primary"])
        top_row.pack(fill="x", pady=(0, SPACING["md"]))

        # Logo y título
        left_section = tk.Frame(top_row, bg=COLORS["bg_primary"])
        left_section.pack(side="left", fill="y")

        logo_label = tk.Label(
            left_section,
            text="❤️",
            font=("Segoe UI", 32),
            bg=COLORS["bg_primary"],
            fg=COLORS["primary"],
        )
        logo_label.pack(side="left", padx=(0, SPACING["md"]))

        title_section = tk.Frame(left_section, bg=COLORS["bg_primary"])
        title_section.pack(side="left")

        tk.Label(
            title_section,
            text="HeartGuard",
            font=FONTS["heading_1"],
            bg=COLORS["bg_primary"],
            fg=COLORS["primary"],
        ).pack(anchor="w")

        tk.Label(
            title_section,
            text="Sistema de Monitoreo Cardíaco",
            font=FONTS["caption"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Información del usuario
        user_section = tk.Frame(top_row, bg=COLORS["bg_primary"])
        user_section.pack(side="right")

        tk.Label(
            user_section,
            textvariable=self.user_name_var,
            font=FONTS["body_large"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
        ).pack(anchor="e")

        tk.Label(
            user_section,
            textvariable=self.role_var,
            font=FONTS["caption"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="e")

        # Row 2: Selector de organización y botones
        bottom_row = tk.Frame(header_card, bg=COLORS["bg_primary"])
        bottom_row.pack(fill="x")

        # Selector de organización
        org_frame = tk.Frame(bottom_row, bg=COLORS["bg_primary"])
        org_frame.pack(side="left", fill="x", expand=True)

        tk.Label(
            org_frame,
            text="🏥 Organización:",
            font=FONTS["label"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, SPACING["sm"]))

        combo = ttk.Combobox(org_frame, state="readonly", width=40, font=FONTS["body"])
        combo.pack(side="left", fill="x", expand=True)
        combo.bind("<<ComboboxSelected>>", lambda _e: self._on_org_selected())
        self.org_combo = combo

        # Botones
        buttons_frame = tk.Frame(bottom_row, bg=COLORS["bg_primary"])
        buttons_frame.pack(side="right", padx=(SPACING["md"], 0))

        refresh_btn = ModernTheme.create_button(
            buttons_frame, "🔄 Actualizar", self._refresh_org, style="secondary"
        )
        refresh_btn.pack(side="left", padx=(0, SPACING["sm"]))

        logout_btn = ModernTheme.create_button(
            buttons_frame, "🚪 Cerrar sesión", self.controller.logout, style="danger"
        )
        logout_btn.pack(side="left")

    def _build_metrics(self, parent: tk.Frame) -> None:
        """Grid de métricas con tarjetas modernas."""
        metrics_container = tk.Frame(parent, bg=COLORS["bg_secondary"])
        metrics_container.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # Grid 2x2 de métricas principales
        metrics = [
            ("👥", "Pacientes", self.patients_var, COLORS["primary"]),
            ("👨‍⚕️", "Equipos", self.teams_var, COLORS["info"]),
            ("🩺", "Cuidadores", self.caregivers_var, COLORS["success"]),
            ("⚠️", "Alertas Activas", self.alerts_var, COLORS["danger"]),
        ]

        for idx, (icon, label, var, color) in enumerate(metrics):
            row = idx // 2
            col = idx % 2

            metric_card = ModernTheme.create_metric_card(
                metrics_container, icon, label, var, color
            )
            metric_card.grid(
                row=row,
                column=col,
                sticky="nsew",
                padx=SPACING["sm"],
                pady=SPACING["sm"],
            )

        # Configurar peso de columnas para distribución uniforme
        metrics_container.columnconfigure(0, weight=1)
        metrics_container.columnconfigure(1, weight=1)

        # Métricas adicionales (alertas 7 días y promedio)
        extra_metrics = ModernTheme.create_card(parent)
        extra_metrics.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        extra_frame = tk.Frame(extra_metrics, bg=COLORS["bg_primary"])
        extra_frame.pack(fill="x")

        # Alertas últimos 7 días
        alerts_7d_frame = tk.Frame(extra_frame, bg=COLORS["bg_primary"])
        alerts_7d_frame.pack(side="left", expand=True, padx=SPACING["md"], pady=SPACING["sm"])

        tk.Label(
            alerts_7d_frame,
            text="📊 Alertas (7 días)",
            font=FONTS["label"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, SPACING["md"]))

        tk.Label(
            alerts_7d_frame,
            textvariable=self.extra_alerts_var,
            font=FONTS["heading_3"],
            bg=COLORS["bg_primary"],
            fg=COLORS["warning"],
        ).pack(side="left")

        # Promedio de alertas por paciente
        avg_frame = tk.Frame(extra_frame, bg=COLORS["bg_primary"])
        avg_frame.pack(side="left", expand=True, padx=SPACING["md"], pady=SPACING["sm"])

        tk.Label(
            avg_frame,
            text="📈 Promedio alertas/paciente",
            font=FONTS["label"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, SPACING["md"]))

        tk.Label(
            avg_frame,
            textvariable=self.avg_alerts_var,
            font=FONTS["heading_3"],
            bg=COLORS["bg_primary"],
            fg=COLORS["info"],
        ).pack(side="left")

    def _build_map_section(self, parent: tk.Frame) -> None:
        """Sección del mapa con diseño moderno."""
        map_card = ModernTheme.create_card(parent)
        map_card.pack(fill="both", expand=False, padx=SPACING["lg"], pady=SPACING["md"])

        # Header del mapa
        map_header = tk.Frame(map_card, bg=COLORS["bg_primary"])
        map_header.pack(fill="x", pady=(0, SPACING["md"]))

        tk.Label(
            map_header,
            text="🗺️ Mapa de Ubicaciones",
            font=FONTS["heading_3"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        tk.Label(
            map_header,
            textvariable=self.map_status_var,
            font=FONTS["caption"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(SPACING["md"], 0))

        refresh_map_btn = ModernTheme.create_button(
            map_header, "🔄", self._refresh_map, style="secondary"
        )
        refresh_map_btn.pack(side="right")

        # Contenedor del mapa
        if TkinterMapView is None:
            message_frame = tk.Frame(map_card, bg=COLORS["warning_bg"], relief="solid", bd=1)
            message_frame.pack(fill="x", pady=SPACING["md"])

            tk.Label(
                message_frame,
                text="⚠️ Mapa no disponible",
                font=FONTS["body_large"],
                bg=COLORS["warning_bg"],
                fg=COLORS["warning"],
            ).pack(pady=SPACING["sm"])

            tk.Label(
                message_frame,
                text="Instala tkintermapview para visualizar ubicaciones:\npip install tkintermapview",
                font=FONTS["caption"],
                bg=COLORS["warning_bg"],
                fg=COLORS["text_secondary"],
                justify="center",
            ).pack(pady=SPACING["sm"])

            self.map_status_var.set("Mapa no disponible")
            return

        # Widget del mapa
        map_container = tk.Frame(map_card, bg=COLORS["bg_primary"])
        map_container.pack(fill="both", expand=True)

        widget = TkinterMapView(map_container, width=1000, height=450, corner_radius=SIZES["border_radius"])
        widget.pack(fill="both", expand=True)
        widget.set_zoom(4)
        widget.set_position(19.4326, -99.1332)  # México City default
        self.map_widget = widget
        self.map_status_var.set("Sin ubicaciones")

    def _build_tabs(self, parent: tk.Frame) -> None:
        """Tabs con tablas de datos."""
        tabs_card = ModernTheme.create_card(parent)
        tabs_card.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["md"])

        notebook = ttk.Notebook(tabs_card)
        notebook.pack(fill="both", expand=True)

        # Tab de Alertas
        alerts_tab = tk.Frame(notebook, bg=COLORS["bg_primary"])
        notebook.add(alerts_tab, text="⚠️  Alertas")

        self.alerts_tree = self._create_modern_treeview(
            alerts_tab,
            columns=("nivel", "paciente", "tipo", "fecha"),
            headings={
                "nivel": "Nivel",
                "paciente": "Paciente",
                "tipo": "Tipo",
                "fecha": "Fecha",
            },
        )

        # Tab de Equipos
        teams_tab = tk.Frame(notebook, bg=COLORS["bg_primary"])
        notebook.add(teams_tab, text="👨‍⚕️  Equipos")

        self.team_tree = self._create_modern_treeview(
            teams_tab,
            columns=("nombre", "rol", "miembros"),
            headings={
                "nombre": "Equipo",
                "rol": "Mi rol",
                "miembros": "Integrantes",
            },
        )

        # Tab de Pacientes
        patients_tab = tk.Frame(notebook, bg=COLORS["bg_primary"])
        notebook.add(patients_tab, text="👥  Pacientes")

        self.patients_tree = self._create_modern_treeview(
            patients_tab,
            columns=("paciente", "equipo", "riesgo"),
            headings={
                "paciente": "Paciente",
                "equipo": "Equipo",
                "riesgo": "Riesgo",
            },
        )

    def _create_modern_treeview(
        self, parent: tk.Frame, columns: tuple, headings: Dict[str, str]
    ) -> ttk.Treeview:
        """Crea un Treeview con estilo moderno."""
        tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=15,  # Aumentado de 10 a 15 para pantalla completa
        )

        # Configurar encabezados
        for col, heading in headings.items():
            tree.heading(col, text=heading, anchor="w")
            tree.column(col, anchor="w", width=200, minwidth=150)  # Aumentado ancho

        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True, padx=SPACING["sm"], pady=SPACING["sm"])
        scrollbar.pack(side="right", fill="y", pady=SPACING["sm"])

        return tree

    def _build_footer(self, parent: tk.Frame) -> None:
        """Footer con estado y acciones."""
        footer = tk.Frame(parent, bg=COLORS["bg_secondary"])
        footer.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        status_label = tk.Label(
            footer,
            textvariable=self.status_var,
            font=FONTS["caption"],
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
        )
        status_label.pack(side="left")

    # ------------------------------------------------------------------
    # Data Loading Methods
    # ------------------------------------------------------------------
    def _load_profile(self) -> None:
        """Carga el perfil del usuario y sus membresías."""
        if not self.token:
            self.status_var.set("⚠️ Token no disponible")
            return

        self.status_var.set("⏳ Cargando perfil...")

        def task() -> Dict[str, Any]:
            api = self.controller.api
            return {
                "profile": api.get_current_user_profile(token=self.token),
                "memberships": api.get_current_user_memberships(token=self.token),
            }

        def handle_success(data: Dict[str, Any]) -> None:
            self.status_var.set("✓ Perfil cargado")
            self._apply_profile(data.get("profile", {}))
            self._apply_memberships(data.get("memberships", {}))
            if self.memberships:
                self.org_combo.set(self.memberships[0]["label"])
                self.selected_org = self.memberships[0]
                self._refresh_org()

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self.status_var.set(f"❌ {exc.message}")
            else:
                self.status_var.set(f"❌ {str(exc)}")
            if self.map_widget is not None:
                self.map_status_var.set("Error al cargar mapa")

        self.run_async(task, on_success=handle_success, on_error=handle_error)

    def _apply_profile(self, profile: Dict[str, Any]) -> None:
        """Aplica los datos del perfil a la UI."""
        data = _dict_from(profile, "data") or profile
        role_list = data.get("roles", [])
        if role_list:
            self.role_var.set(f"🎭 {', '.join(r.get('name', '') for r in role_list)}")
        else:
            self.role_var.set("👤 Usuario")

    def _apply_memberships(self, memberships: Dict[str, Any]) -> None:
        """Aplica las membresías a la UI."""
        data = _dict_from(memberships, "data") or memberships
        items = data.get("items", []) if isinstance(data, dict) else []
        self.memberships = [
            {"id": m["organization_id"], "label": m["organization_name"]}
            for m in items
            if "organization_id" in m and "organization_name" in m
        ]
        if self.org_combo:
            self.org_combo["values"] = [m["label"] for m in self.memberships]

    def _on_org_selected(self) -> None:
        """Maneja la selección de una organización."""
        if not self.org_combo:
            return
        label = self.org_combo.get()
        for m in self.memberships:
            if m["label"] == label:
                self.selected_org = m
                self._refresh_org()
                break

    def _refresh_org(self) -> None:
        """Recarga todos los datos de la organización seleccionada."""
        if not self.selected_org:
            self.status_var.set("⚠️ Selecciona una organización")
            return

        org_id = self.selected_org["id"]
        self.status_var.set("⏳ Cargando datos...")

        def task() -> Dict[str, Any]:
            api = self.controller.api
            return {
                "dashboard": api.get_organization_dashboard(org_id=org_id, token=self.token),
                "metrics": api.get_organization_metrics(org_id=org_id, token=self.token),
                "teams": api.get_organization_care_teams(org_id=org_id, token=self.token),
            }

        def handle_success(data: Dict[str, Any]) -> None:
            self.status_var.set("✓ Datos actualizados")
            self._render_metrics(data.get("dashboard", {}), data.get("metrics", {}))
            self._render_care_teams(data.get("teams", {}))
            self._render_alerts(data.get("dashboard", {}))
            self._refresh_map()

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self.status_var.set(f"❌ {exc.message}")
            else:
                self.status_var.set(f"❌ {str(exc)}")

        self.run_async(task, on_success=handle_success, on_error=handle_error)

    def _render_metrics(self, dashboard: Dict[str, Any], metrics: Dict[str, Any]) -> None:
        """Renderiza las métricas en las tarjetas."""
        dashboard_data = _dict_from(dashboard, "data") or dashboard
        overview = dashboard_data.get("overview", {}) if isinstance(dashboard_data, dict) else {}
        
        metrics_data = _dict_from(metrics, "data") or metrics
        metrics_obj = metrics_data.get("metrics", {}) if isinstance(metrics_data, dict) else {}

        # Debug: Imprimir datos recibidos
        print(f"DEBUG user_dashboard - overview: {overview}")
        print(f"DEBUG user_dashboard - metrics_obj: {metrics_obj}")

        self.patients_var.set(str(overview.get("total_patients", 0)))
        self.alerts_var.set(str(overview.get("open_alerts", 0)))
        self.caregivers_var.set(str(overview.get("total_caregivers", 0)))
        self.teams_var.set(str(overview.get("total_care_teams", 0)))

        alerts_7d = metrics_obj.get("alerts_last_7_days", 0)
        avg_alerts = metrics_obj.get("avg_alerts_per_patient", 0.0)
        self.extra_alerts_var.set(str(alerts_7d))
        self.avg_alerts_var.set(f"{avg_alerts:.2f}")

    def _render_care_teams(self, teams: Dict[str, Any]) -> None:
        """Renderiza los equipos de cuidado."""
        if not self.team_tree:
            return

        for row in self.team_tree.get_children():
            self.team_tree.delete(row)

        data = _dict_from(teams, "data") or teams
        items = data.get("items", []) if isinstance(data, dict) else []

        for team in items:
            name = team.get("name", "—")
            role = team.get("my_role", "—")
            members_count = team.get("member_count", 0)
            self.team_tree.insert("", "end", values=(name, role, members_count))

        # Cargar pacientes de los equipos
        self._load_team_patients(items)

    def _load_team_patients(self, teams: List[Dict[str, Any]]) -> None:
        """Carga los pacientes de todos los equipos."""
        if not self.selected_org or not self.patients_tree:
            return

        for row in self.patients_tree.get_children():
            self.patients_tree.delete(row)

        org_id = self.selected_org["id"]

        def task() -> List[Dict[str, Any]]:
            api = self.controller.api
            all_patients = []
            for team in teams:
                team_id = team.get("id")
                if team_id:
                    resp = api.get_care_team_patients(
                        org_id=org_id, care_team_id=team_id, token=self.token
                    )
                    patients_data = _dict_from(resp, "data") or resp
                    patients = patients_data.get("patients", [])
                    for patient in patients:
                        patient["team_name"] = team.get("name", "—")
                    all_patients.extend(patients)
            return all_patients

        def handle_success(patients: List[Dict[str, Any]]) -> None:
            for patient in patients:
                full_name = patient.get("full_name", "—")
                team_name = patient.get("team_name", "—")
                risk = patient.get("risk_level", {})
                if isinstance(risk, dict):
                    risk_label = risk.get("label", "—")
                else:
                    risk_label = str(risk) if risk else "—"
                self.patients_tree.insert("", "end", values=(full_name, team_name, risk_label))

        def handle_error(exc: Exception) -> None:
            pass  # Silent fail for patients loading

        self.run_async(task, on_success=handle_success, on_error=handle_error)

    def _render_alerts(self, dashboard: Dict[str, Any]) -> None:
        """Renderiza las alertas en la tabla."""
        if not self.alerts_tree:
            return

        for row in self.alerts_tree.get_children():
            self.alerts_tree.delete(row)

        dashboard_data = _dict_from(dashboard, "data") or dashboard
        recent = dashboard_data.get("recent_alerts", [])

        for alert in recent:
            nivel = alert.get("severity", "—")
            patient_data = alert.get("patient", {})
            patient_name = patient_data.get("full_name", "—") if isinstance(patient_data, dict) else "—"
            tipo = alert.get("alert_type", "—")
            timestamp = alert.get("timestamp", "")
            fecha = _format_datetime(timestamp) if timestamp else "—"
            self.alerts_tree.insert("", "end", values=(nivel, patient_name, tipo, fecha))

    def _refresh_map(self) -> None:
        """Actualiza el mapa con ubicaciones."""
        if TkinterMapView is None or self.map_widget is None:
            self.map_status_var.set("Mapa no disponible")
            return
        if not self.selected_org:
            self.map_status_var.set("Selecciona una organización")
            return

        org_id = self.selected_org["id"]
        self.map_status_var.set("Actualizando...")
        self._clear_map_markers()

        def task() -> tuple[Dict[str, Any], Dict[str, Any]]:
            api = self.controller.api
            care_team = api.get_care_team_locations(org_id=org_id, token=self.token)
            caregiver = api.get_caregiver_patient_locations(org_id=org_id, token=self.token)
            return care_team, caregiver

        def handle_success(result: tuple[Dict[str, Any], Dict[str, Any]]) -> None:
            care_team_payload, caregiver_payload = result
            self._render_map(care_team_payload, caregiver_payload)

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self.map_status_var.set(f"Error: {exc.message}")
            else:
                self.map_status_var.set("Error al cargar mapa")

        self.run_async(task, on_success=handle_success, on_error=handle_error)

    def _render_map(self, care_team_payload: Dict[str, Any], caregiver_payload: Dict[str, Any]) -> None:
        """Renderiza las ubicaciones en el mapa."""
        if TkinterMapView is None or self.map_widget is None:
            return

        care_team_data = _dict_from(care_team_payload, "data") or (
            care_team_payload if isinstance(care_team_payload, dict) else {}
        )
        caregiver_data = _dict_from(caregiver_payload, "data") or (
            caregiver_payload if isinstance(caregiver_payload, dict) else {}
        )

        ct_items = care_team_data.get("items", []) if isinstance(care_team_data, dict) else []
        cg_items = caregiver_data.get("items", []) if isinstance(caregiver_data, dict) else []

        all_locs = []
        for item in ct_items:
            loc = item.get("location")
            if loc and isinstance(loc, dict):
                lat, lon = loc.get("latitude"), loc.get("longitude")
                if lat is not None and lon is not None:
                    all_locs.append((lat, lon, item.get("name", "CT")))
        for item in cg_items:
            loc = item.get("location")
            if loc and isinstance(loc, dict):
                lat, lon = loc.get("latitude"), loc.get("longitude")
                if lat is not None and lon is not None:
                    all_locs.append((lat, lon, item.get("name", "CG")))

        if not all_locs:
            self.map_status_var.set("Sin ubicaciones")
            return

        self._clear_map_markers()
        for lat, lon, name in all_locs:
            marker = self.map_widget.set_marker(lat, lon, text=name)
            self._map_markers.append(marker)

        if len(all_locs) > 1:
            lats = [loc[0] for loc in all_locs]
            lons = [loc[1] for loc in all_locs]
            min_lat, max_lat = min(lats), max(lats)
            min_lon, max_lon = min(lons), max(lons)
            top_left = (max_lat, min_lon)
            bottom_right = (min_lat, max_lon)
            self.map_widget.fit_bounding_box(top_left, bottom_right)
        else:
            lat, lon, _ = all_locs[0]
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(12)

        self.map_status_var.set(f"{len(all_locs)} ubicaciones")

    def _clear_map_markers(self) -> None:
        """Limpia los marcadores del mapa."""
        if self.map_widget is None:
            return
        for marker in self._map_markers:
            if hasattr(marker, "delete"):
                marker.delete()
        self._map_markers.clear()


# ------------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------------
def _dict_from(payload: Any, key: str) -> Optional[Dict[str, Any]]:
    """Extrae un diccionario de un payload."""
    if not isinstance(payload, dict):
        return None
    value = payload.get(key)
    return value if isinstance(value, dict) else None


def _format_datetime(iso_str: str) -> str:
    """Formatea una fecha ISO a formato legible."""
    try:
        parsed = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return iso_str
