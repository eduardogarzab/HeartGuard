"""Ventana Tkinter equivalente a ``UserDashboardFrame`` y paneles relacionados."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any, Callable, Dict, List, Optional

from ..api_client import ApiClient, ApiError
from ..config import Colors, Fonts
from ..models import auth as auth_models
from ..models.user import OrgMembership, UserProfile, parse_invitations, parse_memberships
from ..utils.async_utils import run_in_executor
from .widgets import AsyncMixin, ScrollableFrame, setup_styles, styled_button


class UserDashboardWindow(tk.Toplevel, AsyncMixin):
    def __init__(self, api_client: ApiClient, login_response: auth_models.LoginResponse) -> None:
        super().__init__()
        self.api_client = api_client
        self.login_response = login_response
        self.token = login_response.access_token
        self.title("HeartGuard - Command Center")
        self.geometry("1280x840")
        self.configure(background=Colors.BACKGROUND)
        setup_styles(self)

        self.profile: Optional[UserProfile] = None
        self.memberships: List[OrgMembership] = []
        self.selected_membership: Optional[OrgMembership] = None

        self._build_header()
        self._build_body()

        self._load_initial_data()

    def after(self, delay_ms: int, callback: Any, *args: Any) -> None:  # type: ignore[override]
        return super().after(delay_ms, callback, *args)

    # UI ------------------------------------------------------------------
    def _build_header(self) -> None:
        header = ttk.Frame(self, padding=24)
        header.pack(fill="x")

        left = ttk.Frame(header)
        left.pack(side="left", anchor="w")
        ttk.Label(left, text="💙", font=("Segoe UI Emoji", 28)).pack(side="left")
        ttk.Label(left, text="HeartGuard", font=("Inter", 24, "bold"), foreground=Colors.PRIMARY).pack(side="left", padx=6)
        ttk.Label(left, text="Command Center", font=Fonts.SUBTITLE, foreground=Colors.TEXT_SECONDARY).pack(side="left")

        center = ttk.Frame(header)
        center.pack(side="left", expand=True)
        ttk.Label(center, text="Organización:", font=Fonts.BODY).pack(side="left")
        self.org_var = tk.StringVar()
        self.org_selector = ttk.Combobox(center, textvariable=self.org_var, state="readonly", width=40)
        self.org_selector.pack(side="left", padx=12)
        self.org_selector.bind("<<ComboboxSelected>>", lambda _e: self._on_membership_selected())

        right = ttk.Frame(header)
        right.pack(side="right")
        self.name_label = ttk.Label(right, text=self.login_response.full_name, font=Fonts.BODY_BOLD)
        self.name_label.pack(anchor="e")
        ttk.Label(right, text=self.login_response.email or "", font=Fonts.CAPTION, foreground=Colors.TEXT_SECONDARY).pack(anchor="e")

        buttons = ttk.Frame(right)
        buttons.pack(anchor="e", pady=(12, 0))
        styled_button(buttons, "Mi Perfil", self._open_profile_dialog, primary=False, width=14).pack(side="left", padx=4)
        styled_button(buttons, "Invitaciones", self._open_invitations_dialog, primary=False, width=14).pack(side="left", padx=4)
        styled_button(buttons, "Cerrar Sesión", self.destroy, primary=False, width=14).pack(side="left", padx=4)

    def _build_body(self) -> None:
        self.body = ScrollableFrame(self)
        self.body.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.empty_state = ttk.Frame(self.body.content, padding=40)
        ttk.Label(self.empty_state, text="Aún no perteneces a una organización", font=("Inter", 18, "bold")).pack(pady=8)
        ttk.Label(
            self.empty_state,
            text="Solicita acceso o revisa tus invitaciones pendientes",
            font=Fonts.BODY,
            foreground=Colors.TEXT_SECONDARY,
        ).pack(pady=8)
        styled_button(self.empty_state, "Ver mis invitaciones", self._open_invitations_dialog).pack(pady=12)

        self.dashboard_panel = UserDashboardPanel(self.body.content, self.api_client, self.token, self._handle_api_error)

    # Data -----------------------------------------------------------------
    def _load_initial_data(self) -> None:
        def on_success(payload: Dict[str, Any]) -> None:
            self.profile = payload["profile"]
            self.memberships = payload["memberships"]
            self.name_label.configure(text=self.profile.name or self.login_response.full_name)

            if not self.memberships:
                self.empty_state.pack(fill="both", expand=True)
            else:
                self.empty_state.pack_forget()
                self.org_selector["values"] = [m.display_name() for m in self.memberships]
                self.org_selector.current(0)
                self.selected_membership = self.memberships[0]
                self.dashboard_panel.frame.pack(fill="both", expand=True)
                self.dashboard_panel.load_membership(self.selected_membership)

        def on_error(exc: Exception) -> None:
            messagebox.showerror("Error", f"No se pudo cargar la información inicial: {exc}")

        def fetch() -> Dict[str, Any]:
            profile_payload = self.api_client.get_current_user_profile(self.token)
            memberships_payload = self.api_client.get_current_user_memberships(self.token)
            return {
                "profile": UserProfile.from_dict(profile_payload.get("data") or profile_payload),
                "memberships": parse_memberships(memberships_payload),
            }

        self.run_async(fetch, on_success, on_error)

    def _on_membership_selected(self) -> None:
        index = self.org_selector.current()
        if index < 0 or index >= len(self.memberships):
            return
        membership = self.memberships[index]
        self.selected_membership = membership
        self.dashboard_panel.load_membership(membership)

    def _handle_api_error(self, exc: Exception) -> None:
        if isinstance(exc, ApiError) and exc.status_code == 401:
            messagebox.showwarning("Sesión expirada", "Sesión expirada. Por favor, vuelve a iniciar sesión.")
            self.destroy()
        else:
            messagebox.showerror("Error", str(exc))

    # Dialogs --------------------------------------------------------------
    def _open_profile_dialog(self) -> None:
        if not self.profile:
            messagebox.showinfo("Perfil", "La información del perfil aún no está disponible.")
            return
        UserProfileDialog(self, self.api_client, self.token, self.profile, self._refresh_profile)

    def _refresh_profile(self) -> None:
        def fetch() -> UserProfile:
            payload = self.api_client.get_current_user_profile(self.token)
            return UserProfile.from_dict(payload.get("data") or payload)

        def on_success(profile: UserProfile) -> None:
            self.profile = profile
            self.name_label.configure(text=profile.name or self.login_response.full_name)

        self.run_async(fetch, on_success, self._handle_api_error)

    def _open_invitations_dialog(self) -> None:
        dialog = InvitationsDialog(self, self.api_client, self.token)
        self.wait_window(dialog)
        # Recargar membresías por si cambió algo
        self._load_initial_data()


class UserDashboardPanel:
    def __init__(self, master: tk.Widget, api_client: ApiClient, token: str, error_handler: Callable[[Exception], None]) -> None:
        self.api_client = api_client
        self.token = token
        self.error_handler = error_handler

        self.frame = ttk.Frame(master)

        self.metrics_section = _MetricsSection(self.frame)
        self.metrics_section.frame.pack(fill="x", pady=8)

        self.map_section = _MapSection(self.frame)
        self.map_section.frame.pack(fill="x", pady=8)

        self.patients_section = _PatientsSection(self.frame, self._open_patient_detail)
        self.patients_section.frame.pack(fill="x", pady=8)

        self.devices_section = _DevicesSection(self.frame)
        self.devices_section.frame.pack(fill="x", pady=8)

        self.alerts_section = _AlertsBoardSection(self.frame)
        self.alerts_section.frame.pack(fill="x", pady=8)

        self.current_membership: Optional[OrgMembership] = None

    def load_membership(self, membership: OrgMembership) -> None:
        self.current_membership = membership

        def on_success(payload: Dict[str, Any]) -> None:
            self.metrics_section.update(payload["dashboard"], payload["metrics"])
            self.map_section.update(payload["caregiver_locations"], payload["care_team_locations"])
            self.patients_section.update(
                membership,
                payload["caregiver_patients"],
                payload["care_team_patients"],
            )
            self.devices_section.update(payload["care_teams"], membership, self._fetch_team_devices)
            self.alerts_section.update(payload["caregiver_patients"], self._open_patient_detail, membership)

        def on_error(exc: Exception) -> None:
            self.error_handler(exc)

        def fetch() -> Dict[str, Any]:
            org_id = membership.org_id
            return {
                "dashboard": self.api_client.get_organization_dashboard(org_id, token=self.token),
                "metrics": self.api_client.get_organization_metrics(org_id, token=self.token),
                "care_teams": self.api_client.get_organization_care_teams(org_id, token=self.token),
                "care_team_patients": self.api_client.get_organization_care_team_patients(org_id, token=self.token),
                "caregiver_patients": self.api_client.get_caregiver_patients(token=self.token),
                "care_team_locations": self.api_client.get_care_team_locations({"org_id": org_id}, token=self.token),
                "caregiver_locations": self.api_client.get_caregiver_patient_locations({"org_id": org_id}, token=self.token),
            }

        future = run_in_executor(fetch)

        def done(fut):
            try:
                payload = fut.result()
            except Exception as exc:  # pragma: no cover - depende de IO
                self.frame.after(0, lambda: on_error(exc))
                return
            self.frame.after(0, lambda: on_success(payload))

        future.add_done_callback(done)

    # ------------------------------------------------------------------
    def _fetch_team_devices(self, membership: OrgMembership, team_id: str,
                             on_success: Callable[[Dict[str, Any]], None],
                             on_error: Callable[[Exception], None]) -> None:

        def fetch() -> Dict[str, Any]:
            active = self.api_client.get_care_team_devices(membership.org_id, team_id, token=self.token)
            disconnected = self.api_client.get_care_team_disconnected_devices(membership.org_id, team_id, token=self.token)
            return {"active": active, "disconnected": disconnected}

        future = run_in_executor(fetch)

        def done(fut):
            try:
                payload = fut.result()
            except Exception as exc:  # pragma: no cover
                self.frame.after(0, lambda: on_error(exc))
                return
            self.frame.after(0, lambda: on_success(payload))

        future.add_done_callback(done)

    def _open_patient_detail(self, membership: OrgMembership, patient_id: str, patient_name: str) -> None:
        PatientDetailDialog(self.frame.winfo_toplevel(), self.api_client, self.token, membership, patient_id, patient_name)


class _MetricsSection:
    def __init__(self, master: tk.Widget) -> None:
        self.frame = ttk.LabelFrame(master, text="Indicadores principales", padding=16)
        self.vars = {
            "patients": tk.StringVar(value="0"),
            "alerts": tk.StringVar(value="0"),
            "devices": tk.StringVar(value="0"),
            "caregivers": tk.StringVar(value="0"),
        }
        grid = ttk.Frame(self.frame)
        grid.pack(fill="x")
        labels = {
            "patients": "Pacientes activos",
            "alerts": "Alertas abiertas",
            "devices": "Dispositivos activos",
            "caregivers": "Caregivers activos",
        }
        for col, key in enumerate(labels):
            card = ttk.Frame(grid, padding=12, borderwidth=1, relief="ridge")
            card.grid(row=0, column=col, padx=8, sticky="nsew")
            ttk.Label(card, text=labels[key], font=Fonts.SUBTITLE).pack()
            ttk.Label(card, textvariable=self.vars[key], font=("Segoe UI", 18, "bold"), foreground=Colors.PRIMARY).pack()
            grid.columnconfigure(col, weight=1)

    def update(self, dashboard_payload: Dict[str, Any], metrics_payload: Dict[str, Any]) -> None:
        data = dashboard_payload.get("data") or dashboard_payload
        self.vars["patients"].set(str(data.get("patients", {}).get("active") if isinstance(data.get("patients"), dict) else data.get("patients_active", 0)))
        self.vars["alerts"].set(str(data.get("alerts", {}).get("open") if isinstance(data.get("alerts"), dict) else data.get("alerts_open", 0)))
        metrics = metrics_payload.get("data") or metrics_payload
        self.vars["devices"].set(str(metrics.get("devices", {}).get("active") if isinstance(metrics.get("devices"), dict) else metrics.get("devices_active", 0)))
        caregivers = metrics.get("caregivers", {}) if isinstance(metrics.get("caregivers"), dict) else {}
        self.vars["caregivers"].set(str(caregivers.get("active", metrics.get("caregivers_active", 0))))


class _MapSection:
    def __init__(self, master: tk.Widget) -> None:
        self.frame = ttk.LabelFrame(master, text="Mapa de ubicaciones", padding=16)
        ttk.Label(
            self.frame,
            text="Mostramos la lista de ubicaciones recientes debido a que Tkinter no soporta JavaFX WebView.",
            foreground=Colors.TEXT_SECONDARY,
            wraplength=820,
        ).pack(fill="x", pady=(0, 10))
        self.caregiver_list = tk.Listbox(self.frame, height=5)
        self.care_team_list = tk.Listbox(self.frame, height=5)
        ttk.Label(self.frame, text="Pacientes asignados").pack(anchor="w")
        self.caregiver_list.pack(fill="x", pady=4)
        ttk.Label(self.frame, text="Equipos de cuidado").pack(anchor="w", pady=(10, 0))
        self.care_team_list.pack(fill="x", pady=4)

    def update(self, caregiver_payload: Dict[str, Any], care_team_payload: Dict[str, Any]) -> None:
        self.caregiver_list.delete(0, tk.END)
        self.care_team_list.delete(0, tk.END)
        caregiver_locations = caregiver_payload.get("data", {}).get("locations") or caregiver_payload.get("locations") or []
        care_team_locations = care_team_payload.get("data", {}).get("locations") or care_team_payload.get("locations") or []
        for loc in caregiver_locations:
            if isinstance(loc, dict):
                self.caregiver_list.insert(tk.END, f"{loc.get('patient_name', 'Paciente')} - {loc.get('latitude')}, {loc.get('longitude')}")
        if not caregiver_locations:
            self.caregiver_list.insert(tk.END, "Sin ubicaciones recientes")
        for loc in care_team_locations:
            if isinstance(loc, dict):
                self.care_team_list.insert(tk.END, f"{loc.get('team_name', 'Equipo')} - {loc.get('latitude')}, {loc.get('longitude')}")
        if not care_team_locations:
            self.care_team_list.insert(tk.END, "Sin ubicaciones disponibles")


class _PatientsSection:
    def __init__(self, master: tk.Widget, open_detail: Callable[[OrgMembership, str, str], None]) -> None:
        self.frame = ttk.LabelFrame(master, text="Gestión de pacientes", padding=16)
        self.open_detail = open_detail
        self.current_membership: Optional[OrgMembership] = None
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True)

        self.my_patients_list = tk.Listbox(self.notebook, height=8)
        self.team_patients_tree = ttk.Treeview(self.notebook, columns=("equipo", "rol"), show="headings")
        self.team_patients_tree.heading("equipo", text="Equipo")
        self.team_patients_tree.heading("rol", text="Rol en el equipo")

        self.notebook.add(self.my_patients_list, text="Mis pacientes")
        self.notebook.add(self.team_patients_tree, text="Pacientes por equipo")

        btn = styled_button(self.frame, "Ver detalles", self._on_view_detail)
        btn.pack(pady=12)

    def update(self, membership: OrgMembership, caregiver_payload: Dict[str, Any], team_payload: Dict[str, Any]) -> None:
        self.current_membership = membership
        self.my_patients_list.delete(0, tk.END)
        patients = caregiver_payload.get("data", {}).get("patients") or caregiver_payload.get("patients") or []
        self._caregiver_patients_cache: List[Dict[str, Any]] = []
        for item in patients:
            if isinstance(item, dict):
                display = f"{item.get('name')} ({item.get('risk_level', 'N/A')})"
                self.my_patients_list.insert(tk.END, display)
                self._caregiver_patients_cache.append(item)
        if not patients:
            self.my_patients_list.insert(tk.END, "No tienes pacientes asignados")

        for iid in self.team_patients_tree.get_children():
            self.team_patients_tree.delete(iid)
        self._team_patients_cache: List[Dict[str, Any]] = []
        teams = team_payload.get("data", {}).get("patients") or team_payload.get("patients") or []
        for item in teams:
            if isinstance(item, dict):
                self.team_patients_tree.insert("", tk.END, values=(item.get("team_name"), item.get("role_label")))
                self._team_patients_cache.append(item)
        if not teams:
            self.team_patients_tree.insert("", tk.END, values=("--", "Sin pacientes"))

    def _on_view_detail(self) -> None:
        if not self.current_membership:
            return
        if self.notebook.index(self.notebook.select()) == 0:
            selection = self.my_patients_list.curselection()
            if not selection:
                messagebox.showinfo("Pacientes", "Selecciona un paciente")
                return
            patient = self._caregiver_patients_cache[selection[0]] if selection[0] < len(self._caregiver_patients_cache) else None
        else:
            selection = self.team_patients_tree.selection()
            if not selection:
                messagebox.showinfo("Pacientes", "Selecciona un paciente")
                return
            index = self.team_patients_tree.index(selection[0])
            patient = self._team_patients_cache[index] if index < len(self._team_patients_cache) else None
        if not patient:
            return
        patient_id = patient.get("id") or patient.get("patient_id")
        name = patient.get("name") or patient.get("patient_name") or "Paciente"
        self.open_detail(self.current_membership, patient_id, name)


class _DevicesSection:
    def __init__(self, master: tk.Widget) -> None:
        self.frame = ttk.LabelFrame(master, text="Dispositivos por equipo", padding=16)
        self.combo = ttk.Combobox(self.frame, state="readonly")
        self.combo.pack(fill="x")
        columns = ("id", "estado", "tipo")
        self.tree = ttk.Treeview(self.frame, columns=columns, show="headings")
        for col in columns:
            self.tree.heading(col, text=col.capitalize())
        self.tree.pack(fill="both", expand=True, pady=8)
        self.status_var = tk.StringVar(value="Selecciona un equipo para ver sus dispositivos")
        ttk.Label(self.frame, textvariable=self.status_var, foreground=Colors.TEXT_SECONDARY).pack(anchor="w")
        self._teams: List[Dict[str, Any]] = []
        self._callback: Optional[Callable[[str, Callable[[Dict[str, Any]], None], Callable[[Exception], None]], None]] = None
        self.combo.bind("<<ComboboxSelected>>", lambda _e: self._on_team_selected())

    def update(self, care_teams_payload: Dict[str, Any], membership: OrgMembership,
               fetch_callback: Callable[[OrgMembership, str, Callable[[Dict[str, Any]], None], Callable[[Exception], None]], None]) -> None:
        self._teams = care_teams_payload.get("data", {}).get("teams") or care_teams_payload.get("teams") or []
        self.combo["values"] = [team.get("name") for team in self._teams]
        self._callback = lambda team_id, success, error: fetch_callback(membership, team_id, success, error)
        if self._teams:
            self.combo.current(0)
            self._request_devices(self._teams[0].get("id"))
        else:
            self.combo.set("")
            self.status_var.set("No hay equipos de cuidado configurados")
            self._clear_tree()

    def _clear_tree(self) -> None:
        for iid in self.tree.get_children():
            self.tree.delete(iid)

    def _on_team_selected(self) -> None:
        index = self.combo.current()
        if index < 0 or index >= len(self._teams):
            return
        team_id = self._teams[index].get("id")
        self._request_devices(team_id)

    def _request_devices(self, team_id: Optional[str]) -> None:
        if not team_id or not self._callback:
            return

        def success(payload: Dict[str, Any]) -> None:
            self._clear_tree()
            active = payload.get("active", {}).get("data") or payload.get("active", {})
            devices = active.get("devices") if isinstance(active, dict) else []
            for device in devices or []:
                if isinstance(device, dict):
                    self.tree.insert("", tk.END, values=(device.get("id"), "Activo", device.get("type")))
            disconnected = payload.get("disconnected", {}).get("data") or payload.get("disconnected", {})
            disc_devices = disconnected.get("devices") if isinstance(disconnected, dict) else []
            for device in disc_devices or []:
                if isinstance(device, dict):
                    self.tree.insert("", tk.END, values=(device.get("id"), "Desconectado", device.get("type")))
            if not devices and not disc_devices:
                self.status_var.set("Sin dispositivos registrados")
            else:
                self.status_var.set("Dispositivos listados")

        def error(exc: Exception) -> None:
            messagebox.showerror("Dispositivos", str(exc))

        self.status_var.set("Cargando dispositivos...")
        self._callback(team_id, success, error)


class _AlertsBoardSection:
    def __init__(self, master: tk.Widget) -> None:
        self.frame = ttk.LabelFrame(master, text="Alertas y seguimiento", padding=16)
        self.listbox = tk.Listbox(self.frame, height=6)
        self.listbox.pack(fill="both", expand=True)
        self.listbox.bind("<Double-Button-1>", self._on_double_click)
        self._patients: List[Dict[str, Any]] = []
        self._callback: Optional[Callable[[OrgMembership, str, str], None]] = None
        self._membership: Optional[OrgMembership] = None

    def update(self, caregiver_payload: Dict[str, Any], callback: Callable[[OrgMembership, str, str], None],
               membership: OrgMembership) -> None:
        self._callback = callback
        self._membership = membership
        self.listbox.delete(0, tk.END)
        self._patients = []
        patients = caregiver_payload.get("data", {}).get("patients") or caregiver_payload.get("patients") or []
        for patient in patients:
            if isinstance(patient, dict):
                alerts = patient.get("alerts_open") or patient.get("open_alerts")
                self.listbox.insert(
                    tk.END,
                    f"{patient.get('name')} - Alertas abiertas: {alerts if alerts is not None else 'N/A'}",
                )
                self._patients.append(patient)
        if not patients:
            self.listbox.insert(tk.END, "No hay alertas para tus pacientes")

    def _on_double_click(self, _event: tk.Event) -> None:
        if not self._callback or not self._membership:
            return
        selection = self.listbox.curselection()
        if not selection or selection[0] >= len(self._patients):
            return
        patient = self._patients[selection[0]]
        patient_id = patient.get("id") or patient.get("patient_id")
        name = patient.get("name") or "Paciente"
        if patient_id:
            self._callback(self._membership, patient_id, name)


class UserProfileDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, api_client: ApiClient, token: str, profile: UserProfile, on_saved: Callable[[], None]) -> None:
        super().__init__(master)
        self.api_client = api_client
        self.token = token
        self.profile = profile
        self.on_saved = on_saved
        self.title("Perfil de usuario")
        self.resizable(False, False)
        ttk.Label(self, text="Actualizar información personal", font=Fonts.TITLE).pack(pady=12, padx=16)
        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        ttk.Label(form, text="Nombre completo:").grid(row=0, column=0, sticky="w", pady=6)
        self.name_entry = ttk.Entry(form, width=40)
        self.name_entry.grid(row=0, column=1, pady=6)
        self.name_entry.insert(0, profile.name or "")
        ttk.Label(form, text="Email (solo lectura):").grid(row=1, column=0, sticky="w", pady=6)
        email_entry = ttk.Entry(form, width=40)
        email_entry.grid(row=1, column=1, pady=6)
        email_entry.insert(0, profile.email or "")
        email_entry.configure(state="disabled")
        ttk.Label(form, text="Foto de perfil (URL):").grid(row=2, column=0, sticky="w", pady=6)
        self.photo_entry = ttk.Entry(form, width=40)
        self.photo_entry.grid(row=2, column=1, pady=6)
        self.photo_entry.insert(0, profile.profile_photo_url or "")

        buttons = ttk.Frame(self, padding=(16, 0, 16, 16))
        buttons.pack(fill="x")
        styled_button(buttons, "Guardar", self._on_save).pack(side="left", padx=6)
        styled_button(buttons, "Cerrar", self.destroy, primary=False).pack(side="right", padx=6)

    def _on_save(self) -> None:
        updates = {"name": self.name_entry.get().strip(), "profile_photo_url": self.photo_entry.get().strip() or None}

        def success(_payload: Dict[str, Any]) -> None:
            messagebox.showinfo("Perfil", "Perfil actualizado correctamente")
            self.on_saved()
            self.destroy()

        def error(exc: Exception) -> None:
            messagebox.showerror("Perfil", str(exc))

        future = run_in_executor(lambda: self.api_client.update_current_user_profile(updates, token=self.token))

        def done(fut):
            try:
                payload = fut.result()
            except Exception as exc:  # pragma: no cover
                self.after(0, lambda: error(exc))
                return
            self.after(0, lambda: success(payload))

        future.add_done_callback(done)


class InvitationsDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, api_client: ApiClient, token: str) -> None:
        super().__init__(master)
        self.api_client = api_client
        self.token = token
        self.title("Invitaciones pendientes")
        self.geometry("520x420")
        ttk.Label(self, text="Invitaciones", font=Fonts.TITLE).pack(pady=12)
        self.listbox = tk.Listbox(self, height=10)
        self.listbox.pack(fill="both", expand=True, padx=16)
        buttons = ttk.Frame(self, padding=16)
        buttons.pack(fill="x")
        styled_button(buttons, "Aceptar", self._on_accept).pack(side="left", padx=6)
        styled_button(buttons, "Rechazar", self._on_reject, primary=False).pack(side="left", padx=6)
        styled_button(buttons, "Cerrar", self.destroy, primary=False).pack(side="right", padx=6)
        self._invitations: List[Dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        def fetch() -> List[Dict[str, Any]]:
            payload = self.api_client.get_pending_invitations(self.token)
            return parse_invitations(payload)

        def on_success(invitations: List[Dict[str, Any]]) -> None:
            self._invitations = invitations
            self.listbox.delete(0, tk.END)
            for inv in invitations:
                text = f"{inv.get('org_name')} - Rol: {inv.get('role_label')}"
                self.listbox.insert(tk.END, text)
            if not invitations:
                self.listbox.insert(tk.END, "No tienes invitaciones pendientes")

        def on_error(exc: Exception) -> None:
            messagebox.showerror("Invitaciones", str(exc))

        future = run_in_executor(fetch)

        def done(fut):
            try:
                invitations = fut.result()
            except Exception as exc:  # pragma: no cover
                self.after(0, lambda: on_error(exc))
                return
            self.after(0, lambda: on_success(invitations))

        future.add_done_callback(done)

    def _resolve_selection(self) -> Optional[Dict[str, Any]]:
        selection = self.listbox.curselection()
        if not selection or selection[0] >= len(self._invitations):
            messagebox.showinfo("Invitaciones", "Selecciona una invitación")
            return None
        return self._invitations[selection[0]]

    def _on_accept(self) -> None:
        invitation = self._resolve_selection()
        if not invitation:
            return

        def run() -> Dict[str, Any]:
            return self.api_client.accept_invitation(invitation.get("id"), token=self.token)

        future = run_in_executor(run)

        def done(fut):
            try:
                fut.result()
            except Exception as exc:  # pragma: no cover
                self.after(0, lambda: messagebox.showerror("Invitaciones", str(exc)))
                return
            self.after(0, self._load)

        future.add_done_callback(done)

    def _on_reject(self) -> None:
        invitation = self._resolve_selection()
        if not invitation:
            return

        def run() -> Dict[str, Any]:
            return self.api_client.reject_invitation(invitation.get("id"), token=self.token)

        future = run_in_executor(run)

        def done(fut):
            try:
                fut.result()
            except Exception as exc:  # pragma: no cover
                self.after(0, lambda: messagebox.showerror("Invitaciones", str(exc)))
                return
            self.after(0, self._load)

        future.add_done_callback(done)


class PatientDetailDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, api_client: ApiClient, token: str, membership: OrgMembership,
                 patient_id: str, patient_name: str) -> None:
        super().__init__(master)
        self.api_client = api_client
        self.token = token
        self.membership = membership
        self.patient_id = patient_id
        self.title(f"Paciente: {patient_name}")
        self.geometry("720x560")

        header = ttk.Frame(self, padding=16)
        header.pack(fill="x")
        ttk.Label(header, text=patient_name, font=Fonts.TITLE).pack(anchor="w")

        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=16, pady=12)
        self.profile_text = tk.Text(self.tabs, state="disabled")
        self.alerts_list = tk.Listbox(self.tabs)
        self.notes_list = tk.Listbox(self.tabs)
        self.tabs.add(self.profile_text, text="Perfil")
        self.tabs.add(self.alerts_list, text="Alertas")
        self.tabs.add(self.notes_list, text="Notas")

        self._load()

    def _load(self) -> None:
        def fetch() -> Dict[str, Any]:
            detail = self.api_client.get_organization_patient_detail(self.membership.org_id, self.patient_id, token=self.token)
            alerts = self.api_client.get_organization_patient_alerts(self.membership.org_id, self.patient_id, token=self.token)
            notes = self.api_client.get_organization_patient_notes(self.membership.org_id, self.patient_id, token=self.token)
            return {"detail": detail, "alerts": alerts, "notes": notes}

        def on_success(payload: Dict[str, Any]) -> None:
            detail = payload["detail"].get("data") or payload["detail"]
            self.profile_text.configure(state="normal")
            self.profile_text.delete("1.0", tk.END)
            for key, value in detail.items():
                self.profile_text.insert(tk.END, f"{key}: {value}\n")
            self.profile_text.configure(state="disabled")

            self.alerts_list.delete(0, tk.END)
            alerts = payload["alerts"].get("data", {}).get("alerts") or payload["alerts"].get("alerts") or []
            for alert in alerts:
                if isinstance(alert, dict):
                    self.alerts_list.insert(tk.END, f"[{alert.get('status')}] {alert.get('message')}")
            if not alerts:
                self.alerts_list.insert(tk.END, "Sin alertas recientes")

            self.notes_list.delete(0, tk.END)
            notes = payload["notes"].get("data", {}).get("notes") or payload["notes"].get("notes") or []
            for note in notes:
                if isinstance(note, dict):
                    self.notes_list.insert(tk.END, f"{note.get('created_at')}: {note.get('content')}")
            if not notes:
                self.notes_list.insert(tk.END, "No hay notas registradas")

        def on_error(exc: Exception) -> None:
            messagebox.showerror("Paciente", str(exc))

        future = run_in_executor(fetch)

        def done(fut):
            try:
                payload = fut.result()
            except Exception as exc:  # pragma: no cover
                self.after(0, lambda: on_error(exc))
                return
            self.after(0, lambda: on_success(payload))

        future.add_done_callback(done)
