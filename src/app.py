"""Main application window: sidebar navigation, routing and language switch."""
from __future__ import annotations

import os

import customtkinter as ctk

from . import utils
from .config import Config
from .database import Database
from .i18n import I18n
from .ui import components as ui
from .ui.base import Page
from .ui.clients_view import ClientsPage
from .ui.dashboard import DashboardPage
from .ui.invoice_form import InvoiceFormPage
from .ui.invoices_view import InvoicesPage
from .ui.settings_view import SettingsPage

APP_VERSION = "1.0.0"

NAV_ITEMS = [
    ("dashboard", "nav.dashboard", "▤"),
    ("clients", "nav.clients", "👤"),
    ("invoices", "nav.invoices", "🧾"),
    ("settings", "nav.settings", "⚙"),
]


class FakturaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.config = Config()
        ctk.set_appearance_mode(self.config.get("appearance", default="System"))
        ctk.set_default_color_theme("blue")

        self.tr = I18n(self.config.get("language", default="de"))
        self.db = Database()
        self._import_legacy()

        self.current_page_name = "dashboard"
        self.current_page_kwargs: dict = {}
        self.current_page: Page | None = None
        self.nav_buttons: dict[str, ctk.CTkButton] = {}

        self._configure_window()
        self._build_layout()
        self.show_page("dashboard")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------- startup
    def _import_legacy(self):
        legacy = os.path.join(utils.app_base_dir(), "krankenkasse.db")
        try:
            self.db.import_legacy_if_empty(legacy)
        except Exception:
            pass

    def _configure_window(self):
        self.geometry("1180x760")
        self.minsize(1000, 640)
        self._update_title()
        # optional window icon
        icon = utils.resource_path("assets", "icon.png")
        try:
            from tkinter import PhotoImage
            if os.path.exists(icon):
                self._icon_img = PhotoImage(file=icon)
                self.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _update_title(self):
        name = self.config.get("issuer", "name", default="") or self.tr.t("app.title")
        self.title(f"{self.tr.t('app.title')}  ·  {name}" if name != self.tr.t("app.title")
                   else self.tr.t("app.title"))

    # -------------------------------------------------------------- layout
    def _build_layout(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=230, corner_radius=0, fg_color=("#f3f4f6", "#11151c"))
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(2, weight=1)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=18, pady=(22, 6))
        self.brand_title = ctk.CTkLabel(brand, text=self.tr.t("app.title"), anchor="w",
                                        font=ctk.CTkFont(size=20, weight="bold"))
        self.brand_title.pack(anchor="w")
        self.brand_sub = ctk.CTkLabel(brand, text=self.tr.t("app.subtitle"), anchor="w",
                                      text_color=("gray45", "gray60"), font=ctk.CTkFont(size=11))
        self.brand_sub.pack(anchor="w")

        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="ew", padx=12, pady=(16, 0))
        for key, label_key, glyph in NAV_ITEMS:
            btn = ctk.CTkButton(
                nav, text=f"  {glyph}   {self.tr.t(label_key)}", anchor="w", height=42,
                corner_radius=8, fg_color="transparent", hover_color=("#e5e7eb", "#1b2230"),
                text_color=("gray20", "gray85"),
                command=lambda k=key: self.show_page(k))
            btn.pack(fill="x", pady=3)
            self.nav_buttons[key] = btn

        new_btn = ctk.CTkButton(self.sidebar, text=f"＋  {self.tr.t('nav.new_invoice')}", height=42,
                                corner_radius=8, fg_color=ui.ACCENT, hover_color=ui.ACCENT_HOVER,
                                command=lambda: self.show_page("invoice_form"))
        new_btn.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 10))
        self.new_btn = new_btn

        # language switch
        self.lang_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.lang_frame.grid(row=4, column=0, sticky="ew", padx=14, pady=(4, 4))
        self.lang_label = ctk.CTkLabel(self.lang_frame, text=self.tr.t("language"), anchor="w",
                                       font=ctk.CTkFont(size=11, weight="bold"))
        self.lang_label.pack(anchor="w", pady=(0, 3))
        self.lang_seg = ctk.CTkSegmentedButton(
            self.lang_frame, values=["DE", "IT"], command=self._on_language_switch)
        self.lang_seg.set("DE" if self.tr.lang == "de" else "IT")
        self.lang_seg.pack(fill="x")

        self.version_label = ctk.CTkLabel(self.sidebar, text=f"v{APP_VERSION}", anchor="w",
                                          text_color=("gray55", "gray50"), font=ctk.CTkFont(size=10))
        self.version_label.grid(row=5, column=0, sticky="w", padx=18, pady=(2, 14))

        # content area
        self.content = ctk.CTkFrame(self, fg_color=("#fafafa", "#0d1117"), corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    # -------------------------------------------------------------- routing
    def show_page(self, name: str, **kwargs):
        self.current_page_name = name
        self.current_page_kwargs = kwargs
        if self.current_page is not None:
            self.current_page.destroy()
            self.current_page = None

        page = self._create_page(name, kwargs)
        page.grid(row=0, column=0, sticky="nsew", padx=22, pady=20)
        self.current_page = page
        self._highlight_nav(name)

    def _create_page(self, name: str, kwargs: dict) -> Page:
        if name == "clients":
            return ClientsPage(self.content, self)
        if name == "invoices":
            return InvoicesPage(self.content, self)
        if name == "invoice_form":
            return InvoiceFormPage(self.content, self, invoice_id=kwargs.get("invoice_id"))
        if name == "settings":
            return SettingsPage(self.content, self)
        return DashboardPage(self.content, self)

    def _highlight_nav(self, name: str):
        active_key = "invoices" if name == "invoice_form" else name
        for key, btn in self.nav_buttons.items():
            if key == active_key:
                btn.configure(fg_color=("#dbeafe", "#17324d"), text_color=(ui.ACCENT, "#93c5fd"))
            else:
                btn.configure(fg_color="transparent", text_color=("gray20", "gray85"))

    def refresh_current_page(self):
        self.show_page(self.current_page_name, **self.current_page_kwargs)

    # ------------------------------------------------------------- language
    def _on_language_switch(self, value: str):
        lang = "de" if value == "DE" else "it"
        if lang == self.tr.lang:
            return
        self.config.set(lang, "language")
        self.config.save()
        self.apply_language(lang)

    def apply_language(self, lang: str):
        self.tr.set_language(lang)
        self._retranslate()
        self.refresh_current_page()

    def _retranslate(self):
        self._update_title()
        self.brand_title.configure(text=self.tr.t("app.title"))
        self.brand_sub.configure(text=self.tr.t("app.subtitle"))
        for key, label_key, glyph in NAV_ITEMS:
            self.nav_buttons[key].configure(text=f"  {glyph}   {self.tr.t(label_key)}")
        self.new_btn.configure(text=f"＋  {self.tr.t('nav.new_invoice')}")
        self.lang_label.configure(text=self.tr.t("language"))
        self.lang_seg.set("DE" if self.tr.lang == "de" else "IT")

    # --------------------------------------------------------------- close
    def _on_close(self):
        try:
            self.db.close()
        finally:
            self.destroy()
