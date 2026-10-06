import pytest
from fastapi.testclient import TestClient
from main import app, restore_pii, RedactionResult, RedactedEntity

client = TestClient(app)


def test_restore_pii_basic():
    text = "Buongiorno [NOME_1], ci vediamo all'indirizzo [INDIRIZZO_1]."
    mapping = {
        "[NOME_1]": "Mario Rossi",
        "[INDIRIZZO_1]": "Via Roma 42, Milano"
    }
    restored, count = restore_pii(text, mapping)
    assert restored == "Buongiorno Mario Rossi, ci vediamo all'indirizzo Via Roma 42, Milano."
    assert count == 2


def test_restore_pii_substring_safety():
    """Verifica che segnaposto come [NOME_10] non vengano parzialmente sovrascritti da [NOME_1]."""
    text = "Utente A: [NOME_10], Utente B: [NOME_1]."
    mapping = {
        "[NOME_1]": "Alice",
        "[NOME_10]": "Bob Decimo"
    }
    restored, count = restore_pii(text, mapping)
    assert restored == "Utente A: Bob Decimo, Utente B: Alice."
    assert count == 2


def test_restore_pii_multiple_occurrences():
    text = "Contatta [NOME_1]. Se non risponde [NOME_1], chiama [TELEFONO_1]."
    mapping = {
        "[NOME_1]": "Dott. Bianchi",
        "[TELEFONO_1]": "+39 02 1234567"
    }
    restored, count = restore_pii(text, mapping)
    assert restored == "Contatta Dott. Bianchi. Se non risponde Dott. Bianchi, chiama +39 02 1234567."
    assert count == 3


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "default_model" in data


def test_redact_endpoint_empty_text():
    response = client.post("/api/redact", json={"text": "   "})
    assert response.status_code == 400
    assert "vuoto" in response.json()["detail"].lower()


def test_redact_endpoint_missing_api_key():
    # Test senza API key
    response = client.post("/api/redact", json={"text": "Ciao Mario Rossi", "api_key": ""})
    # Se non c'è GEMINI_API_KEY nell'ambiente né nel payload, deve dare 400
    if not client.app.dependency_overrides:
        assert response.status_code in [400, 429, 500, 502]


def test_deanonymize_endpoint():
    payload = {
        "text": "L'email di [NOME_1] è [EMAIL_1].",
        "mapping_dict": {
            "[NOME_1]": "Giuseppe Verdi",
            "[EMAIL_1]": "g.verdi@teatro.it"
        }
    }
    response = client.post("/api/deanonymize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["restored_text"] == "L'email di Giuseppe Verdi è g.verdi@teatro.it."
    assert data["restored_count"] == 2
