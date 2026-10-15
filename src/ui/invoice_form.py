"""Invoice create/edit page with dynamic line items and live totals."""
from __future__ import annotations

import customtkinter as ctk

from .. import database, utils
from . import components as ui
from .base import Page
from .clients_view import ClientDialog

UNITS = {
    "de": ["", "Stunde", "Stück", "Pauschale", "Tag", "km", "Sitzung", "Monat"],
    "it": ["", "Ora", "Pezzo", "Forfait", "Giorno", "km", "Sessione", "Mese"],
}

STATUS_CHOICES = [
    database.STATUS_OPEN,
    database.STATUS_PAID,
    database.STATUS_DRAFT,
    database.STATUS_CANCELLED,
]


class ItemRow:
    """One editable line item (description / qty / unit / price)."""

    def __init__(self, parent, form, data: dict | None = None):
        self.form = form
        self.frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray18"), corner_radius=8)
        self.frame.pack(fill="x", pady=3)
        for col, weight in enumerate([6, 1, 2, 2, 2, 0]):
            self.frame.grid_columnconfigure(col, weight=weight)

        data = data or {}
        self.desc = ctk.CTkEntry(self.frame, placeholder_text=form.tr.t("form.item.description"))
        self.desc.grid(row=0, column=0, sticky="ew", padx=(8, 4), pady=6)
        if data.get("description"):
            self.desc.insert(0, data["description"])

        self.qty = ctk.CTkEntry(self.frame, width=70)
        self.qty.grid(row=0, column=1, sticky="ew", padx=4, pady=6)
        self.qty.insert(0, utils.format_qty(data.get("quantity", 1)))

        self.unit = ctk.CTkComboBox(self.frame, width=110, values=UNITS.get(form.tr.lang, UNITS["de"]))
        self.unit.grid(row=0, column=2, sticky="ew", padx=4, pady=6)
        self.unit.set(data.get("unit", "") or "")

        self.price = ctk.CTkEntry(self.frame, width=110, placeholder_text="0,00")
        self.price.grid(row=0, column=3, sticky="ew", padx=4, pady=6)
        if data.get("unit_price") is not None:
            self.price.insert(0, utils.format_qty(data.get("unit_price")))

        self.line_label = ctk.CTkLabel(self.frame, text="0,00", anchor="e", width=90,
                                       font=ctk.CTkFont(size=12, weight="bold"))
        self.line_label.grid(row=0, column=4, sticky="e", padx=4, pady=6)

        ctk.CTkButton(self.frame, text="✕", width=32, fg_color=ui.RED, hover_color=ui.RED_HOVER,
                      command=lambda: form.remove_item(self)).grid(row=0, column=5, padx=(2, 8), pady=6)

        for widget in (self.qty, self.price):
            widget.bind("<KeyRelease>", lambda e: form.update_totals())
        self.desc.bind("<KeyRelease>", lambda e: form.update_totals())

    def get(self) -> dict | None:
        desc = self.desc.get().strip()
        if not desc:
            return None
        try:
            qty = utils.parse_amount(self.qty.get()) if self.qty.get().strip() else 0.0
            price = utils.parse_amount(self.price.get()) if self.price.get().strip() else 0.0
        except ValueError:
            raise ValueError(self.form.tr.t("form.invalid_number", row=self.frame.grid_info().get("row", "?")))
        return {
            "description": desc,
            "quantity": qty,
            "unit": self.unit.get().strip(),
            "unit_price": price,
        }

    def line_total(self) -> float:
        try:
            qty = utils.parse_amount(self.qty.get()) if self.qty.get().strip() else 0.0
            price = utils.parse_amount(self.price.get()) if self.price.get().strip() else 0.0
            return qty * price
        except ValueError:
            return 0.0

    def refresh_line(self, currency: str):
        self.line_label.configure(text=utils.format_amount(self.line_total(), currency))

    def destroy(self):
        self.frame.destroy()


class InvoiceFormPage(Page):
    def __init__(self, parent, app, invoice_id: int | None = None):
        self.invoice_id = invoice_id
        super().__init__(parent, app)

    # ------------------------------------------------------------------ UI
    def build(self):
        tr = self.tr
        self.currency = self.config.get("currency", default="€")
        self.rows: list[ItemRow] = []
        self.client_map: dict[str, int] = {}
        self._loaded = self.db.get_invoice(self.invoice_id) if self.invoice_id else None

        title = tr.t("form.title_edit") if self._loaded else tr.t("form.title_new")
        self.header(title, "", actions=[
            (tr.t("common.cancel"), lambda: self.app.show_page("invoices"), ui.GRAY, ui.GRAY_HOVER),
            (tr.t("common.save"), self.save, ui.GREEN, ui.GREEN_HOVER),
        ])

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        self._build_recipient(scroll)
        self._build_meta(scroll)
        self._build_items(scroll)
        self._build_totals(scroll)
        self._build_notes(scroll)

        self.update_totals()

    # -- recipient
    def _build_recipient(self, parent):
        tr = self.tr
        card = ui.Card(parent, title=tr.t("form.section.recipient"))
        card.pack(fill="x", pady=(0, 12))
        row = ctk.CTkFrame(card.body, fg_color="transparent")
        row.pack(fill="x")
        self.client_combo = ctk.CTkComboBox(row, width=380, values=[""], command=lambda v: None)
        self.client_combo.pack(side="left")
        ctk.CTkButton(row, text=tr.t("form.new_client"), width=150, fg_color=ui.GRAY,
                      hover_color=ui.GRAY_HOVER, command=self._new_client).pack(side="left", padx=8)
        self._reload_clients()

    def _reload_clients(self):
        clients = self.db.list_clients()
        self.client_map = {}
        values = []
        for c in clients:
            display = (c["company"] or c["name"])
            if c["insurance"]:
                display = f"{display} ({c['insurance']})"
            # ensure uniqueness of the combobox label
            base = display
            i = 2
            while display in self.client_map:
                display = f"{base} #{i}"
                i += 1
            self.client_map[display] = c["id"]
            values.append(display)
        self.client_combo.configure(values=values or [""])
        if self._loaded and self._loaded.get("client_id") in self.client_map.values():
            for label, cid in self.client_map.items():
                if cid == self._loaded["client_id"]:
                    self.client_combo.set(label)
                    break
        elif values:
            self.client_combo.set(values[0])

    def _new_client(self):
        ClientDialog(self.app, self.app, on_saved=self._reload_clients)

    # -- meta
    def _build_meta(self, parent):
        tr = self.tr
        card = ui.Card(parent, title=tr.t("form.section.meta"))
        card.pack(fill="x", pady=(0, 12))
        grid = ctk.CTkFrame(card.body, fg_color="transparent")
        grid.pack(fill="x")

        loaded = self._loaded or {}
        terms = int(self.config.get("tax", "payment_terms_days", default=14) or 14)

        self.number_entry = self._field(grid, tr.t("form.number"), 0, 0)
        self.number_entry.insert(0, loaded.get("number") or self._preview_number())
        self.number_entry.configure(state="normal")

        self.issue_entry = self._field(grid, tr.t("form.issue_date"), 0, 1)
        self.issue_entry.insert(0, utils.format_date(loaded.get("issue_date") or utils.today(), tr.lang))

        self.service_entry = self._field(grid, tr.t("form.service_date"), 1, 0)
        self.service_entry.insert(0, utils.format_date(loaded.get("service_date") or utils.today(), tr.lang))

        self.due_entry = self._field(grid, tr.t("form.due_date"), 1, 1)
        default_due = loaded.get("due_date") or utils.add_days(utils.today(), terms)
        self.due_entry.insert(0, utils.format_date(default_due, tr.lang))

        # status + vat
        ctk.CTkLabel(grid, text=tr.t("form.status"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=0, sticky="w", padx=6, pady=6)
        self.status_labels = {tr.t(f"status.{s}"): s for s in STATUS_CHOICES}
        self.status_menu = ctk.CTkOptionMenu(grid, values=list(self.status_labels), width=200)
        cur = (loaded.get("status") or database.STATUS_OPEN)
        self.status_menu.set(tr.t(f"status.{cur}"))
        self.status_menu.grid(row=3, column=0, sticky="w", padx=6, pady=(0, 6))

        ctk.CTkLabel(grid, text=tr.t("form.vat_regime"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).grid(row=2, column=1, sticky="w", padx=6, pady=6)
        self.vat_entry = ctk.CTkEntry(grid, width=200)
        self.vat_entry.grid(row=3, column=1, sticky="w", padx=6, pady=(0, 6))
        vat = loaded.get("vat_rate")
        if vat is None:
            vat = self.config.effective_vat_rate()
        self.vat_entry.insert(0, utils.format_qty(vat))
        self.vat_entry.bind("<KeyRelease>", lambda e: self.update_totals())

        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)

    def _field(self, parent, label, row, col) -> ctk.CTkEntry:
        wrap = ctk.CTkFrame(parent, fg_color="transparent")
        wrap.grid(row=row, column=col, sticky="ew", padx=6, pady=6)
        ctk.CTkLabel(wrap, text=label, anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        entry = ctk.CTkEntry(wrap, width=220)
        entry.pack(anchor="w", fill="x")
        return entry

    # -- items
    def _build_items(self, parent):
        tr = self.tr
        card = ui.Card(parent, title=tr.t("form.section.items"))
        card.pack(fill="x", pady=(0, 12))

        head = ctk.CTkFrame(card.body, fg_color="transparent")
        head.pack(fill="x")
        headers = [tr.t("form.item.description"), tr.t("form.item.quantity"), tr.t("form.item.unit"),
                   tr.t("form.item.unit_price"), tr.t("form.item.total"), ""]
        for col, (text, weight) in enumerate(zip(headers, [6, 1, 2, 2, 2, 0])):
            head.grid_columnconfigure(col, weight=weight)
            ctk.CTkLabel(head, text=text, anchor="w", text_color=("gray40", "gray65"),
                         font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=col, sticky="w", padx=6)

        self.items_container = ctk.CTkFrame(card.body, fg_color="transparent")
        self.items_container.pack(fill="x", pady=4)

        ctk.CTkButton(card.body, text=tr.t("form.add_item"), command=self.add_item,
                      fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER, width=180).pack(anchor="w", pady=(6, 0))

        if self._loaded:
            for item in self._loaded.get("items", []):
                self.add_item(item)
        if not self.rows:
            self.add_item()

    def add_item(self, data=None):
        row = ItemRow(self.items_container, self, data)
        self.rows.append(row)
        self.update_totals()

    def remove_item(self, row):
        if row in self.rows:
            self.rows.remove(row)
        row.destroy()
        if not self.rows:
            self.add_item()
        else:
            self.update_totals()

    # -- totals
    def _build_totals(self, parent):
        tr = self.tr
        card = ui.Card(parent, title=tr.t("form.section.totals"))
        card.pack(fill="x", pady=(0, 12))
        box = ctk.CTkFrame(card.body, fg_color="transparent")
        box.pack(fill="x")

        self.subtotal_label = self._total_row(box, tr.t("form.subtotal"), "")
        self.vat_total_label = self._total_row(box, tr.t("form.vat"), "")
        self.grand_label = self._total_row(box, tr.t("form.grand_total"), "", bold=True)

    def _total_row(self, parent, label, value, bold=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=2)
        font = ctk.CTkFont(size=14 if bold else 12, weight="bold" if bold else "normal")
        ctk.CTkLabel(row, text=label, anchor="e", font=font).pack(side="right", padx=(0, 10))
        val = ctk.CTkLabel(row, text=value, anchor="e", width=150, font=font,
                           text_color=ui.ACCENT if bold else None)
        val.pack(side="right")
        return val

    def _build_notes(self, parent):
        tr = self.tr
        card = ui.Card(parent, title=tr.t("form.notes"))
        card.pack(fill="x", pady=(0, 20))
        self.notes_box = ctk.CTkTextbox(card.body, height=90)
        self.notes_box.pack(fill="x")
        if self._loaded and self._loaded.get("notes"):
            self.notes_box.insert("1.0", self._loaded["notes"])

    # ------------------------------------------------------------- logic
    def _preview_number(self) -> str:
        prefix = self.config.get("tax", "number_prefix", default="RE") or "RE"
        seq = int(self.config.get("tax", "next_number", default=1) or 1)
        year = utils.today().year
        return f"{prefix}-{year}-{seq:04d}"

    def _current_vat_rate(self) -> float:
        try:
            return utils.parse_amount(self.vat_entry.get()) if self.vat_entry.get().strip() else 0.0
        except ValueError:
            return 0.0

    def update_totals(self):
        if not hasattr(self, "subtotal_label"):
            return
        net = 0.0
        for row in list(self.rows):
            row.refresh_line(self.currency)
            net += row.line_total()
        rate = self._current_vat_rate()
        vat = round(net * rate / 100.0, 2)
        gross = round(net + vat, 2)
        self.subtotal_label.configure(text=utils.format_amount(net, self.currency))
        self.vat_total_label.configure(text=f"{utils.format_amount(vat, self.currency)}  ({utils.format_qty(rate)}%)")
        self.grand_label.configure(text=utils.format_amount(gross, self.currency))

    def _collect(self):
        tr = self.tr
        selected = self.client_combo.get()
        client_id = self.client_map.get(selected)
        if not client_id:
            ui.warn(self.app, tr.t("common.warning"), tr.t("form.need_client"))
            return None

        items = []
        try:
            for row in self.rows:
                data = row.get()
                if data:
                    items.append(data)
        except ValueError as exc:
            ui.warn(self.app, tr.t("common.warning"), str(exc))
            return None
        if not items:
            ui.warn(self.app, tr.t("common.warning"), tr.t("form.need_items"))
            return None

        number = self.number_entry.get().strip() or self._preview_number()
        if self.db.number_exists(number, exclude_id=self.invoice_id):
            ui.warn(self.app, tr.t("common.warning"), f"{number} — " + tr.t("form.number"))
            return None

        data = {
            "number": number,
            "client_id": client_id,
            "issue_date": utils.iso(utils.parse_date(self.issue_entry.get()) or utils.today()),
            "service_date": utils.iso(utils.parse_date(self.service_entry.get()) or utils.today()),
            "due_date": utils.iso(utils.parse_date(self.due_entry.get()) or utils.today()),
            "status": self.status_labels.get(self.status_menu.get(), database.STATUS_OPEN),
            "vat_rate": self._current_vat_rate(),
            "notes": self.notes_box.get("1.0", "end").strip(),
        }
        return data, items

    def save(self):
        tr = self.tr
        collected = self._collect()
        if not collected:
            return
        data, items = collected

        if self.invoice_id:
            self.db.update_invoice(self.invoice_id, data, items)
        else:
            self.db.add_invoice(data, items)
            # advance the auto-number counter when the default pattern was used
            prefix = self.config.get("tax", "number_prefix", default="RE") or "RE"
            if data["number"].startswith(f"{prefix}-{utils.today().year}-"):
                try:
                    seq = int(data["number"].rsplit("-", 1)[-1]) + 1
                    self.config.set(seq, "tax", "next_number")
                    self.config.save()
                except ValueError:
                    pass

        ui.info(self.app, tr.t("common.success"), tr.t("form.saved", number=data["number"]))
        self.app.show_page("invoices")
