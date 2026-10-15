"""SQLite data layer.

The schema is intentionally simple and portable.  Internal status values are
stored in English (``open``, ``paid``, ``overdue``, ``cancelled``, ``draft``)
and translated only in the user interface.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import date

from . import utils

SCHEMA_VERSION = 2

STATUS_OPEN = "open"
STATUS_PAID = "paid"
STATUS_OVERDUE = "overdue"
STATUS_CANCELLED = "cancelled"
STATUS_DRAFT = "draft"

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    type        TEXT NOT NULL DEFAULT 'private',   -- private | business
    name        TEXT NOT NULL,
    company     TEXT,
    contact     TEXT,
    street      TEXT,
    postal      TEXT,
    city        TEXT,
    country     TEXT,
    email       TEXT,
    phone       TEXT,
    vat         TEXT,
    insurance   TEXT,
    notes       TEXT,
    created_at  TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS invoices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    number       TEXT UNIQUE,
    client_id    INTEGER,
    issue_date   TEXT,
    service_date TEXT,
    due_date     TEXT,
    status       TEXT DEFAULT 'open',
    vat_rate     REAL DEFAULT 0,
    notes        TEXT,
    paid_date    TEXT,
    created_at   TEXT DEFAULT (datetime('now')),
    updated_at   TEXT,
    FOREIGN KEY (client_id) REFERENCES clients(id)
);

CREATE TABLE IF NOT EXISTS invoice_items (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  INTEGER NOT NULL,
    position    INTEGER DEFAULT 0,
    description TEXT,
    quantity    REAL DEFAULT 1,
    unit        TEXT,
    unit_price  REAL DEFAULT 0,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
"""


class Database:
    def __init__(self, path: str | None = None):
        self.path = path or utils.default_db_path()
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_schema()

    # -------------------------------------------------------------- schema
    def _init_schema(self) -> None:
        self.conn.executescript(SCHEMA)
        self.conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('schema_version', ?)",
            (str(SCHEMA_VERSION),),
        )
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass

    # ------------------------------------------------------------- helpers
    def _rows(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        cur = self.conn.execute(sql, params)
        return cur.fetchall()

    def _row(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        cur = self.conn.execute(sql, params)
        return cur.fetchone()

    def _exec(self, sql: str, params: tuple = ()) -> int:
        cur = self.conn.execute(sql, params)
        self.conn.commit()
        return cur.lastrowid

    # ------------------------------------------------------------- clients
    def list_clients(self, search: str = "") -> list[sqlite3.Row]:
        if search:
            like = f"%{search.strip()}%"
            return self._rows(
                """SELECT * FROM clients
                   WHERE name LIKE ? OR company LIKE ? OR contact LIKE ?
                         OR insurance LIKE ? OR email LIKE ? OR city LIKE ?
                   ORDER BY COALESCE(NULLIF(company,''), name) COLLATE NOCASE""",
                (like, like, like, like, like, like),
            )
        return self._rows(
            """SELECT * FROM clients
               ORDER BY COALESCE(NULLIF(company,''), name) COLLATE NOCASE"""
        )

    def get_client(self, client_id: int) -> sqlite3.Row | None:
        return self._row("SELECT * FROM clients WHERE id = ?", (client_id,))

    def add_client(self, data: dict) -> int:
        return self._exec(
            """INSERT INTO clients
               (type, name, company, contact, street, postal, city, country,
                email, phone, vat, insurance, notes)
               VALUES (:type, :name, :company, :contact, :street, :postal, :city,
                       :country, :email, :phone, :vat, :insurance, :notes)""",
            data,
        )

    def update_client(self, client_id: int, data: dict) -> None:
        data = dict(data)
        data["id"] = client_id
        self.conn.execute(
            """UPDATE clients SET
               type=:type, name=:name, company=:company, contact=:contact,
               street=:street, postal=:postal, city=:city, country=:country,
               email=:email, phone=:phone, vat=:vat, insurance=:insurance,
               notes=:notes
               WHERE id=:id""",
            data,
        )
        self.conn.commit()

    def delete_client(self, client_id: int) -> None:
        self.conn.execute("UPDATE invoices SET client_id = NULL WHERE client_id = ?", (client_id,))
        self.conn.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        self.conn.commit()

    def client_invoice_count(self, client_id: int) -> int:
        row = self._row("SELECT COUNT(*) AS n FROM invoices WHERE client_id = ?", (client_id,))
        return row["n"] if row else 0

    def client_display_name(self, client) -> str:
        if client is None:
            return ""
        if isinstance(client, sqlite3.Row):
            client = dict(client)
        if client.get("type") == "business" and (client.get("company") or "").strip():
            return client["company"].strip()
        return (client.get("name") or "").strip()

    # ------------------------------------------------------------ invoices
    def list_invoices(self, search: str = "", status: str = "all") -> list[sqlite3.Row]:
        sql = """
            SELECT i.*, c.name AS client_name, c.company AS client_company
            FROM invoices i
            LEFT JOIN clients c ON c.id = i.client_id
        """
        params: list = []
        where = []
        if search:
            like = f"%{search.strip()}%"
            where.append("(i.number LIKE ? OR c.name LIKE ? OR c.company LIKE ?)")
            params.extend([like, like, like])
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY i.issue_date DESC, i.id DESC"
        rows = [dict(r) for r in self._rows(sql, tuple(params))]
        for r in rows:
            r["display_status"] = self.effective_status(r)
            r["totals"] = self.invoice_totals(r["id"], r.get("vat_rate") or 0)
        if status and status != "all":
            rows = [r for r in rows if r["display_status"] == status]
        return rows

    def get_invoice(self, invoice_id: int) -> dict | None:
        row = self._row(
            """SELECT i.*, c.name AS client_name, c.company AS client_company
               FROM invoices i LEFT JOIN clients c ON c.id = i.client_id
               WHERE i.id = ?""",
            (invoice_id,),
        )
        if not row:
            return None
        data = dict(row)
        data["display_status"] = self.effective_status(data)
        data["items"] = [dict(r) for r in self.get_items(invoice_id)]
        data["totals"] = self.invoice_totals(invoice_id, data.get("vat_rate") or 0)
        return data

    def get_items(self, invoice_id: int) -> list[sqlite3.Row]:
        return self._rows(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY position, id",
            (invoice_id,),
        )

    def add_invoice(self, data: dict, items: list[dict]) -> int:
        invoice_id = self._exec(
            """INSERT INTO invoices
               (number, client_id, issue_date, service_date, due_date,
                status, vat_rate, notes, updated_at)
               VALUES (:number, :client_id, :issue_date, :service_date, :due_date,
                       :status, :vat_rate, :notes, datetime('now'))""",
            data,
        )
        self._save_items(invoice_id, items)
        return invoice_id

    def update_invoice(self, invoice_id: int, data: dict, items: list[dict]) -> None:
        data = dict(data)
        data["id"] = invoice_id
        self.conn.execute(
            """UPDATE invoices SET
               number=:number, client_id=:client_id, issue_date=:issue_date,
               service_date=:service_date, due_date=:due_date, status=:status,
               vat_rate=:vat_rate, notes=:notes, updated_at=datetime('now')
               WHERE id=:id""",
            data,
        )
        self.conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        self.conn.commit()
        self._save_items(invoice_id, items)

    def _save_items(self, invoice_id: int, items: list[dict]) -> None:
        for pos, item in enumerate(items):
            self.conn.execute(
                """INSERT INTO invoice_items
                   (invoice_id, position, description, quantity, unit, unit_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    invoice_id,
                    pos,
                    item.get("description", ""),
                    float(item.get("quantity") or 0),
                    item.get("unit", ""),
                    float(item.get("unit_price") or 0),
                ),
            )
        self.conn.commit()

    def delete_invoice(self, invoice_id: int) -> None:
        self.conn.execute("DELETE FROM invoice_items WHERE invoice_id = ?", (invoice_id,))
        self.conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        self.conn.commit()

    def set_status(self, invoice_id: int, status: str) -> None:
        if status == STATUS_PAID:
            self.conn.execute(
                "UPDATE invoices SET status = ?, paid_date = date('now'), updated_at = datetime('now') WHERE id = ?",
                (status, invoice_id),
            )
        else:
            self.conn.execute(
                "UPDATE invoices SET status = ?, paid_date = NULL, updated_at = datetime('now') WHERE id = ?",
                (status, invoice_id),
            )
        self.conn.commit()

    def number_exists(self, number: str, exclude_id: int | None = None) -> bool:
        if exclude_id:
            row = self._row("SELECT 1 FROM invoices WHERE number = ? AND id != ?", (number, exclude_id))
        else:
            row = self._row("SELECT 1 FROM invoices WHERE number = ?", (number,))
        return row is not None

    # ------------------------------------------------------------- totals
    def invoice_totals(self, invoice_id: int, vat_rate: float) -> dict:
        rows = self.get_items(invoice_id)
        net = 0.0
        for r in rows:
            net += float(r["quantity"] or 0) * float(r["unit_price"] or 0)
        vat = round(net * float(vat_rate or 0) / 100.0, 2)
        gross = round(net + vat, 2)
        return {"net": round(net, 2), "vat": vat, "gross": gross, "vat_rate": float(vat_rate or 0)}

    @staticmethod
    def effective_status(invoice: dict) -> str:
        """Return the status shown to the user (computes 'overdue' on the fly)."""
        status = invoice.get("status") or STATUS_OPEN
        if status == STATUS_OPEN:
            due = utils.parse_date(invoice.get("due_date"))
            if due and due < date.today():
                return STATUS_OVERDUE
        return status

    # -------------------------------------------------------------- stats
    def dashboard_stats(self) -> dict:
        invoices = self.list_invoices()
        total_count = len(invoices)
        open_amount = 0.0
        paid_amount = 0.0
        overdue_count = 0
        for inv in invoices:
            gross = inv["totals"]["gross"]
            if inv["display_status"] in (STATUS_OPEN, STATUS_OVERDUE):
                open_amount += gross
            elif inv["display_status"] == STATUS_PAID:
                paid_amount += gross
            if inv["display_status"] == STATUS_OVERDUE:
                overdue_count += 1
        client_row = self._row("SELECT COUNT(*) AS n FROM clients")
        return {
            "invoice_count": total_count,
            "client_count": client_row["n"] if client_row else 0,
            "open_amount": round(open_amount, 2),
            "paid_amount": round(paid_amount, 2),
            "overdue_count": overdue_count,
        }

    # --------------------------------------------------------- migration
    def import_legacy_if_empty(self, legacy_path: str) -> int:
        """Import clients/invoices from the old ``krankenkasse.db`` once.

        Returns the number of imported clients (0 when nothing was done).
        """
        if not legacy_path or not os.path.exists(legacy_path):
            return 0
        if os.path.abspath(self.path) == os.path.abspath(legacy_path):
            return 0
        # never import twice
        flag = self._row("SELECT value FROM meta WHERE key = 'legacy_imported'")
        if flag and flag["value"] == "1":
            return 0
        row = self._row("SELECT COUNT(*) AS n FROM clients")
        if row and row["n"] > 0:
            self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('legacy_imported', '1')")
            self.conn.commit()
            return 0
        try:
            legacy = sqlite3.connect(legacy_path)
            legacy.row_factory = sqlite3.Row
            tables = {r["name"] for r in legacy.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()}
            if "clients" not in tables:
                legacy.close()
                return 0
            imported = 0
            id_map: dict[int, int] = {}
            for c in legacy.execute("SELECT * FROM clients").fetchall():
                c = dict(c)
                new_id = self.add_client({
                    "type": "private",
                    "name": (c.get("name") or "").strip(),
                    "company": "",
                    "contact": "",
                    "street": "",
                    "postal": "",
                    "city": "",
                    "country": "Deutschland",
                    "email": c.get("email") or "",
                    "phone": "",
                    "vat": "",
                    "insurance": c.get("insurance_num") or "",
                    "notes": "",
                })
                id_map[c["id"]] = new_id
                imported += 1
            if "invoices" in tables:
                for inv in legacy.execute("SELECT * FROM invoices").fetchall():
                    inv = dict(inv)
                    status = "paid" if str(inv.get("status", "")).lower().startswith("bez") else "open"
                    items = [{
                        "description": inv.get("description") or "Leistung",
                        "quantity": 1,
                        "unit": "",
                        "unit_price": float(inv.get("amount") or 0),
                    }]
                    self.add_invoice({
                        "number": f"ALT-{inv['id']:04d}",
                        "client_id": id_map.get(inv.get("client_id")),
                        "issue_date": utils.iso(inv.get("date")),
                        "service_date": utils.iso(inv.get("date")),
                        "due_date": utils.iso(inv.get("date")),
                        "status": status,
                        "vat_rate": 0,
                        "notes": "",
                    }, items)
            legacy.close()
            self.conn.execute("INSERT OR REPLACE INTO meta (key, value) VALUES ('legacy_imported', '1')")
            self.conn.commit()
            return imported
        except Exception:
            return 0
