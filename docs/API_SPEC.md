# 📡 Specifica delle API REST

Tutti gli endpoint scambiano payload in formato `application/json` e sono conformi allo standard OpenAPI 3.0.
La documentazione interattiva Swagger UI è disponibile all'indirizzo `http://127.0.0.1:8000/docs`.

---

## 1. `GET /api/health`
Verifica lo stato di funzionamento del backend e lo stato della configurazione dell'API Key.

### Risposta (200 OK)
```json
{
  "status": "healthy",
  "has_configured_api_key": true,
  "default_model": "gemini-2.5-flash-lite",
  "daily_free_limit": "500 richieste/giorno (Flash-Lite)"
}
```

---

## 2. `POST /api/redact`
Analizza il testo sorgente, rileva le entità PII ed esegue la sostituzione con token semantici reversibili.

### Richiesta (JSON)
```json
{
  "text": "Mario Rossi ha chiesto info per conto di info@azienda.it al +39 02 998877.",
  "api_key": "opzionale_se_configurata_in_env",
  "model": "gemini-2.5-flash-lite",
  "custom_rules": "Censura anche i nomi di dipartimento"
}
```

### Risposta (200 OK)
```json
{
  "redacted_text": "[NOME_1] ha chiesto info per conto di [EMAIL_1] al [TELEFONO_1].",
  "entities": [
    {
      "original_value": "Mario Rossi",
      "placeholder": "[NOME_1]",
      "category": "PERSON",
      "explanation": "Nome e cognome di persona fisica identificabile."
    },
    {
      "original_value": "info@azienda.it",
      "placeholder": "[EMAIL_1]",
      "category": "EMAIL",
      "explanation": "Indirizzo di posta elettronica aziendale."
    },
    {
      "original_value": "+39 02 998877",
      "placeholder": "[TELEFONO_1]",
      "category": "PHONE",
      "explanation": "Numero di telefono con prefisso."
    }
  ],
  "mapping_dict": {
    "[NOME_1]": "Mario Rossi",
    "[EMAIL_1]": "info@azienda.it",
    "[TELEFONO_1]": "+39 02 998877"
  }
}
```

### Codici di Errore
- `400 Bad Request`: Testo vuoto o nessuna API Key specificata.
- `429 Too Many Requests`: Quota di 500 RPD o limite per minuto esaurito su Google AI Studio.
- `502 Bad Gateway`: Errore a monte restituito dai server di Google.

---

## 3. `POST /api/deanonymize`
Effettua la ricostruzione deterministica del testo sostituendo i placeholder con i valori originali memorizzati nel dizionario.
Non consuma alcuna richiesta o token Gemini (elaborazione 100% CPU locale).

### Richiesta (JSON)
```json
{
  "text": "Ecco la bozza contrattuale per [NOME_1] inviata a [EMAIL_1].",
  "mapping_dict": {
    "[NOME_1]": "Mario Rossi",
    "[EMAIL_1]": "info@azienda.it"
  }
}
```

### Risposta (200 OK)
```json
{
  "restored_text": "Ecco la bozza contrattuale per Mario Rossi inviata a info@azienda.it.",
  "restored_count": 2
}
```
