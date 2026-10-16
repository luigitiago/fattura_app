# Guida alla distribuzione (build & USB)

Questa cartella contiene gli strumenti per trasformare l'app in un **eseguibile
autonomo** e distribuirlo su **chiavetta USB**.

---

## 1. Perché serve compilare

L'app è scritta in Python: per farla partire su un PC **senza Python installato**
è necessario generare un eseguibile che includa tutto (interprete, librerie, risorse).
Si usa **PyInstaller**, che produce **un unico file** per sistema operativo.

> ⚠️ **Un eseguibile va creato sul sistema di destinazione.** Non è possibile
> generare un `.exe` di Windows da Linux/macOS (e viceversa) con PyInstaller.

---

## 2. Windows (caso più probabile)

Sul PC **Windows**:

1. Installa **Python 3.10+** da python.org (durante l'installazione spunta
   *"Add Python to PATH"*).
2. Copia la cartella del progetto sul PC.
3. Doppio clic su **`build_windows.bat`**.
4. Al termine trovi l'eseguibile in:

   ```
   dist\FakturaManager.exe
   ```

Questo è l'unico file da copiare sulla chiavetta.

### Modalità portatile (dati sulla chiavetta)
Copia na chiavetta **`FakturaManager.exe`** e **`portable_windows.bat`** nella stessa
cartella, poi avvia **`portable_windows.bat`**: tutti i dati finiscono nella
sottocartella `dati\` accanto all'eseguibile.

---

## 3. Linux

```bash
./build_linux.sh
```

Risultato: `dist/FakturaManager`.

---

## 4. macOS

```bash
./build_macos.sh
```

Risultato: `dist/FakturaManager.app`.
La prima apertura può richiedere *Click destro → Apri* (Gatekeeper).

---

## 5. Build automatica su GitHub (nessun PC Windows necessario)

Il progetto include il workflow `.github/workflows/build.yml`. Se carichi il
progetto su GitHub puoi generare **tutti** gli eseguibili dai server di GitHub:

1. Carica il progetto sul tuo repository GitHub.
2. Vai nella scheda **Actions** → seleziona **Build executables** → **Run workflow**.
3. Al termine, scarica l'artefatto **`FakturaManager-windows`** (contiene l'`.exe`).

Per creare una **Release** con i file allegati, basta fare push di un tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

---

## 6. Nota sugli antivirus (falso positivo)

Gli eseguibili creati con PyInstaller a volte vengono segnalati come sospetti da
Windows Defender o da altri antivirus: è un **falso positivo** noto (il file
"si scompatta da solo" all'avvio).

Come gestirlo:
- Aggiungi un'**esclusione** per il file `FakturaManager.exe` nell'antivirus.
- In alternativa, avvia tramite **`portable_windows.bat`**.
- Su Windows 11 puoi segnalare il falso positivo a Microsoft (Defender → *Protezione
  da virus e minacce* → *Invia file*).

---

## 7. Riepilogo file su chiavetta

**Installazione normale:** solo `FakturaManager.exe`.

**Portatile:** `FakturaManager.exe` + `portable_windows.bat` (+ `dati\` creato al volo).

I dati della modalità normale si trovano in `%APPDATA%\FakturaManager\` e si copiano
per backup.
