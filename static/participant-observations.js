(() => {
  'use strict';

  const EXPERIMENTS = { queda: 'Queda Livre', pendulo: 'Pêndulo Simples', plano: 'Plano Inclinado' };
  const $ = (s, r = document) => r.querySelector(s);
  const groupId = () => new URLSearchParams(location.search).get('grupo_id') || '';
  const experimentKey = () => {
    const key = new URLSearchParams(location.search).get('experimento') || '';
    return EXPERIMENTS[key] ? key : '';
  };
  const csrf = () => $('[name="csrf_token"]')?.value || '';
  const esc = (s) => String(s ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));

  function participants() {
    const form = $('#grupoForm');
    if (!form) return [];
    return [1,2,3,4,5].map(i => {
      const input = form.querySelector(`[name="nome${i}"]`);
      const name = input?.value?.trim() || '';
      return name ? { codigo: `P${String(i).padStart(2,'0')}`, nome: name } : null;
    }).filter(Boolean);
  }

  function target() {
    const key = experimentKey();
    if (!key) return null;
    const cards = [...document.querySelectorAll('#experimentos .experiment')];
    return cards.find(card => {
      const action = card.querySelector('form[action]')?.getAttribute('action') || '';
      return (key === 'queda' && action === '/queda-livre') ||
             (key === 'pendulo' && action === '/pendulo') ||
             (key === 'plano' && action === '/plano');
    }) || cards[0] || null;
  }

  function speechAvailable() {
    return 'SpeechRecognition' in window || 'webkitSpeechRecognition' in window;
  }

  async function loadObservations(panel, key) {
    try {
      const r = await fetch(`/api/observacoes/${encodeURIComponent(key)}?grupo_id=${encodeURIComponent(groupId())}`, {
        credentials: 'same-origin', headers: { Accept: 'application/json' }
      });
      if (!r.ok) return;
      const data = await r.json();
      const byCode = Object.fromEntries((data.observacoes || []).map(o => [o.codigo, o]));
      panel.querySelectorAll('.participant-observation-row').forEach(row => {
        const o = byCode[row.dataset.codigo];
        if (o) {
          row.querySelector('textarea').value = o.observacao || '';
          row.querySelector('.observation-origin').textContent = o.origem === 'voz_transcrita' ? 'Registrada por voz e transcrita' : 'Registrada por escrito';
        }
      });
    } catch (_) {}
  }

  async function save(row, key) {
    const message = row.querySelector('.observation-status');
    const text = row.querySelector('textarea').value.trim();
    if (!text) {
      message.textContent = 'Digite ou dite uma observação antes de salvar.';
      return;
    }
    message.textContent = 'Salvando...';
    const body = new URLSearchParams({
      grupo_id: groupId(),
      codigo: row.dataset.codigo,
      observacao: text,
      origem: row.dataset.origem || 'escrita',
      csrf_token: csrf()
    });
    try {
      const r = await fetch(`/api/observacoes/${encodeURIComponent(key)}`, {
        method: 'POST', credentials: 'same-origin',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8', 'X-CSRF-Token': csrf(), Accept: 'application/json' },
        body
      });
      const data = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(data.erro || 'Não foi possível salvar.');
      message.textContent = '✓ Observação salva.';
      row.dataset.origem = data.observacao?.origem || row.dataset.origem || 'escrita';
      row.querySelector('.observation-origin').textContent = row.dataset.origem === 'voz_transcrita' ? 'Registrada por voz e transcrita' : 'Registrada por escrito';
    } catch (e) {
      message.textContent = e.message || 'Não foi possível salvar a observação.';
    }
  }

  function startSpeech(row) {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) return;
    const recognition = new Recognition();
    recognition.lang = 'pt-BR';
    recognition.interimResults = true;
    recognition.continuous = false;
    const button = row.querySelector('.observation-speech');
    const textarea = row.querySelector('textarea');
    const status = row.querySelector('.observation-status');
    const base = textarea.value.trim();
    let finalText = '';
    button.disabled = true;
    button.textContent = '🎙️ Ouvindo...';
    status.textContent = 'Fale a observação do participante.';
    recognition.onresult = event => {
      let interim = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const part = event.results[i][0].transcript;
        if (event.results[i].isFinal) finalText += part;
        else interim += part;
      }
      textarea.value = [base, finalText, interim].filter(Boolean).join(' ').trim();
      row.dataset.origem = 'voz_transcrita';
    };
    recognition.onerror = event => {
      status.textContent = `Não foi possível captar a fala (${event.error}).`;
    };
    recognition.onend = () => {
      button.disabled = false;
      button.textContent = '🎙️ Gravar descrição';
      if (finalText) status.textContent = 'Transcrição concluída. Revise o texto e salve.';
    };
    recognition.start();
  }

  function buildPanel(card, key) {
    if (!groupId() || !card || card.querySelector('.participant-observations')) return;
    const ps = participants();
    if (!ps.length) return;

    const panel = document.createElement('section');
    panel.className = 'participant-observations';
    panel.setAttribute('aria-labelledby', `observacoes-${key}`);
    panel.innerHTML = `
      <div class="observation-heading">
        <div><span class="observation-eyebrow">Registro inclusivo</span><h3 id="observacoes-${key}">📝 Observações do participante</h3></div>
        <p>Escreva ou use a voz para registrar a percepção do participante sobre o experimento.</p>
      </div>
      <div class="observation-list"></div>`;
    const list = $('.observation-list', panel);
    ps.forEach(p => {
      const row = document.createElement('div');
      row.className = 'participant-observation-row';
      row.dataset.codigo = p.codigo;
      row.dataset.origem = 'escrita';
      row.innerHTML = `
        <label><strong>${esc(p.codigo)} · ${esc(p.nome)}</strong></label>
        <textarea rows="4" maxlength="4000" aria-label="Observação de ${esc(p.nome)}" placeholder="Registre aqui a observação do participante..."></textarea>
        <div class="observation-actions">
          <button type="button" class="secondary observation-speech" ${speechAvailable() ? '' : 'hidden'}>🎙️ Gravar descrição</button>
          <button type="button" class="primary observation-save">Salvar observação</button>
        </div>
        <div class="observation-origin" aria-live="polite">Registrada por escrito</div>
        <div class="observation-status" role="status" aria-live="polite"></div>`;
      $('.observation-speech', row)?.addEventListener('click', () => startSpeech(row));
      $('.observation-save', row).addEventListener('click', () => save(row, key));
      list.appendChild(row);
    });

    const dataForm = card.querySelector('form[action]');
    if (dataForm) dataForm.insertAdjacentElement('afterend', panel);
    else card.appendChild(panel);
    loadObservations(panel, key);
  }

  function styles() {
    if ($('#participant-observation-styles')) return;
    const style = document.createElement('style');
    style.id = 'participant-observation-styles';
    style.textContent = `
      .participant-observations{margin-top:18px;padding:18px;border:1px solid #d9e3ec;border-radius:14px;background:#f8fbfd}
      .observation-heading{margin-bottom:14px}.observation-heading h3{margin:2px 0 4px;color:#173b59}.observation-heading p{margin:0;color:#536b80;font-size:.92rem}
      .observation-eyebrow{font-size:.72rem;text-transform:uppercase;letter-spacing:.08em;font-weight:700;color:#60758a}
      .observation-list{display:grid;gap:14px}.participant-observation-row{padding:14px;background:#fff;border:1px solid #d9e3ec;border-radius:10px}
      .participant-observation-row label{display:block;margin-bottom:7px;color:#173b59}.participant-observation-row textarea{width:100%;box-sizing:border-box;resize:vertical;border:1px solid #b9c9d7;border-radius:8px;padding:10px;font:inherit;line-height:1.45}
      .observation-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}.observation-actions button{min-height:40px}.observation-origin{margin-top:7px;font-size:.78rem;color:#60758a}.observation-status{margin-top:4px;font-size:.82rem;font-weight:600;min-height:1.2em;color:#31546f}
      @media(max-width:600px){.observation-actions{display:grid;grid-template-columns:1fr}.observation-actions button{width:100%}}
    `;
    document.head.appendChild(style);
  }

  function run() {
    const key = experimentKey();
    if (!key || !groupId()) return;
    const card = target();
    if (!card) return;
    styles();
    buildPanel(card, key);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true });
  else run();
})();
