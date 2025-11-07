"""Tema visual moderno para HeartGuard - HealthTech UI/UX."""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Any

# Paleta de colores HealthTech profesional
COLORS = {
    # Colores primarios
    "primary": "#0ea5e9",        # Azul cielo (confianza, tecnología)
    "primary_dark": "#0284c7",   # Azul oscuro
    "primary_light": "#7dd3fc",  # Azul claro
    
    # Colores secundarios
    "secondary": "#06b6d4",      # Cyan (frescura, salud)
    "accent": "#8b5cf6",         # Púrpura (innovación)
    
    # Colores de estado
    "success": "#10b981",        # Verde (positivo, salud)
    "warning": "#f59e0b",        # Naranja (precaución)
    "danger": "#ef4444",         # Rojo (alerta, crítico)
    "info": "#3b82f6",           # Azul información
    
    # Niveles de riesgo
    "risk_low": "#10b981",       # Verde
    "risk_medium": "#f59e0b",    # Naranja
    "risk_high": "#ef4444",      # Rojo
    "risk_critical": "#dc2626",  # Rojo oscuro
    
    # Grises y fondos
    "bg_primary": "#ffffff",     # Blanco puro
    "bg_secondary": "#f8fafc",   # Gris muy claro
    "bg_tertiary": "#f1f5f9",    # Gris claro
    "bg_card": "#ffffff",        # Blanco para tarjetas
    
    # Textos
    "text_primary": "#0f172a",   # Gris muy oscuro (casi negro)
    "text_secondary": "#475569", # Gris medio
    "text_tertiary": "#94a3b8",  # Gris claro
    "text_on_primary": "#ffffff",# Blanco sobre primario
    
    # Bordes y divisores
    "border": "#e2e8f0",         # Gris muy claro
    "border_hover": "#cbd5e1",   # Gris claro hover
    "divider": "#e2e8f0",        # Línea divisoria
    
    # Sombras (como tuplas RGB para tk)
    "shadow_light": "#f1f5f9",
    "shadow_medium": "#cbd5e1",
}

# Tipografía
FONTS = {
    "heading_1": ("Segoe UI", 28, "bold"),
    "heading_2": ("Segoe UI", 24, "bold"),
    "heading_3": ("Segoe UI", 20, "bold"),
    "heading_4": ("Segoe UI", 16, "bold"),
    "body_large": ("Segoe UI", 14),
    "body": ("Segoe UI", 12),
    "body_small": ("Segoe UI", 11),
    "caption": ("Segoe UI", 10),
    "button": ("Segoe UI", 12, "bold"),
    "label": ("Segoe UI", 11),
    "metric_value": ("Segoe UI", 36, "bold"),  # Aumentado para pantalla completa
    "metric_label": ("Segoe UI", 12),  # Aumentado para mejor legibilidad
}

# Dimensiones y espaciado
SPACING = {
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "xxl": 32,
}

SIZES = {
    "border_radius": 12,
    "button_height": 40,
    "input_height": 38,
    "card_padding": 24,  # Aumentado de 20 a 24 para pantalla completa
    "section_padding": 16,
}


class ModernTheme:
    """Gestor de tema visual moderno."""
    
    @staticmethod
    def configure_style(root: tk.Tk) -> ttk.Style:
        """Configura el estilo ttk con tema moderno."""
        style = ttk.Style(root)
        
        # Configurar tema base
        style.theme_use('clam')
        
        # Configurar colores generales
        style.configure(".", 
            background=COLORS["bg_secondary"],
            foreground=COLORS["text_primary"],
            font=FONTS["body"],
            borderwidth=0,
            relief="flat"
        )
        
        # Frame principal
        style.configure("Main.TFrame",
            background=COLORS["bg_secondary"]
        )
        
        # Tarjetas (Card)
        style.configure("Card.TFrame",
            background=COLORS["bg_card"],
            relief="flat",
            borderwidth=1
        )
        
        # Labels
        style.configure("TLabel",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            font=FONTS["body"]
        )
        
        style.configure("Heading1.TLabel",
            font=FONTS["heading_1"],
            foreground=COLORS["primary"]
        )
        
        style.configure("Heading2.TLabel",
            font=FONTS["heading_2"],
            foreground=COLORS["text_primary"]
        )
        
        style.configure("Heading3.TLabel",
            font=FONTS["heading_3"],
            foreground=COLORS["text_primary"]
        )
        
        style.configure("Secondary.TLabel",
            foreground=COLORS["text_secondary"],
            font=FONTS["body_small"]
        )
        
        style.configure("Caption.TLabel",
            foreground=COLORS["text_tertiary"],
            font=FONTS["caption"]
        )
        
        # Métricas
        style.configure("MetricValue.TLabel",
            font=FONTS["metric_value"],
            foreground=COLORS["primary"]
        )
        
        style.configure("MetricLabel.TLabel",
            font=FONTS["metric_label"],
            foreground=COLORS["text_secondary"]
        )
        
        # Botones modernos
        style.configure("TButton",
            font=FONTS["button"],
            borderwidth=0,
            relief="flat",
            padding=(20, 10),
            background=COLORS["primary"],
            foreground=COLORS["text_on_primary"]
        )
        
        style.map("TButton",
            background=[
                ("active", COLORS["primary_dark"]),
                ("pressed", COLORS["primary_dark"]),
                ("disabled", COLORS["border"])
            ],
            foreground=[
                ("disabled", COLORS["text_tertiary"])
            ]
        )
        
        # Botón primario
        style.configure("Primary.TButton",
            background=COLORS["primary"],
            foreground=COLORS["text_on_primary"]
        )
        
        # Botón secundario
        style.configure("Secondary.TButton",
            background=COLORS["bg_tertiary"],
            foreground=COLORS["text_primary"]
        )
        
        style.map("Secondary.TButton",
            background=[("active", COLORS["border_hover"])]
        )
        
        # Botón de éxito
        style.configure("Success.TButton",
            background=COLORS["success"],
            foreground=COLORS["text_on_primary"]
        )
        
        # Botón de peligro
        style.configure("Danger.TButton",
            background=COLORS["danger"],
            foreground=COLORS["text_on_primary"]
        )
        
        # Entry (inputs)
        style.configure("TEntry",
            fieldbackground=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            borderwidth=1,
            relief="solid",
            padding=10
        )
        
        # Combobox
        style.configure("TCombobox",
            fieldbackground=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            background=COLORS["bg_card"],
            borderwidth=1,
            relief="solid",
            padding=8
        )
        
        style.map("TCombobox",
            fieldbackground=[("readonly", COLORS["bg_card"])],
            selectbackground=[("readonly", COLORS["primary"])],
            selectforeground=[("readonly", COLORS["text_on_primary"])]
        )
        
        # Notebook (tabs)
        style.configure("TNotebook",
            background=COLORS["bg_secondary"],
            borderwidth=0,
            padding=0
        )
        
        style.configure("TNotebook.Tab",
            background=COLORS["bg_tertiary"],
            foreground=COLORS["text_secondary"],
            padding=(20, 10),
            borderwidth=0
        )
        
        style.map("TNotebook.Tab",
            background=[("selected", COLORS["bg_card"])],
            foreground=[("selected", COLORS["primary"])],
            expand=[("selected", [1, 1, 1, 0])]
        )
        
        # Treeview (tablas)
        style.configure("Treeview",
            background=COLORS["bg_card"],
            foreground=COLORS["text_primary"],
            fieldbackground=COLORS["bg_card"],
            borderwidth=0,
            font=FONTS["body"],
            rowheight=36
        )
        
        style.configure("Treeview.Heading",
            background=COLORS["bg_tertiary"],
            foreground=COLORS["text_secondary"],
            borderwidth=0,
            font=FONTS["label"],
            relief="flat"
        )
        
        style.map("Treeview",
            background=[("selected", COLORS["primary_light"])],
            foreground=[("selected", COLORS["text_primary"])]
        )
        
        # Scrollbar
        style.configure("Vertical.TScrollbar",
            background=COLORS["border"],
            troughcolor=COLORS["bg_tertiary"],
            borderwidth=0,
            arrowcolor=COLORS["text_secondary"]
        )
        
        return style
    
    @staticmethod
    def create_card(parent: tk.Widget, **kwargs) -> ttk.Frame:
        """Crea una tarjeta estilo material design."""
        card = ttk.Frame(parent, style="Card.TFrame", **kwargs)
        card.configure(relief="solid", borderwidth=1)
        return card
    
    @staticmethod
    def create_metric_card(parent: tk.Widget, icon: str, label: str, 
                          value_var: tk.StringVar, color: str = None) -> ttk.Frame:
        """Crea tarjeta de métrica con diseño moderno.
        
        Args:
            parent: Widget padre
            icon: Emoji o icono a mostrar
            label: Etiqueta descriptiva
            value_var: StringVar con el valor de la métrica
            color: Color del icono y valor (opcional)
        """
        card = ModernTheme.create_card(parent, padding=SIZES["card_padding"])
        
        # Container
        container = ttk.Frame(card, style="Card.TFrame")
        container.pack(fill="both", expand=True)
        
        # Icono
        icon_label = ttk.Label(container, text=icon, 
                              font=("Segoe UI", 32),  # Aumentado de 24 a 32
                              foreground=color or COLORS["primary"])
        icon_label.pack(anchor="w", pady=(0, SPACING["sm"]))
        
        # Valor
        value_label = ttk.Label(container, textvariable=value_var,
                               style="MetricValue.TLabel")
        if color:
            value_label.configure(foreground=color)
        value_label.pack(anchor="w")
        
        # Label
        label_widget = ttk.Label(container, text=label,
                                style="MetricLabel.TLabel")
        label_widget.pack(anchor="w", pady=(SPACING["xs"], 0))
        
        return card
    
    @staticmethod
    def create_button(parent: tk.Widget, text: str, command=None, 
                     style: str = "primary", **kwargs) -> ttk.Button:
        """Crea botón con estilo moderno.
        
        Args:
            parent: Widget padre
            text: Texto del botón
            command: Callback al hacer clic
            style: Estilo del botón ("primary", "secondary", "danger", "success")
            **kwargs: Argumentos adicionales para ttk.Button
        """
        # Mapear estilo a nombre de estilo ttk
        style_map = {
            "primary": "Primary.TButton",
            "secondary": "Secondary.TButton",
            "danger": "Danger.TButton",
            "success": "Success.TButton",
        }
        
        ttk_style = style_map.get(style, "TButton")
        btn = ttk.Button(parent, text=text, command=command, style=ttk_style, **kwargs)
        return btn
    
    @staticmethod
    def create_section_header(parent: tk.Widget, text: str, 
                             subtitle: str = None) -> ttk.Frame:
        """Crea encabezado de sección."""
        frame = ttk.Frame(parent)
        
        ttk.Label(frame, text=text, style="Heading3.TLabel").pack(
            anchor="w", side="left"
        )
        
        if subtitle:
            ttk.Label(frame, text=subtitle, style="Secondary.TLabel").pack(
                anchor="w", side="left", padx=(SPACING["md"], 0)
            )
        
        return frame


def hex_to_rgb(hex_color: str) -> tuple:
    """Convierte color hexadecimal a RGB."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def create_gradient(canvas: tk.Canvas, width: int, height: int, 
                   color1: str, color2: str) -> None:
    """Crea gradiente en canvas."""
    rgb1 = hex_to_rgb(color1)
    rgb2 = hex_to_rgb(color2)
    
    for i in range(height):
        ratio = i / height
        r = int(rgb1[0] + (rgb2[0] - rgb1[0]) * ratio)
        g = int(rgb1[1] + (rgb2[1] - rgb1[1]) * ratio)
        b = int(rgb1[2] + (rgb2[2] - rgb1[2]) * ratio)
        
        color = f'#{r:02x}{g:02x}{b:02x}'
        canvas.create_line(0, i, width, i, fill=color, width=1)
