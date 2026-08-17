(() => {
  'use strict';

  const synth = 'speechSynthesis' in window ? window.speechSynthesis : null;
  const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition || null;
  let voiceEnabled = false;
  let guidedMode = false;
  let recognition = null;
  let speaking = false;
  let currentQueue = [];
  let currentIndex = 0;
  let preferredVoice = null;

  const labels = new WeakMap();

  const css = `
    .fw-a11y-launcher{position:fixed;right:16px;bottom:18px;z-index:2147483000;display:flex;gap:8px;align-items:center}
    .fw-a11y-button,.fw-a11y-panel button{font:inherit;font-weight:800;border:2px solid #fff;border-radius:12px;padding:11px 14px;background:#073b82;color:#fff;box-shadow:0 6px 20px rgba(0,0,0,.28);cursor:pointer}
    .fw-a11y-button:focus-visible,.fw-a11y-panel button:focus-visible,.fw-a11y-panel a:focus-visible{outline:4px solid #ffd54a;outline-offset:3px}
    .fw-a11y-panel{position:fixed;right:16px;bottom:78px;z-index:2147482999;width:min(430px,calc(100vw - 24px));max-height:min(78vh,720px);overflow:auto;background:#071b36;color:#fff;border:2px solid #74c7ff;border-radius:18px;padding:18px;box-shadow:0 18px 50px rgba(0,0,0,.45)}
    .fw-a11y-panel[hidden]{display:none!important}
    .fw-a11y-panel h2{margin:0 0 8px;font-size:1.25rem}
    .fw-a11y-panel p{margin:7px 0;line-height:1.5;color:#e7f2ff}
    .fw-a11y-status{padding:10px;border-radius:10px;background:#0d315d;border:1px solid #397db4;margin:10px 0;font-weight:700}
    .fw-a11y-actions{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:12px 0}
    .fw-a11y-actions button{min-height:46px}
    .fw-a11y-actions .primary{background:#0b73e8}
    .fw-a11y-actions .danger{background:#702333}
    .fw-a11y-help{border-top:1px solid #397db4;margin-top:14px;padding-top:12px}
    .fw-a11y-help ul{margin:7px 0;padding-left:22px;line-height:1.6}
    .fw-a11y-command{font-weight:800;color:#9de7ff}
    .fw-a11y-hidden-live{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
    body.fw-voice-guided :focus-visible{outline:4px solid #ffd54a!important;outline-offset:3px!important}
    @media(max-width:600px){.fw-a11y-launcher{right:10px;bottom:76px}.fw-a11y-panel{right:10px;bottom:132px}.fw-a11y-actions{grid-template-columns:1fr}}
  `;

  function addStyle() {
    if (document.getElementById('fw-a11y-style')) return;
    const style = document.createElement('style');
    style.id = 'fw-a11y-style';
    style.textContent = css;
    document.head.appendChild(style);
  }

  function chooseVoice() {
    if (!synth) return null;
    const voices = synth.getVoices() || [];
    const pt = voices.filter(v => /^pt(?:-BR)?/i.test(String(v.lang || '')));
    const score = voice => {
      const name = String(voice.name || '').toLowerCase();
      let value = 0;
      if (/pt-br/i.test(voice.lang || '')) value += 100;
      if (voice.localService) value += 20;
      if (voice.default) value += 5;
      if (/natural|neural|enhanced|premium|luciana|francisca|joana/i.test(name)) value += 30;
      return value;
    };
    preferredVoice = [...pt].sort((a, b) => score(b) - score(a))[0] || voices.find(v => /^pt/i.test(v.lang || '')) || null;
    return preferredVoice;
  }

  function speak(text, options = {}) {
    if (!synth || !text) return false;
    const clean = humanize(text);
    if (!clean) return false;
    synth.cancel();
    const utterance = new SpeechSynthesisUtterance(clean);
    utterance.lang = 'pt-BR';
    utterance.rate = options.rate || 0.9;
    utterance.pitch = 1;
    utterance.volume = 1;
    const voice = preferredVoice || chooseVoice();
    if (voice) utterance.voice = voice;
    utterance.onstart = () => { speaking = true; setStatus('Orientação falada ativa.'); };
    utterance.onend = () => { speaking = false; if (options.onend) options.onend(); };
    utterance.onerror = () => { speaking = false; setStatus('A leitura de voz encontrou um problema. O leitor de tela do dispositivo continua disponível.'); };
    synth.speak(utterance);
    return true;
  }

  function humanize(text) {
    return String(text || '')
      .replace(/\s+/g, ' ')
      .replace(/m\/s²|m\/s2/gi, 'metros por segundo ao quadrado')
      .replace(/m\/s/gi, 'metros por segundo')
      .replace(/cm²/gi, 'centímetros quadrados')
      .replace(/R²/gi, 'R ao quadrado')
      .replace(/²/g, ' ao quadrado')
      .replace(/³/g, ' ao cubo')
      .replace(/→/g, ' depois ')
      .trim();
  }

  function chunks(text, size = 360) {
    const clean = humanize(text);
    if (!clean) return [];
    const sentences = clean.match(/[^.!?;:]+[.!?;:]?/g) || [clean];
    const result = [];
    let buffer = '';
    sentences.forEach(sentence => {
      const piece = sentence.trim();
      if (!piece) return;
      if (buffer && (buffer + ' ' + piece).length > size) {
        result.push(buffer);
        buffer = piece;
      } else {
        buffer = (buffer + ' ' + piece).trim();
      }
    });
    if (buffer) result.push(buffer);
    return result;
  }

  function speakQueue(text) {
    if (!synth) return;
    synth.cancel();
    currentQueue = chunks(text);
    currentIndex = 0;
    voiceEnabled = true;
    playNext();
  }

  function playNext() {
    if (!voiceEnabled || !currentQueue.length || currentIndex >= currentQueue.length) {
      speaking = false;
      setStatus(currentQueue.length ? 'Leitura concluída.' : 'Não há conteúdo acessível para leitura nesta tela.');
      return;
    }
    const text = currentQueue[currentIndex++];
    speak(text, { onend: () => window.setTimeout(playNext, 120) });
  }

  function stopSpeech(message = 'Leitura interrompida.') {
    voiceEnabled = false;
    currentQueue = [];
    currentIndex = 0;
    if (synth) synth.cancel();
    speaking = false;
    setStatus(message);
  }

  function pauseSpeech() {
    if (!synth) return;
    if (synth.speaking && !synth.paused) {
      synth.pause();
      setStatus('Leitura pausada.');
    }
  }

  function resumeSpeech() {
    if (!synth) return;
    if (synth.paused) {
      synth.resume();
      setStatus('Leitura retomada.');
    }
  }

  function visibleText(root = document.body) {
    const clone = root.cloneNode(true);
    clone.querySelectorAll('script,style,noscript,[aria-hidden="true"],.fw-a11y-launcher,.fw-a11y-panel,.fw-a11y-hidden-live').forEach(el => el.remove());
    return humanize(clone.innerText || clone.textContent || '');
  }

  function pageSummary() {
    const title = document.title || 'Física Web';
    const headings = [...document.querySelectorAll('h1,h2,h3')].filter(isVisible).map(el => humanize(el.innerText)).filter(Boolean).slice(0, 14);
    const nav = [...document.querySelectorAll('nav a,[role="navigation"] a')].filter(isVisible).map(el => accessibleName(el)).filter(Boolean).slice(0, 12);
    const buttons = [...document.querySelectorAll('button,a,input,select,textarea')].filter(isVisible).map(el => accessibleName(el)).filter(Boolean).slice(0, 18);
    let text = `Física Web. ${title}. `;
    if (headings.length) text += `Seções disponíveis: ${headings.join(', ')}. `;
    if (nav.length) text += `Navegação: ${nav.join(', ')}. `;
    if (buttons.length) text += `Controles principais: ${buttons.join(', ')}.`;
    return text;
  }

  function currentContext() {
    const focused = document.activeElement;
    if (focused && focused !== document.body && isVisible(focused)) {
      return `Você está em ${accessibleName(focused)}.`;
    }
    const section = [...document.querySelectorAll('main section,section,article')].find(el => {
      if (!isVisible(el)) return false;
      const rect = el.getBoundingClientRect();
      return rect.top <= window.innerHeight * 0.45 && rect.bottom >= window.innerHeight * 0.25;
    });
    if (section) {
      const heading = section.querySelector('h1,h2,h3');
      if (heading) return `Você está na seção ${humanize(heading.innerText)}.`;
    }
    return 'Você está na página atual do Física Web.';
  }

  function experimentDescription(container) {
    if (!container) return '';
    const title = container.dataset.title || container.querySelector('h2,h3,h1')?.innerText || 'experimento';
    const objective = container.querySelector('[data-accessibility-objective]')?.innerText || container.querySelector('.experiment-description,p')?.innerText || '';
    const fields = [...container.querySelectorAll('input:not([type="hidden"]),select,textarea')].map(field => {
      const label = document.querySelector(`label[for="${CSS.escape(field.id || '')}"]`)?.innerText || field.getAttribute('aria-label') || field.name || 'campo';
      const value = field.value ? ` Valor atual: ${field.value}.` : '';
      return `${label}.${value}`;
    }).slice(0, 12);
    const controls = [...container.querySelectorAll('button,a')].filter(isVisible).map(accessibleName).filter(Boolean).slice(0, 14);
    let text = `Experimento ${humanize(title)}. `;
    if (objective) text += `Descrição: ${humanize(objective)} `;
    if (fields.length) text += `Campos de entrada: ${fields.join(' ')} `;
    if (controls.length) text += `Controles: ${controls.join(', ')}.`;
    return text;
  }

  function findExperiment() {
    const focused = document.activeElement?.closest?.('[data-experiment]');
    if (focused) return focused;
    const active = document.querySelector('.experiment-active[data-experiment], [data-experiment]:not([hidden])');
    return active || null;
  }

  function accessibleName(el) {
    if (!el) return '';
    const aria = el.getAttribute('aria-label') || el.getAttribute('title');
    if (aria) return humanize(aria);
    const labelled = el.getAttribute('aria-labelledby');
    if (labelled) {
      const text = labelled.split(/\s+/).map(id => document.getElementById(id)?.innerText || '').join(' ');
      if (text.trim()) return humanize(text);
    }
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT') {
      const label = el.id ? document.querySelector(`label[for="${CSS.escape(el.id)}"]`) : el.closest('label');
      if (label) return humanize(label.innerText);
      if (el.placeholder) return humanize(el.placeholder);
    }
    const text = el.innerText || el.textContent || '';
    return humanize(text).slice(0, 180);
  }

  function isVisible(el) {
    if (!el || el.hidden) return false;
    const style = window.getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }

  function setStatus(text) {
    const status = document.getElementById('fw-a11y-status');
    if (status) status.textContent = text;
    const live = document.getElementById('fw-a11y-live');
    if (live) live.textContent = text;
  }

  function labelControls() {
    document.querySelectorAll('button,a,input,select,textarea').forEach(el => {
      if (!isVisible(el)) return;
      const name = accessibleName(el);
      if (name && !el.getAttribute('aria-label') && (el.tagName === 'BUTTON' || el.tagName === 'INPUT' || el.tagName === 'SELECT' || el.tagName === 'TEXTAREA')) {
        el.setAttribute('aria-label', name);
      }
      if (el.tagName === 'A' && !el.getAttribute('aria-label') && !el.innerText.trim()) {
        el.setAttribute('aria-label', el.getAttribute('href') || 'Link');
      }
    });
  }

  function improveImages() {
    document.querySelectorAll('img').forEach(img => {
      if (!img.hasAttribute('alt')) img.alt = '';
      if (img.alt === '' && img.closest('button,a')) {
        const parentName = accessibleName(img.closest('button,a'));
        if (parentName) img.alt = parentName;
      }
    });
  }

  function announceFocus() {
    document.addEventListener('focusin', event => {
      if (!guidedMode) return;
      const name = accessibleName(event.target);
      if (!name) return;
      setStatus(`Foco em ${name}.`);
      speak(`Foco em ${name}.`, { rate: 0.92 });
    });
  }

  function navigateTo(selector, spoken) {
    const target = document.querySelector(selector);
    if (!target) {
      speak(`Não encontrei ${spoken}.`);
      return false;
    }
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const focusTarget = target.matches('section,main,article') ? target.querySelector('h1,h2,h3,a,button,input') : target;
    if (focusTarget && !focusTarget.hasAttribute('tabindex')) focusTarget.setAttribute('tabindex', '-1');
    window.setTimeout(() => focusTarget?.focus?.({ preventScroll: true }), 400);
    speak(`Abrindo ${spoken}.`);
    return true;
  }

  function nextInteractive() {
    const items = [...document.querySelectorAll('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])')].filter(isVisible);
    const index = items.indexOf(document.activeElement);
    const next = items[index + 1] || items[0];
    next?.focus();
    if (next) speak(`Próximo controle: ${accessibleName(next)}.`);
  }

  function previousInteractive() {
    const items = [...document.querySelectorAll('a,button,input,select,textarea,[tabindex]:not([tabindex="-1"])')].filter(isVisible);
    const index = items.indexOf(document.activeElement);
    const previous = items[index - 1] || items[items.length - 1];
    previous?.focus();
    if (previous) speak(`Controle anterior: ${accessibleName(previous)}.`);
  }

  function startRecognition() {
    if (!Recognition) {
      setStatus('Reconhecimento de voz não está disponível neste navegador. Use VoiceOver ou TalkBack e a navegação por teclado/toque.');
      speak('O reconhecimento de voz não está disponível neste navegador. O leitor de tela do dispositivo continua compatível com a página.');
      return false;
    }
    if (recognition) {
      try { recognition.stop(); } catch (_) {}
    }
    recognition = new Recognition();
    recognition.lang = 'pt-BR';
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.maxAlternatives = 3;
    recognition.onstart = () => {
      setStatus('Comandos de voz ativos. Diga ajuda para conhecer os comandos.');
    };
    recognition.onresult = event => {
      const result = event.results[event.results.length - 1];
      const transcript = String(result[0]?.transcript || '').toLowerCase().trim();
      if (transcript) executeCommand(transcript);
    };
    recognition.onerror = event => {
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        setStatus('O navegador não autorizou o microfone. Ative o microfone nas permissões do navegador.');
      }
    };
    recognition.onend = () => {
      if (voiceEnabled && guidedMode) {
        window.setTimeout(() => { try { recognition.start(); } catch (_) {} }, 500);
      }
    };
    try { recognition.start(); return true; } catch (_) { return false; }
  }

  function stopRecognition() {
    if (recognition) {
      try { recognition.stop(); } catch (_) {}
      recognition = null;
    }
  }

  function executeCommand(command) {
    const c = command.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    if (/^(ajuda|comandos|o que posso dizer)/.test(c)) {
      speak('Comandos disponíveis: dizer início, laboratórios, dados, meus grupos, laboratório móvel, ler tela, ler experimento, onde estou, próximo, voltar, repetir, pausar, continuar ou parar.');
      return;
    }
    if (/^(parar|silencio|silêncio|cancelar)/.test(c)) { stopSpeech(); return; }
    if (/^(pausar|pausa)/.test(c)) { pauseSpeech(); return; }
    if (/^(continuar|retomar)/.test(c)) { resumeSpeech(); return; }
    if (/onde estou|minha localizacao|minha localização/.test(c)) { speak(currentContext()); return; }
    if (/ler tela|leia tela|ler pagina|ler página|descrever tela|audiodescricao|audiodescrição/.test(c)) { speakQueue(pageSummary()); return; }
    if (/ler experimento|descrever experimento|como fazer experimento|orientacao do experimento|orientação do experimento/.test(c)) {
      const exp = findExperiment();
      speakQueue(exp ? experimentDescription(exp) : 'Não encontrei um experimento ativo nesta tela.');
      return;
    }
    if (/^inicio$|^início$|pagina inicial|página inicial/.test(c)) { navigateTo('#inicio', 'o início'); return; }
    if (/laboratorios|laboratórios|experimentos/.test(c)) { navigateTo('#experimentos', 'os laboratórios'); return; }
    if (/^dados$|resultados|analise|análise/.test(c)) { navigateTo('#dados', 'os dados e resultados'); return; }
    if (/meus grupos|grupos/.test(c)) { const link = [...document.querySelectorAll('a')].find(a => /meus grupos/i.test(a.innerText)); if (link) { link.click(); speak('Abrindo meus grupos.'); } else speak('Não encontrei o acesso a meus grupos.'); return; }
    if (/laboratorio movel|laboratório móvel/.test(c)) { const link = [...document.querySelectorAll('a')].find(a => /laboratório móvel/i.test(a.innerText)); if (link) { link.click(); speak('Abrindo laboratório móvel.'); } else speak('Não encontrei o laboratório móvel.'); return; }
    if (/proximo|próximo/.test(c)) { nextInteractive(); return; }
    if (/voltar|anterior/.test(c)) { previousInteractive(); return; }
    if (/repetir/.test(c)) { if (currentQueue.length) { currentIndex = Math.max(0, currentIndex - 1); playNext(); } else speak(currentContext()); return; }
    speak('Não reconheci esse comando. Diga ajuda para ouvir os comandos disponíveis.');
  }

  function buildUI() {
    if (document.getElementById('fw-a11y-launcher')) return;

    const live = document.createElement('div');
    live.id = 'fw-a11y-live';
    live.className = 'fw-a11y-hidden-live';
    live.setAttribute('aria-live', 'polite');
    live.setAttribute('aria-atomic', 'true');
    document.body.appendChild(live);

    const launcher = document.createElement('div');
    launcher.id = 'fw-a11y-launcher';
    launcher.className = 'fw-a11y-launcher';

    const open = document.createElement('button');
    open.type = 'button';
    open.id = 'fw-a11y-open';
    open.className = 'fw-a11y-button';
    open.textContent = 'Acessibilidade e voz';
    open.setAttribute('aria-haspopup', 'dialog');
    open.setAttribute('aria-controls', 'fw-a11y-panel');
    launcher.appendChild(open);
    document.body.appendChild(launcher);

    const panel = document.createElement('section');
    panel.id = 'fw-a11y-panel';
    panel.className = 'fw-a11y-panel';
    panel.hidden = true;
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-modal', 'false');
    panel.setAttribute('aria-labelledby', 'fw-a11y-title');
    panel.innerHTML = `
      <h2 id="fw-a11y-title">Acessibilidade do Física Web</h2>
      <p>Use esta camada para ouvir a tela, receber orientação dos experimentos e, quando o navegador permitir, navegar por comandos de voz.</p>
      <div id="fw-a11y-status" class="fw-a11y-status" role="status" aria-live="polite">Recursos de voz prontos.</div>
      <div class="fw-a11y-actions">
        <button type="button" class="primary" data-action="read-page">Ler esta tela</button>
        <button type="button" data-action="read-experiment">Orientação do experimento</button>
        <button type="button" data-action="where">Onde estou?</button>
        <button type="button" data-action="guided">Ativar orientação falada</button>
        <button type="button" data-action="voice-command">Ativar comandos de voz</button>
        <button type="button" data-action="pause">Pausar</button>
        <button type="button" data-action="resume">Continuar</button>
        <button type="button" class="danger" data-action="stop">Parar voz</button>
      </div>
      <div class="fw-a11y-help">
        <strong>Comandos de voz</strong>
        <p>Diga <span class="fw-a11y-command">“ajuda”</span> para ouvir a lista completa.</p>
        <ul>
          <li>“Ler tela”</li>
          <li>“Ler experimento”</li>
          <li>“Onde estou?”</li>
          <li>“Próximo” e “voltar”</li>
          <li>“Início”, “laboratórios” e “dados”</li>
          <li>“Repetir”, “pausar”, “continuar” e “parar”</li>
        </ul>
        <p><strong>Compatibilidade:</strong> o Física Web continua utilizando a semântica HTML e é compatível com leitores de tela do dispositivo, como VoiceOver e TalkBack. O comando de voz depende do suporte do navegador e da permissão do microfone.</p>
      </div>`;
    document.body.appendChild(panel);

    open.addEventListener('click', () => {
      panel.hidden = !panel.hidden;
      if (!panel.hidden) panel.querySelector('button')?.focus();
    });

    panel.addEventListener('click', event => {
      const action = event.target.closest('[data-action]')?.dataset.action;
      if (!action) return;
      if (action === 'read-page') speakQueue(pageSummary());
      if (action === 'read-experiment') {
        const exp = findExperiment();
        speakQueue(exp ? experimentDescription(exp) : 'Não encontrei um experimento ativo nesta tela.');
      }
      if (action === 'where') speak(currentContext());
      if (action === 'pause') pauseSpeech();
      if (action === 'resume') resumeSpeech();
      if (action === 'stop') { stopSpeech(); stopRecognition(); guidedMode = false; document.body.classList.remove('fw-voice-guided'); }
      if (action === 'guided') {
        guidedMode = !guidedMode;
        document.body.classList.toggle('fw-voice-guided', guidedMode);
        event.target.textContent = guidedMode ? 'Desativar orientação falada' : 'Ativar orientação falada';
        if (guidedMode) speak('Orientação falada ativada. Ao navegar pelos controles, vou informar onde você está.');
        else speak('Orientação falada desativada.');
      }
      if (action === 'voice-command') {
        if (!Recognition) {
          speak('O reconhecimento de voz não é suportado neste navegador. Use o leitor de tela do dispositivo.');
          return;
        }
        voiceEnabled = true;
        guidedMode = true;
        document.body.classList.add('fw-voice-guided');
        startRecognition();
        speak('Comandos de voz ativados. Diga ajuda para conhecer os comandos.');
      }
    });
  }

  function init() {
    addStyle();
    chooseVoice();
    if (synth) synth.addEventListener?.('voiceschanged', chooseVoice);
    labelControls();
    improveImages();
    buildUI();
    announceFocus();

    const observer = new MutationObserver(() => {
      labelControls();
      improveImages();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    document.addEventListener('visibilitychange', () => {
      if (document.hidden && synth) synth.cancel();
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
