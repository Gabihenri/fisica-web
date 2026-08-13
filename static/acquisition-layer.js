(() => {
  const FIELD_MAP = {
    queda: [
      { name: 'altura', label: 'Altura (m)' },
      { name: 'tempo', label: 'Tempo (s)' },
    ],
    pendulo: [
      { name: 'comprimento', label: 'Comprimento (m)' },
      { name: 'periodo', label: 'Período (s)' },
    ],
    plano: [
      { name: 'angulo', label: 'Ângulo (°)' },
      { name: 'distancia', label: 'Distância (m)' },
      { name: 'tempo', label: 'Tempo (s)' },
    ],
  };

  let serialPort = null;
  let serialReader = null;
  let serialRunning = false;
  let serialBuffer = '';
  let activePanel = null;

  function supportsWebSerial() {
    return 'serial' in navigator;
  }

  function make(tag, attrs = {}, text = '') {
    const el = document.createElement(tag);
    Object.entries(attrs).forEach(([key, value]) => {
      if (key === 'class') el.className = value;
      else if (key === 'for') el.htmlFor = value;
      else el.setAttribute(key, value);
    });
    if (text) el.textContent = text;
    return el;
  }

  function setStatus(panel, message, type = 'info') {
    const status = panel.querySelector('.acq-status');
    if (!status) return;
    status.dataset.type = type;
    status.textContent = message;
  }

  function selectedSource(panel) {
    return panel.querySelector('input[name="acq-source"]:checked')?.value || 'manual';
  }

  function ensureOriginInput(article) {
    const form = article.querySelector('form.measure');
    if (!form) return null;
    let hidden = form.querySelector('input[name="origem"]');
    if (!hidden) {
      hidden = make('input', { type: 'hidden', name: 'origem', value: 'manual' });
      form.appendChild(hidden);
    }
    return hidden;
  }

  function applySource(panel) {
    const source = selectedSource(panel);
    const article = panel.closest('[data-experiment]');
    const hidden = ensureOriginInput(article);
    if (hidden) hidden.value = source;

    panel.querySelectorAll('[data-acq-section]').forEach((section) => {
      section.hidden = section.dataset.acqSection !== source;
    });

    if (source === 'manual') setStatus(panel, 'Entrada manual ativa. Digite os valores e registre a medição.');
    if (source === 'arduino') {
      if (supportsWebSerial()) setStatus(panel, 'Arduino selecionado. Conecte a placa e escolha o canal/variável.');
      else setStatus(panel, 'Web Serial não está disponível neste navegador. Use um navegador compatível no computador ou o modo manual.', 'warn');
    }
    if (source === 'raspberry') setStatus(panel, 'Raspberry Pi selecionado. A integração de rede/GPIO será ativada na próxima etapa.');
    if (source === 'other') setStatus(panel, 'Outra fonte selecionada. Use a leitura recebida para preencher a variável escolhida.');
  }

  function parseSerialLine(line) {
    const text = line.trim();
    if (!text) return null;

    try {
      const obj = JSON.parse(text);
      if (typeof obj === 'number') return { value: obj };
      if (obj && typeof obj === 'object') {
        const value = Number(obj.value ?? obj.valor ?? obj.v);
        if (Number.isFinite(value)) {
          return {
            value,
            channel: String(obj.channel ?? obj.canal ?? obj.pin ?? '').trim(),
            field: String(obj.field ?? obj.campo ?? '').trim(),
          };
        }
      }
    } catch (_) {}

    const parts = text.split(/[;,\t]/).map((p) => p.trim()).filter(Boolean);
    if (parts.length >= 2) {
      const value = Number(parts[parts.length - 1].replace(',', '.'));
      if (Number.isFinite(value)) return { channel: parts[0], value };
    }

    const value = Number(text.replace(',', '.'));
    return Number.isFinite(value) ? { value } : null;
  }

  function deliverReading(reading) {
    if (!activePanel || !reading) return;
    const article = activePanel.closest('[data-experiment]');
    const targetSelect = activePanel.querySelector('.acq-target');
    const channelInput = activePanel.querySelector('.acq-channel');
    const configuredChannel = channelInput?.value.trim();

    if (configuredChannel && reading.channel && configuredChannel.toLowerCase() !== reading.channel.toLowerCase()) return;

    const fieldName = reading.field || targetSelect?.value;
    const input = article?.querySelector(`form.measure [name="${CSS.escape(fieldName || '')}"]`);
    if (!input) {
      setStatus(activePanel, `Leitura recebida (${reading.value}), mas nenhuma variável de destino foi selecionada.`, 'warn');
      return;
    }

    input.value = String(reading.value);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    setStatus(activePanel, `Leitura recebida${reading.channel ? ` de ${reading.channel}` : ''}: ${reading.value} → ${targetSelect.options[targetSelect.selectedIndex]?.text || fieldName}.`, 'ok');
  }

  async function serialLoop(panel) {
    const decoder = new TextDecoder();
    serialRunning = true;
    while (serialPort?.readable && serialRunning) {
      serialReader = serialPort.readable.getReader();
      try {
        while (serialRunning) {
          const { value, done } = await serialReader.read();
          if (done) break;
          serialBuffer += decoder.decode(value, { stream: true });
          const lines = serialBuffer.split(/\r?\n/);
          serialBuffer = lines.pop() || '';
          lines.forEach((line) => deliverReading(parseSerialLine(line)));
        }
      } catch (error) {
        if (serialRunning) setStatus(panel, `Falha na leitura serial: ${error.message}`, 'error');
      } finally {
        serialReader.releaseLock();
        serialReader = null;
      }
    }
  }

  async function connectSerial(panel) {
    activePanel = panel;
    if (!supportsWebSerial()) {
      setStatus(panel, 'Este navegador não oferece Web Serial. Tente Chrome/Edge em um computador ou use entrada manual.', 'warn');
      return;
    }

    try {
      const baudRate = Number(panel.querySelector('.acq-baud')?.value || 9600);
      serialPort = await navigator.serial.requestPort();
      await serialPort.open({ baudRate });
      setStatus(panel, `Placa conectada em ${baudRate} baud. Aguardando leituras…`, 'ok');
      panel.querySelector('.acq-connect').disabled = true;
      panel.querySelector('.acq-disconnect').disabled = false;
      serialLoop(panel);
    } catch (error) {
      setStatus(panel, `Não foi possível conectar à porta serial: ${error.message}`, 'error');
    }
  }

  async function disconnectSerial(panel) {
    serialRunning = false;
    try {
      if (serialReader) await serialReader.cancel();
    } catch (_) {}
    try {
      if (serialPort) await serialPort.close();
    } catch (_) {}
    serialPort = null;
    activePanel = null;
    panel.querySelector('.acq-connect').disabled = false;
    panel.querySelector('.acq-disconnect').disabled = true;
    setStatus(panel, 'Placa desconectada.');
  }

  function buildPanel(article) {
    const key = article.dataset.experiment;
    const fields = FIELD_MAP[key] || [];
    const form = article.querySelector('form.measure');
    if (!form || article.querySelector('.acquisition-panel')) return;

    const panel = make('section', { class: 'acquisition-panel', 'aria-label': 'Aquisição de dados' });
    panel.innerHTML = `
      <div class="acq-heading">
        <div><span class="acq-kicker">Aquisição de dados</span><h4>Fonte da medição</h4></div>
        <span class="acq-badge">Universal</span>
      </div>
      <div class="acq-sources" role="radiogroup" aria-label="Fonte dos dados">
        <label><input type="radio" name="acq-source" value="manual" checked> Manual</label>
        <label><input type="radio" name="acq-source" value="arduino"> Arduino / Serial</label>
        <label><input type="radio" name="acq-source" value="raspberry"> Raspberry Pi</label>
        <label><input type="radio" name="acq-source" value="other"> Outro</label>
      </div>
      <div data-acq-section="manual" class="acq-section"><small>Use os campos do experimento normalmente.</small></div>
      <div data-acq-section="arduino" class="acq-section" hidden>
        <div class="acq-grid">
          <label>Baud rate<select class="acq-baud"><option>9600</option><option>19200</option><option>38400</option><option>57600</option><option>115200</option></select></label>
          <label>Canal / porta<input class="acq-channel" placeholder="Ex.: A0, D2, CH1"></label>
          <label>Variável de destino<select class="acq-target"></select></label>
        </div>
        <div class="acq-actions"><button type="button" class="secondary acq-connect">Conectar placa</button><button type="button" class="secondary acq-disconnect" disabled>Desconectar</button></div>
        <small>Formato aceito: <code>12.3</code>, <code>A0,12.3</code> ou JSON como <code>{"channel":"A0","value":12.3}</code>.</small>
      </div>
      <div data-acq-section="raspberry" class="acq-section" hidden>
        <div class="acq-grid"><label>Interface<select><option>GPIO</option><option>I²C</option><option>SPI</option><option>Serial</option><option>Rede / API</option></select></label><label>Canal / pino<input placeholder="Ex.: GPIO17"></label><label>Variável de destino<select class="acq-target-rpi"></select></label></div>
        <small>Estrutura preparada. A conexão de rede/GPIO será habilitada na próxima etapa.</small>
      </div>
      <div data-acq-section="other" class="acq-section" hidden><small>Camada preparada para sensores ou dispositivos externos adicionais.</small></div>
      <p class="acq-status" role="status" aria-live="polite">Entrada manual ativa.</p>
    `;

    [panel.querySelector('.acq-target'), panel.querySelector('.acq-target-rpi')].forEach((select) => {
      fields.forEach((field) => select.appendChild(new Option(field.label, field.name)));
    });

    panel.querySelectorAll('input[name="acq-source"]').forEach((radio) => radio.addEventListener('change', () => applySource(panel)));
    panel.querySelector('.acq-connect').addEventListener('click', () => connectSerial(panel));
    panel.querySelector('.acq-disconnect').addEventListener('click', () => disconnectSerial(panel));

    ensureOriginInput(article);
    form.insertAdjacentElement('beforebegin', panel);
    applySource(panel);
  }

  const style = make('style');
  style.textContent = `
    .acquisition-panel{margin:18px 0;padding:16px;border:1px solid var(--border);border-radius:14px;background:linear-gradient(180deg,var(--surface2),var(--surface));}
    .acq-heading{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:12px}.acq-heading h4{margin:2px 0;font-size:1.05rem}.acq-kicker{font-size:.72rem;text-transform:uppercase;letter-spacing:.1em;font-weight:800;color:var(--primary)}.acq-badge{font-size:.75rem;padding:4px 8px;border-radius:999px;background:var(--surface);border:1px solid var(--border);color:var(--muted)}
    .acq-sources{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}.acq-sources label{display:flex;gap:7px;align-items:center;padding:9px;border:1px solid var(--border);border-radius:10px;background:var(--surface);font-weight:650;cursor:pointer}.acq-sources input{width:auto;min-height:auto}
    .acq-section{margin-top:12px;padding-top:12px;border-top:1px solid var(--border)}.acq-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}.acq-grid label{font-size:.82rem;font-weight:700;color:var(--muted)}.acq-grid input,.acq-grid select{width:100%;min-height:42px;margin-top:4px;padding:8px;border:1px solid #b9c6d5;border-radius:9px;background:var(--surface);color:var(--text)}.acq-actions{display:flex;gap:8px;margin:10px 0}.acq-status{margin:10px 0 0;padding:8px 10px;border-radius:9px;background:var(--surface);font-size:.88rem;color:var(--muted)}.acq-status[data-type="ok"]{background:#eaf7ee;color:#245b32}.acq-status[data-type="warn"]{background:#fff7e6;color:#7a5410}.acq-status[data-type="error"]{background:#fff0f1;color:#8a2632}.acq-section code{font-size:.78rem}
    @media(max-width:700px){.acq-sources{grid-template-columns:repeat(2,1fr)}.acq-grid{grid-template-columns:1fr}.acq-actions>*{flex:1}}
  `;
  document.head.appendChild(style);

  function init() {
    document.querySelectorAll('[data-experiment]').forEach(buildPanel);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();