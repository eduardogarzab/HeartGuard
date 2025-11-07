"""Simple snackbar notifications for Tkinter."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class Snackbar(tk.Toplevel):
    def __init__(self, master: tk.Widget, message: str, *, duration: int = 3000,
                 bg: str = "#2d3748", fg: str = "#ffffff") -> None:
        super().__init__(master)
        self.withdraw()
        self.overrideredirect(True)
        self.configure(bg=bg)
        self.attributes("-topmost", True)

        label = ttk.Label(self, text=message, foreground=fg, background=bg)
        label.pack(padx=16, pady=10)

        self.update_idletasks()
        root = master.winfo_toplevel()
        x = root.winfo_x() + (root.winfo_width() - self.winfo_width()) // 2
        y = root.winfo_y() + root.winfo_height() - self.winfo_height() - 40
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}+{x}+{y}")
        self.deiconify()
        self.after(duration, self.destroy)


def show_snackbar(master: tk.Widget, message: str, *, duration: int = 3000,
                  bg: str = "#2d3748", fg: str = "#ffffff") -> None:
    Snackbar(master, message, duration=duration, bg=bg, fg=fg)
