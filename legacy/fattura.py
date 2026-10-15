import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk

# Configurazione dello stile grafico dell'interfaccia
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class KrankenkasseBillingApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Krankenkasse Billing System - Manager Offline")
        self.geometry("1000x650")
        
        # Inizializzazione del Database locale SQLite
        self.init_database()
        
        # Struttura della Finestra (Grid layout 1x2 per Menu Laterale e Contenuto)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Creazione del Menu di Navigazione Laterale
        self.nav_frame = ctk.CTkFrame(self, corner_radius=0)
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_rowconfigure(4, weight=1)
        
        self.nav_title = ctk.CTkLabel(self.nav_frame, text="Krankenkasse Manager", font=ctk.CTkFont(size=20, weight="bold"))
        self.nav_title.grid(row=0, column=0, padx=20, pady=20)
        
        self.btn_clients = ctk.CTkButton(self.nav_frame, text="Nuovo Cliente", command=self.show_clients_frame)
        self.btn_clients.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_invoices = ctk.CTkButton(self.nav_frame, text="Nuova Fattura", command=self.show_invoices_frame)
        self.btn_invoices.grid(row=2, column=0, padx=20, pady=10)
        
        self.btn_view_invoices = ctk.CTkButton(self.nav_frame, text="Registro Fatture / Stato", command=self.show_view_invoices_frame)
        self.btn_view_invoices.grid(row=3, column=0, padx=20, pady=10)
        
        # Contenitori dei diversi pannelli di lavoro
        self.clients_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.invoices_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.view_invoices_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        
        # Avvia sul pannello principale
        self.show_view_invoices_frame()

    def init_database(self):
        """Crea il file database locale 'krankenkasse.db' e le relative tabelle se non esistono."""
        conn = sqlite3.connect("krankenkasse.db")
        cursor = conn.cursor()
        
        # Tabella Clienti (con ID Assicurativo Tedesco)
        cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            insurance_num TEXT UNIQUE NOT NULL,
                            email TEXT)''')
                            
        # Tabella Fatture (Stato di default: Offen / Aperta)
        cursor.execute('''CREATE TABLE IF NOT EXISTS invoices (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            client_id INTEGER,
                            amount REAL NOT NULL,
                            description TEXT,
                            date TEXT DEFAULT (date('now')),
                            status TEXT DEFAULT 'Offen', 
                            FOREIGN KEY(client_id) REFERENCES clients(id))''')
        conn.commit()
        conn.close()

    def clear_frames(self):
        """Nasconde tutti i pannelli per mostrare solo quello selezionato."""
        self.clients_frame.grid_forget()
        self.invoices_frame.grid_forget()
        self.view_invoices_frame.grid_forget()

    # --- PANNELLO 1: REGISTRAZIONE CLIENTI ---
    def show_clients_frame(self):
        self.clear_frames()
        self.clients_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Reset componenti interni per evitare duplicazioni grafiche al click
        for widget in self.clients_frame.winfo_children():
            widget.destroy()
            
        lbl = ctk.CTkLabel(self.clients_frame, text="Registrazione Nuovo Paziente / Cliente", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(pady=20)
        
        self.ent_name = ctk.CTkEntry(self.clients_frame, placeholder_text="Nome Completo", width=300)
        self.ent_name.pack(pady=10)
        
        self.ent_ins = ctk.CTkEntry(self.clients_frame, placeholder_text="Versichertennummer (ID Assicurazione)", width=300)
        self.ent_ins.pack(pady=10)
        
        self.ent_email = ctk.CTkEntry(self.clients_frame, placeholder_text="Email (Opzionale)", width=300)
        self.ent_email.pack(pady=10)
        
        btn_save = ctk.CTkButton(self.clients_frame, text="Salva nel Database", command=self.save_client)
        btn_save.pack(pady=20)

    def save_client(self):
        name = self.ent_name.get()
        ins = self.ent_ins.get()
        email = self.ent_email.get()
        
        if not name or not ins:
            messagebox.showerror("Errore", "Nome e Versichertennummer sono obbligatori!")
            return
            
        try:
            conn = sqlite3.connect("krankenkasse.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO clients (name, insurance_num, email) VALUES (?, ?, ?)", (name, ins, email))
            conn.commit()
            conn.close()
            messagebox.showinfo("Successo", f"Cliente {name} registrato correttamente!")
            self.show_view_invoices_frame()
        except sqlite3.IntegrityError:
            messagebox.showerror("Errore", "Questo numero identificativo assicurativo esiste già nel sistema.")

    # --- PANNELLO 2: CREAZIONE FATTURE ---
    def show_invoices_frame(self):
        self.clear_frames()
        self.invoices_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        for widget in self.invoices_frame.winfo_children():
            widget.destroy()
            
        lbl = ctk.CTkLabel(self.invoices_frame, text="Emissione Nuova Fattura", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(pady=20)
        
        # Recupera la lista aggiornata dei clienti per il menu a tendina
        conn = sqlite3.connect("krankenkasse.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, insurance_num FROM clients")
        clients_list = cursor.fetchall()
        conn.close()
        
        if not clients_list:
            ctk.CTkLabel(self.invoices_frame, text="⚠️ Devi prima inserire almeno un cliente per fare una fattura.").pack(pady=20)
            return
            
        self.client_mapping = {f"{c} ({c})": c for c in clients_list}
        
        self.dropdown_client = ctk.CTkComboBox(self.invoices_frame, values=list(self.client_mapping.keys()), width=300)
        self.dropdown_client.pack(pady=10)
        
        self.ent_amount = ctk.CTkEntry(self.invoices_frame, placeholder_text="Importo (€) es. 150.50", width=300)
        self.ent_amount.pack(pady=10)
        
        self.ent_desc = ctk.CTkEntry(self.invoices_frame, placeholder_text="Descrizione o Tipo di Trattamento/Servizio", width=300)
        self.ent_desc.pack(pady=10)
        
        btn_save_inv = ctk.CTkButton(self.invoices_frame, text="Genera Fattura", command=self.save_invoice)
        btn_save_inv.pack(pady=20)

    def save_invoice(self):
        selected_client = self.dropdown_client.get()
        amount_str = self.ent_amount.get()
        desc = self.ent_desc.get()
        
        if not selected_client or not amount_str:
            messagebox.showerror("Errore", "Seleziona un cliente e inserisci un importo valido.")
            return
            
        try:
            amount = float(amount_str)
            client_id = self.client_mapping[selected_client]
            
            conn = sqlite3.connect("krankenkasse.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO invoices (client_id, amount, description) VALUES (?, ?, ?)", (client_id, amount, desc))
            conn.commit()
            conn.close()
            
            messagebox.showinfo("Successo", "Fattura emessa correttamente in stato 'Offen' (Aperta)!")
            self.show_view_invoices_frame()
        except ValueError:
            messagebox.showerror("Errore", "L'importo deve essere un numero valido (usa il punto per i decimali).")

    # --- PANNELLO 3: REGISTRO FATTURE, FILTRI E STAMPA ---
    def show_view_invoices_frame(self):
        self.clear_frames()
        self.view_invoices_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        for widget in self.view_invoices_frame.winfo_children():
            widget.destroy()
            
        lbl = ctk.CTkLabel(self.view_invoices_frame, text="Registro Storico Fatture", font=ctk.CTkFont(size=18, weight="bold"))
        lbl.pack(pady=10)
        
        # Sezione Filtri rapidi di stato
        filter_frame = ctk.CTkFrame(self.view_invoices_frame, fg_color="transparent")
        filter_frame.pack(pady=5, fill="x")
        
        ctk.CTkButton(filter_frame, text="Tutte", width=100, command=lambda: self.load_invoices_data("All")).pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="Solo Da Pagare (Offen)", fg_color="#C0392B", hover_color="#962D22", width=160, command=lambda: self.load_invoices_data("Offen")).pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="Solo Pagate (Bezahlt)", fg_color="#27AE60", hover_color="#1E8449", width=160, command=lambda: self.load_invoices_data("Bezahlt")).pack(side="left", padx=5)
        
        # Contenitore per la griglia dati ad alta scannabilità
        self.scroll_canvas = ctk.CTkScrollableFrame(self.view_invoices_frame, width=720, height=400)
        self.scroll_canvas.pack(pady=15, fill="both", expand=True)
        
        self.load_invoices_data("All")

    def load_invoices_data(self, filter_status):
        for widget in self.scroll_canvas.winfo_children():
            widget.destroy()
            
        conn = sqlite3.connect("krankenkasse.db")
        cursor = conn.cursor()
        
        query = '''SELECT invoices.id, clients.name, clients.insurance_num, invoices.amount, invoices.description, invoices.date, invoices.status 
                   FROM invoices JOIN clients ON invoices.client_id = clients.id'''
                   
        if filter_status != "All":
            query += f" WHERE invoices.status = '{filter_status}'"
            
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        
        # Header della tabella
        headers = ["ID", "Paziente / Cliente", "N. Assicurazione", "Importo", "Data", "Stato", "Azioni"]
        for col_idx, text in enumerate(headers):
            lbl = ctk.CTkLabel(self.scroll_canvas, text=text, font=ctk.CTkFont(weight="bold"))
            lbl.grid(row=0, column=col_idx, padx=10, pady=5, sticky="w")
            
        # Righe della tabella interattive
        for row_idx, data in enumerate(rows, start=1):
            inv_id, c_name, c_ins, amount, desc, date, status = data
            
            ctk.CTkLabel(self.scroll_canvas, text=str(inv_id)).grid(row=row_idx, column=0, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.scroll_canvas, text=c_name).grid(row=row_idx, column=1, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.scroll_canvas, text=c_ins).grid(row=row_idx, column=2, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.scroll_canvas, text=f"€ {amount:.2f}").grid(row=row_idx, column=3, padx=10, pady=5, sticky="w")
            ctk.CTkLabel(self.scroll_canvas, text=date).grid(row=row_idx, column=4, padx=10, pady=5, sticky="w")
            
            # Bottone di cambio stato dinamico (Offen <-> Bezahl)
            status_color = "#C0392B" if status == "Offen" else "#27AE60"
            btn_status = ctk.CTkButton(self.scroll_canvas, text=status, fg_color=status_color, width=80,
                                       command=lambda i=inv_id, s=status: self.toggle_invoice_status(i, s))
            btn_status.grid(row=row_idx, column=5, padx=10, pady=5)
            
            # Bottone per esportare in formato testo pulito pronto per stampa
            btn_print = ctk.CTkButton(self.scroll_canvas, text="Stampa/PDF", width=80, fg_color="#7F8C8D", hover_color="#626567",
                                      command=lambda d=data: self.print_invoice_txt(d))
            btn_print.grid(row=row_idx, column=6, padx=10, pady=5)

    def toggle_invoice_status(self, inv_id, current_status):
        new_status = "Bezahlt" if current_status == "Offen" else "Offen"
        conn = sqlite3.connect("krankenkasse.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE invoices SET status = ? WHERE id = ?", (new_status, inv_id))
        conn.commit()
        conn.close()
        self.load_invoices_data("All")

    def print_invoice_txt(self, data):
        """Genera una ricevuta strutturata in un file di testo leggibile e pronto all'invio alla stampante fisica."""
        inv_id, c_name, c_ins, amount, desc, date, status = data
        
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                filetypes=[("File di testo", "*.txt")],
                                                initialfile=f"Fattura_{inv_id}_{c_name.replace(' ', '_')}")
        if not file_path:
            return
            
        receipt_content = f"""
===================================================
             RECHNUNG / FATTURA N. {inv_id}
===================================================
Data Emissione: {date}
Stato Ricevuta: {status.upper()}

DATI PAZIENTE / CLIENTE:
Nome: {c_name}
Versichertennummer: {c_ins}

DETTAGLIO PRESTAZIONE:
Descrizione: {desc if desc else 'Prestazioni professionali / Consulenza'}

---------------------------------------------------
TOTALE DA CORRISPONDERE:         EUR {amount:.2f}
---------------------------------------------------

Documento ad uso interno Krankenkasse / Monitoraggio.
===================================================
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(receipt_content)
        messagebox.showinfo("Successo", "Ricevuta generata e salvata! Ora puoi aprirla e stamparla con un click.")

if __name__ == "__main__":
    app = KrankenkasseBillingApp()
    app.mainloop()