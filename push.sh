#!/usr/bin/env bash
# ------------------------------------------------------------------
#  Salva le modifiche e le carica su GitHub.
#  Uso:  ./push.sh          (oppure doppio clic, se il sistema lo consente)
# ------------------------------------------------------------------
cd "$(dirname "$0")" || exit 1

echo "=================================================="
echo "  Caricamento modifiche su GitHub"
echo "  Repo: $(git remote get-url origin)"
echo "=================================================="
echo

if [ -z "$(git status --porcelain)" ]; then
    echo "Nessuna modifica da caricare. Tutto aggiornato!"
    echo
    read -rp "Premi Invio per chiudere..." _
    exit 0
fi

echo "Modifiche rilevate:"
git status --short
echo
read -rp "Descrizione della modifica (Invio per 'Aggiornamento'): " MSG
MSG="${MSG:-Aggiornamento}"

git add -A || { echo "Errore nel preparare i file."; read -rp "Invio per chiudere..." _; exit 1; }
git commit -m "$MSG" || { echo "Errore nel creare il commit."; read -rp "Invio per chiudere..." _; exit 1; }

echo
echo "Invio a GitHub..."
if git push; then
    echo
    echo "Fatto! Le modifiche sono su GitHub."
    echo "La build automatica (Windows/Linux/macOS) e' stata avviata."
    echo "Controlla qui: https://github.com/luigitiago/fattura_app/actions"
else
    echo
    echo "Il push non e' riuscito (credenziali?)."
    echo "Incolla di nuovo il token quando richiesto."
fi

echo
read -rp "Premi Invio per chiudere..." _
