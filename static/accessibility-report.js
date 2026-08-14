(() => {
  const synth = window.speechSynthesis;
  let utteranceAtual = null;
  let vozPreferida = null;
  let filaLeitura = [];
  let indiceFila = 0;
  let leituraCancelada = false;

  function grupoIdAtual() {
    return new URLSearchParams(window.location.search).get('grupo_id') || '';
  }

  function endpoint(chave) {
    const grupoId = grupoIdAtual();
    return `/api/relatorio-acessivel/${chave}${grupoId ? `?grupo_id=${encodeURIComponent(grupoId)}` : ''}`;
  }

  function pontuarVoz(voz) {
    const lang = String(voz.lang || '').toLowerCase();
    const nome = String(voz.name || '').toLowerCase();
    let pontos = 0;
    if (lang === 'pt-br') pontos += 100;
    else if (lang.startsWith('pt')) pontos += 60;
    if (voz.localService) pontos += 15;
    if (voz.default) pontos += 5;
    if (/enhanced|premium|natural|neural/.test(nome)) pontos += 25;
    if (/compact|espeak/.test(nome)) pontos -= 20;
    return pontos;
  }

  function selecionarVoz() {
    if (!synth) return null;
    const vozes = synth.getVoices() || [];
    if (!vozes.length) return null;
    vozPreferida = vozes
      .filter((voz) => String(voz.lang || '').toLowerCase().startsWith('pt'))
      .sort((a, b) => pontuarVoz(b) - pontuarVoz(a))[0] || null;
    return vozPreferida;
  }

  if (synth) {
    selecionarVoz();
    synth.addEventListener?.('voiceschanged', selecionarVoz);
    window.speechSynthesis.onvoiceschanged = selecionarVoz;
  }

  function humanizarTexto(texto) {
    return String(texto || '')
      .replace(/\bg\b/g, 'gê')
      .replace(/m\/s²|m\/s2/gi, 'metros por segundo ao quadrado')
      .replace(/m\/s/gi, 'metros por segundo')
      .replace(/R²/gi, 'R ao quadrado')
      .replace(/\s+/g, ' ')
      .trim();
  }

  function segmentarTexto(texto) {
    const limpo = humanizarTexto(texto);
    if (!limpo) return [];
    const sentencas = limpo.match(/[^.!?;:]+[.!?;:]?/g) || [limpo];
    const blocos = [];
    let atual = '';
    for (const sentenca of sentencas) {
      const trecho = sentenca.trim();
      if (!trecho) continue;
      if ((atual + ' ' + trecho).trim().length > 330 && atual) {
        blocos.push(atual.trim());
        atual = trecho;
      } else {
        atual = `${atual} ${trecho}`.trim();
      }
    }
    if (atual) blocos.push(atual.trim());
    return blocos;
  }

  function criarUtterance(texto, status) {
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = 'pt-BR';
    u.rate = 0.88;
    u.pitch = 1.02;
    u.volume = 1;
    const voz = vozPreferida || selecionarVoz();
    if (voz) u.voice = voz;
    u.onerror = () => {
      if (!leituraCancelada) status.textContent = 'Não foi possível concluir a leitura.';
    };
    return u;
  }

  function falarProximo(status) {
    if (leituraCancelada || indiceFila >= filaLeitura.length) {
      utteranceAtual = null;
      if (!leituraCancelada) status.textContent = 'Leitura concluída.';
      return;
    }

    const texto = filaLeitura[indiceFila++];
    utteranceAtual = criarUtterance(texto, status);
    utteranceAtual.onstart = () => { status.textContent = 'Lendo relatório com voz em português do Brasil.'; };
    utteranceAtual.onend = () => {
      if (!leituraCancelada) window.setTimeout(() => falarProximo(status), 180);
    };
    synth.speak(utteranceAtual);
  }

  function iniciarLeitura(texto, status) {
    synth.cancel();
    leituraCancelada = false;
    filaLeitura = segmentarTexto(texto);
    indiceFila = 0;
    if (!filaLeitura.length) {
      status.textContent = 'Não há conteúdo disponível para leitura.';
      return;
    }
    falarProximo(status);
  }

  function criarBotao(rotulo, acao, ariaLabel) {
    const botao = document.createElement('button');
    botao.type = 'button';
    botao.textContent = rotulo;
    botao.className = 'secondary';
    botao.setAttribute('aria-label', ariaLabel || rotulo);
    botao.addEventListener('click', acao);
    return botao;
  }

  async function ouvirRelatorio(chave, status) {
    if (!('speechSynthesis' in window)) {
      status.textContent = 'A síntese de voz não está disponível neste navegador.';
      return;
    }

    status.textContent = 'Preparando leitura natural do relatório...';
    try {
      const resposta = await fetch(endpoint(chave), { headers: { Accept: 'application/json' } });
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
      const relatorio = await resposta.json();
      const texto = relatorio.texto_completo || 'Não há conteúdo disponível para leitura.';
      iniciarLeitura(texto, status);
    } catch (erro) {
      status.textContent = 'Não foi possível carregar o relatório acessível.';
      console.error('Física Web — relatório acessível:', erro);
    }
  }

  function montarControles(container, chave, titulo) {
    if (container.querySelector('.accessible-report-controls')) return;

    const bloco = document.createElement('div');
    bloco.className = 'accessible-report-controls';
    bloco.style.marginTop = '12px';
    bloco.style.paddingTop = '12px';
    bloco.style.borderTop = '1px solid var(--border, currentColor)';

    const rotulo = document.createElement('strong');
    rotulo.textContent = 'Relatório acessível em áudio';
    bloco.appendChild(rotulo);

    const botoes = document.createElement('div');
    botoes.className = 'actions';
    botoes.style.marginTop = '8px';

    const status = document.createElement('span');
    status.setAttribute('role', 'status');
    status.setAttribute('aria-live', 'polite');
    status.style.display = 'block';
    status.style.marginTop = '8px';

    botoes.appendChild(criarBotao('▶ Ouvir', () => ouvirRelatorio(chave, status), `Ouvir relatório acessível de ${titulo}`));
    botoes.appendChild(criarBotao('⏸ Pausar', () => {
      if (synth.speaking && !synth.paused) {
        synth.pause();
        status.textContent = 'Leitura pausada.';
      }
    }, `Pausar relatório de ${titulo}`));
    botoes.appendChild(criarBotao('⏯ Continuar', () => {
      if (synth.paused) {
        synth.resume();
        status.textContent = 'Leitura retomada.';
      }
    }, `Continuar relatório de ${titulo}`));
    botoes.appendChild(criarBotao('⏹ Parar', () => {
      leituraCancelada = true;
      synth.cancel();
      utteranceAtual = null;
      filaLeitura = [];
      indiceFila = 0;
      status.textContent = 'Leitura encerrada.';
    }, `Parar relatório de ${titulo}`));

    bloco.appendChild(botoes);
    bloco.appendChild(status);
    container.appendChild(bloco);
  }

  function inicializar() {
    document.querySelectorAll('[data-experiment]').forEach((container) => {
      const chave = container.dataset.experiment;
      const titulo = container.dataset.title || container.querySelector('h3')?.textContent || 'experimento';
      if (chave) montarControles(container, chave, titulo);
    });
  }

  function carregarCamadaExperimental() {
    if (document.querySelector('script[data-experiment-focus]')) return;
    const script = document.createElement('script');
    script.src = '/static/experiment-focus.js';
    script.defer = true;
    script.dataset.experimentFocus = 'true';
    document.body.appendChild(script);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      inicializar();
      carregarCamadaExperimental();
    });
  } else {
    inicializar();
    carregarCamadaExperimental();
  }

  document.addEventListener('fisicaweb:experiment-updated', inicializar);
})();
