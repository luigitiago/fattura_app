"""First-run welcome dialog (non-blocking, unlike a message box)."""
from __future__ import annotations

import customtkinter as ctk

from . import components as ui


class WelcomeDialog(ui.ModalDialog):
    def __init__(self, master, app, on_open_settings=None):
        super().__init__(master, app, app.tr.t("welcome.title"), size=(540, 360))
        self.on_open_settings = on_open_settings
        self._build()

    def _build(self):
        tr = self.tr
        wrap = ctk.CTkFrame(self, fg_color="transparent")
        wrap.pack(fill="both", expand=True, padx=24, pady=24)

        ctk.CTkLabel(wrap, text="🧾  " + tr.t("app.title"), anchor="w",
                     font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", pady=(0, 2))
        ctk.CTkLabel(wrap, text=tr.t("app.subtitle"), anchor="w", text_color=("gray45", "gray60"),
                     font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 16))
        ctk.CTkLabel(wrap, text=tr.t("welcome.text"), anchor="w", justify="left", wraplength=470,
                     font=ctk.CTkFont(size=13)).pack(anchor="w")

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=24, pady=(0, 20))
        ctk.CTkButton(btns, text=tr.t("set.title"), command=self._open_settings,
                      width=180).pack(side="right")
        ctk.CTkButton(btns, text=tr.t("common.close"), command=self.destroy, width=120,
                      fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER).pack(side="right", padx=8)

    def _open_settings(self):
        self.destroy()
        if self.on_open_settings:
            self.on_open_settings()
