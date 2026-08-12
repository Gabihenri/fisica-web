(() => {
  const synth = window.speechSynthesis;
  let utteranceAtual = null;

  function grupoIdAtual() {
    return new URLSearchParams(window.location.search).get('grupo_id') || '';
  }

  function endpoint(chave) {
    const grupoId = grupoIdAtual();
    return `/api/relatorio-acessivel/${chave}${grupoId ? `?grupo_id=${encodeURIComponent(grupoId)}` : ''}`;
  }

  function criarBotao(rotulo, acao, ariaLabel) {
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.textContent = rotulo;
    botao.setAttribute('aria-label', ariaLabel || rotulo);
    botao.addEventListener('click', acao);
    return botao;
  }

  async function ouvirRelatorio(chave, status) {
    if (!('speechSynthesis' in window)) {
      status.textContent = 'A síntese de voz não está disponível neste navegador.';
      return;
    }

    status.textContent = 'Preparando relatório acessível...';
    try {
      const resposta = await fetch(endpoint(chave), { headers: { Accept: 'application/json' } });
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
      const relatorio = await resposta.json();
      const texto = relatorio.texto_completo || 'Não há conteúdo disponível para leitura.';

      synth.cancel();
      utteranceAtual = new SpeechSynthesisUtterance(texto);
      utteranceAtual.lang = 'pt-BR';
      utteranceAtual.rate = 0.95;
      utteranceAtual.onstart = () => { status.textContent = 'Lendo relatório acessível.'; };
      utteranceAtual.onend = () => { status.textContent = 'Leitura concluída.'; };
      utteranceAtual.onerror = () => { status.textContent = 'Não foi possível concluir a leitura.'; };
      synth.speak(utteranceAtual);
    } catch (erro) {
      status.textContent = 'Não foi possível carregar o relatório acessível.';
      console.error('Física Web — relatório acessível:', erro);
    }
  }

  function montarControles(secao, chave, titulo) {
    if (secao.querySelector('.accessible-report-controls')) return;

    const bloco = document.createElement('div');
    bloco.className = 'accessible-report-controls';
    bloco.style.marginTop = '12px';
    bloco.style.padding = '10px';
    bloco.style.border = '1px solid currentColor';
    bloco.style.borderRadius = '8px';

    const rotulo = document.createElement('strong');
    rotulo.textContent = 'Relatório acessível em áudio';
    bloco.appendChild(rotulo);
    bloco.appendChild(document.createElement('br'));

    const status = document.createElement('span');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    status.style.display = 'block';
    status.style.marginTop = '8px';

    bloco.appendChild(criarBotao('▶ Ouvir', () => ouvirRelatorio(chave, status), `Ouvir relatório acessível de ${titulo}`));
    bloco.appendChild(criarBotao('⏸ Pausar', () => {
      if (synth.speaking && !synth.paused) {
        synth.pause();
        status.textContent = 'Leitura pausada.';
      }
    }, `Pausar relatório de ${titulo}`));
    bloco.appendChild(criarBotao('⏯ Continuar', () => {
      if (synth.paused) {
        synth.resume();
        status.textContent = 'Leitura retomada.';
      }
    }, `Continuar relatório de ${titulo}`));
    bloco.appendChild(criarBotao('⏹ Parar', () => {
      synth.cancel();
      utteranceAtual = null;
      status.textContent = 'Leitura encerrada.';
    }, `Parar relatório de ${titulo}`));

    bloco.appendChild(status);
    secao.appendChild(bloco);
  }

  function inicializar() {
    const experimentos = [
      { chave: 'queda', titulo: 'Queda Livre' },
      { chave: 'pendulo', titulo: 'Pêndulo Simples' },
      { chave: 'plano', titulo: 'Plano Inclinado' },
    ];

    document.querySelectorAll('section').forEach((secao) => {
      const titulo = secao.querySelector('h2')?.textContent || '';
      const experimento = experimentos.find((item) => titulo.includes(item.titulo));
      if (experimento) montarControles(secao, experimento.chave, experimento.titulo);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inicializar);
  } else {
    inicializar();
  }
})();
