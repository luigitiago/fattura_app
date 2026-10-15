#!/usr/bin/env python3
"""Faktura Manager – entry point.

A simple, offline, bilingual (DE/IT) desktop application to create, print and
e-mail invoices, manage customers and track payments.
"""
from __future__ import annotations

import os
import sys


def _prepare_path():
    """Make the ``src`` package importable both in dev and in a frozen build."""
    if getattr(sys, "frozen", False):
        # PyInstaller unpacks everything into _MEIPASS; the package is importable
        return
    base = os.path.dirname(os.path.abspath(__file__))
    if base not in sys.path:
        sys.path.insert(0, base)


def main() -> int:
    _prepare_path()
    try:
        from src.app import FakturaApp
    except Exception as exc:  # noqa: BLE001
        sys.stderr.write(f"Failed to start Faktura Manager: {exc}\n")
        raise

    app = FakturaApp()
    # Headless-ish self test used by the build pipeline: start, paint, quit.
    if os.environ.get("FAKTURA_SELFTEST"):
        app.after(int(os.environ.get("FAKTURA_SELFTEST_MS", "1500")), app.destroy)
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
