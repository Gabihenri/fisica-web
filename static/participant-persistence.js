(() => {
  'use strict';

  function participantInputs() {
    const form = document.getElementById('grupoForm');
    if (!form) return [];

    const inputs = [...form.querySelectorAll('input')];
    const found = [];
    for (let i = 1; i <= 5; i += 1) {
      let input = form.querySelector(`[name="nome${i}"]`);
      if (!input) {
        input = inputs.find((candidate) => String(candidate.getAttribute('placeholder') || '').trim() === `Participante ${i}`);
      }
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

    // O grupo já existe: não pedir novamente escola, turma, série etc.
    form.action = '/salvar-participantes';
    const contextBlock = form.querySelector('.context-block');
    if (contextBlock) {
      contextBlock.style.display = 'none';
      contextBlock.querySelectorAll('input, select, textarea').forEach((field) => {
        field.disabled = true;
      });
    }

    const button = form.querySelector('button[type="submit"]');
    if (button) button.textContent = 'Salvar participantes';

    const actions = form.querySelector('.actions');
    if (actions) actions.style.marginTop = '0';

    const participantsBlock = document.querySelector('.participants')?.closest('.context-block');
    if (participantsBlock) {
      const note = participantsBlock.querySelector('.context-note');
      if (note) note.textContent = 'Os nomes ficam salvos no grupo e disponíveis para todos os integrantes.';
    }
  }

  async function loadParticipants() {
    const id = groupId();
    const inputs = participantInputs();
    if (!id || !inputs.length) return;

    try {
      const response = await fetch(`/api/grupo/${encodeURIComponent(id)}/participantes`, {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' }
      });
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
    loadParticipants();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true });
  else run();
})();
