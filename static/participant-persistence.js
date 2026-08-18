(() => {
  'use strict';

  const EXPERIMENTS = {
    queda: { title: 'Queda Livre', icon: '◉' },
    pendulo: { title: 'Pêndulo Simples', icon: '↻' },
    plano: { title: 'Plano Inclinado', icon: '▱' }
  };

  function participantInputs() {
    const form = document.getElementById('grupoForm');
    if (!form) return [];
    const inputs = [...form.querySelectorAll('input')];
    const found = [];
    for (let i = 1; i <= 5; i += 1) {
      let input = form.querySelector(`[name="nome${i}"]`);
      if (!input) input = inputs.find((candidate) => String(candidate.getAttribute('placeholder') || '').trim() === `Participante ${i}`);
      if (input) {
        input.name = `nome${i}`;
        found.push(input);
      }
    }
    return found;
  }

  function groupId() {
    return new URLSearchParams(window.location.search).get('grupo_id') || '';
  }

  function experimentKey() {
    const key = new URLSearchParams(window.location.search).get('experimento') || '';
    return Object.prototype.hasOwnProperty.call(EXPERIMENTS, key) ? key : '';
  }

  function experimentCards() {
    return [...document.querySelectorAll('#experimentos .experiment')];
  }

  function cardKey(card) {
    const form = card.querySelector('form[action]');
    if (!form) return '';
    const action = form.getAttribute('action') || '';
    if (action === '/queda-livre') return 'queda';
    if (action === '/pendulo') return 'pendulo';
    if (action === '/plano') return 'plano';
    return '';
  }

  function experimentUrl(key) {
    const params = new URLSearchParams();
    const id = groupId();
    if (id) params.set('grupo_id', id);
    params.set('experimento', key);
    return `/?${params.toString()}#experimentos`;
  }

  function addOpenButtons() {
    experimentCards().forEach((card) => {
      const key = cardKey(card);
      if (!key || card.dataset.experimentNavigationReady === 'true') return;

      const title = card.querySelector('h3');
      if (title) {
        title.setAttribute('role', 'link');
        title.setAttribute('tabindex', '0');
        title.setAttribute('aria-label', `Abrir experimento ${EXPERIMENTS[key].title}`);
        title.addEventListener('click', () => { window.location.href = experimentUrl(key); });
        title.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            window.location.href = experimentUrl(key);
          }
        });
      }

      const actions = card.querySelector('.actions');
      if (actions) {
        const button = document.createElement('a');
        button.className = 'secondary experiment-open';
        button.href = experimentUrl(key);
        button.textContent = 'Abrir experimento';
        actions.insertBefore(button, actions.firstChild);
      }
      card.dataset.experimentNavigationReady = 'true';
    });
  }

  function createWorkspaceHeader(key) {
    const section = document.getElementById('experimentos');
    if (!section || section.querySelector('.experiment-workspace-header')) return;
    const head = section.querySelector('.section-head');
    if (!head) return;

    const id = groupId();
    const backUrl = id ? `/?grupo_id=${encodeURIComponent(id)}#experimentos` : '/#experimentos';
    const header = document.createElement('div');
    header.className = 'experiment-workspace-header';
    header.innerHTML = `<a class="secondary" href="${backUrl}">← Voltar aos experimentos</a><div class="workspace-title"><span class="workspace-icon" aria-hidden="true">${EXPERIMENTS[key].icon}</span><div><div class="eyebrow">Laboratório individual</div><h2>${EXPERIMENTS[key].title}</h2><p>Registre as medições deste experimento sem outros laboratórios na tela.</p></div></div>`;
    head.replaceWith(header);
  }

  function addWorkspaceStyles() {
    if (document.getElementById('experiment-workspace-styles')) return;
    const style = document.createElement('style');
    style.id = 'experiment-workspace-styles';
    style.textContent = `
      .experiment h3[role="link"]{cursor:pointer}
      .experiment-workspace-header{display:flex;gap:16px;align-items:center;margin-bottom:14px;padding:4px 0}
      .experiment-workspace-header .secondary{flex:0 0 auto}
      .workspace-title{display:flex;gap:12px;align-items:center}
      .workspace-title h2{margin:2px 0 2px;font-size:1.55rem;color:#173b59}
      .workspace-title p{margin:0;color:#536b80;font-size:.9rem}
      .workspace-icon{display:grid;place-items:center;width:48px;height:48px;border-radius:12px;background:#1267b1;color:#fff;font-size:1.35rem;font-weight:900}
      #experimentos.experiment-focused .grid-3{grid-template-columns:minmax(0,1fr);max-width:900px;margin:0 auto}
      #experimentos.experiment-focused .experiment{width:100%}
      #experimentos.experiment-focused .experiment-open{display:none}
      #experimentos.experiment-focused .experiment{box-shadow:0 8px 28px rgba(28,67,101,.10)}
      @media(max-width:600px){.experiment-workspace-header{align-items:flex-start;flex-direction:column}.experiment-workspace-header .secondary{width:100%}.workspace-title{align-items:flex-start}.workspace-title h2{font-size:1.35rem}#experimentos.experiment-focused .grid-3{max-width:none}}
    `;
    document.head.appendChild(style);
  }

  function isolateExperimentView() {
    const key = experimentKey();
    const section = document.getElementById('experimentos');
    const cards = experimentCards();
    if (!section || !cards.length) return;
    addWorkspaceStyles();

    if (!key) {
      cards.forEach((card) => { card.hidden = false; });
      return;
    }

    section.classList.add('experiment-focused');
    cards.forEach((card) => { card.hidden = cardKey(card) !== key; });
    ['inicio', 'contexto', 'dados'].forEach((id) => {
      const element = document.getElementById(id);
      if (element) element.hidden = true;
    });
    const access = document.querySelector('.access');
    if (access) access.hidden = true;
    createWorkspaceHeader(key);
    requestAnimationFrame(() => section.scrollIntoView({ block: 'start', behavior: 'auto' }));
  }

  function prepareExistingGroupForm() {
    const id = groupId();
    const form = document.getElementById('grupoForm');
    if (!id || !form) return;

    let hidden = form.querySelector('[name="grupo_id"]');
    if (!hidden) {
      hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = 'grupo_id';
      form.appendChild(hidden);
    }
    hidden.value = id;
    form.action = '/salvar-participantes';

    const contextBlock = form.querySelector('.context-block');
    if (contextBlock) {
      contextBlock.style.display = 'none';
      contextBlock.querySelectorAll('input, select, textarea').forEach((field) => { field.disabled = true; });
    }
    const button = form.querySelector('button[type="submit"]');
    if (button) button.textContent = 'Salvar participantes';
    const actions = form.querySelector('.actions');
    if (actions) actions.style.marginTop = '0';

    const participantsBlock = document.querySelector('.participants')?.closest('.context-block');
    if (participantsBlock) {
      const note = participantsBlock.querySelector('.context-note');
      if (note) note.textContent = 'Os nomes ficam salvos no grupo e disponíveis para os integrantes autorizados.';
    }
  }

  async function loadParticipants() {
    const id = groupId();
    const inputs = participantInputs();
    if (!id || !inputs.length) return;
    try {
      const response = await fetch(`/api/grupo/${encodeURIComponent(id)}/participantes`, { credentials: 'same-origin', headers: { Accept: 'application/json' } });
      if (!response.ok) return;
      const data = await response.json();
      const participantes = Array.isArray(data.participantes) ? data.participantes : [];
      participantes.forEach((participante, index) => {
        if (inputs[index] && participante && participante.nome) inputs[index].value = participante.nome;
      });
    } catch (_) {
      // A página continua utilizável mesmo se a recuperação automática falhar.
    }
  }

  function run() {
    participantInputs();
    prepareExistingGroupForm();
    addOpenButtons();
    isolateExperimentView();
    loadParticipants();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true });
  else run();
})();
