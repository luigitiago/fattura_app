"""CSV export helpers.

Files are written with a UTF-8 BOM and a semicolon separator so that Microsoft
Excel in Germany/Italy opens Umlauts and the German decimal comma correctly.
"""
from __future__ import annotations

import csv

from . import utils


def _write(path: str, header: list[str], rows: list[list]) -> str:
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(header)
        writer.writerows(rows)
    return path


def _amount(value, currency: str) -> str:
    """Excel-friendly German number (comma decimals, no thousands points)."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        num = 0.0
    return f"{num:.2f}".replace(".", ",")


def export_invoices(invoices: list[dict], path: str, tr, currency: str = "€") -> str:
    """Export the invoice list to CSV."""
    header = [
        tr.t("inv.col.number"),
        tr.t("inv.col.client"),
        tr.t("inv.col.issue_date"),
        tr.t("pdf.service_date"),
        tr.t("inv.col.due_date"),
        tr.t("inv.col.status"),
        tr.t("form.subtotal"),
        tr.t("form.vat"),
        tr.t("form.grand_total"),
        tr.t("set.tax.currency"),
    ]
    rows = []
    for inv in invoices:
        totals = inv.get("totals", {}) or {}
        client = inv.get("client_company") or inv.get("client_name") or ""
        rows.append([
            inv.get("number") or "",
            client,
            utils.format_date(inv.get("issue_date"), tr.lang),
            utils.format_date(inv.get("service_date"), tr.lang),
            utils.format_date(inv.get("due_date"), tr.lang),
            tr.t(f"status.{inv.get('display_status', 'open')}"),
            _amount(totals.get("net", 0), currency),
            _amount(totals.get("vat", 0), currency),
            _amount(totals.get("gross", 0), currency),
            currency,
        ])
    return _write(path, header, rows)


def export_clients(clients: list, path: str, tr) -> str:
    """Export the client list to CSV."""
    header = [
        tr.t("clients.col.type"),
        tr.t("clients.col.name"),
        tr.t("clients.field.contact"),
        tr.t("clients.field.street"),
        tr.t("clients.field.postal"),
        tr.t("clients.field.city"),
        tr.t("clients.field.country"),
        tr.t("clients.col.email"),
        tr.t("clients.field.phone"),
        tr.t("clients.field.vat"),
        tr.t("clients.col.insurance"),
        tr.t("clients.field.notes"),
    ]
    rows = []
    for c in clients:
        c = dict(c)
        rows.append([
            tr.t("clients.type.business") if c.get("type") == "business" else tr.t("clients.type.private"),
            c.get("company") or c.get("name") or "",
            c.get("contact") or "",
            c.get("street") or "",
            c.get("postal") or "",
            c.get("city") or "",
            c.get("country") or "",
            c.get("email") or "",
            c.get("phone") or "",
            c.get("vat") or "",
            c.get("insurance") or "",
            (c.get("notes") or "").replace("\n", " "),
        ])
    return _write(path, header, rows)
