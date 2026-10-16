"""Headless smoke test for the core (no GUI): database + PDF generation."""
import os
import sys
import tempfile

# isolate data dir
tmp = tempfile.mkdtemp(prefix="faktura_test_")
os.environ["FAKTURA_DATA_DIR"] = tmp

sys.path.insert(0, os.environ.get("PROJECT_DIR", os.getcwd()))

from src.config import Config
from src.database import Database
from src.i18n import I18n
from src import pdf_generator, utils


def main():
    cfg = Config()
    cfg.set("Musterpraxis GmbH", "issuer", "name")
    cfg.set("Hauptstraße 1", "issuer", "street")
    cfg.set("10115", "issuer", "postal")
    cfg.set("Berlin", "issuer", "city")
    cfg.set("info@musterpraxis.de", "issuer", "email")
    cfg.set("DE123456789", "tax", "vat_id")
    cfg.set("12/345/67890", "tax", "tax_number")
    cfg.set("Musterbank", "bank", "bank_name")
    cfg.set("DE89 3704 0044 0532 0130 00", "bank", "iban")
    cfg.set("COBADEFFXXX", "bank", "bic")
    cfg.set("standard", "tax", "regime")
    cfg.save()

    db = Database()
    cid = db.add_client({
        "type": "business", "name": "Frau Erika Beispiel", "company": "Beispiel AG",
        "contact": "Frau Erika Beispiel", "street": "Kundenweg 5", "postal": "50667",
        "city": "Köln", "country": "Deutschland", "email": "erika@beispiel.de",
        "phone": "+49 221 123456", "vat": "DE987654321", "insurance": "A123456789", "notes": "",
    })
    print("client id:", cid)

    items = [
        {"description": "Physiotherapie, 6 Sitzungen", "quantity": 6, "unit": "Sitzung", "unit_price": 45.50},
        {"description": "Beratungsgespräch", "quantity": 1.5, "unit": "Stunde", "unit_price": 80.0},
    ]
    inv_data = {
        "number": "RE-2026-0001", "client_id": cid, "issue_date": utils.iso(utils.today()),
        "service_date": utils.iso(utils.today()), "due_date": utils.iso(utils.add_days(utils.today(), 14)),
        "status": "open", "vat_rate": 19.0, "notes": "Vielen Dank für Ihren Auftrag.",
    }
    inv_id = db.add_invoice(inv_data, items)
    print("invoice id:", inv_id)

    inv = db.get_invoice(inv_id)
    inv["client"] = dict(db.get_client(cid))
    print("totals:", inv["totals"])
    assert inv["totals"]["net"] == round(6 * 45.50 + 1.5 * 80.0, 2)
    assert inv["totals"]["vat"] == round(inv["totals"]["net"] * 0.19, 2)

    stats = db.dashboard_stats()
    print("stats:", stats)

    for lang in ("de", "it"):
        tr = I18n(lang)
        path = os.path.join(tmp, f"test_{lang}.pdf")
        pdf_generator.generate_invoice_pdf(inv, cfg, tr, path)
        size = os.path.getsize(path)
        print(f"PDF {lang}: {path} ({size} bytes)")
        assert size > 1000, "PDF too small"

    # list + filters
    print("open invoices:", len(db.list_invoices(status="open")))
    print("paid invoices:", len(db.list_invoices(status="paid")))
    db.set_status(inv_id, "paid")
    print("after paid, paid invoices:", len(db.list_invoices(status="paid")))
    assert db.get_invoice(inv_id)["status"] == "paid"

    # client update/delete
    db.update_client(cid, {**{k: db.get_client(cid)[k] for k in db.get_client(cid).keys()}, "city": "Düsseldorf"})
    print("updated city:", db.get_client(cid)["city"])

    db.close()
    print("\nALL CORE TESTS PASSED")


if __name__ == "__main__":
    main()
