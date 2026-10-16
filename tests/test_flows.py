"""End-to-end write flows: create a client and an invoice through the real UI code."""
import os
import sys
import tempfile
import traceback

tmp = tempfile.mkdtemp(prefix="faktura_flow_")
os.environ["FAKTURA_DATA_DIR"] = tmp
sys.path.insert(0, os.environ.get("PROJECT_DIR", os.getcwd()))

from src import utils
from src.ui import components as ui
from src.ui.clients_view import ClientDialog
from src.ui.invoices_view import InvoiceDetailDialog

# silence all modal popups for the automated test
ui.info = lambda *a, **k: None
ui.warn = lambda *a, **k: print("   [warn]", a[2] if len(a) > 2 else a)
ui.error = lambda *a, **k: print("   [error]", a[2] if len(a) > 2 else a)
ui.confirm = lambda *a, **k: True

from src.app import FakturaApp

results = []


def check(label, cond):
    results.append((label, bool(cond)))
    print(("  OK  " if cond else "  FAIL ") + label)


def main():
    app = FakturaApp()
    app.config.set("Muster GmbH", "issuer", "name")
    app.config.set("Berlin", "issuer", "city")
    app.config.set("standard", "tax", "regime")
    app.config.save()

    base_clients = len(app.db.list_clients())  # may already contain legacy imports

    # ---- create client via dialog
    app.show_page("clients")
    d = ClientDialog(app, app)
    d.name_field.set("Mario Rossi")
    d.email_field.set("mario@example.it")
    d.city_field.set("Roma")
    d._save()
    clients = app.db.list_clients()
    check("client created", len(clients) == base_clients + 1
          and any(c["name"] == "Mario Rossi" for c in clients))

    # ---- business client
    d2 = ClientDialog(app, app)
    d2.type_seg.set(d2.tr.t("clients.type.business"))
    d2._on_type_change(d2.type_seg.get())
    d2.company_field.set("Beispiel AG")
    d2.name_field.set("Frau Beispiel")
    d2._save()
    check("business client created", len(app.db.list_clients()) == base_clients + 2)

    # ---- create invoice via form
    app.show_page("invoice_form")
    page = app.current_page
    first_label = page.client_combo.get()
    check("combo has a client selected", bool(first_label) and first_label in page.client_map)

    row = page.rows[0]
    row.desc.delete(0, "end")
    row.desc.insert(0, "Beratungsleistung")
    row.qty.delete(0, "end")
    row.qty.insert(0, "2")
    row.price.delete(0, "end")
    row.price.insert(0, "75,50")
    page.update_totals()
    check("live total computed", "151,00" in page.grand_label.cget("text") or "151" in page.subtotal_label.cget("text"))

    number = page.number_entry.get()
    page.save()
    invoices = app.db.list_invoices()
    check("invoice created", len(invoices) == 1)
    check("invoice number pattern", invoices and number.startswith(f"RE-{utils.today().year}-"))
    check("next_number advanced", int(app.config.get("tax", "next_number")) == 2)

    inv = invoices[0]
    check("invoice totals 2x75.50 net", inv["totals"]["net"] == 151.0)
    check("invoice vat 19%", inv["totals"]["vat"] == round(151.0 * 0.19, 2))

    # ---- mark as paid via detail dialog
    app.show_page("invoices")
    det = InvoiceDetailDialog(app, app, inv["id"])
    det._set_status("paid")
    check("marked paid", app.db.get_invoice(inv["id"])["status"] == "paid")
    check("paid_date set", bool(app.db.get_invoice(inv["id"])["paid_date"]))

    # ---- filters
    check("filter paid finds it", len(app.db.list_invoices(status="paid")) == 1)
    check("filter open empty", len(app.db.list_invoices(status="open")) == 0)

    # ---- edit invoice: change quantity
    app.show_page("invoice_form", invoice_id=inv["id"])
    page2 = app.current_page
    check("edit loads items", len(page2.rows) == 1)
    page2.rows[0].qty.delete(0, "end")
    page2.rows[0].qty.insert(0, "3")
    page2.save()
    check("invoice updated", app.db.get_invoice(inv["id"])["totals"]["net"] == 226.5)

    # ---- language switch keeps data
    app.apply_language("it")
    check("language switched", app.tr.lang == "it")
    check("data intact after lang switch", len(app.db.list_invoices()) == 1)
    app.apply_language("de")

    app.destroy()

    failed = [l for l, ok in results if not ok]
    print()
    if failed:
        print(f"FLOW TEST FAILED: {len(failed)} -> {failed}")
        sys.exit(1)
    print(f"FLOW TEST PASSED ({len(results)} checks)")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
