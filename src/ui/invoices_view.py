"""Invoices page: filters, list, detail dialog and PDF/e-mail actions."""
from __future__ import annotations

import os
import threading

import customtkinter as ctk

from .. import database, mailer, pdf_generator, utils
from . import components as ui
from .base import Page

FILTERS = [
    ("all", "inv.filter.all"),
    (database.STATUS_OPEN, "inv.filter.open"),
    (database.STATUS_PAID, "inv.filter.paid"),
    (database.STATUS_OVERDUE, "inv.filter.overdue"),
    (database.STATUS_CANCELLED, "inv.filter.cancelled"),
    (database.STATUS_DRAFT, "inv.filter.draft"),
]


class InvoicesPage(Page):
    def build(self):
        tr = self.tr
        self.current_filter = "all"
        self.header(tr.t("inv.title"), tr.t("inv.subtitle"),
                    actions=[(f"＋ {tr.t('inv.new')}", lambda: self.app.show_page("invoice_form"))])

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.pack(fill="x", pady=(0, 10))

        self.filter_buttons = {}
        for key, label_key in FILTERS:
            btn = ctk.CTkButton(controls, text=tr.t(label_key), width=100,
                                command=lambda k=key: self._set_filter(k),
                                fg_color=ui.ACCENT if key == "all" else ui.GRAY,
                                hover_color=ui.ACCENT_HOVER if key == "all" else ui.GRAY_HOVER)
            btn.pack(side="left", padx=(0, 6))
            self.filter_buttons[key] = btn

        self.search_entry = ctk.CTkEntry(self, placeholder_text=tr.t("inv.search_placeholder"), width=420)
        self.search_entry.pack(anchor="w", pady=(0, 12))
        self.search_entry.bind("<KeyRelease>", lambda e: self._reload())

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)
        self._reload()

    # ------------------------------------------------------------- filters
    def _set_filter(self, key):
        self.current_filter = key
        for k, btn in self.filter_buttons.items():
            active = k == key
            btn.configure(fg_color=ui.ACCENT if active else ui.GRAY,
                          hover_color=ui.ACCENT_HOVER if active else ui.GRAY_HOVER)
        self._reload()

    def _reload(self):
        tr = self.tr
        for child in self.list_frame.winfo_children():
            child.destroy()
        search = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        invoices = self.db.list_invoices(search, self.current_filter)
        if not invoices:
            msg = tr.t("inv.none_yet") if not search and self.current_filter == "all" else tr.t("inv.no_results")
            ctk.CTkLabel(self.list_frame, text=msg, text_color=("gray45", "gray65")).pack(pady=30)
            return
        for inv in invoices:
            self._row(inv)

    def _row(self, inv):
        tr = self.tr
        currency = self.config.get("currency", default="€")
        card = ctk.CTkFrame(self.list_frame, corner_radius=10, fg_color=("gray92", "gray17"))
        card.pack(fill="x", pady=4)
        weights = [2, 4, 2, 2, 2, 2, 0]
        for col, w in enumerate(weights):
            card.grid_columnconfigure(col, weight=w)

        ctk.CTkLabel(card, text=inv.get("number") or "—", anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky="ew", padx=10, pady=9)
        name = inv.get("client_company") or inv.get("client_name") or "—"
        ctk.CTkLabel(card, text=name, anchor="w").grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=utils.format_date(inv.get("issue_date"), tr.lang), anchor="w").grid(
            row=0, column=2, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=utils.format_date(inv.get("due_date"), tr.lang), anchor="w").grid(
            row=0, column=3, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=utils.format_amount(inv["totals"]["gross"], currency), anchor="e",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=4, sticky="ew", padx=6)

        status = inv["display_status"]
        badge = ctk.CTkFrame(card, fg_color=ui.status_color(status), corner_radius=6)
        badge.grid(row=0, column=5, sticky="w", padx=6)
        ctk.CTkLabel(badge, text=tr.t(f"status.{status}"), text_color="white",
                     font=ctk.CTkFont(size=11, weight="bold")).pack(padx=10, pady=3)

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=6, padx=8)
        ctk.CTkButton(actions, text=tr.t("action.view"), width=70, fg_color=ui.ACCENT,
                      command=lambda i=inv["id"]: self._open_detail(i)).pack(side="left", padx=2)
        ctk.CTkButton(actions, text="PDF", width=60, fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER,
                      command=lambda i=inv["id"]: self._make_pdf(i)).pack(side="left", padx=2)

    # ------------------------------------------------------------ actions
    def _open_detail(self, invoice_id):
        InvoiceDetailDialog(self.app, self.app, invoice_id, on_change=self._reload)

    def _make_pdf(self, invoice_id):
        make_invoice_pdf(self.app, invoice_id)


class InvoiceDetailDialog(ui.ModalDialog):
    def __init__(self, master, app, invoice_id, on_change=None):
        super().__init__(master, app, app.tr.t("common.details"), size=(640, 640))
        self.invoice_id = invoice_id
        self.on_change = on_change
        self.invoice = self.db.get_invoice(invoice_id)
        self._build()

    def _build(self):
        tr = self.tr
        inv = self.invoice
        if not inv:
            self.destroy()
            return
        currency = self.config.get("currency", default="€")
        self.title(f"{tr.t('pdf.title')} {inv.get('number')}")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=10)

        # header line
        top = ctk.CTkFrame(scroll, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=inv.get("number") or "—",
                     font=ctk.CTkFont(size=20, weight="bold")).pack(side="left")
        status = inv["display_status"]
        badge = ctk.CTkFrame(top, fg_color=ui.status_color(status), corner_radius=6)
        badge.pack(side="right")
        ctk.CTkLabel(badge, text=tr.t(f"status.{status}"), text_color="white",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(padx=12, pady=4)

        # recipient
        client = self.db.get_client(inv["client_id"]) if inv.get("client_id") else None
        ui.section_label(scroll, tr.t("detail.recipient"), pad=(10, 2))
        rec = ctk.CTkLabel(scroll, text=self._recipient_text(client), justify="left", anchor="w")
        rec.pack(anchor="w")

        # data
        ui.section_label(scroll, tr.t("detail.data"), pad=(12, 2))
        meta = (
            f"{tr.t('pdf.date')}: {utils.format_date(inv.get('issue_date'), tr.lang)}    "
            f"{tr.t('pdf.service_date')}: {utils.format_date(inv.get('service_date'), tr.lang)}    "
            f"{tr.t('pdf.due_date')}: {utils.format_date(inv.get('due_date'), tr.lang)}"
        )
        ctk.CTkLabel(scroll, text=meta, anchor="w").pack(anchor="w")

        # items
        ui.section_label(scroll, tr.t("detail.items"), pad=(12, 2))
        for item in inv.get("items", []):
            qty = float(item.get("quantity") or 0)
            price = float(item.get("unit_price") or 0)
            line = qty * price
            text = f"{utils.format_qty(qty)} {item.get('unit') or ''} × {utils.format_amount(price, currency)}"
            row = ctk.CTkFrame(scroll, fg_color=("gray92", "gray17"), corner_radius=6)
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=item.get("description") or "—", anchor="w").pack(side="left", padx=8, pady=6)
            ctk.CTkLabel(row, text=utils.format_amount(line, currency),
                         font=ctk.CTkFont(size=12, weight="bold")).pack(side="right", padx=8)
            ctk.CTkLabel(row, text=text, text_color=("gray45", "gray60")).pack(side="right", padx=8)

        # totals
        ui.section_label(scroll, tr.t("detail.totals"), pad=(12, 2))
        t = inv["totals"]
        totals_text = f"{tr.t('pdf.subtotal')}: {utils.format_amount(t['net'], currency)}"
        if t["vat"]:
            totals_text += f"    {tr.t('pdf.vat', rate=utils.format_qty(t['vat_rate']))}: {utils.format_amount(t['vat'], currency)}"
        ctk.CTkLabel(scroll, text=totals_text, anchor="w").pack(anchor="w")
        ctk.CTkLabel(scroll, text=f"{tr.t('pdf.grand_total')}: {utils.format_amount(t['gross'], currency)}",
                     font=ctk.CTkFont(size=15, weight="bold"), text_color=ui.ACCENT).pack(anchor="w", pady=(2, 6))

        if inv.get("notes"):
            ui.section_label(scroll, tr.t("detail.notes"), pad=(12, 2))
            ctk.CTkLabel(scroll, text=inv["notes"], justify="left", anchor="w", wraplength=580).pack(anchor="w")

        # buttons
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=14, pady=(0, 14))
        ctk.CTkButton(btns, text=tr.t("action.pdf"), command=lambda: make_invoice_pdf(self.app, self.invoice_id),
                      width=120).pack(side="left", padx=3)
        ctk.CTkButton(btns, text=tr.t("action.email"), fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER,
                      command=lambda: send_invoice_email(self.app, self.invoice_id), width=120).pack(side="left", padx=3)
        ctk.CTkButton(btns, text=tr.t("action.edit"),
                      command=lambda: self._edit(), width=120).pack(side="left", padx=3)

        if status == database.STATUS_PAID:
            ctk.CTkButton(btns, text=tr.t("action.mark_open"), fg_color=ui.AMBER, hover_color="#b45309",
                          command=lambda: self._set_status(database.STATUS_OPEN), width=150).pack(side="left", padx=3)
        else:
            ctk.CTkButton(btns, text=tr.t("action.mark_paid"), fg_color=ui.GREEN, hover_color=ui.GREEN_HOVER,
                          command=lambda: self._set_status(database.STATUS_PAID), width=150).pack(side="left", padx=3)

        ctk.CTkButton(btns, text=tr.t("common.delete"), fg_color=ui.RED, hover_color=ui.RED_HOVER,
                      command=self._delete, width=110).pack(side="right", padx=3)
        ctk.CTkButton(btns, text=tr.t("common.close"), fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER,
                      command=self.destroy, width=100).pack(side="right", padx=3)

    def _recipient_text(self, client):
        if not client:
            return "—"
        lines = []
        if client["type"] == "business" and client["company"]:
            lines.append(client["company"] + (f" · {client['contact']}" if client["contact"] else ""))
        else:
            lines.append(client["name"])
        addr = " ".join(p for p in [client["street"], client["postal"], client["city"]] if p)
        if addr:
            lines.append(addr)
        if client["email"]:
            lines.append(client["email"])
        return "\n".join(lines)

    def _set_status(self, status):
        self.db.set_status(self.invoice_id, status)
        ui.info(self.app, self.tr.t("common.success"), self.tr.t("inv.status_changed"))
        if self.on_change:
            self.on_change()
        self.destroy()

    def _edit(self):
        self.destroy()
        self.app.show_page("invoice_form", invoice_id=self.invoice_id)

    def _delete(self):
        tr = self.tr
        if ui.confirm(self.app, tr.t("common.confirm"),
                      tr.t("inv.delete_confirm", number=self.invoice.get("number"))):
            self.db.delete_invoice(self.invoice_id)
            ui.info(self.app, tr.t("common.success"), tr.t("inv.deleted"))
            if self.on_change:
                self.on_change()
            self.destroy()


# ------------------------------------------------------------- email dialog
class EmailDialog(ui.ModalDialog):
    def __init__(self, master, app, invoice_id, pdf_path):
        super().__init__(master, app, app.tr.t("mail.title"), size=(600, 520))
        self.invoice_id = invoice_id
        self.pdf_path = pdf_path
        self._result = None
        self._build()

    def _build(self):
        tr = self.tr
        inv = self.db.get_invoice(self.invoice_id)
        client = self.db.get_client(inv["client_id"]) if inv.get("client_id") else None
        issuer = self.config.get("issuer", default={}) or {}
        currency = self.config.get("currency", default="€")
        total = utils.format_amount(inv["totals"]["gross"], currency)

        ctk.CTkLabel(self, text=tr.t("mail.to"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(14, 2))
        self.to_entry = ctk.CTkEntry(self, width=520)
        self.to_entry.pack(padx=16, fill="x")
        if client and client["email"]:
            self.to_entry.insert(0, client["email"])

        ctk.CTkLabel(self, text=tr.t("mail.subject"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(10, 2))
        self.subject_entry = ctk.CTkEntry(self, width=520)
        self.subject_entry.pack(padx=16, fill="x")
        self.subject_entry.insert(0, tr.t("mail.default_subject", number=inv.get("number")))

        ctk.CTkLabel(self, text=tr.t("mail.body"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", padx=16, pady=(10, 2))
        self.body_box = ctk.CTkTextbox(self, width=520, height=220)
        self.body_box.pack(padx=16, fill="both", expand=True)
        self.body_box.insert("1.0", tr.t("mail.default_body", number=inv.get("number"), total=total,
                                         company=issuer.get("name", "")))

        att = ctk.CTkLabel(self, text=f"📎 {os.path.basename(self.pdf_path)}", anchor="w",
                           text_color=("gray40", "gray65"))
        att.pack(anchor="w", padx=16, pady=(8, 0))

        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(btns, text=tr.t("common.cancel"), fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER,
                      command=self.destroy, width=110).pack(side="right")
        self.send_btn = ctk.CTkButton(btns, text=tr.t("mail.send"), command=self._send, width=150)
        self.send_btn.pack(side="right", padx=8)

    def _send(self):
        tr = self.tr
        to = self.to_entry.get().strip()
        if not to:
            ui.warn(self, tr.t("common.warning"), tr.t("mail.no_recipient"))
            return
        self._result = None
        self.send_btn.configure(state="disabled", text=tr.t("mail.sending"))
        threading.Thread(target=self._worker_send, args=(to,), daemon=True).start()
        self._poll_result()

    def _worker_send(self, to):
        """Runs in a background thread; only sets a plain attribute."""
        tr = self.tr
        try:
            mailer.send_invoice(self.config, to, self.subject_entry.get().strip(),
                                self.body_box.get("1.0", "end").strip(), self.pdf_path)
            self._result = (True, tr.t("mail.sent", to=to))
        except Exception as exc:  # noqa: BLE001
            self._result = (False, tr.t("mail.failed", error=exc))

    def _poll_result(self):
        """Polls the result from the main (Tk) thread – safe."""
        if self._result is not None:
            ok, message = self._result
            self._result = None
            self._done(ok, message)
        else:
            self.after(150, self._poll_result)

    def _done(self, ok, message):
        self.send_btn.configure(state="normal", text=self.tr.t("mail.send"))
        if ok:
            ui.info(self.app, self.tr.t("common.success"), message)
            self.destroy()
        else:
            ui.error(self.app, self.tr.t("common.error"), message)


# ------------------------------------------------------------------ helpers
def build_invoice_payload(app, invoice_id: int) -> dict | None:
    """Return the invoice dict enriched with the full client record."""
    inv = app.db.get_invoice(invoice_id)
    if not inv:
        return None
    client = app.db.get_client(inv["client_id"]) if inv.get("client_id") else None
    inv["client"] = dict(client) if client else {}
    return inv


def make_invoice_pdf(app, invoice_id: int, ask_open: bool = True) -> str | None:
    """Generate the PDF and return its path.

    When *ask_open* is True the user is asked whether to open the file.
    """
    tr = app.tr
    issuer = app.config.get("issuer", default={}) or {}
    if not utils.is_app_configured(issuer):
        ui.warn(app, tr.t("common.warning"), tr.t("pdf.no_issuer"))
        return None
    inv = build_invoice_payload(app, invoice_id)
    if not inv:
        return None

    folder = os.path.join(utils.documents_dir(), app.config.get("issuer", "name", default="Faktura")
                          or "Faktura", "Rechnungen")
    os.makedirs(folder, exist_ok=True)
    safe_number = (inv.get("number") or f"invoice-{invoice_id}").replace("/", "-").replace("\\", "-")
    path = os.path.join(folder, f"Rechnung_{safe_number}.pdf")
    try:
        pdf_generator.generate_invoice_pdf(inv, app.config, tr, path)
    except Exception as exc:  # noqa: BLE001
        ui.error(app, tr.t("common.error"), f"{exc}")
        return None

    if ask_open and ui.confirm(app, tr.t("common.success"), tr.t("pdf.print_question")):
        if not utils.open_path(path):
            ui.warn(app, tr.t("common.warning"), tr.t("pdf.open_failed", path=path))
    return path


def send_invoice_email(app, invoice_id: int):
    tr = app.tr
    if not mailer.is_configured(app.config):
        ui.warn(app, tr.t("common.warning"), tr.t("mail.not_configured"))
        return
    path = make_invoice_pdf(app, invoice_id, ask_open=False)
    if not path:
        return
    EmailDialog(app, app, invoice_id, path)
