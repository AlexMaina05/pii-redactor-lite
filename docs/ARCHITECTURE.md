# 🏗️ Architettura di Sistema & Design Tecnico

**PII Redactor Lite** è una piattaforma di data sanitization progettata per processare flussi di testo, estrarre in modo deterministico e coerente qualsiasi elemento riconducibile a dati personali o sensibili (PII/GDPR) e sostituirli con token semantici reversibili, sfruttando la velocità e l'elevato throughput del modello **Google Gemini Flash-Lite**.

---

## 1. Schema Architetturale ad Alto Livello

```mermaid
flowchart TD
    User([Utente / Browser]) -->|HTTP / JSON| WebUI[Frontend Web App / SPA]
    WebUI -->|POST /api/redact| API[FastAPI Backend]
    
    subgraph Sanitization Pipeline
        API -->|Prompt + JSON Schema| GenAI[Google Gemini Flash-Lite]
        GenAI -->|Structured JSON| API
        API -->|Redacted Text + Dict| WebUI
    end

    subgraph LLM Processing Terze Parti
        WebUI -->|Testo con Token es. [NOME_1]| ExternalLLM[ChatGPT / Claude / Altro LLM]
        ExternalLLM -->|Risposta con Token| WebUI
    end

    subgraph Reversibility Pipeline
        WebUI -->|POST /api/deanonymize| DeanonEngine[De-anonymizer Locale]
        DeanonEngine -->|Zero-Token Local Replacement| CleanResult([Testo Finale con Dati Reali])
    end
```

---

## 2. Dimensionamento & Quota del Piano Free (500 RPD)

Il tier gratuito di **Gemini Flash-Lite** mette a disposizione **500 richieste giornaliere (RPD)** con un throughput elevato e latenza sub-secondo.

### Modello di Consumo Risorse
| Operazione | Quota Consumata | Latenza Tipica | Note |
|---|---|---|---|
| **Anonimizzazione (`/api/redact`)** | **1 Richiesta** | 400ms - 900ms | Sfrutta `response_schema` per output JSON strutturato |
| **De-anonimizzazione (`/api/deanonymize`)** | **0 Richieste (Zero Token)** | < 2ms | Algoritmo deterministico locale |
| **Health Check (`/api/health`)** | **0 Richieste** | < 1ms | Servizio locale |

### Capacità Operativa Giornaliera
- **500 documenti/testi completi elaborabili al giorno** per utente o team.
- A 1.000 parole per documento medio, corrisponde a **~500.000 parole di testo confidenziale analizzato e protetto ogni 24 ore a costo zero**.
- Raggiunto il limite giornaliero o il rate limit per minuto (RPM), il sistema risponde con `HTTP 429 Too Many Requests` fornendo dettagli per il recupero senza crash.

---

## 3. Algoritmo di Sostituzione & Reversibilità

Uno dei rischi critici nelle pipeline di token replacement è la **collisione di sottostringhe**.
Ad esempio, se il dizionario contiene sia `[NOME_1]` che `[NOME_10]`, sostituire ingenuamente `[NOME_1]` per primo distruggerebbe `[NOME_10]` generando `[Mario_0]`.

### Soluzione Implementata:
1. **Ordinamento Decrescente per Lunghezza**:
   ```python
   sorted_placeholders = sorted(mapping_dict.keys(), key=len, reverse=True)
   ```
2. **Sostituzione Atomica per Chiave**:
   Ogni placeholder viene processato nell'ordine garantito, preservando la coerenza di token nidificati o prefissati.
3. **Zero Token & Zero Egress**:
   Il ripristino non invia mai il testo o il dizionario a server esterni: l'operazione avviene in-memory sul server locale o nel browser dell'utente.

---

## 4. Categorie PII Rilevate

1. **PERSON**: Nomi, cognomi, soprannomi, alias.
2. **EMAIL**: Indirizzi email personali e aziendali.
3. **PHONE**: Numeri di telefono fissi, cellulari, prefissi internazionali.
4. **TAX_ID**: Codici fiscali italiani (C.F.), Partite IVA, numeri di passaporto, carte d'identità, SSN.
5. **FINANCIAL**: Codici IBAN, numeri di carte di credito/debito, BIC/SWIFT.
6. **LOCATION**: Indirizzi stradali, numeri civici, CAP, coordinate specifiche.
7. **OTHER**: Password, chiavi API, referti medici, date di nascita isolate.
