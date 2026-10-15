"""Settings page: company data, bank, tax, e-mail and general options."""
from __future__ import annotations

import os
from tkinter import filedialog

import customtkinter as ctk

from .. import mailer, utils
from . import components as ui
from .base import Page

REGIME_KEYS = ["kleinunternehmer", "standard", "reduced", "custom"]
APPEARANCE_KEYS = ["System", "Light", "Dark"]
SECURITY_KEYS = ["STARTTLS", "SSL", "None"]


class SettingsPage(Page):
    def build(self):
        tr = self.tr
        self.entries: dict[tuple, ctk.CTkEntry] = {}
        self.header(tr.t("set.title"), tr.t("set.subtitle"),
                    actions=[(tr.t("common.save"), self.save, ui.GREEN, ui.GREEN_HOVER)])

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._company_section()
        self._bank_section()
        self._tax_section()
        self._email_section()
        self._general_section()
        self._data_section()

    # ------------------------------------------------------------- helpers
    def _entry(self, parent, section: str, key: str, label: str, value="", width=260, show=None):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.pack(fill="x", pady=4)
        ctk.CTkLabel(wrap, text=label, anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        entry = ctk.CTkEntry(wrap, width=width, show=show) if show else ctk.CTkEntry(wrap, width=width)
        entry.pack(anchor="w", fill="x")
        if value not in (None, ""):
            entry.insert(0, str(value))
        self.entries[(section, key)] = entry
        return entry

    def _grid_two(self, parent) -> ctk.CTkFrame:
        grid = ctk.CTkFrame(parent, fg_color="transparent")
        grid.pack(fill="x")
        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        return grid

    def _cell(self, parent, row, col):
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, sticky="ew", padx=6, pady=4)
        return wrap

    def _get(self, section, key, default=""):
        return self.config.get(section, key, default=default)

    # ------------------------------------------------------------ sections
    def _company_section(self):
        tr = self.tr
        card = ui.Card(self.scroll, title=tr.t("set.section.company"))
        card.pack(fill="x", pady=(0, 12))
        self._entry(card.body, "issuer", "name", tr.t("set.company.name"), self._get("issuer", "name"))
        self._entry(card.body, "issuer", "street", tr.t("set.company.street"), self._get("issuer", "street"))

        g = self._grid_two(card.body)
        wrap = self._cell(g, 0, 0)
        ctk.CTkLabel(wrap, text=tr.t("set.company.postal"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(wrap)
        e.pack(fill="x")
        e.insert(0, str(self._get("issuer", "postal")))
        self.entries[("issuer", "postal")] = e
        wrap2 = self._cell(g, 0, 1)
        ctk.CTkLabel(wrap2, text=tr.t("set.company.city"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e2 = ctk.CTkEntry(wrap2)
        e2.pack(fill="x")
        e2.insert(0, str(self._get("issuer", "city")))
        self.entries[("issuer", "city")] = e2

        self._entry(card.body, "issuer", "country", tr.t("set.company.country"),
                    self._get("issuer", "country", "Deutschland"))

        g2 = self._grid_two(card.body)
        wrap = self._cell(g2, 0, 0)
        ctk.CTkLabel(wrap, text=tr.t("set.company.email"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(wrap)
        e.pack(fill="x")
        e.insert(0, str(self._get("issuer", "email")))
        self.entries[("issuer", "email")] = e
        wrap2 = self._cell(g2, 0, 1)
        ctk.CTkLabel(wrap2, text=tr.t("set.company.phone"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e2 = ctk.CTkEntry(wrap2)
        e2.pack(fill="x")
        e2.insert(0, str(self._get("issuer", "phone")))
        self.entries[("issuer", "phone")] = e2

        # logo
        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="x", pady=(6, 0))
        ctk.CTkLabel(row, text=tr.t("set.company.logo"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        line = ctk.CTkFrame(row, fg_color="transparent")
        line.pack(fill="x")
        self.logo_entry = ctk.CTkEntry(line)
        self.logo_entry.pack(side="left", fill="x", expand=True)
        self.logo_entry.insert(0, str(self._get("issuer", "logo")))
        ctk.CTkButton(line, text=tr.t("set.company.logo_choose"), width=140, fg_color=ui.GRAY,
                      hover_color=ui.GRAY_HOVER, command=self._choose_logo).pack(side="left", padx=6)
        ctk.CTkButton(line, text=tr.t("set.company.logo_clear"), width=120, fg_color=ui.RED,
                      hover_color=ui.RED_HOVER, command=lambda: self._set_entry(self.logo_entry, "")).pack(side="left")

    def _choose_logo(self):
        path = filedialog.askopenfilename(
            parent=self.app, title=self.tr.t("set.company.logo"),
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp"), ("All files", "*.*")])
        if path:
            self._set_entry(self.logo_entry, path)

    @staticmethod
    def _set_entry(entry, value):
        entry.delete(0, "end")
        if value:
            entry.insert(0, value)

    def _bank_section(self):
        tr = self.tr
        card = ui.Card(self.scroll, title=tr.t("set.section.bank"))
        card.pack(fill="x", pady=(0, 12))
        self._entry(card.body, "bank", "bank_name", tr.t("set.bank.name"), self._get("bank", "bank_name"))
        self._entry(card.body, "bank", "holder", tr.t("set.bank.holder"), self._get("bank", "holder"))
        self._entry(card.body, "bank", "iban", tr.t("set.bank.iban"), self._get("bank", "iban"))
        self._entry(card.body, "bank", "bic", tr.t("set.bank.bic"), self._get("bank", "bic"))

    def _tax_section(self):
        tr = self.tr
        card = ui.Card(self.scroll, title=tr.t("set.section.tax"))
        card.pack(fill="x", pady=(0, 12))

        g = self._grid_two(card.body)
        wrap = self._cell(g, 0, 0)
        ctk.CTkLabel(wrap, text=tr.t("set.tax.number"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(wrap)
        e.pack(fill="x")
        e.insert(0, str(self._get("tax", "tax_number")))
        self.entries[("tax", "tax_number")] = e
        wrap2 = self._cell(g, 0, 1)
        ctk.CTkLabel(wrap2, text=tr.t("set.tax.vat_id"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e2 = ctk.CTkEntry(wrap2)
        e2.pack(fill="x")
        e2.insert(0, str(self._get("tax", "vat_id")))
        self.entries[("tax", "vat_id")] = e2

        # VAT regime
        ctk.CTkLabel(card.body, text=tr.t("set.tax.regime"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(6, 2))
        self.regime_labels = {
            tr.t("set.tax.regime.kleinunternehmer"): "kleinunternehmer",
            tr.t("set.tax.regime.standard"): "standard",
            tr.t("set.tax.regime.reduced"): "reduced",
            tr.t("set.tax.regime.custom"): "custom",
        }
        cur_regime = self._get("tax", "regime", "kleinunternehmer")
        cur_label = next((k for k, v in self.regime_labels.items() if v == cur_regime),
                         list(self.regime_labels)[0])
        self.regime_menu = ctk.CTkOptionMenu(card.body, values=list(self.regime_labels), width=380)
        self.regime_menu.set(cur_label)
        self.regime_menu.pack(anchor="w")
        self._entry(card.body, "tax", "custom_rate", tr.t("set.tax.custom_rate"),
                    utils.format_qty(self._get("tax", "custom_rate", 19)), width=160)

        g2 = self._grid_two(card.body)
        wrap = self._cell(g2, 0, 0)
        ctk.CTkLabel(wrap, text=tr.t("set.tax.number_prefix"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(wrap)
        e.pack(fill="x")
        e.insert(0, str(self._get("tax", "number_prefix", "RE")))
        self.entries[("tax", "number_prefix")] = e
        wrap2 = self._cell(g2, 0, 1)
        ctk.CTkLabel(wrap2, text=tr.t("set.tax.next_number"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e2 = ctk.CTkEntry(wrap2)
        e2.pack(fill="x")
        e2.insert(0, str(self._get("tax", "next_number", 1)))
        self.entries[("tax", "next_number")] = e2

        g3 = self._grid_two(card.body)
        wrap = self._cell(g3, 0, 0)
        ctk.CTkLabel(wrap, text=tr.t("set.tax.payment_terms"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(wrap)
        e.pack(fill="x")
        e.insert(0, str(self._get("tax", "payment_terms_days", 14)))
        self.entries[("tax", "payment_terms_days")] = e
        wrap2 = self._cell(g3, 0, 1)
        ctk.CTkLabel(wrap2, text=tr.t("set.tax.currency"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e2 = ctk.CTkEntry(wrap2)
        e2.pack(fill="x")
        e2.insert(0, str(self.config.get("currency", default="€")))
        self.entries[("", "currency")] = e2

    def _email_section(self):
        tr = self.tr
        card = ui.Card(self.scroll, title=tr.t("set.section.email"))
        card.pack(fill="x", pady=(0, 12))

        self.email_enabled = ctk.CTkSwitch(card.body, text=tr.t("set.email.enabled"))
        if self._get("email", "enabled", False):
            self.email_enabled.select()
        self.email_enabled.pack(anchor="w", pady=(0, 8))

        g = self._grid_two(card.body)
        wrap = self._cell(g, 0, 0)
        ctk.CTkLabel(wrap, text=tr.t("set.email.host"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(wrap)
        e.pack(fill="x")
        e.insert(0, str(self._get("email", "host")))
        self.entries[("email", "host")] = e
        wrap2 = self._cell(g, 0, 1)
        ctk.CTkLabel(wrap2, text=tr.t("set.email.port"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e2 = ctk.CTkEntry(wrap2)
        e2.pack(fill="x")
        e2.insert(0, str(self._get("email", "port", 587)))
        self.entries[("email", "port")] = e2

        ctk.CTkLabel(card.body, text=tr.t("set.email.security"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(6, 2))
        self.security_menu = ctk.CTkOptionMenu(card.body, values=SECURITY_KEYS, width=200)
        self.security_menu.set(self._get("email", "security", "STARTTLS") or "STARTTLS")
        self.security_menu.pack(anchor="w")

        self._entry(card.body, "email", "user", tr.t("set.email.user"), self._get("email", "user"))
        self._entry(card.body, "email", "password", tr.t("set.email.password"),
                    self._get("email", "password"), show="•")
        g2 = self._grid_two(card.body)
        wrap = self._cell(g2, 0, 0)
        ctk.CTkLabel(wrap, text=tr.t("set.email.sender_name"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e = ctk.CTkEntry(wrap)
        e.pack(fill="x")
        e.insert(0, str(self._get("email", "sender_name")))
        self.entries[("email", "sender_name")] = e
        wrap2 = self._cell(g2, 0, 1)
        ctk.CTkLabel(wrap2, text=tr.t("set.email.sender_email"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        e2 = ctk.CTkEntry(wrap2)
        e2.pack(fill="x")
        e2.insert(0, str(self._get("email", "sender_email")))
        self.entries[("email", "sender_email")] = e2

        self._entry(card.body, "email", "reply_to", tr.t("set.email.reply_to"), self._get("email", "reply_to"))
        ctk.CTkButton(card.body, text=tr.t("set.email.test"), width=180, fg_color=ui.GRAY,
                      hover_color=ui.GRAY_HOVER, command=self._test_email).pack(anchor="w", pady=(8, 0))

    def _general_section(self):
        tr = self.tr
        card = ui.Card(self.scroll, title=tr.t("set.section.general"))
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card.body, text=tr.t("set.general.language"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.lang_labels = {"Deutsch": "de", "Italiano": "it"}
        self.lang_menu = ctk.CTkOptionMenu(card.body, values=list(self.lang_labels), width=200)
        cur_lang = self.config.get("language", default="de")
        self.lang_menu.set("Deutsch" if cur_lang == "de" else "Italiano")
        self.lang_menu.pack(anchor="w")

        ctk.CTkLabel(card.body, text=tr.t("set.general.appearance"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(10, 2))
        self.appearance_menu = ctk.CTkOptionMenu(
            card.body,
            values=[tr.t("appearance.system"), tr.t("appearance.light"), tr.t("appearance.dark")],
            width=200)
        cur_app = self.config.get("appearance", default="System")
        labels = {"System": tr.t("appearance.system"), "Light": tr.t("appearance.light"),
                  "Dark": tr.t("appearance.dark")}
        self.appearance_menu.set(labels.get(cur_app, tr.t("appearance.system")))
        self.appearance_menu.pack(anchor="w")
        self.appearance_labels = {tr.t("appearance.system"): "System", tr.t("appearance.light"): "Light",
                                  tr.t("appearance.dark"): "Dark"}

    def _data_section(self):
        tr = self.tr
        card = ui.Card(self.scroll, title=tr.t("set.section.data"))
        card.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(card.body, text=f"{tr.t('set.data.folder')}: {utils.user_data_dir()}",
                     anchor="w", text_color=("gray40", "gray65")).pack(anchor="w")
        ctk.CTkLabel(card.body, text=f"{tr.t('set.data.db')}: {self.db.path}",
                     anchor="w", text_color=("gray40", "gray65")).pack(anchor="w", pady=(2, 8))
        ctk.CTkButton(card.body, text=tr.t("set.data.open_folder"), width=180, fg_color=ui.GRAY,
                      hover_color=ui.GRAY_HOVER,
                      command=lambda: utils.open_path(utils.user_data_dir())).pack(anchor="w")

    # ------------------------------------------------------------- actions
    def _test_email(self):
        tr = self.tr
        self._apply_to_config()
        try:
            mailer.test_connection(self.config)
            ui.info(self.app, tr.t("common.success"), tr.t("set.email.test_ok"))
        except Exception as exc:  # noqa: BLE001
            ui.error(self.app, tr.t("common.error"), tr.t("set.email.test_fail", error=exc))

    def _apply_to_config(self):
        for (section, key), entry in self.entries.items():
            value = entry.get().strip()
            if section == "":
                self.config.set(value, key)
            else:
                self.config.set(value, section, key)
        # numeric / typed values
        try:
            self.config.set(int(utils.parse_amount(self.entries[("tax", "next_number")].get() or 1)),
                            "tax", "next_number")
        except Exception:
            pass
        try:
            self.config.set(int(utils.parse_amount(self.entries[("tax", "payment_terms_days")].get() or 14)),
                            "tax", "payment_terms_days")
        except Exception:
            pass
        try:
            self.config.set(float(utils.parse_amount(self.entries[("tax", "custom_rate")].get() or 0)),
                            "tax", "custom_rate")
        except Exception:
            pass
        try:
            self.config.set(int(utils.parse_amount(self.entries[("email", "port")].get() or 587)),
                            "email", "port")
        except Exception:
            pass

        self.config.set(self.regime_labels.get(self.regime_menu.get(), "kleinunternehmer"), "tax", "regime")
        self.config.set(self.security_menu.get(), "email", "security")
        self.config.set(self.email_enabled.get() == 1, "email", "enabled")
        self.config.set(self.lang_labels.get(self.lang_menu.get(), "de"), "language")
        self.config.set(self.appearance_labels.get(self.appearance_menu.get(), "System"), "appearance")

    def save(self):
        tr = self.tr
        old_lang = self.config.get("language", default="de")
        self._apply_to_config()
        self.config.save()

        appearance = self.config.get("appearance", default="System")
        ctk.set_appearance_mode(appearance)
        ui.info(self.app, tr.t("common.success"), tr.t("set.saved"))

        new_lang = self.config.get("language", default="de")
        if new_lang != old_lang:
            self.app.apply_language(new_lang)
        else:
            self.app.refresh_current_page()
