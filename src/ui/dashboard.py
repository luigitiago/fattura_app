"""Dashboard / overview page."""
from __future__ import annotations

import customtkinter as ctk

from .. import utils
from . import components as ui
from .base import Page


class DashboardPage(Page):
    def build(self) -> None:
        tr = self.tr
        self.header(
            tr.t("dash.title"),
            tr.t("dash.subtitle"),
            actions=[(f"＋ {tr.t('nav.new_invoice')}", lambda: self.app.show_page("invoice_form"))],
        )

        if not utils.is_app_configured(self.config.get("issuer", default={})):
            banner = ctk.CTkFrame(self, fg_color=("#fef3c7", "#3a2e10"), corner_radius=10)
            banner.pack(fill="x", pady=(0, 14))
            ctk.CTkLabel(banner, text="⚠  " + tr.t("dash.company_missing"), wraplength=880,
                         justify="left", text_color=("#92400e", "#fbbf24"),
                         font=ctk.CTkFont(size=12)).pack(anchor="w", padx=14, pady=10)

        stats = self.db.dashboard_stats()
        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.pack(fill="x", pady=(0, 18))
        for col in range(4):
            cards.grid_columnconfigure(col, weight=1, uniform="stat")

        currency = self.config.get("currency", default="€")
        items = [
            (tr.t("dash.card.invoices"), str(stats["invoice_count"]), ui.ACCENT),
            (tr.t("dash.card.open"), utils.format_amount(stats["open_amount"], currency), ui.AMBER),
            (tr.t("dash.card.paid"), utils.format_amount(stats["paid_amount"], currency), ui.GREEN),
            (tr.t("dash.card.overdue"), str(stats["overdue_count"]), ui.RED),
        ]
        for idx, (label, value, color) in enumerate(items):
            card = ui.StatCard(cards, label, value, color)
            card.grid(row=0, column=idx, sticky="nsew", padx=(0 if idx == 0 else 10, 0))

        recent = ui.Card(self, title=tr.t("dash.recent"))
        recent.pack(fill="both", expand=True)

        invoices = self.db.list_invoices()[:6]
        if not invoices:
            empty = ctk.CTkFrame(recent.body, fg_color="transparent")
            empty.pack(expand=True, pady=30)
            ctk.CTkLabel(empty, text=tr.t("dash.empty"), font=ctk.CTkFont(size=14, weight="bold"),
                         text_color=("gray40", "gray65")).pack()
            ctk.CTkLabel(empty, text=tr.t("dash.empty_hint"), justify="center",
                         text_color=("gray50", "gray60")).pack(pady=(6, 0))
            return

        # table header
        self._table_header(recent.body, [
            (tr.t("inv.col.number"), 0, "w"),
            (tr.t("inv.col.client"), 1, "w"),
            (tr.t("inv.col.issue_date"), 2, "w"),
            (tr.t("inv.col.total"), 3, "e"),
            (tr.t("inv.col.status"), 4, "w"),
        ])

        for inv in invoices:
            self._table_row(recent.body, inv)

    def _table_header(self, parent, cols):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", pady=(0, 4))
        for text, col, anchor in cols:
            header.grid_columnconfigure(col, weight=1)
            ctk.CTkLabel(header, text=text, anchor=anchor, text_color=("gray40", "gray65"),
                         font=ctk.CTkFont(size=11, weight="bold")).grid(
                row=0, column=col, sticky="ew", padx=6)

    def _table_row(self, parent, inv):
        tr = self.tr
        currency = self.config.get("currency", default="€")
        row = ctk.CTkFrame(parent, fg_color=("gray92", "gray17"), corner_radius=8)
        row.pack(fill="x", pady=3)
        for col in range(5):
            row.grid_columnconfigure(col, weight=1)

        name = inv.get("client_company") or inv.get("client_name") or "—"
        ctk.CTkLabel(row, text=inv.get("number") or "—", anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(row, text=name, anchor="w").grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkLabel(row, text=utils.format_date(inv.get("issue_date"), tr.lang), anchor="w").grid(
            row=0, column=2, sticky="ew", padx=6)
        ctk.CTkLabel(row, text=utils.format_amount(inv["totals"]["gross"], currency), anchor="e",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=3, sticky="ew", padx=6)

        status = inv["display_status"]
        badge = ctk.CTkFrame(row, fg_color=ui.status_color(status), corner_radius=6)
        badge.grid(row=0, column=4, sticky="w", padx=8)
        ctk.CTkLabel(badge, text=tr.t(f"status.{status}"), text_color="white",
                     font=ctk.CTkFont(size=11, weight="bold")).pack(padx=10, pady=3)
