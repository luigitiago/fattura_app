"""Persistent application settings stored as JSON in the user data folder."""
from __future__ import annotations

import copy
import json
import os

from . import utils

# Defaults mirror a typical small business / freelancer in Germany.
DEFAULT_CONFIG: dict = {
    "language": "de",
    "appearance": "System",  # System | Light | Dark
    "currency": "€",
    "first_run": True,
    "issuer": {
        "name": "",
        "street": "",
        "postal": "",
        "city": "",
        "country": "Deutschland",
        "email": "",
        "phone": "",
        "web": "",
        "logo": "",
    },
    "bank": {
        "bank_name": "",
        "holder": "",
        "iban": "",
        "bic": "",
    },
    "tax": {
        "tax_number": "",
        "vat_id": "",
        # kleinunternehmer | standard | reduced | custom
        "regime": "kleinunternehmer",
        "custom_rate": 19.0,
        "number_prefix": "RE",
        "next_number": 1,
        "payment_terms_days": 14,
    },
    "email": {
        "enabled": False,
        "host": "",
        "port": 587,
        "security": "STARTTLS",  # STARTTLS | SSL | None
        "user": "",
        "password": "",
        "sender_name": "",
        "sender_email": "",
        "reply_to": "",
    },
    # persist a small "remembered" delay counter used by the UI not needed here
}


def _deep_merge(base: dict, override: dict) -> dict:
    """Return base updated with override, recursively for dict values."""
    result = copy.deepcopy(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


class Config:
    """Load / save the JSON config, falling back to defaults on any error."""

    def __init__(self, path: str | None = None):
        self.path = path or utils.default_config_path()
        self.data: dict = copy.deepcopy(DEFAULT_CONFIG)
        self.load()

    def load(self) -> None:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                self.data = _deep_merge(DEFAULT_CONFIG, stored)
            except Exception:
                self.data = copy.deepcopy(DEFAULT_CONFIG)

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(self.data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

    # convenience accessors -------------------------------------------------
    def get(self, *keys, default=None):
        node = self.data
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default
        return node

    def set(self, value, *keys) -> None:
        node = self.data
        for key in keys[:-1]:
            node = node.setdefault(key, {})
        node[keys[-1]] = value

    # ---- VAT helpers ------------------------------------------------------
    def effective_vat_rate(self) -> float:
        regime = self.get("tax", "regime", default="kleinunternehmer")
        if regime == "standard":
            return 19.0
        if regime == "reduced":
            return 7.0
        if regime == "custom":
            try:
                return float(self.get("tax", "custom_rate", default=19.0))
            except (TypeError, ValueError):
                return 19.0
        return 0.0  # Kleinunternehmer

    def is_kleinunternehmer(self) -> bool:
        return self.get("tax", "regime", default="kleinunternehmer") == "kleinunternehmer"
