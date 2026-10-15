"""Reusable CustomTkinter widgets and small helpers for the UI layer."""
from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk

# ------------------------------------------------------------------ palette
ACCENT = "#1f6feb"
ACCENT_HOVER = "#1a5fd0"
GREEN = "#16a34a"
GREEN_HOVER = "#15803d"
AMBER = "#d97706"
RED = "#dc2626"
RED_HOVER = "#b91c1c"
GRAY = "#6b7280"
GRAY_HOVER = "#4b5563"

STATUS_COLORS = {
    "open": AMBER,
    "paid": GREEN,
    "overdue": RED,
    "cancelled": GRAY,
    "draft": "#475569",
}

FONT = "CTkFont"


def status_color(status: str) -> str:
    return STATUS_COLORS.get(status, GRAY)


def center(win, parent, width: int | None = None, height: int | None = None):
    """Center a Toplevel relative to its parent (best effort)."""
    win.update_idletasks()
    if width and height:
        win.geometry(f"{width}x{height}")
    parent.update_idletasks()
    try:
        px, py = parent.winfo_rootx(), parent.winfo_rooty()
        pw, ph = parent.winfo_width(), parent.winfo_height()
        w, h = win.winfo_width(), win.winfo_height()
        x = px + max(0, (pw - w) // 2)
        y = py + max(0, (ph - h) // 3)
        win.geometry(f"+{x}+{y}")
    except Exception:
        pass


class ModalDialog(ctk.CTkToplevel):
    """Base class for modal windows."""

    def __init__(self, master, app, title: str, size=(520, 500)):
        super().__init__(master)
        self.app = app
        self.tr = app.tr
        self.db = app.db
        self.config = app.config
        self.title(title)
        self.configure(fg_color=("gray95", "gray10"))
        self.transient(master)
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        center(self, master, size[0], size[1])
        self.after(80, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass


class Field:
    """Label + entry stacked vertically, with optional helper text."""

    def __init__(self, parent, label: str, placeholder: str = "", width: int = 360, show: str | None = None):
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        self.label = ctk.CTkLabel(self.frame, text=label, anchor="w",
                                  font=ctk.CTkFont(size=12, weight="bold"))
        self.label.pack(anchor="w", pady=(0, 2))
        self.entry = ctk.CTkEntry(self.frame, placeholder_text=placeholder, width=width,
                                  show=show) if show else ctk.CTkEntry(self.frame, placeholder_text=placeholder, width=width)
        self.entry.pack(anchor="w", fill="x")

    def pack(self, **kw):
        self.frame.pack(**kw)

    def grid(self, **kw):
        self.frame.grid(**kw)

    def pack_forget(self):
        self.frame.pack_forget()

    def grid_forget(self):
        self.frame.grid_forget()

    def get(self) -> str:
        return self.entry.get().strip()

    def set(self, value: str) -> None:
        self.entry.delete(0, "end")
        if value:
            self.entry.insert(0, str(value))


class Card(ctk.CTkFrame):
    """A titled container frame."""

    def __init__(self, parent, title: str = "", **kwargs):
        kwargs.setdefault("corner_radius", 12)
        kwargs.setdefault("fg_color", ("#ffffff", "#1b1f27"))
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", ("#e5e7eb", "#2a2f3a"))
        super().__init__(parent, **kwargs)
        self.body = self
        if title:
            self.title_label = ctk.CTkLabel(self, text=title, anchor="w",
                                            font=ctk.CTkFont(size=14, weight="bold"))
            self.title_label.pack(anchor="w", padx=16, pady=(12, 6))
            self.body = ctk.CTkFrame(self, fg_color="transparent")
            self.body.pack(fill="both", expand=True, padx=16, pady=(0, 14))


class StatCard(ctk.CTkFrame):
    def __init__(self, parent, label: str, value: str, color: str = ACCENT):
        super().__init__(parent, corner_radius=12, fg_color=("#ffffff", "#1b1f27"),
                         border_width=1, border_color=("#e5e7eb", "#2a2f3a"))
        self.bar = ctk.CTkFrame(self, width=6, corner_radius=3, fg_color=color)
        self.bar.pack(side="left", fill="y", padx=(10, 0), pady=10)
        self.inner = ctk.CTkFrame(self, fg_color="transparent")
        self.inner.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        self.value_label = ctk.CTkLabel(self.inner, text=value, anchor="w",
                                        font=ctk.CTkFont(size=22, weight="bold"))
        self.value_label.pack(anchor="w")
        self.label = ctk.CTkLabel(self.inner, text=label, anchor="w", text_color=("gray40", "gray65"),
                                  font=ctk.CTkFont(size=11))
        self.label.pack(anchor="w")


def section_label(parent, text: str, pad=(0, 6)):
    lbl = ctk.CTkLabel(parent, text=text, anchor="w",
                       font=ctk.CTkFont(size=13, weight="bold"))
    lbl.pack(anchor="w", pady=pad)
    return lbl


# ------------------------------------------------------------ message boxes
def info(parent, title: str, message: str):
    messagebox.showinfo(title, message, parent=parent)


def warn(parent, title: str, message: str):
    messagebox.showwarning(title, message, parent=parent)


def error(parent, title: str, message: str):
    messagebox.showerror(title, message, parent=parent)


def confirm(parent, title: str, message: str) -> bool:
    return bool(messagebox.askyesno(title, message, parent=parent, default="no"))
