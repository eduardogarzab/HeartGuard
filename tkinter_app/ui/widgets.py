"""Widgets reutilizables para la interfaz de HeartGuard en Tkinter."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Optional

from ..utils.async_utils import run_in_executor


class AsyncMixin:
    """Mezcla que facilita ejecutar funciones en segundo plano."""

    def run_async(self, func: Callable[..., Any], callback: Optional[Callable[[Any], None]] = None,
                  error_callback: Optional[Callable[[Exception], None]] = None, *args: Any, **kwargs: Any) -> None:
        future = run_in_executor(func, *args, **kwargs)

        def _on_done(fut):
            try:
                result = fut.result()
            except Exception as exc:  # pragma: no cover - depende de IO real
                if error_callback:
                    self.after(0, error_callback, exc)
                else:
                    self.after(0, lambda: messagebox.showerror("Error", str(exc)))
                return
            if callback:
                self.after(0, callback, result)

        future.add_done_callback(_on_done)

    def after(self, delay_ms: int, callback: Callable[..., Any], *args: Any) -> None:  # pragma: no cover - implementado por Tk
        raise NotImplementedError


class ScrollableFrame(ttk.Frame):
    """Contenedor con scroll vertical."""

    def __init__(self, master: tk.Widget, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self._content = ttk.Frame(canvas)

        self._content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    @property
    def content(self) -> ttk.Frame:
        return self._content


def styled_button(master: tk.Widget, text: str, command: Callable[[], Any], *, primary: bool = True, width: int = 18) -> ttk.Button:
    style_name = "HeartGuard.Primary.TButton" if primary else "HeartGuard.Secondary.TButton"
    button = ttk.Button(master, text=text, command=command, style=style_name, width=width)
    return button


def setup_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    if style.theme_use() == "classic":
        style.theme_use("clam")

    style.configure(
        "HeartGuard.Primary.TButton",
        foreground="white",
        background="#2196F3",
        padding=8,
        relief="flat",
    )
    style.map(
        "HeartGuard.Primary.TButton",
        background=[("active", "#1976D2"), ("disabled", "#90CAF9")],
    )
    style.configure(
        "HeartGuard.Secondary.TButton",
        foreground="#233446",
        background="#ECEFF1",
        padding=8,
        relief="flat",
    )
    style.map(
        "HeartGuard.Secondary.TButton",
        background=[("active", "#CFD8DC"), ("disabled", "#ECEFF1")],
    )
