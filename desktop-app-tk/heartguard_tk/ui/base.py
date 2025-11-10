"""Shared Tkinter helpers."""

from __future__ import annotations

import threading
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional


class BaseView(tk.Frame):
    """Base frame that stores a reference to the application controller."""

    def __init__(self, master: tk.Misc, controller: "AppController", **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self.controller = controller

    def run_async(
        self,
        task: Callable[[], Any],
        *,
        on_success: Optional[Callable[[Any], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> None:
        """Execute a blocking task on a background thread."""

        def target() -> None:
            try:
                result = task()
            except Exception as exc:  # pragma: no cover - GUI path
                if on_error:
                    # Capturar exc en el scope correcto usando un argumento por defecto
                    self.controller.call_soon(lambda e=exc: on_error(e))
            else:
                if on_success:
                    self.controller.call_soon(lambda: on_success(result))

        threading.Thread(target=target, daemon=True).start()


class Scrollable(ttk.Frame):
    """Vertical scroll container using a Canvas + interior frame."""

    def __init__(self, master: tk.Misc, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)

        self.inner.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, _event: tk.Event) -> None:
        self.canvas.configure(width=self.winfo_width())

    def get_inner(self) -> ttk.Frame:
        return self.inner


class AppController:
    """Protocol satisfied by the Tk application controller."""

    def call_soon(self, callback: Callable[[], None]) -> None:
        raise NotImplementedError

    @property
    def api(self) -> Any:
        raise NotImplementedError
