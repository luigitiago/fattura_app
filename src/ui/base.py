"""Base class shared by every content page."""
from __future__ import annotations

import customtkinter as ctk

from . import components as ui


class Page(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="transparent")
        self.app = app
        self.db = app.db
        self.config = app.config
        self.tr = app.tr
        self.build()

    # subclasses override --------------------------------------------------
    def build(self) -> None:  # pragma: no cover - abstract
        raise NotImplementedError

    def refresh(self) -> None:
        """Rebuild the page content (used after external changes)."""
        for child in self.winfo_children():
            child.destroy()
        self.build()

    # shared helpers -------------------------------------------------------
    def header(self, title: str, subtitle: str = "", actions: list[tuple] | None = None) -> ctk.CTkFrame:
        """Standard page header: title on the left, optional action buttons right.

        ``actions`` is a list of ``(text, command)`` or ``(text, command, fg_color)``.
        """
        bar = ctk.CTkFrame(self, fg_color="transparent")
        bar.pack(fill="x", pady=(0, 16))

        left = ctk.CTkFrame(bar, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(left, text=title, anchor="w",
                     font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(left, text=subtitle, anchor="w", text_color=("gray40", "gray65"),
                         font=ctk.CTkFont(size=12)).pack(anchor="w")

        if actions:
            right = ctk.CTkFrame(bar, fg_color="transparent")
            right.pack(side="right")
            for action in actions:
                text, command = action[0], action[1]
                color = action[2] if len(action) > 2 else ui.ACCENT
                hover = action[3] if len(action) > 3 else ui.ACCENT_HOVER
                ctk.CTkButton(right, text=text, command=command, fg_color=color,
                              hover_color=hover, width=150).pack(side="left", padx=(8, 0))
        return bar
