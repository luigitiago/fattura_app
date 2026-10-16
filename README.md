# Faktura Manager

Applicazione desktop **offline** (nessuna connessione internet necessaria) per creare,
stampare ed inviare **fatture in stile tedesco**, gestire i clienti (privati e aziende)
e tenere traccia di chi ha pagato e chi no. Interfaccia **bilingue Italiano / Deutsch**,
pensata per essere semplice da usare e distribuibile tramite **chiavetta USB**.

> Sostituisce il vecchio prototipo `fattura.py` (spostato in `legacy/`).

---

## Funzionalità

- **Panoramica**: fatture totali, importo da incassare, importo incassato, fatture scadute.
- **Clienti**: privati e aziende (ragione sociale, referente, indirizzo, email, telefono,
  Partita IVA / USt-IdNr., numero assicurativo, note). Ricerca istantanea.
- **Fatture**: numero progressivo automatico, date (emissione / prestazione / scadenza),
  voci multiple (codice prestazione, descrizione, quantità, unità, prezzo), calcolo
  automatico di netto, IVA e totale. Filtri per stato (aperte / pagate / scadute / annullate / bozza).
- **PDF professionale** conforme ai requisiti tedeschi, pronto per la stampa.
- **Invio email** opzionale con PDF allegato (SMTP configurabile).
- **Esportazione CSV** di fatture e clienti (compatibile con Excel tedesco/italiano).
- **Gestione pagamenti**: segna una fattura come pagata/aperta; le scadute vengono
  evidenziate automaticamente confrontando la data di scadenza con oggi.
- **IVA flessibile**: *Kleinunternehmer §19 UStG* (senza IVA), 19%, 7% o aliquota personalizzata.
- **Lingua** IT/DE cambiabile in qualsiasi momento; tema chiaro/scuro/sistema.
- **Dati locali** salvati in un database SQLite: nessun cloud, nessun tracciamento.

---

## Requisiti

- **Python 3.10+** e **Tkinter** (incluso in Python; su Linux a volte serve `python3-tk`).
- Librerie Python: `customtkinter`, `reportlab`, `Pillow` (vedi `requirements.txt`).

---

## Avvio rapido (dallo sorgente)

**Linux / macOS**

```bash
./run_source.sh
```

**Windows**

```bat
run_source.bat
```

Lo script crea automaticamente un ambiente virtuale `.venv`, installa le dipendenze
e avvia l'app. In alternativa:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

---

## Creare l'eseguibile (build)

L'app è **multipiattaforma**, ma l'eseguibile va creato **sul sistema di destinazione**
(non è possibile creare un `.exe` di Windows da Linux). Sono pronti gli script:

| Sistema  | Script                          | Risultato                       |
|----------|---------------------------------|---------------------------------|
| Windows  | `packaging\build_windows.bat`   | `dist\FakturaManager.exe`       |
| Linux    | `packaging/build_linux.sh`      | `dist/FakturaManager`           |
| macOS    | `packaging/build_macos.sh`      | `dist/FakturaManager.app`       |

Esempio (Linux):

```bash
./packaging/build_linux.sh
```

Lo script installa PyInstaller, impacchetta l'app in un **unico file** e lo mette in `dist/`.
La prima esecuzione è leggermente più lenta (l'app si scompatta in una cartella temporanea).

### Build automatica senza il sistema operativo (GitHub Actions)

Se non hai un PC Windows, puoi generare l'eseguibile `.exe` usando il workflow incluso
`.github/workflows/build.yml`: carica il progetto su GitHub, poi dalla scheda **Actions**
avvia il workflow *Build executables* e scarica l'artefatto `FakturaManager-windows`.
Facendo push di un tag (es. `v1.0.0`) viene creata automaticamente una **Release** con
tutti gli eseguibili allegati.

Per i dettagli (build, USB, antivirus) vedi **[`packaging/README.md`](packaging/README.md)**.

---

## Distribuzione tramite chiavetta USB

L'app è un singolo file eseguibile: si copia sulla chiavetta e si esegue. Non serve
installazione. Esistono due modalità di conservazione dei dati:

### Opzione 1 — Installazione normale (consigliata)
1. Copia sulla chiavetta il file `FakturaManager.exe` (Windows) o `FakturaManager` (Linux).
2. Sul PC del cliente, copialo in una cartella (es. `C:\FakturaManager\`) e crea un
   collegamento sul desktop.
3. I dati vengono salvati nei **dati utente del PC** (vedi sotto), quindi restano anche
   se si rimuove la chiavetta.

### Opzione 2 — Modalità portatile (dati sulla chiavetta)
Usa i launcher in `packaging/`:
- Windows: copia `FakturaManager.exe` + `packaging\portable_windows.bat` nella stessa
  cartella della chiavetta e avvia **`portable_windows.bat`**.
- Linux: copia `FakturaManager` + `packaging/portable_linux.sh` e avvia lo script.

In questa modalità tutti i dati finiscono nella sottocartella `dati/` accanto all'eseguibile
(variabile `FAKTURA_DATA_DIR`), così il cliente può portarsi dietro anche le sue fatture.

---

## Dove vengono salvati i dati

| Sistema | Percorso |
|---------|----------|
| Windows | `%APPDATA%\FakturaManager\` |
| Linux   | `~/.local/share/FakturaManager/` |
| macOS   | `~/Library/Application Support/FakturaManager/` |

Contiene:
- `faktura.db` — il database SQLite (clienti, fatture, voci).
- `config.json` — impostazioni (dati azienda, banca, fisco, email).

I **PDF** generati vengono salvati in `Documenti/<Nome azienda>/Rechnungen/`.

### Backup
Basta copiare la cartella dei dati (o, in modalità portatile, la cartella `dati/`).
Il pulsante **Impostazioni → Dati → Apri cartella** la apre al volo.

---

## Configurazione email (SMTP)

In **Impostazioni → Invio email**:

- **Gmail**: server `smtp.gmail.com`, porta `587`, sicurezza `STARTTLS`,
  utente = tua email, password = **password per le app** (non la password normale;
  va creata nell'account Google con la verifica in due passaggi).
- **Outlook/Office 365**: server `smtp.office365.com`, porta `587`, `STARTTLS`.
- **Aruba / altri**: chiedi al provider i parametri SMTP.

Usa **Testa connessione** per verificare i parametri prima di inviare.

---

## Note sulla fatturazione tedesca

Una *Rechnung* regolare in Germania deve contenere (l'app li gestisce tutti):
nome e indirizzo del mittente e del destinatario, numero di fattura univoco,
data di emissione, data/periodo della prestazione, descrizione della prestazione,
importo netto, aliquota e importo dell'IVA, importo lordo, e (per i *Kleinunternehmer*)
la nota *„Gemäß § 19 UStG wird keine Umsatzsteuer berechnet."*.

Compila bene i dati in **Impostazioni** prima della prima fattura (absender, banca,
Steuernummer / USt-IdNr.). L'app avvisa finché i dati non sono completi.

---

## Struttura del progetto

```
Fattura-app/
├── main.py                    # entry point
├── requirements.txt
├── run_source.sh / .bat       # avvio da sorgente
├── src/
│   ├── app.py                 # finestra principale, menu, navigazione, lingua
│   ├── config.py              # impostazioni persistenti (JSON)
│   ├── database.py            # livello SQLite (+ migrazioni schema)
│   ├── exporter.py            # esportazione CSV
│   ├── i18n.py                # traduzioni IT/DE
│   ├── pdf_generator.py       # creazione PDF (reportlab)
│   ├── mailer.py              # invio email (SMTP)
│   ├── utils.py               # percorsi, formattazione, integrazione OS
│   └── ui/                    # pagine e dialoghi (CustomTkinter)
├── assets/                    # icona
├── packaging/                 # script di build + launcher portatili + guida
├── tests/                     # test automatici (logica, GUI, flussi, nuove funzioni)
├── legacy/                    # vecchio prototipo (fattura.py)
└── krankenkasse.db            # database legacy (importato al primo avvio, se presente)
```

---

## Test automatici (sviluppo)

```bash
./tests/run_all.sh
```

Esegue: logica di base + PDF, migrazioni/CSV, flussi end-to-end e uno smoke test
grafico. I test usano una cartella dati temporanea e non toccano i dati reali.

---

## Risoluzione problemi

- **Su Linux non si apre**: manca Tkinter → `sudo apt install python3-tk`.
- **Il PDF è vuoto / errore**: controlla di aver compilato i dati azienda in Impostazioni.
- **L'email non parte**: verifica host/porta/sicurezza e usa *Testa connessione*;
  con Gmail serve la *password per le app*.
- **Antivirus Windows blocca l'exe**: è un falso positivo tipico dei file creati con
  PyInstaller; aggiungi un'esclusione.

---

## Kurzanleitung (Deutsch)

**Faktura Manager** ist eine Offline-Desktop-App zum Erstellen, Drucken und Versenden
von Rechnungen (**Deutsch / Italiano**), inklusive Kundenverwaltung und Zahlungsstatus.

- **Start (Quellcode)**: `run_source.bat` (Windows) bzw. `./run_source.sh` (Linux/macOS).
- **EXE erstellen**: `packaging\build_windows.bat` → `dist\FakturaManager.exe`.
- **USB-Verteilung**: einfach die erzeugte Datei auf den USB-Stick kopieren und starten.
  Für „portable" Nutzung (Daten auf dem Stick) `packaging\portable_windows.bat` verwenden.
- **Daten**: liegen unter `%APPDATA%\FakturaManager\` (Windows) und überleben das
  Entfernen des USB-Sticks. Backup = diesen Ordner kopieren.
- **Erste Schritte**: unter **Einstellungen** Firma, Bank und Steuernummer eintragen,
  dann Kunden anlegen und die erste Rechnung erstellen. Beim ersten Start öffnet sich
  ein Willkommensdialog, der direkt zu den Einstellungen führt.
- **Weitere Funktionen**: optionale **Leistungsziffer** je Position (erscheint im PDF),
  **CSV-Export** von Rechnungen und Kunden (Excel-kompatibel, `;`-getrennt).

Version 1.0.0
