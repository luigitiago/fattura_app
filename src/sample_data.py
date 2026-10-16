"""Create clearly-labelled example data so a new user can try the app at once.

The generated invoices use the prefix ``BEISPIEL-`` so they are easy to recognise
and delete. Nothing here touches the real tax settings beyond the effective VAT
rate configured by the user.
"""
from __future__ import annotations

from datetime import timedelta

from . import utils
from .database import STATUS_OPEN, STATUS_PAID


def _client(kind: str, name: str, **rest) -> dict:
    data = {
        "type": kind, "name": name, "company": "", "contact": "", "street": "",
        "postal": "", "city": "", "country": "Deutschland", "email": "", "phone": "",
        "vat": "", "insurance": "", "notes": "",
    }
    data.update(rest)
    return data


def create_sample_data(db, config, tr) -> int:
    """Insert a few example clients and invoices. Returns the number of invoices added."""
    vat_rate = config.effective_vat_rate()
    today = utils.today()

    clients = [
        _client("private", "Max Mustermann", street="Hauptstraße 12", postal="10115",
                city="Berlin", email="max.mustermann@example.de", phone="030 111222",
                insurance="A123456789", notes=tr.t("sample.note_private")),
        _client("business", "Physiotherapie Zentrum GmbH", company="Physiotherapie Zentrum GmbH",
                contact="Frau Erika Beispiel", street="Gesundheitsweg 3", postal="50667",
                city="Köln", email="rechnung@physio-beispiel.de", phone="0221 333444",
                vat="DE987654321"),
        _client("private", "Anna Schmidt", street="Lindenallee 8", postal="80331",
                city="München", email="anna.schmidt@example.de", insurance="B987654321"),
    ]

    ids = [db.add_client(c) for c in clients]

    invoices = [
        # paid, issued last month
        (f"{tr.t('sample.prefix')}-2026-001", ids[0], today - timedelta(days=45),
         today - timedelta(days=45), today - timedelta(days=31), STATUS_PAID,
         [{"description": tr.t("sample.item1"), "code": "20710", "quantity": 6,
           "unit": "Sitzung", "unit_price": 35.0}]),
        # open, due in two weeks
        (f"{tr.t('sample.prefix')}-2026-002", ids[1], today - timedelta(days=3),
         today - timedelta(days=3), today + timedelta(days=14), STATUS_OPEN,
         [{"description": tr.t("sample.item2"), "code": "28510", "quantity": 3,
           "unit": "Sitzung", "unit_price": 30.0},
          {"description": tr.t("sample.item3"), "code": "", "quantity": 1,
           "unit": "Pauschale", "unit_price": 25.0}]),
        # overdue (open + past due date)
        (f"{tr.t('sample.prefix')}-2026-003", ids[2], today - timedelta(days=40),
         today - timedelta(days=40), today - timedelta(days=26), STATUS_OPEN,
         [{"description": tr.t("sample.item1"), "code": "20710", "quantity": 4,
           "unit": "Sitzung", "unit_price": 35.0}]),
    ]

    count = 0
    for number, client_id, issue, service, due, status, items in invoices:
        iid = db.add_invoice({
            "number": number, "client_id": client_id,
            "issue_date": utils.iso(issue), "service_date": utils.iso(service),
            "due_date": utils.iso(due), "status": status,
            "vat_rate": vat_rate, "notes": tr.t("sample.invoice_note"),
        }, items)
        if status == STATUS_PAID:
            db.set_status(iid, STATUS_PAID)
        count += 1
    return count
