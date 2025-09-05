document.addEventListener('DOMContentLoaded', () => {
  const inputText = document.getElementById('inputText');
  const analyzeButton = document.getElementById('analyzeButton');
  const uploadButton = document.getElementById('uploadButton');
  const fileInput = document.getElementById('fileInput');
  const jsonOutput = document.getElementById('jsonOutput');
  const downloadButton = document.getElementById('downloadButton');
  const inputPanel = document.getElementById('input-panel');
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
        response = await fetch('/api/analyze-upload', { method: 'POST', body: form });
      } else {
        if (!userInput) {
          alert('El campo de texto no puede estar vacío.');
          setLoading(false);
          return;
        }
        response = await fetch('/api/analyze', {
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
