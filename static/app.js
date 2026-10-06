// PII Redactor Lite Frontend Engine

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Lucide icons
  lucide.createIcons();

  // State
  let currentMapping = {};
  let currentEntities = [];

  // DOM Elements
  const tabRedactBtn = document.getElementById('tab-redact-btn');
  const tabRestoreBtn = document.getElementById('tab-restore-btn');
  const tabRedactView = document.getElementById('tab-redact-view');
  const tabRestoreView = document.getElementById('tab-restore-view');

  const inputText = document.getElementById('input-text');
  const outputText = document.getElementById('output-text');
  const charCount = document.getElementById('char-count');
  const redactBtn = document.getElementById('redact-btn');
  const sampleTextBtn = document.getElementById('sample-text-btn');
  const clearInputBtn = document.getElementById('clear-input-btn');
  const copyRedactedBtn = document.getElementById('copy-redacted-btn');
  const sendToRestoreBtn = document.getElementById('send-to-restore-btn');
  const loadingSpinner = document.getElementById('loading-spinner');

  const entitiesSection = document.getElementById('entities-section');
  const entitiesCount = document.getElementById('entities-count');
  const entitiesTableBody = document.getElementById('entities-table-body');
  const exportMappingBtn = document.getElementById('export-mapping-btn');

  const restoreInputText = document.getElementById('restore-input-text');
  const restoreOutputText = document.getElementById('restore-output-text');
  const runRestoreBtn = document.getElementById('run-restore-btn');
  const copyRestoredBtn = document.getElementById('copy-restored-btn');
  const restoreDictCount = document.getElementById('restore-dict-count');

  // Settings Modal Elements
  const openSettingsBtn = document.getElementById('open-settings-btn');
  const closeSettingsBtn = document.getElementById('close-settings-btn');
  const settingsModal = document.getElementById('settings-modal');
  const saveSettingsBtn = document.getElementById('save-settings-btn');
  const apiKeyInput = document.getElementById('api-key-input');
  const modelSelect = document.getElementById('model-select');
  const currentModelDisplay = document.getElementById('current-model-display');

  // Load saved preferences
  const savedApiKey = localStorage.getItem('gemini_api_key') || '';
  const savedModel = localStorage.getItem('gemini_model') || 'gemini-2.5-flash-lite';
  
  apiKeyInput.value = savedApiKey;
  modelSelect.value = savedModel;
  currentModelDisplay.textContent = savedModel;

  // Check health and server configuration
  fetch('/api/health')
    .then(res => res.json())
    .then(data => {
      const statusBadge = document.getElementById('status-badge');
      const statusText = document.getElementById('status-text');
      if (data.status === 'healthy') {
        statusBadge.classList.remove('hidden');
        if (data.has_configured_api_key) {
          statusText.textContent = 'Server Connesso (Env Key OK)';
        } else if (savedApiKey) {
          statusText.textContent = 'Client API Key attiva';
        } else {
          statusText.textContent = 'API Key richiesta';
        }
      }
    })
    .catch(() => {
      console.warn('Backend non raggiungibile');
    });

  // Sample Text Data (Italian real-world realistic example)
  const SAMPLE_TEXT = `Gentile Dott.ssa Francesca Ferri,
Le confermo che il Sig. Marco Rossi (nato a Milano il 14/05/1982, C.F. RSSMRC82E14F205W) ha richiesto la documentazione fiscale relativa al contratto di consulenza.
Il cliente è raggiungibile telefonicamente al +39 347 1234567 o via email all'indirizzo marco.rossi@example.com.
Per l'accredito dell'onorario di € 2.450,00 si prega di fare riferimento all'IBAN IT60X0542811101000000123456 intestato a Rossi Consulting S.r.l., con sede legale in Corso Buenos Aires 45, 20124 Milano.
In caso di chiarimenti tecnici potete contattare anche il referente commerciale Ing. Valerio Conti (v.conti@azienda-partner.it).

Cordiali saluti,
Elena Moretti`;

  // Event Listeners for Tabs
  tabRedactBtn.addEventListener('click', () => switchTab('redact'));
  tabRestoreBtn.addEventListener('click', () => switchTab('restore'));

  function switchTab(tab) {
    if (tab === 'redact') {
      tabRedactView.classList.remove('hidden');
      tabRestoreView.classList.add('hidden');
      tabRedactBtn.classList.add('text-indigo-400', 'border-indigo-500');
      tabRedactBtn.classList.remove('text-slate-400', 'border-transparent');
      tabRestoreBtn.classList.add('text-slate-400', 'border-transparent');
      tabRestoreBtn.classList.remove('text-indigo-400', 'border-indigo-500');
    } else {
      tabRedactView.classList.add('hidden');
      tabRestoreView.classList.remove('hidden');
      tabRestoreBtn.classList.add('text-indigo-400', 'border-indigo-500');
      tabRestoreBtn.classList.remove('text-slate-400', 'border-transparent');
      tabRedactBtn.classList.add('text-slate-400', 'border-transparent');
      tabRedactBtn.classList.remove('text-indigo-400', 'border-indigo-500');
      updateRestoreStats();
    }
  }

  // Character counter
  inputText.addEventListener('input', () => {
    charCount.textContent = `${inputText.value.length} caratteri`;
  });

  // Sample button
  sampleTextBtn.addEventListener('click', () => {
    inputText.value = SAMPLE_TEXT;
    charCount.textContent = `${inputText.value.length} caratteri`;
    showToast('Testo di esempio caricato!', 'info');
  });

  // Clear button
  clearInputBtn.addEventListener('click', () => {
    inputText.value = '';
    outputText.value = '';
    charCount.textContent = '0 caratteri';
    entitiesSection.classList.add('hidden');
    currentMapping = {};
    currentEntities = [];
  });

  // Redact Action
  redactBtn.addEventListener('click', async () => {
    const text = inputText.value.trim();
    if (!text) {
      showToast('Inserisci un testo da analizzare prima di procedere.', 'error');
      return;
    }

    const apiKey = localStorage.getItem('gemini_api_key') || '';
    const model = localStorage.getItem('gemini_model') || 'gemini-2.5-flash-lite';

    // Show loading
    loadingSpinner.classList.remove('hidden');
    redactBtn.disabled = true;

    try {
      const response = await fetch('/api/redact', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: text,
          api_key: apiKey || null,
          model: model
        })
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Quota limite di 500 richieste giornaliere raggiunta per questo account Gemini (HTTP 429).');
        } else {
          throw new Error(data.detail || 'Si è verificato un errore durante l\'elaborazione.');
        }
      }

      // Populate results
      outputText.value = data.redacted_text;
      currentMapping = data.mapping_dict || {};
      currentEntities = data.entities || [];

      renderEntitiesTable(currentEntities);
      entitiesSection.classList.remove('hidden');
      updateRestoreStats();

      showToast(`Anonimizzazione completata! Individuate ${currentEntities.length} entità.`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      loadingSpinner.classList.add('hidden');
      redactBtn.disabled = false;
    }
  });

  // Render Table
  function renderEntitiesTable(entities) {
    entitiesCount.textContent = entities.length;
    entitiesTableBody.innerHTML = '';

    entities.forEach(item => {
      const tr = document.createElement('tr');
      tr.className = 'hover:bg-slate-800/80 transition-colors';

      const catBadge = `<span class="px-2 py-0.5 rounded text-[11px] font-mono font-semibold badge-${item.category}">${item.category}</span>`;
      
      tr.innerHTML = `
        <td class="py-2.5 px-4 font-mono text-indigo-400 font-bold">${escapeHtml(item.placeholder)}</td>
        <td class="py-2.5 px-4 font-mono text-slate-200">${escapeHtml(item.original_value)}</td>
        <td class="py-2.5 px-4">${catBadge}</td>
        <td class="py-2.5 px-4 text-slate-400">${escapeHtml(item.explanation || '')}</td>
      `;
      entitiesTableBody.appendChild(tr);
    });
  }

  // De-anonymize / Restore Action
  runRestoreBtn.addEventListener('click', async () => {
    const textToRestore = restoreInputText.value.trim();
    if (!textToRestore) {
      showToast('Inserisci il testo contenente i segnaposto da ripristinare.', 'error');
      return;
    }

    if (Object.keys(currentMapping).length === 0) {
      showToast('Nessun dizionario di mappatura disponibile. Esegui prima un\'anonimizzazione.', 'error');
      return;
    }

    try {
      const response = await fetch('/api/deanonymize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToRestore,
          mapping_dict: currentMapping
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Errore nel ripristino');
      }

      restoreOutputText.value = data.restored_text;
      showToast(`Ripristino completato! Sostituiti ${data.restored_count} segnaposto.`, 'success');
    } catch (err) {
      showToast(err.message, 'error');
    }
  });

  // Transfer redacted to restore tab
  sendToRestoreBtn.addEventListener('click', () => {
    if (!outputText.value) {
      showToast('Nessun testo anonimizzato disponibile da trasferire.', 'error');
      return;
    }
    restoreInputText.value = outputText.value;
    switchTab('restore');
    showToast('Testo trasferito nella sezione di ripristino.', 'info');
  });

  function updateRestoreStats() {
    const count = Object.keys(currentMapping).length;
    restoreDictCount.textContent = count;
  }

  // Copy buttons
  copyRedactedBtn.addEventListener('click', () => copyToClipboard(outputText.value, 'Testo anonimizzato copiato!'));
  copyRestoredBtn.addEventListener('click', () => copyToClipboard(restoreOutputText.value, 'Testo finale ripristinato copiato!'));

  // Export mapping JSON
  exportMappingBtn.addEventListener('click', () => {
    if (Object.keys(currentMapping).length === 0) {
      showToast('Nessun dizionario da esportare.', 'error');
      return;
    }
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentMapping, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", "pii_mapping_dictionary.json");
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast('Dizionario esportato come file JSON.', 'success');
  });

  // Settings Modal Controls
  openSettingsBtn.addEventListener('click', () => settingsModal.classList.remove('hidden'));
  closeSettingsBtn.addEventListener('click', () => settingsModal.classList.add('hidden'));

  saveSettingsBtn.addEventListener('click', () => {
    const key = apiKeyInput.value.trim();
    const model = modelSelect.value;

    localStorage.setItem('gemini_api_key', key);
    localStorage.setItem('gemini_model', model);
    currentModelDisplay.textContent = model;

    settingsModal.classList.add('hidden');
    showToast('Impostazioni salvate con successo!', 'success');
  });

  // Helpers
  function copyToClipboard(text, message) {
    if (!text) {
      showToast('Nessun contenuto da copiare.', 'error');
      return;
    }
    navigator.clipboard.writeText(text).then(() => {
      showToast(message, 'success');
    }).catch(() => {
      showToast('Impossibile copiare negli appunti.', 'error');
    });
  }

  function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toast-message');
    const toastIcon = document.getElementById('toast-icon');

    toastMessage.textContent = message;

    if (type === 'success') {
      toast.className = 'fixed bottom-6 right-6 z-50 max-w-sm px-4 py-3 rounded-xl shadow-2xl border text-xs font-medium flex items-center gap-2.5 transition-all bg-emerald-950/90 border-emerald-500 text-emerald-200';
    } else if (type === 'error') {
      toast.className = 'fixed bottom-6 right-6 z-50 max-w-sm px-4 py-3 rounded-xl shadow-2xl border text-xs font-medium flex items-center gap-2.5 transition-all bg-rose-950/90 border-rose-500 text-rose-200';
    } else {
      toast.className = 'fixed bottom-6 right-6 z-50 max-w-sm px-4 py-3 rounded-xl shadow-2xl border text-xs font-medium flex items-center gap-2.5 transition-all bg-indigo-950/90 border-indigo-500 text-indigo-200';
    }

    toast.classList.remove('hidden');
    setTimeout(() => {
      toast.classList.add('hidden');
    }, 4000);
  }

  function escapeHtml(string) {
    return String(string).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }
});
