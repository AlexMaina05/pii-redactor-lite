"""
PII Redactor & Text Sanitizer
Powered by Google Gemini Flash-Lite & FastAPI
"""

import os
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Carica configurazione da .env se presente
load_dotenv()

app = FastAPI(
    title="PII Redactor & Text Sanitizer",
    description="Strumento intelligente per rilevare e anonimizzare dati personali sensibili (GDPR-compliant) con ripristino reversibile.",
    version="1.0.0"
)

# Abilita CORS per permettere eventuali integrazioni esterne
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Modelli Pydantic / Schemi Dati
# ==========================================

class RedactedEntity(BaseModel):
    original_value: str = Field(description="Il valore sensibile originale estratto dal testo.")
    placeholder: str = Field(description="Il token segnaposto univoco assegnato (es. [NOME_1], [EMAIL_1]).")
    category: str = Field(description="Categoria dell'entità: PERSON, EMAIL, PHONE, TAX_ID, FINANCIAL, LOCATION, OTHER.")
    explanation: str = Field(description="Breve motivazione per cui il dato è considerato PII o sensibile.")

class RedactionResult(BaseModel):
    redacted_text: str = Field(description="Il testo completo con tutte le entità PII sostituite dai rispettivi segnaposto.")
    entities: List[RedactedEntity] = Field(description="Elenco dettagliato di tutte le entità individuate e sostituite.")
    mapping_dict: Dict[str, str] = Field(description="Dizionario di corrispondenza che mappa ciascun segnaposto al suo valore originale.")

class RedactRequest(BaseModel):
    text: str = Field(..., description="Il testo sorgente da analizzare e ripulire dai dati personali.")
    api_key: Optional[str] = Field(None, description="Gemini API Key opzionale. Se omessa, verrà usata quella configurata nelle variabili d'ambiente.")
    model: Optional[str] = Field("gemini-2.5-flash-lite", description="Identificativo del modello Gemini da utilizzare.")
    custom_rules: Optional[str] = Field(None, description="Regole speciali o istruzioni aggiuntive per l'anonimizzazione.")

class DeanonymizeRequest(BaseModel):
    text: str = Field(..., description="Testo contenente i segnaposto da ripristinare con i valori originali.")
    mapping_dict: Dict[str, str] = Field(..., description="Dizionario con le associazioni segnaposto -> valore originale.")

class DeanonymizeResponse(BaseModel):
    restored_text: str
    restored_count: int


# ==========================================
# Logica di Supporto & Gemini Engine
# ==========================================

SYSTEM_PROMPT = """You are a high-precision PII (Personally Identifiable Information) Redaction & Text Sanitization Engine adhering to GDPR, HIPAA, and data protection best practices.

Your task is to analyze the input text and detect all sensitive personal data and confidential identifiers:
- Full names, first names, surnames, nicknames (Category: PERSON)
- Email addresses (Category: EMAIL)
- Phone and mobile numbers (Category: PHONE)
- Tax codes, Codice Fiscale, SSN, VAT numbers, passport/ID numbers (Category: TAX_ID)
- Bank accounts, IBANs, BIC/SWIFT, Credit card numbers (Category: FINANCIAL)
- Physical addresses, street names, postal/ZIP codes, house numbers (Category: LOCATION)
- Passwords, credentials, dates of birth, sensitive health/biometric details, secret keys (Category: OTHER)

STRICT RULES:
1. Replace each unique sensitive entity with an Italian/International semantic bracketed placeholder:
   - For names: [NOME_1], [NOME_2], etc.
   - For emails: [EMAIL_1], [EMAIL_2], etc.
   - For phones: [TELEFONO_1], [TELEFONO_2], etc.
   - For tax codes: [CODICE_FISCALE_1], [PARTITA_IVA_1], etc.
   - For bank details: [IBAN_1], [CARTA_1], etc.
   - For addresses: [INDIRIZZO_1], [CITTA_1], etc.
   - For others: [DATO_SENSIBILE_1], etc.
2. CONSISTENCY IS MANDATORY: If the same person or entity appears multiple times across the text, use the EXACT SAME placeholder for all occurrences!
3. PRESERVE SURROUNDINGS: Keep punctuation, non-sensitive words, syntax, formatting, and markdown structures completely unchanged.
4. MAPPING ACCURACY: Populate the `mapping_dict` with each exact placeholder as key and its original unmasked string as value.
5. In `entities`, include every found item with its category and a concise explanation in Italian.
"""


def perform_gemini_redaction(text: str, api_key: str, model_name: str, custom_rules: Optional[str] = None) -> RedactionResult:
    """Interroga Gemini via google-genai SDK con structured output Pydantic."""
    try:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La libreria google-genai non è installata correttamente nell'ambiente."
        )

    # Inizializza il client con la chiave fornita
    client = genai.Client(api_key=api_key)

    prompt = f"Analizza il seguente testo ed effettua l'anonimizzazione PII seguendo le istruzioni:\n\n---\n{text}\n---"
    if custom_rules:
        prompt += f"\n\nRegole aggiuntive dell'utente:\n{custom_rules}"

    try:
        # Chiamata al modello con response_schema strutturato
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=RedactionResult,
                temperature=0.1,  # Bassa temperatura per massima precisione e determinismo
            ),
        )

        if not response.parsed:
            # Fallback nel caso in cui parsed non sia valorizzato direttamente
            import json
            data = json.loads(response.text)
            return RedactionResult(**data)

        return response.parsed

    except APIError as e:
        err_msg = str(e)
        # Controllo specifico su quota / 429 Too Many Requests
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "Quota exceeded" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Quota giornaliera o per minuto dell'API Gemini raggiunta (HTTP 429). Attendi il reset della quota (piano free: 500 richieste/giorno)."
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Errore restituito da Google Gemini API: {err_msg}"
        )
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Quota delle richieste Gemini esaurita (HTTP 429). Attendi qualche istante o il reset giornaliero."
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Errore durante l'elaborazione del testo: {err_msg}"
        )


def restore_pii(text: str, mapping_dict: Dict[str, str]) -> tuple[str, int]:
    """
    Ripristina i dati originali sostituendo i segnaposto nel testo in ordine decrescente di lunghezza
    per evitare collisioni parziali. Esecuzione 100% locale a zero token.
    """
    if not mapping_dict or not text:
        return text, 0

    # Ordina i placeholder dal più lungo al più corto per evitare collisioni (es. [NOME_10] prima di [NOME_1])
    sorted_placeholders = sorted(mapping_dict.keys(), key=len, reverse=True)
    restored = text
    count = 0

    for placeholder in sorted_placeholders:
        original = mapping_dict[placeholder]
        if placeholder in restored:
            occurrences = restored.count(placeholder)
            count += occurrences
            restored = restored.replace(placeholder, original)

    return restored, count


# ==========================================
# Endpoint API
# ==========================================

@app.get("/api/health")
def health_check():
    """Verifica lo stato del servizio e la disponibilità della chiave d'ambiente."""
    env_key = os.getenv("GEMINI_API_KEY")
    default_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")
    return {
        "status": "healthy",
        "has_configured_api_key": bool(env_key and env_key.strip()),
        "default_model": default_model,
        "daily_free_limit": "500 richieste/giorno (Flash-Lite)"
    }


@app.post("/api/redact", response_model=RedactionResult)
def redact_text(req: RedactRequest):
    """
    Analizza il testo fornito ed esegue l'anonimizzazione dei dati personali tramite Gemini Flash-Lite.
    Restituisce il testo censurato, l'elenco delle entità e il dizionario per la de-anonimizzazione.
    """
    raw_text = req.text.strip()
    if not raw_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Il testo inserito è vuoto.")

    # Risoluzione della chiave API: payload prioritario, altrimenti variabile d'ambiente
    api_key = req.api_key.strip() if req.api_key else os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessuna Gemini API Key configurata. Inseriscila nell'interfaccia o definisci GEMINI_API_KEY nel file .env."
        )

    model_name = (req.model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")).strip()

    result = perform_gemini_redaction(
        text=raw_text,
        api_key=api_key,
        model_name=model_name,
        custom_rules=req.custom_rules
    )

    return result


@app.post("/api/deanonymize", response_model=DeanonymizeResponse)
def deanonymize_text(req: DeanonymizeRequest):
    """
    Ripristina un testo anonimizzato reinserendo i dati originali tramite il dizionario di mappatura.
    Operazione istantanea eseguita interamente in locale.
    """
    restored, count = restore_pii(req.text, req.mapping_dict)
    return DeanonymizeResponse(restored_text=restored, restored_count=count)


# Monta i file statici della Web App
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    """Serve la pagina principale della Web Application."""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Interfaccia web non trovata. Controlla la cartella static/."}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 Avvio PII Redactor su http://{host}:{port}")
    uvicorn.run("main:app", host=host, port=port, reload=True)
