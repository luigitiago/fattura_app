"""Small cross-platform helpers: paths, formatting and platform integration."""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import date, datetime, timedelta

APP_FOLDER_NAME = "FakturaManager"
DB_FILENAME = "faktura.db"
CONFIG_FILENAME = "config.json"


# --------------------------------------------------------------------- paths
def is_frozen() -> bool:
    """True when running from a PyInstaller bundle."""
    return getattr(sys, "frozen", False)


def app_base_dir() -> str:
    """Directory that contains the application (the .exe when frozen)."""
    if is_frozen():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def resource_path(*parts: str) -> str:
    """Path to a bundled resource, works both in dev and in a PyInstaller build."""
    if is_frozen():
        base = getattr(sys, "_MEIPASS", app_base_dir())
    else:
        base = app_base_dir()
    return os.path.join(base, *parts)


def user_data_dir() -> str:
    """Platform-appropriate writable folder where the database lives."""
    custom = os.environ.get("FAKTURA_DATA_DIR")
    if custom:
        base = custom
    elif sys.platform.startswith("win"):
        base = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_FOLDER_NAME)
    elif sys.platform == "darwin":
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_FOLDER_NAME)
    else:
        xdg = os.environ.get("XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share"))
        base = os.path.join(xdg, APP_FOLDER_NAME)
    os.makedirs(base, exist_ok=True)
    return base


def default_db_path() -> str:
    return os.path.join(user_data_dir(), DB_FILENAME)


def default_config_path() -> str:
    return os.path.join(user_data_dir(), CONFIG_FILENAME)


def documents_dir() -> str:
    """Best-effort user Documents folder, falling back to the home directory."""
    home = os.path.expanduser("~")
    for name in ("Documents", "Documenti"):
        candidate = os.path.join(home, name)
        if os.path.isdir(candidate):
            return candidate
    return home


# ---------------------------------------------------------------- formatting
def parse_amount(value) -> float:
    """Parse a number that may be written with ',' or '.' as decimal separator."""
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace("€", "").replace(" ", "")
    if not text:
        return 0.0
    # 1.234,56 -> 1234.56 ; 1234.56 -> 1234.56 ; 1234,56 -> 1234.56
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    return float(text)


def format_amount(value: float, currency: str = "€") -> str:
    """Format like German/Italian convention: 1.234,56 €."""
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    formatted = f"{value:,.2f}"
    # swap separators to the German/Italian style
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} {currency}".strip()


def format_qty(value: float) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        value = 0.0
    if abs(value - round(value)) < 1e-9:
        return str(int(round(value)))
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------- dates
def today() -> date:
    return date.today()


def parse_date(value) -> date | None:
    """Parse common date formats (ISO, dd.mm.yyyy, dd/mm/yyyy)."""
    if not value:
        return None
    if isinstance(value, date):
        return value
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def iso(value) -> str:
    """Return YYYY-MM-DD for storing in the database."""
    d = parse_date(value)
    return d.isoformat() if d else ""


def format_date(value, lang: str = "de") -> str:
    d = parse_date(value)
    if not d:
        return ""
    return d.strftime("%d.%m.%Y") if lang == "de" else d.strftime("%d/%m/%Y")


def add_days(value, days: int) -> date:
    d = parse_date(value) or date.today()
    return d + timedelta(days=int(days))


# ------------------------------------------------------------ OS integration
def open_path(path: str) -> bool:
    """Open a file or folder with the default application."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
        return True
    except Exception:
        return False


def is_app_configured(issuer: dict) -> bool:
    """Heuristic: does the issuer block contain enough data to issue invoices?"""
    return bool((issuer.get("name") or "").strip() and (issuer.get("city") or "").strip())
