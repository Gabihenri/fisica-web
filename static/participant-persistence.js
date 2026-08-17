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
        input = inputs.find((candidate) => {
          const placeholder = String(candidate.getAttribute('placeholder') || '').trim();
          return placeholder === `Participante ${i}`;
        });
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
        if (inputs[index] && participante && participante.nome) {
          inputs[index].value = participante.nome;
        }
      });
    } catch (_) {
      // A página continua utilizável mesmo se a recuperação automática falhar.
    }
  }

  function ensureNamesBeforeSubmit() {
    participantInputs();
  }

  function run() {
    const form = document.getElementById('grupoForm');
    participantInputs();
    if (form && !form.dataset.participantPersistenceBound) {
      form.addEventListener('submit', ensureNamesBeforeSubmit);
      form.dataset.participantPersistenceBound = 'true';
    }
    loadParticipants();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', run, { once: true });
  } else {
    run();
  }
})();
