document.addEventListener('DOMContentLoaded', () => {
  const inputText = document.getElementById('inputText');
  const analyzeButton = document.getElementById('analyzeButton');
  const uploadButton = document.getElementById('uploadButton');
  const fileInput = document.getElementById('fileInput');
  const jsonOutput = document.getElementById('jsonOutput');
  const downloadButton = document.getElementById('downloadButton');
  const inputPanel = document.getElementById('input-panel');
  // Mode switch UI (render in host if present)
  const host = document.getElementById('modeSwitchHost');
  const modeSwitchContainer = document.createElement('div');
  modeSwitchContainer.className = 'flex items-center justify-center gap-3 mb-2';
  const modeLabel = document.createElement('span');
  modeLabel.className = 'text-sm text-gray-300';
  modeLabel.textContent = 'Modo:';
  const switchWrap = document.createElement('button');
  switchWrap.id = 'modeSwitch';
  switchWrap.className = 'relative inline-flex h-6 w-12 items-center rounded-full bg-gray-700 transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-400';
  const switchDot = document.createElement('span');
  switchDot.className = 'inline-block h-5 w-5 transform rounded-full bg-white transition-transform duration-200 translate-x-1';
  const modeText = document.createElement('span');
  modeText.className = 'text-sm text-gray-200 ml-2';
  modeText.textContent = 'Turbo';
  switchWrap.appendChild(switchDot);
  modeSwitchContainer.appendChild(modeLabel);
  modeSwitchContainer.appendChild(switchWrap);
  modeSwitchContainer.appendChild(modeText);
  if (host) {
    host.appendChild(modeSwitchContainer);
  } else {
    inputPanel.insertBefore(modeSwitchContainer, inputPanel.firstChild);
  }
  let currentMode = (localStorage.getItem('analyzer_mode') || 'turbo');
  function renderSwitch() {
    const isTurbo = currentMode === 'turbo';
    switchWrap.classList.toggle('bg-yellow-500', isTurbo);
    switchWrap.classList.toggle('bg-gray-700', !isTurbo);
    switchDot.style.transform = isTurbo ? 'translateX(24px)' : 'translateX(4px)';
    modeText.textContent = isTurbo ? 'Turbo' : 'Heavy';
  }
  renderSwitch();
  switchWrap.addEventListener('click', () => {
    currentMode = currentMode === 'turbo' ? 'heavy' : 'turbo';
    localStorage.setItem('analyzer_mode', currentMode);
    renderSwitch();
  });
  const loadingOverlay = document.getElementById('loadingOverlay');
  const githubLink = document.getElementById('githubLink');

  // Configure GitHub link from meta tag
  try {
    const meta = document.querySelector('meta[name="repo-url"]');
    if (meta && meta.content) githubLink.href = meta.content;
  } catch {}

  // Pre-fill example text (concise to keep UI clean)
  const initialText = `Nombre: Internal Payments Hub

Uso:
- Consultar pagos históricos de clientes y proveedores.
- Aprobar, modificar o bloquear pagos de alto riesgo.
- Ajustar límites y desbloquear cuentas bajo investigación.

APIs expuestas:
- /api/payments/submit
- /api/payments/refund
- /api/account/limit-adjust
- /api/account/audit-log

Controles actuales:
- Logs de acciones sensibles
- Roles (operator, supervisor, auditor)
- Sin scoring automático de anomalías`;
  inputText.value = initialText;

  // File Upload UI
  uploadButton.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', (event) => {
    const file = event.target.files[0];
    if (file) {
      // Preview locally in textarea
      readFile(file);
    }
  });

  // Drag and Drop
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    inputPanel.addEventListener(eventName, preventDefaults, false);
  });
  function preventDefaults(e) { e.preventDefault(); e.stopPropagation(); }
  ['dragenter', 'dragover'].forEach(eventName => {
    inputPanel.addEventListener(eventName, () => inputPanel.classList.add('drop-zone-active'), false);
  });
  ['dragleave', 'drop'].forEach(eventName => {
    inputPanel.addEventListener(eventName, () => inputPanel.classList.remove('drop-zone-active'), false);
  });
  inputPanel.addEventListener('drop', (event) => {
    const dt = event.dataTransfer;
    const file = dt.files[0];
    if (file && (file.type === 'text/plain' || file.name.endsWith('.txt'))) {
      readFile(file);
      fileInput.files = dt.files; // keep selection
    } else {
      alert('Por favor, suelta un archivo .txt');
    }
  }, false);

  function readFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => { inputText.value = e.target.result; };
    reader.readAsText(file);
  }

  // API Call Logic
  let reportData = null;
  analyzeButton.addEventListener('click', async () => {
    const userInput = inputText.value.trim();
    setLoading(true);
    jsonOutput.textContent = 'Procesando...';
    reportData = null;

    try {
      let response;
      if (!userInput && fileInput.files.length > 0) {
        // Submit file to upload endpoint
        const form = new FormData();
        form.append('file', fileInput.files[0]);
        const qsU = `?mode=${encodeURIComponent(currentMode)}`;
        response = await fetch('/api/analyze-upload' + qsU, { method: 'POST', body: form });
      } else {
        if (!userInput) {
          alert('El campo de texto no puede estar vacío.');
          setLoading(false);
          return;
        }
        const qs = `?mode=${encodeURIComponent(currentMode)}`;
        response = await fetch('/api/analyze' + qs, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_input: userInput })
        });
      }

      if (!response.ok) {
        let msg = `HTTP error! status: ${response.status}`;
        try { const err = await response.json(); if (err.detail) msg = err.detail; } catch {}
        throw new Error(msg);
      }

      const result = await response.json();
      const parsedReport = JSON.parse(result.report_json);
      // Merge timing_ms from envelope if present
      try {
        if (typeof result.timing_ms === 'number') {
          parsedReport.timing_ms = result.timing_ms;
        } else if (typeof parsedReport._timing_ms === 'number' && typeof parsedReport.timing_ms !== 'number') {
          // Backward compatibility
          parsedReport.timing_ms = parsedReport._timing_ms;
        }
      } catch {}
      reportData = parsedReport;
      jsonOutput.textContent = JSON.stringify(parsedReport, null, 2);
      downloadButton.disabled = false;
    } catch (error) {
      console.error('Error during analysis:', error);
      jsonOutput.textContent = `Error al procesar la solicitud:\n\n${error.message}`;
      downloadButton.disabled = true;
    } finally {
      setLoading(false);
    }
  });

  function setLoading(isLoading) {
    if (isLoading) {
      loadingOverlay.classList.remove('hidden');
      analyzeButton.disabled = true;
      analyzeButton.textContent = 'Analizando...';
    } else {
      loadingOverlay.classList.add('hidden');
      analyzeButton.disabled = false;
      analyzeButton.textContent = 'Analizar';
    }
  }

  // Download Logic
  downloadButton.addEventListener('click', () => {
    if (!reportData) return;
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(reportData, null, 2));
    const a = document.createElement('a');
    a.setAttribute('href', dataStr);
    a.setAttribute('download', 'security_report.json');
    document.body.appendChild(a);
    a.click();
    a.remove();
  });
});
