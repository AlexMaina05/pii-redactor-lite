# 🛡️ PII Redactor Lite

> **Anonimizzatore intelligente e reversibile per dati sensibili (GDPR-ready), alimentato da Google Gemini Flash-Lite e FastAPI.**  
> *Progettato specificamente per sfruttare al meglio il piano Free da **500 richieste giornaliere**.*

---

## 🌟 Caratteristiche Principali

- ⚡ **Ottimizzato per Gemini Flash-Lite**: Elaborazione ultra-rapida con output JSON strutturato via `google-genai` SDK.
- 🔁 **Anonimizzazione Reversibile**: Sostituisce i dati sensibili con placeholder semantici (es. `[NOME_1]`, `[EMAIL_1]`, `[CODICE_FISCALE_1]`, `[IBAN_1]`) e genera un dizionario per il ripristino istantaneo a **zero token**.
- 📋 **Doppia Vista & Interfaccia Web Moderna**: Dashboard SPA reattiva con anteprima affiancata (Originale vs Anonimizzato), conteggio caratteri, tabella delle entità rilevate e copia rapida con un click.
- 🔒 **Zero Persistence (Privacy by Design)**: Nessun database. I dati risiedono unicamente nella memoria volatile durante la richiesta.
- ⏱️ **Gestione Quota Free (500 RPD)**: Gestione puntuale e chiara degli errori di quota (HTTP 429) senza crash.
- 🔄 **Configurazione Doppio Remote**: Configurato nativamente sia su **Gitea locale** che su **GitHub**.

---

## 🚀 Quickstart & Installazione

### 1. Prerequisiti
- Python 3.10+
- Una chiave API Google Gemini (gratuita su [Google AI Studio](https://aistudio.google.com/))

### 2. Installazione delle Dipendenze

```bash
# Entra nella directory del progetto
cd pii-redactor-lite

# Crea e attiva l'ambiente virtuale
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # Su Windows PowerShell
# source .venv/bin/activate      # Su Linux/macOS

# Installa i pacchetti
pip install -r requirements.txt
```

### 3. Configurazione Variabili d'Ambiente

Copia il file di esempio `.env.example` in `.env`:
```bash
cp .env.example .env
```
Configura la tua API key all'interno di `.env`:
```ini
GEMINI_API_KEY=tua_api_key_qui
GEMINI_MODEL=gemini-2.5-flash-lite
HOST=127.0.0.1
PORT=8000
```
*(Nota: se non imposti la chiave nel file `.env`, potrai comunque inserirla direttamente dalla schermata impostazioni dell'interfaccia web).*

### 4. Avvio dell'Applicazione

```bash
python main.py
```
Oppure direttamente con Uvicorn:
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Apri il browser all'indirizzo:  
👉 **`http://127.0.0.1:8000`**  
Documentazione interattiva API (Swagger UI):  
👉 **`http://127.0.0.1:8000/docs`**

---

## 🧪 Esecuzione dei Test Automatizzati

```bash
python -m pytest -v
```

---

## 📚 Documentazione Tecnica Approfondita

I dettagli implementativi e le specifiche sono disponibili nella cartella [`docs/`](docs/):
- 🏗️ [**Architettura di Sistema & Design**](docs/ARCHITECTURE.md)
- 📡 [**Specifica API REST**](docs/API_SPEC.md)
- 🔒 [**Privacy, GDPR & Threat Model**](docs/SECURITY_PRIVACY.md)

---

## 🌐 Configurazione Doppio Remote Git (Gitea + GitHub)

Il repository è predisposto per sincronizzarsi sia con il server **Gitea locale** che con **GitHub**:

```bash
# Verifica i remoti attivi
git remote -v

# Push su entrambi i remoti
git push gitea master
git push github master

# Oppure configurando un remote "all" per inviare con un unico comando:
git push all master
```

---

## 📄 Licenza
Rilasciato sotto licenza MIT. Libero per uso personale e commerciale.
