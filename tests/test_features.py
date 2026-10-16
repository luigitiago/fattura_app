"""Tests for the new features: item code, CSV export and schema migration."""
import os
import sqlite3
import sys
import tempfile

tmp = tempfile.mkdtemp(prefix="faktura_new_")
os.environ["FAKTURA_DATA_DIR"] = tmp
sys.path.insert(0, os.environ.get("PROJECT_DIR", os.getcwd()))

from src.config import Config
from src.database import Database
from src.i18n import I18n
from src import exporter, pdf_generator, utils

ok = []


def check(label, cond):
    ok.append(bool(cond))
    print(("  OK  " if cond else "  FAIL ") + label)


def test_migration():
    """Create a v2-style DB (no 'code' column) and make sure it migrates."""
    path = os.path.join(tmp, "old.db")
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE clients (id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, name TEXT,
            company TEXT, contact TEXT, street TEXT, postal TEXT, city TEXT, country TEXT,
            email TEXT, phone TEXT, vat TEXT, insurance TEXT, notes TEXT, created_at TEXT);
        CREATE TABLE invoices (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT UNIQUE,
            client_id INTEGER, issue_date TEXT, service_date TEXT, due_date TEXT, status TEXT,
            vat_rate REAL, notes TEXT, created_at TEXT);
        CREATE TABLE invoice_items (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_id INTEGER,
            position INTEGER, description TEXT, quantity REAL, unit TEXT, unit_price REAL);
    """)
    conn.execute("INSERT INTO clients (type,name,city) VALUES ('private','Alt Kunde','Berlin')")
    conn.execute("INSERT INTO invoices (number,client_id,status,vat_rate) VALUES ('ALT-1',1,'open',19)")
    conn.execute("INSERT INTO invoice_items (invoice_id,position,description,quantity,unit,unit_price) VALUES (1,0,'Alt',1,'Stk',10)")
    conn.commit()
    conn.close()

    db = Database(path)
    # migration should have added the column
    cols = {r["name"] for r in db.conn.execute("PRAGMA table_info(invoice_items)").fetchall()}
    check("migration added 'code' column", "code" in cols)
    inv = db.get_invoice(1)
    check("old data preserved", inv["number"] == "ALT-1" and len(inv["items"]) == 1)
    # now save an item with a code
    client = dict(db.list_clients()[0])
    db.update_invoice(1, {
        "number": "ALT-1", "client_id": client["id"], "issue_date": utils.iso(utils.today()),
        "service_date": utils.iso(utils.today()), "due_date": utils.iso(utils.today()),
        "status": "open", "vat_rate": 19.0, "notes": "",
    }, [{"description": "Leistung", "code": "GOÄ 6", "quantity": 2, "unit": "Stk", "unit_price": 23.5}])
    inv = db.get_invoice(1)
    check("code persisted", inv["items"][0]["code"] == "GOÄ 6")
    db.close()


def test_pdf_with_code():
    cfg = Config()
    cfg.set("Praxis", "issuer", "name")
    cfg.set("Berlin", "issuer", "city")
    db = Database(os.path.join(tmp, "p.db"))
    cid = db.add_client({"type": "private", "name": "Max", "company": "", "contact": "",
                         "street": "A", "postal": "1", "city": "Berlin", "country": "DE",
                         "email": "", "phone": "", "vat": "", "insurance": "", "notes": ""})
    iid = db.add_invoice({
        "number": "R-1", "client_id": cid, "issue_date": utils.iso(utils.today()),
        "service_date": utils.iso(utils.today()), "due_date": utils.iso(utils.today()),
        "status": "open", "vat_rate": 0.0, "notes": "",
    }, [{"description": "Massage", "code": "28510", "quantity": 3, "unit": "Sitzung", "unit_price": 30.0}])
    inv = db.get_invoice(iid)
    inv["client"] = dict(db.get_client(cid))
    path = os.path.join(tmp, "code.pdf")
    pdf_generator.generate_invoice_pdf(inv, cfg, I18n("de"), path)
    check("pdf with code generated", os.path.getsize(path) > 1000)
    db.close()


def test_export():
    db = Database(os.path.join(tmp, "e.db"))
    cid = db.add_client({"type": "business", "name": "Kontakt", "company": "Firma GmbH",
                         "contact": "Kontakt", "street": "Straße 1", "postal": "10115",
                         "city": "München", "country": "Deutschland", "email": "a@b.de",
                         "phone": "", "vat": "DE1", "insurance": "A1", "notes": "Grüße"})
    db.add_invoice({"number": "R-2", "client_id": cid, "issue_date": utils.iso(utils.today()),
                    "service_date": utils.iso(utils.today()), "due_date": utils.iso(utils.today()),
                    "status": "open", "vat_rate": 19.0, "notes": ""},
                   [{"description": "Test", "code": "", "quantity": 2, "unit": "Stk", "unit_price": 50.0}])
    tr = I18n("de")
    p1 = exporter.export_invoices(db.list_invoices(), os.path.join(tmp, "inv.csv"), tr)
    p2 = exporter.export_clients(db.list_clients(), os.path.join(tmp, "cli.csv"), tr)
    inv_txt = open(p1, encoding="utf-8-sig").read()
    cli_txt = open(p2, encoding="utf-8-sig").read()
    check("invoice csv has header + row", "Nr." in inv_txt and "R-2" in inv_txt and "Firma GmbH" in inv_txt)
    check("invoice csv uses semicolon", ";" in inv_txt.splitlines()[0])
    check("invoice csv german decimals", "100,00" in inv_txt.replace("\t", ""))
    check("client csv has umlauts", "München" in cli_txt and "Grüße" in cli_txt)
    check("client csv has semicolon", ";" in cli_txt.splitlines()[0])
    db.close()


print("== migration ==")
test_migration()
print("== pdf with code ==")
test_pdf_with_code()
print("== csv export ==")
test_export()

print()
if all(ok):
    print(f"NEW FEATURE TESTS PASSED ({len(ok)} checks)")
else:
    print(f"FAILED: {ok.count(False)} of {len(ok)}")
    sys.exit(1)
