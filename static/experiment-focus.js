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

  function esconderConteudoCatalogo(artigo) {
    artigo.querySelectorAll('form,.actions,.table-wrap,.accessible-report-controls').forEach((el) => {
      el.hidden = true;
    });
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
    if (nova && atual) atual.replaceWith(nova);
  }

  function mensagem(artigo, texto, tipo = 'ok') {
    let status = artigo.querySelector('.async-status');
    if (!status) {
      status = document.createElement('p');
      status.className = 'async-status';
      status.setAttribute('role', 'status');
      status.setAttribute('aria-live', 'polite');
      artigo.querySelector('form')?.insertAdjacentElement('afterend', status);
    }
    status.dataset.tipo = tipo;
    status.textContent = texto;
  }

  async function executarPostSemRecarregar(form, artigo, opcoes = {}) {
    const botao = form.querySelector('button[type="submit"]');
    const textoOriginal = botao?.textContent;
    if (botao) { botao.disabled = true; botao.textContent = opcoes.processando || 'Processando…'; }
    mensagem(artigo, opcoes.status || 'Salvando…');
    try {
      const resposta = await fetch(form.action, { method: 'POST', body: new FormData(form) });
      const html = await resposta.text();
      if (!resposta.ok) throw new Error(html || `Erro ${resposta.status}`);
      atualizarTabelaDoHtml(html, artigo.dataset.experiment);
      if (opcoes.resetar) {
        form.reset();
        const hidden = form.querySelector('input[name="grupo_id"]');
        if (hidden) hidden.value = grupoId;
      }
      mensagem(artigo, opcoes.sucesso || 'Operação concluída.');
      document.dispatchEvent(new CustomEvent('fisicaweb:experiment-updated'));
    } catch (erro) {
      mensagem(artigo, opcoes.erro || 'Não foi possível concluir a operação.', 'erro');
      console.error('Física Web — operação assíncrona:', erro);
    } finally {
      if (botao) { botao.disabled = false; botao.textContent = textoOriginal; }
    }
  }

  function modoFocado(chave) {
    document.body.classList.add('experiment-focus-mode');
    document.getElementById('ambientes')?.setAttribute('hidden', '');
    document.getElementById('contexto')?.setAttribute('hidden', '');
    document.getElementById('acessibilidade')?.classList.add('focus-accessibility');

    artigos.forEach((artigo) => {
      if (artigo.dataset.experiment !== chave) artigo.hidden = true;
    });

    const ativo = artigos.find((a) => a.dataset.experiment === chave);
    if (!ativo) return modoCatalogo();
    ativo.classList.add('experiment-active');
    adicionarCabecalhoFoco(ativo);

    const formulario = ativo.querySelector('form:not([action*="limpar"])');
    if (formulario) {
      formulario.addEventListener('submit', (evento) => {
        evento.preventDefault();
        executarPostSemRecarregar(formulario, ativo, {
          processando: 'Registrando…',
          status: 'Salvando medição…',
          sucesso: 'Medição registrada com sucesso.',
          erro: 'Não foi possível registrar a medição. Verifique os valores e tente novamente.',
          resetar: true,
        });
      });
    }

    const limpar = ativo.querySelector('form[action*="limpar"]');
    if (limpar) {
      limpar.addEventListener('submit', (evento) => {
        evento.preventDefault();
        executarPostSemRecarregar(limpar, ativo, {
          processando: 'Limpando…',
          status: 'Limpando medições…',
          sucesso: 'Medições removidas.',
          erro: 'Não foi possível limpar as medições.',
          resetar: false,
        });
      });
    }
  }

  const style = document.createElement('style');
  style.textContent = `
    .open-experiment{display:inline-flex;margin-top:14px;min-height:46px;align-items:center;justify-content:center;padding:10px 14px;border-radius:10px;background:var(--primary);color:#fff;text-decoration:none;font-weight:750}
    .catalog-mode .experiment{min-height:190px;display:flex;flex-direction:column}.catalog-mode .open-experiment{margin-top:auto}
    .experiment-focus-mode .layout{grid-template-columns:1fr;max-width:900px;margin:auto}.experiment-focus-mode .focus-accessibility{display:none}.experiment-focus-mode #experimentos>.section-head,.experiment-focus-mode #experimentos>.workflow{display:none}.experiment-focus-mode .experiments{display:block}.experiment-focus-mode .experiment-active{max-width:820px;margin:0 auto;border:0;box-shadow:none;padding:8px 0}.experiment-focus-mode .experiment-active form{max-width:560px}.experiment-focus-mode .table-wrap{margin-top:24px}.focus-toolbar{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:18px;padding-bottom:12px;border-bottom:1px solid var(--border)}.focus-toolbar a{text-decoration:none;font-weight:750}.focus-toolbar span{font-size:.85rem;color:var(--muted)}.async-status{padding:10px 12px;border-radius:10px;background:var(--surface2);font-weight:650}.async-status[data-tipo="erro"]{background:#fff0f1;color:#8a2632}
    @media(max-width:600px){.experiment-focus-mode #experimentos{padding:14px}.experiment-focus-mode .experiment-active{padding:0}.focus-toolbar{align-items:flex-start;flex-direction:column}.catalog-mode .experiment{min-height:160px}}
  `;
  document.head.appendChild(style);

  if (foco && validos.has(foco)) modoFocado(foco); else modoCatalogo();
})();