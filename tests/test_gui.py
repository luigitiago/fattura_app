"""GUI smoke test: build the app, visit every page/dialog, switch language, quit."""
import os
import sys
import tempfile
import traceback

tmp = tempfile.mkdtemp(prefix="faktura_gui_")
os.environ["FAKTURA_DATA_DIR"] = tmp
sys.path.insert(0, os.environ.get("PROJECT_DIR", os.getcwd()))

from src.app import FakturaApp
from src import utils
from src.config import Config
from src.ui.clients_view import ClientDialog
from src.ui.invoices_view import InvoiceDetailDialog, EmailDialog

errors = []


def seed(app):
    # configure issuer so PDF works
    app.config.set("Muster GmbH", "issuer", "name")
    app.config.set("Berlin", "issuer", "city")
    app.config.set("straße 1", "issuer", "street")
    app.config.set("10115", "issuer", "postal")
    app.config.set("standard", "tax", "regime")
    app.config.save()
    cid = app.db.add_client({
        "type": "business", "name": "Herr Test", "company": "Test AG", "contact": "Herr Test",
        "street": "Weg 2", "postal": "10115", "city": "Berlin", "country": "Deutschland",
        "email": "a@b.de", "phone": "", "vat": "", "insurance": "A1", "notes": "",
    })
    app.db.add_invoice({
        "number": "RE-2026-0001", "client_id": cid, "issue_date": utils.iso(utils.today()),
        "service_date": utils.iso(utils.today()), "due_date": utils.iso(utils.add_days(utils.today(), 14)),
        "status": "open", "vat_rate": 19.0, "notes": "Danke",
    }, [{"description": "Leistung", "quantity": 2, "unit": "Stunde", "unit_price": 50.0}])
    return cid


def step(app, fn, label):
    try:
        fn()
        print(f"  OK  {label}")
    except Exception as exc:  # noqa: BLE001
        errors.append((label, exc))
        print(f"  ERR {label}: {exc}")
        traceback.print_exc()


def main():
    app = FakturaApp()
    cid = seed(app)

    def run():
        step(app, lambda: app.show_page("dashboard"), "dashboard")
        step(app, lambda: app.show_page("clients"), "clients")
        step(app, lambda: app.show_page("invoices"), "invoices")
        step(app, lambda: app.show_page("invoice_form"), "invoice_form(new)")
        step(app, lambda: app.show_page("invoice_form", invoice_id=1), "invoice_form(edit)")
        step(app, lambda: app.show_page("settings"), "settings")
        step(app, lambda: app.apply_language("it"), "language->it")
        step(app, lambda: app.apply_language("de"), "language->de")

        def open_client():
            d = ClientDialog(app, app)
            app.after(300, d.destroy)
        step(app, open_client, "client dialog")

        def open_detail():
            d = InvoiceDetailDialog(app, app, 1)
            app.after(300, d.destroy)
        step(app, open_detail, "invoice detail dialog")

        def open_email():
            path = os.path.join(tmp, "x.pdf")
            from src import pdf_generator
            inv = app.db.get_invoice(1)
            inv["client"] = dict(app.db.get_client(1))
            pdf_generator.generate_invoice_pdf(inv, app.config, app.tr, path)
            d = EmailDialog(app, app, 1, path)
            app.after(300, d.destroy)
        step(app, open_email, "email dialog")

        app.after(400, app.destroy)

    app.after(200, run)
    try:
        app.mainloop()
    except Exception as exc:  # noqa: BLE001
        errors.append(("mainloop", exc))
        traceback.print_exc()

    print()
    if errors:
        print(f"GUI TEST FAILED with {len(errors)} error(s)")
        sys.exit(1)
    print("GUI SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
