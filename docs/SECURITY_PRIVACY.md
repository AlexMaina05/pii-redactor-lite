# 🔒 Sicurezza, Privacy e Conformità GDPR

## 1. Principi di Trattamento dei Dati

Il software **PII Redactor Lite** è stato concepito con il principio di **Privacy by Design** (Art. 25 GDPR).

### A. Zero Persistence Guarantee (Nessun Database)
- L'applicazione **non include alcun database** (né SQLite, né PostgreSQL, né Redis).
- Nessun log su file su disco contiene i testi inviati o il dizionario delle entità.
- Il ciclo di vita delle informazioni sensibili è strettamente vincolato al singolo ciclo di richiesta HTTP request/response in memoria RAM effimera.

### B. Protezione delle Chiavi API
- Le chiavi API caricate via file `.env` non vengono mai esposte al client (l'endpoint `/api/health` restituisce solo un flag booleano `has_configured_api_key: true`).
- Le chiavi inserite tramite interfaccia utente rimangono confinate nel `localStorage` del browser locale dell'utente e trasmesse al server solo per autorizzare la richiesta.

### C. Mappatura & De-anonimizzazione Locale
- Il dizionario di conversione `mapping_dict` risiede unicamente nel client o nei sistemi del richiedente.
- Il processo di ripristino (`/api/deanonymize`) viene eseguito tramite algoritmo di sostituzione locale. Nessun fornitore esterno (inclusi OpenAI, Anthropic o altri provider a valle) riceverà mai le entità reali, ma unicamente i segnaposto opachi.

---

## 2. Minaccia e Mitigazioni

| Vettore di Rischio | Mitigazione Implementata |
|---|---|
| **Egress non autorizzato di PII verso LLM terzi** | I prompt inviati a servizi terzi contengono unicamente i token di sostituzione (`[NOME_1]`, `[IBAN_1]`). |
| **Collisione di token in ripristino** | Algoritmo decrescente di lunghezza (`sorted(keys, key=len, reverse=True)`). |
| **Esaurimento imprevisto quota** | Intercettazione formale dell'errore HTTP 429 con messaggio descrittivo. |
| **CORS Abuse** | Middleware configurato con impostazioni modificabili in ambiente di produzione. |
