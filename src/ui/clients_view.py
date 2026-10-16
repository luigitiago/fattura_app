"""Clients page: list, search and create/edit dialog."""
from __future__ import annotations

import os
from tkinter import filedialog

import customtkinter as ctk

from .. import exporter, utils
from . import components as ui
from .base import Page

TYPE_PRIVATE = "private"
TYPE_BUSINESS = "business"


class ClientDialog(ui.ModalDialog):
    def __init__(self, master, app, client=None, on_saved=None):
        tr = app.tr
        title = tr.t("clients.edit") if client else tr.t("clients.add")
        super().__init__(master, app, title, size=(560, 640))
        self.client = dict(client) if client else None
        self.on_saved = on_saved
        self._build()

    def _build(self):
        tr = self.tr
        container = ctk.CTkScrollableFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=8, pady=8)

        # --- type selector -------------------------------------------------
        ctk.CTkLabel(container, text=tr.t("clients.field.type"), anchor="w",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 2))
        self.type_var = ctk.StringVar(value=self.client.get("type", TYPE_PRIVATE) if self.client else TYPE_PRIVATE)
        self.type_seg = ctk.CTkSegmentedButton(
            container,
            values=[tr.t("clients.type.private"), tr.t("clients.type.business")],
            command=self._on_type_change,
        )
        self.type_seg.set(tr.t("clients.type.business") if self.type_var.get() == TYPE_BUSINESS
                          else tr.t("clients.type.private"))
        self.type_seg.pack(anchor="w", pady=(0, 12))

        self.company_field = ui.Field(container, tr.t("clients.field.company"),
                                      placeholder="Muster GmbH")
        self.name_field = ui.Field(container, tr.t("clients.field.name"),
                                   placeholder="Max Mustermann")
        self.name_field.pack(anchor="w", pady=6)
        self.company_field.pack(anchor="w", pady=6)

        ui.section_label(container, tr.t("clients.section.address"), pad=(8, 4))
        self.street_field = ui.Field(container, tr.t("clients.field.street"), placeholder="Musterstraße 12")
        self.street_field.pack(anchor="w", pady=6)
        self.city_row = ctk.CTkFrame(container, fg_color="transparent")
        self.city_row.pack(anchor="w", pady=6, fill="x")
        self.postal_field = ui.Field(self.city_row, tr.t("clients.field.postal"), width=120)
        self.postal_field.pack(side="left", padx=(0, 10))
        self.city_field = ui.Field(self.city_row, tr.t("clients.field.city"), width=230)
        self.city_field.pack(side="left")
        self.country_field = ui.Field(container, tr.t("clients.field.country"), placeholder="Deutschland")
        self.country_field.pack(anchor="w", pady=6)

        ui.section_label(container, tr.t("clients.section.contact"), pad=(8, 4))
        self.email_field = ui.Field(container, tr.t("clients.field.email"), placeholder="name@example.de")
        self.email_field.pack(anchor="w", pady=6)
        self.phone_field = ui.Field(container, tr.t("clients.field.phone"), placeholder="+49 …")
        self.phone_field.pack(anchor="w", pady=6)
        self.vat_field = ui.Field(container, tr.t("clients.field.vat"), placeholder="DE123456789")
        self.vat_field.pack(anchor="w", pady=6)
        self.insurance_field = ui.Field(container, tr.t("clients.field.insurance"), placeholder="A123456789")
        self.insurance_field.pack(anchor="w", pady=6)

        ui.section_label(container, tr.t("clients.field.notes"), pad=(8, 4))
        self.notes_box = ctk.CTkTextbox(container, height=70)
        self.notes_box.pack(fill="x", pady=(0, 8))

        # fill values when editing
        if self.client:
            self.name_field.set(self.client.get("name", ""))
            self.company_field.set(self.client.get("company", ""))
            self.street_field.set(self.client.get("street", ""))
            self.postal_field.set(self.client.get("postal", ""))
            self.city_field.set(self.client.get("city", ""))
            self.country_field.set(self.client.get("country", ""))
            self.email_field.set(self.client.get("email", ""))
            self.phone_field.set(self.client.get("phone", ""))
            self.vat_field.set(self.client.get("vat", ""))
            self.insurance_field.set(self.client.get("insurance", ""))
            self.notes_box.insert("1.0", self.client.get("notes", "") or "")
        else:
            self.country_field.set("Deutschland")

        # --- buttons -------------------------------------------------------
        btns = ctk.CTkFrame(self, fg_color="transparent")
        btns.pack(fill="x", padx=16, pady=(0, 14))
        ctk.CTkButton(btns, text=tr.t("common.cancel"), fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER,
                      command=self.destroy, width=120).pack(side="right")
        ctk.CTkButton(btns, text=tr.t("common.save"), command=self._save, width=150).pack(side="right", padx=8)

        self._on_type_change(self.type_seg.get())

    def _on_type_change(self, value):
        tr = self.tr
        if value == tr.t("clients.type.business"):
            self.company_field.pack(anchor="w", pady=6, before=self.name_field.frame)
            self.name_field.label.configure(text=tr.t("clients.field.contact"))
        else:
            self.company_field.pack_forget()
            self.name_field.label.configure(text=tr.t("clients.field.name"))

    def _save(self):
        tr = self.tr
        is_business = self.type_seg.get() == tr.t("clients.type.business")
        company = self.company_field.get()
        name = self.name_field.get()

        if is_business and not company:
            ui.warn(self, tr.t("common.warning"), tr.t("clients.required"))
            return
        if not is_business and not name:
            ui.warn(self, tr.t("common.warning"), tr.t("clients.required"))
            return

        data = {
            "type": TYPE_BUSINESS if is_business else TYPE_PRIVATE,
            "name": name or company,
            "company": company if is_business else "",
            "contact": name if is_business else "",
            "street": self.street_field.get(),
            "postal": self.postal_field.get(),
            "city": self.city_field.get(),
            "country": self.country_field.get(),
            "email": self.email_field.get(),
            "phone": self.phone_field.get(),
            "vat": self.vat_field.get(),
            "insurance": self.insurance_field.get(),
            "notes": self.notes_box.get("1.0", "end").strip(),
        }
        if self.client:
            self.app.db.update_client(self.client["id"], data)
        else:
            self.app.db.add_client(data)
        display = data["company"] or data["name"]
        ui.info(self, tr.t("common.success"), tr.t("clients.saved", name=display))
        if self.on_saved:
            self.on_saved()
        self.destroy()


class ClientsPage(Page):
    def build(self):
        tr = self.tr
        self.search = ""
        self.header(tr.t("clients.title"), tr.t("clients.subtitle"),
                    actions=[
                        (tr.t("export.button"), self._export_csv, ui.GRAY, ui.GRAY_HOVER),
                        (f"＋ {tr.t('clients.add')}", self._new_client),
                    ])

        search_bar = ctk.CTkFrame(self, fg_color="transparent")
        search_bar.pack(fill="x", pady=(0, 12))
        self.search_entry = ctk.CTkEntry(search_bar, placeholder_text=tr.t("clients.search_placeholder"),
                                         width=420)
        self.search_entry.pack(side="left")
        self.search_entry.bind("<KeyRelease>", lambda e: self._reload())
        ctk.CTkButton(search_bar, text=tr.t("common.search"), width=110, command=self._reload,
                      fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER).pack(side="left", padx=8)

        self.list_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)
        self._reload()

    def _new_client(self):
        ClientDialog(self.app, self.app, on_saved=self._reload)

    def _export_csv(self):
        tr = self.tr
        clients = self.db.list_clients()
        if not clients:
            ui.warn(self.app, tr.t("common.warning"), tr.t("export.empty"))
            return
        default = os.path.join(utils.documents_dir(), f"Kunden_{utils.today().isoformat()}.csv")
        path = filedialog.asksaveasfilename(
            parent=self.app, title=tr.t("export.clients_title"), defaultextension=".csv",
            initialfile=os.path.basename(default), initialdir=os.path.dirname(default),
            filetypes=[(tr.t("export.csv_filter"), "*.csv")])
        if not path:
            return
        exporter.export_clients(clients, path, tr)
        if ui.confirm(self.app, tr.t("common.success"), tr.t("export.saved", path=path)):
            utils.open_path(path)

    def _edit_client(self, client_id):
        client = self.db.get_client(client_id)
        if client:
            ClientDialog(self.app, self.app, client=client, on_saved=self._reload)

    def _delete_client(self, client_id):
        tr = self.tr
        client = self.db.get_client(client_id)
        if not client:
            return
        display = client["company"] or client["name"]
        if self.db.client_invoice_count(client_id) > 0:
            ui.warn(self, tr.t("common.warning"), tr.t("clients.delete_has_invoices"))
            return
        if ui.confirm(self.app, tr.t("common.confirm"), tr.t("clients.delete_confirm", name=display)):
            self.db.delete_client(client_id)
            ui.info(self.app, tr.t("common.success"), tr.t("clients.deleted"))
            self._reload()

    def _reload(self):
        tr = self.tr
        for child in self.list_frame.winfo_children():
            child.destroy()
        search = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        clients = self.db.list_clients(search)

        if not clients:
            ctk.CTkLabel(self.list_frame, text=tr.t("clients.none_yet"), text_color=("gray45", "gray65")).pack(
                pady=30)
            return

        for client in clients:
            self._row(client)

    def _row(self, client):
        tr = self.tr
        card = ctk.CTkFrame(self.list_frame, corner_radius=10, fg_color=("gray92", "gray17"))
        card.pack(fill="x", pady=4)
        for col in range(5):
            card.grid_columnconfigure(col, weight=1)

        is_business = client["type"] == TYPE_BUSINESS
        display = (client["company"] or client["name"] or "—") if is_business else (client["name"] or "—")
        type_text = tr.t("clients.type.business") if is_business else tr.t("clients.type.private")

        ctk.CTkLabel(card, text=display, anchor="w",
                     font=ctk.CTkFont(size=13, weight="bold")).grid(row=0, column=0, sticky="ew", padx=10, pady=9)
        badge = ctk.CTkFrame(card, fg_color=ui.ACCENT if is_business else ui.GRAY, corner_radius=6)
        badge.grid(row=0, column=1, sticky="w", padx=4)
        ctk.CTkLabel(badge, text=type_text, text_color="white",
                     font=ctk.CTkFont(size=10, weight="bold")).pack(padx=8, pady=2)
        ctk.CTkLabel(card, text=client["city"] or "—", anchor="w").grid(row=0, column=2, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=client["email"] or "—", anchor="w").grid(row=0, column=3, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=client["insurance"] or "—", anchor="w").grid(row=0, column=4, sticky="ew", padx=6)

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=5, padx=8)
        ctk.CTkButton(actions, text=tr.t("common.edit"), width=70, fg_color=ui.GRAY, hover_color=ui.GRAY_HOVER,
                      command=lambda cid=client["id"]: self._edit_client(cid)).pack(side="left", padx=2)
        ctk.CTkButton(actions, text=tr.t("common.delete"), width=70, fg_color=ui.RED, hover_color=ui.RED_HOVER,
                      command=lambda cid=client["id"]: self._delete_client(cid)).pack(side="left", padx=2)
