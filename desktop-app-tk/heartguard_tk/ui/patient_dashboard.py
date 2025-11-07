"""Dashboard para pacientes - Diseño moderno HealthTech."""

from __future__ import annotations

import datetime as dt
import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, List, Optional

from ..api import ApiError
from ..models import LoginResponse
from .base import BaseView
from .theme import ModernTheme, COLORS, FONTS, SPACING, SIZES

try:  # pragma: no cover - optional dependency
    from tkintermapview import TkinterMapView
except ImportError:  # pragma: no cover - optional dependency
    TkinterMapView = None  # type: ignore


class PatientDashboardView(BaseView):
    """Dashboard moderno para pacientes con diseño HealthTech."""

    def __init__(self, master: tk.Misc, controller, login: LoginResponse, **kwargs):
        super().__init__(master, controller, **kwargs)
        self.login = login
        self.token = login.access_token

        # Variables de perfil
        self.name_var = tk.StringVar(value=login.full_name)
        self.email_var = tk.StringVar(value=login.email or "")
        self.org_var = tk.StringVar(value="")
        self.birthdate_var = tk.StringVar(value="")
        self.risk_var = tk.StringVar(value="")
        self.risk_color = COLORS["text_secondary"]

        # Variables de métricas
        self.total_alerts_var = tk.StringVar(value="0")
        self.pending_alerts_var = tk.StringVar(value="0")
        self.devices_var = tk.StringVar(value="0")
        self.last_reading_var = tk.StringVar(value="N/A")
        self.status_var = tk.StringVar(value="Listo")
        self.map_status_var = tk.StringVar(value="Mapa listo")

        # Widgets principales
        self.alerts_tree: ttk.Treeview | None = None
        self.care_team_tree: ttk.Treeview | None = None
        self.caregivers_tree: ttk.Treeview | None = None
        self.devices_tree: ttk.Treeview | None = None
        self.map_widget = None
        self._map_markers: List[Any] = []

        self.configure(bg=COLORS["bg_secondary"])
        self._build()
        self.refresh()

    # ------------------------------------------------------------------
    # UI Construction - Modern Design
    # ------------------------------------------------------------------
    def _build(self) -> None:
        """Construye el dashboard con diseño moderno."""
        # Contenedor principal con scroll
        main_container = tk.Frame(self, bg=COLORS["bg_secondary"])
        main_container.pack(fill="both", expand=True)

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
        self._build_profile(scrollable_frame)
        self._build_metrics(scrollable_frame)
        self._build_tabs(scrollable_frame)
        self._build_map(scrollable_frame)
        self._build_footer(scrollable_frame)

    def _build_header(self, parent: tk.Frame) -> None:
        """Header moderno con logo y botón de logout."""
        header_card = ModernTheme.create_card(parent)
        header_card.pack(fill="x", padx=SPACING["lg"], pady=(SPACING["lg"], SPACING["md"]))

        header_content = tk.Frame(header_card, bg=COLORS["bg_primary"])
        header_content.pack(fill="x")

        # Logo y título
        left_section = tk.Frame(header_content, bg=COLORS["bg_primary"])
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
            text="Mi Portal de Salud",
            font=FONTS["heading_1"],
            bg=COLORS["bg_primary"],
            fg=COLORS["primary"],
        ).pack(anchor="w")

        tk.Label(
            title_section,
            text="HeartGuard - Monitoreo Cardíaco",
            font=FONTS["caption"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(anchor="w")

        # Botones
        buttons_frame = tk.Frame(header_content, bg=COLORS["bg_primary"])
        buttons_frame.pack(side="right")

        refresh_btn = ModernTheme.create_button(
            buttons_frame, "🔄 Actualizar", self.refresh, style="secondary"
        )
        refresh_btn.pack(side="left", padx=(0, SPACING["sm"]))

        logout_btn = ModernTheme.create_button(
            buttons_frame, "🚪 Cerrar sesión", self.controller.logout, style="danger"
        )
        logout_btn.pack(side="left")

    def _build_profile(self, parent: tk.Frame) -> None:
        """Perfil del paciente con información clave."""
        profile_card = ModernTheme.create_card(parent)
        profile_card.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        # Header del perfil
        profile_header = tk.Frame(profile_card, bg=COLORS["bg_primary"])
        profile_header.pack(fill="x", pady=(0, SPACING["md"]))

        tk.Label(
            profile_header,
            text="👤 Mi Perfil",
            font=FONTS["heading_3"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
        ).pack(side="left")

        # Contenido del perfil en grid
        profile_content = tk.Frame(profile_card, bg=COLORS["bg_primary"])
        profile_content.pack(fill="x")

        # Nombre completo
        self._create_profile_row(profile_content, "Nombre:", self.name_var, 0)
        
        # Email
        self._create_profile_row(profile_content, "Email:", self.email_var, 1)
        
        # Organización
        self._create_profile_row(profile_content, "Organización:", self.org_var, 2)
        
        # Fecha de nacimiento
        self._create_profile_row(profile_content, "Fecha de nacimiento:", self.birthdate_var, 3)
        
        # Nivel de riesgo (destacado)
        risk_frame = tk.Frame(profile_content, bg=COLORS["bg_primary"])
        risk_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=SPACING["sm"])

        tk.Label(
            risk_frame,
            text="⚠️ Nivel de Riesgo:",
            font=FONTS["body_large"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
        ).pack(side="left", padx=(0, SPACING["md"]))

        self.risk_label = tk.Label(
            risk_frame,
            textvariable=self.risk_var,
            font=FONTS["heading_3"],
            bg=COLORS["bg_primary"],
            fg=self.risk_color,
        )
        self.risk_label.pack(side="left")

    def _create_profile_row(self, parent: tk.Frame, label: str, var: tk.StringVar, row: int) -> None:
        """Crea una fila de información del perfil."""
        tk.Label(
            parent,
            text=label,
            font=FONTS["label"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_secondary"],
            anchor="e",
        ).grid(row=row, column=0, sticky="e", padx=(0, SPACING["md"]), pady=SPACING["xs"])

        tk.Label(
            parent,
            textvariable=var,
            font=FONTS["body"],
            bg=COLORS["bg_primary"],
            fg=COLORS["text_primary"],
            anchor="w",
        ).grid(row=row, column=1, sticky="w", pady=SPACING["xs"])

    def _build_metrics(self, parent: tk.Frame) -> None:
        """Métricas del paciente en tarjetas."""
        metrics_container = tk.Frame(parent, bg=COLORS["bg_secondary"])
        metrics_container.pack(fill="x", padx=SPACING["lg"], pady=SPACING["md"])

        metrics = [
            ("⚠️", "Total Alertas", self.total_alerts_var, COLORS["warning"]),
            ("🔔", "Alertas Pendientes", self.pending_alerts_var, COLORS["danger"]),
            ("📱", "Dispositivos", self.devices_var, COLORS["info"]),
            ("📊", "Última Lectura", self.last_reading_var, COLORS["success"]),
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

        metrics_container.columnconfigure(0, weight=1)
        metrics_container.columnconfigure(1, weight=1)

    def _build_tabs(self, parent: tk.Frame) -> None:
        """Tabs con información detallada."""
        tabs_card = ModernTheme.create_card(parent)
        tabs_card.pack(fill="both", expand=True, padx=SPACING["lg"], pady=SPACING["md"])

        notebook = ttk.Notebook(tabs_card)
        notebook.pack(fill="both", expand=True)

        # Tab de Alertas
        alerts_tab = tk.Frame(notebook, bg=COLORS["bg_primary"])
        notebook.add(alerts_tab, text="⚠️  Mis Alertas")

        self.alerts_tree = self._create_modern_treeview(
            alerts_tab,
            columns=("nivel", "tipo", "fecha", "estado"),
            headings={
                "nivel": "Nivel",
                "tipo": "Tipo",
                "fecha": "Fecha",
                "estado": "Estado",
            },
        )

        # Tab de Equipo de Cuidado
        team_tab = tk.Frame(notebook, bg=COLORS["bg_primary"])
        notebook.add(team_tab, text="👨‍⚕️  Mi Equipo")

        self.care_team_tree = self._create_modern_treeview(
            team_tab,
            columns=("nombre",),
            headings={"nombre": "Equipo de Cuidado"},
        )

        # Tab de Cuidadores
        caregivers_tab = tk.Frame(notebook, bg=COLORS["bg_primary"])
        notebook.add(caregivers_tab, text="🩺  Cuidadores")

        self.caregivers_tree = self._create_modern_treeview(
            caregivers_tab,
            columns=("nombre", "email"),
            headings={
                "nombre": "Nombre",
                "email": "Email",
            },
        )

        # Tab de Dispositivos
        devices_tab = tk.Frame(notebook, bg=COLORS["bg_primary"])
        notebook.add(devices_tab, text="📱  Dispositivos")

        self.devices_tree = self._create_modern_treeview(
            devices_tab,
            columns=("serial", "tipo", "estado", "ultima"),
            headings={
                "serial": "Serial",
                "tipo": "Tipo",
                "estado": "Estado",
                "ultima": "Última actividad",
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
            height=12,  # Aumentado de 8 a 12 para pantalla completa
        )

        for col, heading in headings.items():
            tree.heading(col, text=heading, anchor="w")
            tree.column(col, anchor="w", width=200, minwidth=150)  # Aumentado ancho

        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True, padx=SPACING["sm"], pady=SPACING["sm"])
        scrollbar.pack(side="right", fill="y", pady=SPACING["sm"])

        return tree

    def _build_map(self, parent: tk.Frame) -> None:
        """Mapa de ubicaciones del paciente."""
        map_card = ModernTheme.create_card(parent)
        map_card.pack(fill="both", expand=False, padx=SPACING["lg"], pady=SPACING["md"])

        # Header del mapa
        map_header = tk.Frame(map_card, bg=COLORS["bg_primary"])
        map_header.pack(fill="x", pady=(0, SPACING["md"]))

        tk.Label(
            map_header,
            text="🗺️ Mis Ubicaciones",
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
                text="Instala tkintermapview para visualizar ubicaciones",
                font=FONTS["caption"],
                bg=COLORS["warning_bg"],
                fg=COLORS["text_secondary"],
            ).pack(pady=SPACING["sm"])

            self.map_status_var.set("Mapa no disponible")
            return

        map_container = tk.Frame(map_card, bg=COLORS["bg_primary"])
        map_container.pack(fill="both", expand=True)

        widget = TkinterMapView(map_container, width=1000, height=400, corner_radius=SIZES["border_radius"])
        widget.pack(fill="both", expand=True)
        widget.set_zoom(12)
        widget.set_position(19.4326, -99.1332)
        self.map_widget = widget
        self.map_status_var.set("Sin ubicaciones")

    def _build_footer(self, parent: tk.Frame) -> None:
        """Footer con estado."""
        footer = tk.Frame(parent, bg=COLORS["bg_secondary"])
        footer.pack(fill="x", padx=SPACING["lg"], pady=SPACING["lg"])

        tk.Label(
            footer,
            textvariable=self.status_var,
            font=FONTS["caption"],
            bg=COLORS["bg_secondary"],
            fg=COLORS["text_secondary"],
        ).pack(side="left")

    # ------------------------------------------------------------------
    # Data Loading Methods
    # ------------------------------------------------------------------
    def refresh(self) -> None:
        """Recarga todos los datos del paciente."""
        self.status_var.set("⏳ Cargando datos...")

        def task() -> Dict[str, Any]:
            api = self.controller.api
            # Llamar al dashboard y devices
            return {
                "dashboard": api.get_patient_dashboard(token=self.token),
                "devices": api.get_patient_devices(token=self.token),
            }

        def handle_success(data: Dict[str, Any]) -> None:
            self.status_var.set("✓ Datos actualizados")
            dashboard_data = data.get("dashboard", {})
            self._apply_dashboard(dashboard_data)
            # Aplicar devices
            devices_data = data.get("devices", {})
            self._apply_devices_from_response(devices_data)
            # El mapa sigue requiriendo su propio endpoint
            self._refresh_map()

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self.status_var.set(f"❌ {exc.message}")
            else:
                self.status_var.set(f"❌ {str(exc)}")

        self.run_async(task, on_success=handle_success, on_error=handle_error)

    def _apply_dashboard(self, payload: Dict[str, Any]) -> None:
        """Aplica los datos del dashboard al perfil y métricas."""
        # El dashboard del paciente NO tiene wrapper "data", viene directo
        data = payload  # Directamente las keys: patient, stats, care_team, caregivers, recent_alerts
        patient = data.get("patient", {}) if isinstance(data, dict) else {}

        # Debug: Imprimir datos recibidos
        print(f"DEBUG patient_dashboard - payload keys: {data.keys() if isinstance(data, dict) else 'N/A'}")
        print(f"DEBUG patient_dashboard - patient keys: {patient.keys() if isinstance(patient, dict) else 'N/A'}")

        # Perfil - usar org_name (es el correcto según la API)
        org_name = patient.get("org_name", "—")
        print(f"DEBUG org_name: {org_name}")
        self.org_var.set(org_name)
        
        # Fecha de nacimiento - viene como "birthdate"
        birthdate = patient.get("birthdate", "")
        if birthdate:
            self.birthdate_var.set(_format_date(birthdate))
        else:
            self.birthdate_var.set("—")

        # Nivel de riesgo - viene como STRING "Alto", "Bajo", etc.
        risk = patient.get("risk_level", "—")
        print(f"DEBUG risk_level: {risk} (type: {type(risk).__name__})")
        
        if isinstance(risk, str) and risk != "—":
            # Mapear a colores
            risk_lower = risk.lower()
            self.risk_var.set(risk)
            
            if "bajo" in risk_lower or "low" in risk_lower:
                self.risk_color = COLORS["risk_low"]
            elif "medio" in risk_lower or "medium" in risk_lower:
                self.risk_color = COLORS["risk_medium"]
            elif "alto" in risk_lower or "high" in risk_lower:
                self.risk_color = COLORS["risk_high"]
            elif "crítico" in risk_lower or "critical" in risk_lower:
                self.risk_color = COLORS["risk_critical"]
            else:
                self.risk_color = COLORS["text_secondary"]
            
            self.risk_label.config(fg=self.risk_color)
        else:
            self.risk_var.set("—")
            self.risk_color = COLORS["text_secondary"]
            self.risk_label.config(fg=self.risk_color)

        # Métricas - vienen en "stats"
        stats = data.get("stats", {})
        print(f"DEBUG stats: {stats}")
        
        self.total_alerts_var.set(str(stats.get("total_alerts", 0)))
        self.pending_alerts_var.set(str(stats.get("pending_alerts", 0)))
        self.devices_var.set(str(stats.get("devices_count", 0)))

        last_reading = stats.get("last_reading")
        if last_reading:
            self.last_reading_var.set(_format_datetime(last_reading))
        else:
            self.last_reading_var.set("N/A")
        
        # NUEVO: Cargar datos de las tabs directamente desde el dashboard
        # El dashboard YA trae: recent_alerts, caregivers, care_team
        print(f"DEBUG recent_alerts: {data.get('recent_alerts', [])}")
        print(f"DEBUG caregivers: {data.get('caregivers', [])}")
        print(f"DEBUG care_team: {data.get('care_team', {})}")
        
        # Aplicar alertas desde recent_alerts
        self._apply_alerts_from_dashboard(data.get("recent_alerts", []))
        
        # Aplicar cuidadores desde caregivers
        self._apply_caregivers_from_dashboard(data.get("caregivers", []))
        
        # Aplicar equipo de cuidado desde care_team
        self._apply_care_team_from_dashboard(data.get("care_team", {}))

    def _apply_alerts(self, payload: Dict[str, Any]) -> None:
        """Aplica las alertas a la tabla."""
        if not self.alerts_tree:
            return

        for row in self.alerts_tree.get_children():
            self.alerts_tree.delete(row)

        data = _dict_from(payload, "data") or payload
        items = data.get("items", []) if isinstance(data, dict) else []

        for alert in items:
            nivel = alert.get("severity", "—")
            tipo = alert.get("alert_type", "—")
            timestamp = alert.get("timestamp", "")
            fecha = _format_datetime(timestamp) if timestamp else "—"
            estado = alert.get("status", "—")
            self.alerts_tree.insert("", "end", values=(nivel, tipo, fecha, estado))
    
    def _apply_alerts_from_dashboard(self, alerts: list) -> None:
        """Aplica las alertas directamente desde el array recent_alerts del dashboard."""
        if not self.alerts_tree:
            return

        for row in self.alerts_tree.get_children():
            self.alerts_tree.delete(row)

        print(f"DEBUG _apply_alerts_from_dashboard: {len(alerts)} alertas")
        
        for alert in alerts:
            # Los campos correctos son: level (no severity), type (no alert_type), created_at (no timestamp)
            nivel = alert.get("level") or alert.get("level_label") or alert.get("severity") or "—"
            tipo = alert.get("type") or alert.get("alert_type") or "—"
            timestamp = alert.get("created_at") or alert.get("timestamp") or ""
            fecha = _format_datetime(timestamp) if timestamp else "—"
            estado = alert.get("status") or alert.get("status_label") or "—"
            self.alerts_tree.insert("", "end", values=(nivel, tipo, fecha, estado))
            print(f"  -> Alerta: {nivel} | {tipo} | {fecha} | {estado}")

    def _apply_devices(self, payload: Dict[str, Any]) -> None:
        """Aplica los dispositivos a la tabla."""
        if not self.devices_tree:
            return

        for row in self.devices_tree.get_children():
            self.devices_tree.delete(row)

        data = _dict_from(payload, "data") or payload
        items = data.get("items", []) if isinstance(data, dict) else []

        # Actualizar contador de dispositivos
        self.devices_var.set(str(len(items)))

        for device in items:
            serial = device.get("serial_number", "—")
            tipo = device.get("device_type", "—")
            estado = device.get("status", "—")
            last_activity = device.get("last_activity", "")
            ultima = _format_datetime(last_activity) if last_activity else "—"
            self.devices_tree.insert("", "end", values=(serial, tipo, estado, ultima))
    
    def _apply_devices_from_response(self, payload: Dict[str, Any]) -> None:
        """Aplica los dispositivos desde la respuesta del endpoint /patient/devices."""
        if not self.devices_tree:
            return

        for row in self.devices_tree.get_children():
            self.devices_tree.delete(row)

        # La respuesta viene como {devices: [...]}
        devices = payload.get("devices", []) if isinstance(payload, dict) else []
        
        print(f"DEBUG _apply_devices_from_response: {len(devices)} dispositivos")

        # Actualizar contador de dispositivos
        self.devices_var.set(str(len(devices)))

        for device in devices:
            # Los campos correctos son: serial, type (no device_type), brand, model
            serial = device.get("serial") or device.get("serial_number") or "—"
            tipo = device.get("type") or device.get("device_type") or "—"
            
            # El endpoint NO trae "status" ni "last_activity", solo active/registered_at
            active = device.get("active", True)
            estado = "Activo" if active else "Inactivo"
            
            registered_at = device.get("registered_at", "")
            ultima = _format_datetime(registered_at) if registered_at else "—"
            
            # Agregar info extra si hay brand/model
            brand = device.get("brand", "")
            model = device.get("model", "")
            if brand and model:
                tipo = f"{brand} {model} - {tipo}"
            
            self.devices_tree.insert("", "end", values=(serial, tipo, estado, ultima))
            print(f"  -> Device: {serial} | {tipo} | {estado} | {ultima}")

    def _apply_caregivers(self, payload: Dict[str, Any]) -> None:
        """Aplica los cuidadores a la tabla."""
        if not self.caregivers_tree:
            return

        for row in self.caregivers_tree.get_children():
            self.caregivers_tree.delete(row)

        data = _dict_from(payload, "data") or payload
        items = data.get("items", []) if isinstance(data, dict) else []

        for caregiver in items:
            nombre = caregiver.get("full_name", "—")
            email = caregiver.get("email", "—")
            self.caregivers_tree.insert("", "end", values=(nombre, email))
    
    def _apply_caregivers_from_dashboard(self, caregivers: list) -> None:
        """Aplica los cuidadores directamente desde el array caregivers del dashboard."""
        if not self.caregivers_tree:
            return

        for row in self.caregivers_tree.get_children():
            self.caregivers_tree.delete(row)

        print(f"DEBUG _apply_caregivers_from_dashboard: {len(caregivers)} cuidadores")
        
        for caregiver in caregivers:
            # El campo correcto es "name" no "full_name"
            nombre = caregiver.get("name") or caregiver.get("full_name") or "—"
            email = caregiver.get("email") or "—"
            self.caregivers_tree.insert("", "end", values=(nombre, email))
            print(f"  -> Cuidador: {nombre} | {email}")

    def _apply_care_team(self, payload: Dict[str, Any]) -> None:
        """Aplica el equipo de cuidado a la tabla."""
        if not self.care_team_tree:
            return

        for row in self.care_team_tree.get_children():
            self.care_team_tree.delete(row)

        data = _dict_from(payload, "data") or payload
        team = data.get("care_team", {}) if isinstance(data, dict) else {}

        if team:
            nombre = team.get("name", "—")
            self.care_team_tree.insert("", "end", values=(nombre,))
    
    def _apply_care_team_from_dashboard(self, care_team: dict) -> None:
        """Aplica el equipo de cuidado directamente desde el dict/list care_team del dashboard."""
        if not self.care_team_tree:
            return

        for row in self.care_team_tree.get_children():
            self.care_team_tree.delete(row)

        print(f"DEBUG _apply_care_team_from_dashboard: {care_team} (type: {type(care_team).__name__})")
        
        # Care team puede venir como dict o como list
        if isinstance(care_team, dict) and care_team:
            nombre = care_team.get("name") or care_team.get("team_name") or "—"
            self.care_team_tree.insert("", "end", values=(nombre,))
            print(f"  -> Care Team (dict): {nombre}")
        elif isinstance(care_team, list):
            # Si es una lista de equipos, cada uno tiene team_name y members
            for team in care_team:
                if isinstance(team, dict):
                    nombre = team.get("team_name") or team.get("name") or "Equipo"
                    self.care_team_tree.insert("", "end", values=(nombre,))
                    print(f"  -> Care Team: {nombre}")
                    
                    # Opcionalmente agregar miembros
                    members = team.get("members", [])
                    for member in members:
                        member_name = member.get("name", "")
                        member_role = member.get("role", "")
                        member_label = f"  • {member_name} ({member_role})"
                        self.care_team_tree.insert("", "end", values=(member_label,))
                        print(f"    -> Miembro: {member_name} - {member_role}")
        else:
            print(f"  -> Care Team: formato desconocido")

    def _refresh_map(self) -> None:
        """Actualiza el mapa con las ubicaciones del paciente."""
        if TkinterMapView is None or self.map_widget is None:
            self.map_status_var.set("Mapa no disponible")
            return

        self.map_status_var.set("Actualizando...")
        self._clear_map_markers()

        def task() -> Dict[str, Any]:
            return self.controller.api.get_patient_locations(token=self.token)

        def handle_success(payload: Dict[str, Any]) -> None:
            self._render_map(payload)

        def handle_error(exc: Exception) -> None:
            if isinstance(exc, ApiError):
                self.map_status_var.set(f"Error: {exc.message}")
            else:
                self.map_status_var.set("Error al cargar mapa")

        self.run_async(task, on_success=handle_success, on_error=handle_error)

    def _render_map(self, payload: Dict[str, Any]) -> None:
        """Renderiza las ubicaciones en el mapa."""
        if TkinterMapView is None or self.map_widget is None:
            return

        print(f"DEBUG _render_map - payload: {payload}")
        
        # El payload puede venir como {data: {items: [...]}} o directamente {locations: [...]}
        if "data" in payload:
            data = payload["data"]
        else:
            data = payload
        
        # Las ubicaciones pueden estar en "items" o "locations"
        items = data.get("items") or data.get("locations", [])
        
        print(f"DEBUG _render_map - items count: {len(items)}")
        if items:
            print(f"DEBUG _render_map - first item: {items[0]}")

        all_locs = []
        for item in items:
            # Las coordenadas pueden estar en item.location.latitude o directamente en item.latitude
            if "location" in item and isinstance(item["location"], dict):
                loc = item["location"]
                lat, lon = loc.get("latitude"), loc.get("longitude")
            else:
                # Coordenadas directas en el item
                lat = item.get("latitude") or item.get("lat")
                lon = item.get("longitude") or item.get("lon") or item.get("lng")
            
            if lat is not None and lon is not None:
                timestamp = item.get("timestamp") or item.get("created_at") or ""
                label = _format_datetime(timestamp) if timestamp else "Ubicación"
                all_locs.append((lat, lon, label))
                print(f"  -> Ubicación: {lat}, {lon} - {label}")

        if not all_locs:
            print("DEBUG _render_map - NO HAY UBICACIONES")
            self.map_status_var.set("Sin ubicaciones registradas")
            return

        self._clear_map_markers()
        for lat, lon, label in all_locs:
            marker = self.map_widget.set_marker(lat, lon, text=label)
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
            self.map_widget.set_zoom(14)

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


def _format_date(iso_str: str) -> str:
    """Formatea una fecha ISO a formato de solo fecha."""
    try:
        parsed = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return parsed.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return iso_str
