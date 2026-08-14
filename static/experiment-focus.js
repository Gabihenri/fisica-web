(() => {
  const params = new URLSearchParams(window.location.search);
  const grupoId = params.get('grupo_id') || '';
  const foco = params.get('experimento') || '';
  const artigos = [...document.querySelectorAll('[data-experiment]')];
  const validos = new Set(artigos.map((a) => a.dataset.experiment));

  function urlFoco(chave) {
    const q = new URLSearchParams();
    if (grupoId) q.set('grupo_id', grupoId);
    q.set('experimento', chave);
    return `/?${q.toString()}#experimentos`;
  }

  function urlCatalogo() {
    return grupoId ? `/?grupo_id=${encodeURIComponent(grupoId)}#experimentos` : '/#experimentos';
  }

  function ocultar(el) {
    if (!el) return;
    el.hidden = true;
    el.style.setProperty('display', 'none', 'important');
  }

  function mostrar(el) {
    if (!el) return;
    el.hidden = false;
    el.style.removeProperty('display');
  }

  function escolherVozPtBR() {
    if (!('speechSynthesis' in window)) return null;
    const vozes = window.speechSynthesis.getVoices();
    const pt = vozes.filter(v => String(v.lang || '').toLowerCase().startsWith('pt-br'));
    const preferidas = ['premium', 'enhanced', 'natural', 'luciana', 'joana', 'francisca'];
    return pt.find(v => preferidas.some(p => String(v.name || '').toLowerCase().includes(p))) || pt[0] || vozes.find(v => String(v.lang || '').toLowerCase().startsWith('pt')) || null;
  }

  function falarConfirmacao(texto) {
    if (!('speechSynthesis' in window)) return false;
    const synth = window.speechSynthesis;
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = 'pt-BR';
    u.rate = 0.9;
    u.pitch = 1.02;
    const voz = escolherVozPtBR();
    if (voz) u.voice = voz;
    synth.cancel();
    synth.speak(u);
    return true;
  }

  function configurarControlesGlobais() {
    const botaoAudio = document.getElementById('toggle-voice');
    const painelAcessibilidade = document.getElementById('acessibilidade');
    const botaoAcessibilidade = [...document.querySelectorAll('button')].find(b => /acessibilidade/i.test(b.textContent || ''));

    if (botaoAudio && botaoAudio.dataset.fwControl !== '1') {
      botaoAudio.dataset.fwControl = '1';
      let ativo = false;
      botaoAudio.setAttribute('aria-pressed', 'false');
      botaoAudio.addEventListener('click', () => {
        ativo = !ativo;
        botaoAudio.setAttribute('aria-pressed', ativo ? 'true' : 'false');
        botaoAudio.innerHTML = ativo ? '🔊 Áudio ligado' : '🔇 Áudio desligado';
        if (ativo) {
          if (!falarConfirmacao('Áudio ativado. Os recursos de leitura estão disponíveis.')) {
            botaoAudio.title = 'Síntese de voz não disponível neste navegador.';
          }
        } else if ('speechSynthesis' in window) {
          window.speechSynthesis.cancel();
        }
      });
    }

    if (botaoAcessibilidade && painelAcessibilidade && botaoAcessibilidade.dataset.fwControl !== '1') {
      botaoAcessibilidade.dataset.fwControl = '1';
      botaoAcessibilidade.addEventListener('click', (evento) => {
        evento.preventDefault();
        mostrar(painelAcessibilidade);
        painelAcessibilidade.open = true;
        painelAcessibilidade.scrollIntoView({ behavior: 'smooth', block: 'start' });
        window.setTimeout(() => painelAcessibilidade.querySelector('summary')?.focus(), 350);
      });
    }
  }

  function esconderConteudoCatalogo(artigo) {
    artigo.querySelectorAll('form,.actions,.table-wrap,.accessible-report-controls,.async-status').forEach(ocultar);
    if (!artigo.querySelector('.open-experiment')) {
      const link = document.createElement('a');
      link.className = 'open-experiment';
      link.href = urlFoco(artigo.dataset.experiment);
      link.textContent = 'Abrir experimento →';
      artigo.appendChild(link);
    }
  }

  function modoCatalogo() {
    document.body.classList.add('catalog-mode');
    artigos.forEach(esconderConteudoCatalogo);
    const observer = new MutationObserver(() => artigos.forEach(esconderConteudoCatalogo));
    observer.observe(document.body, { childList: true, subtree: true });
  }

  function adicionarCabecalhoFoco(artigo) {
    const container = artigo.parentElement;
    if (container && !container.querySelector('.focus-toolbar')) {
      const barra = document.createElement('div');
      barra.className = 'focus-toolbar';
      barra.innerHTML = `<a href="${urlCatalogo()}">← Voltar aos experimentos</a><span>Experimento ativo</span>`;
      container.insertBefore(barra, artigo);
    }
  }

  function atualizarTabelaDoHtml(html, chave) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    const nova = doc.querySelector(`[data-experiment="${chave}"] .table-wrap`);
    const atual = document.querySelector(`[data-experiment="${chave}"] .table-wrap`);
    if (nova && atual) {
      nova.hidden = false;
      nova.style.removeProperty('display');
      atual.replaceWith(nova);
      return true;
    }
    return false;
  }

  function mensagem(artigo, texto, tipo = 'ok') {
    let status = artigo.querySelector('.async-status');
    if (!status) {
      status = document.createElement('p');
      status.className = 'async-status';
      status.setAttribute('role', tipo === 'erro' ? 'alert' : 'status');
      status.setAttribute('aria-live', tipo === 'erro' ? 'assertive' : 'polite');
      artigo.querySelector('form.measure')?.insertAdjacentElement('afterend', status);
    }
    mostrar(status);
    status.dataset.tipo = tipo;
    status.textContent = texto;
  }

  function numeroCampo(form, nome) {
    const campo = form.querySelector(`[name="${nome}"]`);
    if (!campo) return { campo: null, valor: NaN };
    const valor = Number(String(campo.value).trim().replace(',', '.'));
    return { campo, valor };
  }

  function marcarInvalido(campo, invalido) {
    if (!campo) return;
    campo.setAttribute('aria-invalid', invalido ? 'true' : 'false');
    campo.classList.toggle('field-invalid', invalido);
  }

  function validarMedicao(form, artigo) {
    const chave = artigo.dataset.experiment;
    const erros = [];
    form.querySelectorAll('input').forEach(c => marcarInvalido(c, false));

    if (chave === 'queda') {
      const altura = numeroCampo(form, 'altura');
      const tempo = numeroCampo(form, 'tempo');
      if (!Number.isFinite(altura.valor) || altura.valor <= 0) { erros.push('Informe uma altura maior que zero.'); marcarInvalido(altura.campo, true); }
      if (!Number.isFinite(tempo.valor) || tempo.valor <= 0) { erros.push('Informe um tempo maior que zero.'); marcarInvalido(tempo.campo, true); }
    }

    if (chave === 'pendulo') {
      const comprimento = numeroCampo(form, 'comprimento');
      const periodo = numeroCampo(form, 'periodo');
      if (!Number.isFinite(comprimento.valor) || comprimento.valor <= 0) { erros.push('Informe um comprimento maior que zero.'); marcarInvalido(comprimento.campo, true); }
      if (!Number.isFinite(periodo.valor) || periodo.valor <= 0) { erros.push('Informe um período maior que zero.'); marcarInvalido(periodo.campo, true); }
    }

    if (chave === 'plano') {
      const angulo = numeroCampo(form, 'angulo');
      const distancia = numeroCampo(form, 'distancia');
      const tempo = numeroCampo(form, 'tempo');
      if (!Number.isFinite(angulo.valor) || angulo.valor <= 0 || angulo.valor >= 90) { erros.push('Informe um ângulo entre 0° e 90°.'); marcarInvalido(angulo.campo, true); }
      if (!Number.isFinite(distancia.valor) || distancia.valor <= 0) { erros.push('Informe uma distância maior que zero.'); marcarInvalido(distancia.campo, true); }
      if (!Number.isFinite(tempo.valor) || tempo.valor <= 0) { erros.push('Informe um tempo maior que zero.'); marcarInvalido(tempo.campo, true); }
    }

    if (erros.length) {
      mensagem(artigo, erros.join(' '), 'erro');
      const primeiro = form.querySelector('.field-invalid');
      primeiro?.focus();
      return false;
    }
    return true;
  }

  async function executarPostSemRecarregar(form, artigo, opcoes = {}) {
    if (form.dataset.enviando === '1') return;
    if (form.classList.contains('measure') && !validarMedicao(form, artigo)) return;
    form.dataset.enviando = '1';

    const botao = form.querySelector('button[type="submit"]');
    const textoOriginal = botao?.textContent;
    if (botao) {
      botao.disabled = true;
      botao.setAttribute('aria-disabled', 'true');
      botao.textContent = opcoes.processando || 'Processando…';
    }
    mensagem(artigo, opcoes.status || 'Salvando…');

    try {
      const resposta = await fetch(form.action, {
        method: 'POST',
        body: new FormData(form),
        headers: { 'X-Fisica-Web-Async': '1' },
        redirect: 'follow',
        cache: 'no-store'
      });
      const html = await resposta.text();
      if (!resposta.ok) throw new Error(html || `Erro ${resposta.status}`);

      const atualizou = atualizarTabelaDoHtml(html, artigo.dataset.experiment);
      if (!atualizou) throw new Error('A tabela atualizada não foi encontrada na resposta.');

      if (opcoes.resetar) {
        form.reset();
        const hidden = form.querySelector('input[name="grupo_id"]');
        if (hidden) hidden.value = grupoId;
      }

      mensagem(artigo, opcoes.sucesso || 'Operação concluída.');
      document.dispatchEvent(new CustomEvent('fisicaweb:experiment-updated'));
    } catch (erro) {
      const detalhe = String(erro?.message || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
      mensagem(artigo, detalhe && detalhe.length < 220 ? detalhe : (opcoes.erro || 'Não foi possível concluir a operação.'), 'erro');
      console.error('Física Web — operação assíncrona:', erro);
    } finally {
      window.setTimeout(() => {
        form.dataset.enviando = '0';
        if (botao) {
          botao.disabled = false;
          botao.removeAttribute('aria-disabled');
          botao.textContent = textoOriginal;
        }
      }, 500);
    }
  }

  function protegerFormulario(form, artigo, opcoes) {
    if (!form || form.dataset.asyncProtegido === '1') return;
    form.dataset.asyncProtegido = '1';
    form.addEventListener('submit', (evento) => {
      evento.preventDefault();
      evento.stopImmediatePropagation();
      if (form.dataset.enviando === '1') return false;
      executarPostSemRecarregar(form, artigo, opcoes);
      return false;
    }, true);
  }

  function modoFocado(chave) {
    document.body.classList.add('experiment-focus-mode');
    ocultar(document.getElementById('ambientes'));
    ocultar(document.getElementById('contexto'));
    const painelAcessibilidade = document.getElementById('acessibilidade');
    if (painelAcessibilidade) {
      painelAcessibilidade.classList.add('focus-accessibility');
      mostrar(painelAcessibilidade);
    }

    artigos.forEach((artigo) => {
      if (artigo.dataset.experiment !== chave) ocultar(artigo);
      else {
        mostrar(artigo);
        artigo.querySelectorAll('form,.actions,.table-wrap,.accessible-report-controls').forEach(mostrar);
      }
    });

    const ativo = artigos.find((a) => a.dataset.experiment === chave);
    if (!ativo) return modoCatalogo();

    ativo.classList.add('experiment-active');
    adicionarCabecalhoFoco(ativo);

    ativo.querySelectorAll('form.measure input[inputmode="decimal"]').forEach(input => {
      input.setAttribute('min', input.name === 'angulo' ? '0.01' : '0.000001');
      input.setAttribute('step', 'any');
    });

    protegerFormulario(ativo.querySelector('form.measure'), ativo, {
      processando: 'Registrando…',
      status: 'Salvando medição…',
      sucesso: 'Medição registrada e salva. A tabela foi atualizada.',
      erro: 'Não foi possível registrar a medição. Verifique os valores e tente novamente.',
      resetar: true,
    });

    protegerFormulario(ativo.querySelector('form[action*="limpar"]'), ativo, {
      processando: 'Limpando…',
      status: 'Limpando medições…',
      sucesso: 'Medições removidas.',
      erro: 'Não foi possível limpar as medições.',
      resetar: false,
    });
  }

  const style = document.createElement('style');
  style.textContent = `
    [hidden]{display:none!important}
    .open-experiment{display:inline-flex;margin-top:14px;min-height:46px;align-items:center;justify-content:center;padding:10px 14px;border-radius:10px;background:var(--primary);color:#fff;text-decoration:none;font-weight:750}
    .catalog-mode .experiment{min-height:190px;display:flex;flex-direction:column}
    .catalog-mode .open-experiment{margin-top:auto}
    .catalog-mode .experiment>form,.catalog-mode .experiment>.actions,.catalog-mode .experiment>.table-wrap,.catalog-mode .experiment>.accessible-report-controls{display:none!important}
    .experiment-focus-mode #inicio,.experiment-focus-mode #coleta{display:none!important}
    .experiment-focus-mode #ambientes,.experiment-focus-mode #contexto{display:none!important}
    .experiment-focus-mode .focus-accessibility{display:block!important;margin:16px auto;max-width:820px}
    .experiment-focus-mode #experimentos>.section-title{display:none}
    .experiment-focus-mode .experiments{display:block}
    .experiment-focus-mode .experiment-active{max-width:820px;margin:0 auto;border:0;box-shadow:none;padding:8px 0}
    .experiment-focus-mode .experiment-active form.measure{display:grid!important;max-width:560px}
    .experiment-focus-mode .experiment-active>.actions{display:flex!important}
    .experiment-focus-mode .experiment-active>.table-wrap{display:block!important;margin-top:24px}
    .focus-toolbar{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid var(--border)}
    .focus-toolbar a{text-decoration:none;font-weight:750}
    .focus-toolbar span{font-size:.85rem;color:var(--muted)}
    .async-status{padding:10px 12px;border-radius:10px;background:var(--surface2);font-weight:650}
    .async-status[data-tipo="erro"]{background:#fff0f1;color:#8a2632;border:1px solid #e6b7bd}
    .field-invalid{border-color:#9b3a44!important;outline:2px solid rgba(155,58,68,.16)}
    @media(max-width:600px){.experiment-focus-mode #experimentos{padding:14px}.experiment-focus-mode .experiment-active{padding:0}.focus-toolbar{align-items:flex-start;flex-direction:column}.catalog-mode .experiment{min-height:160px}}
  `;
  document.head.appendChild(style);

  configurarControlesGlobais();
  if ('speechSynthesis' in window) window.speechSynthesis.onvoiceschanged = escolherVozPtBR;

  if (foco && validos.has(foco)) modoFocado(foco);
  else modoCatalogo();
})();