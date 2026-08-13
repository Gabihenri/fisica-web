(() => {
  const params = new URLSearchParams(window.location.search);
  const grupoId = params.get('grupo_id') || '';
  const chave = params.get('experimento') || '';
  if (!chave) return;

  const artigo = document.querySelector(`[data-experiment="${chave}"]`);
  if (!artigo) return;

  function endpointAnalise() {
    const q = grupoId ? `?grupo_id=${encodeURIComponent(grupoId)}` : '';
    return `/api/analise/${encodeURIComponent(chave)}${q}`;
  }

  function endpointGrafico() {
    const q = new URLSearchParams();
    if (grupoId) q.set('grupo_id', grupoId);
    q.set('_', Date.now().toString());
    return `/grafico/${encodeURIComponent(chave)}?${q.toString()}`;
  }

  function numero(v, casas = 4) {
    if (v === null || v === undefined || Number.isNaN(Number(v))) return '—';
    return Number(v).toLocaleString('pt-BR', { maximumFractionDigits: casas, minimumFractionDigits: Math.min(2, casas) });
  }

  function painel() {
    let el = artigo.querySelector('.scientific-panel');
    if (el) return el;
    el = document.createElement('section');
    el.className = 'scientific-panel';
    el.setAttribute('aria-labelledby', `analise-${chave}`);
    el.innerHTML = `
      <div class="scientific-head">
        <div><span class="scientific-kicker">Análise científica</span><h3 id="analise-${chave}">Tratamento estatístico e gráfico</h3></div>
        <span class="scientific-live" role="status" aria-live="polite">Carregando…</span>
      </div>
      <div class="scientific-metrics"></div>
      <div class="scientific-chart-card">
        <div class="scientific-chart-copy"></div>
        <img class="scientific-chart" alt="Gráfico científico do experimento" hidden>
      </div>
      <div class="scientific-interpretation"></div>`;
    artigo.appendChild(el);
    return el;
  }

  function metric(rotulo, valor, unidade = '') {
    return `<div class="metric"><small>${rotulo}</small><strong>${valor}</strong>${unidade ? `<span>${unidade}</span>` : ''}</div>`;
  }

  async function atualizar() {
    const p = painel();
    const status = p.querySelector('.scientific-live');
    status.textContent = 'Atualizando análise…';
    try {
      const resposta = await fetch(endpointAnalise(), { headers: { Accept: 'application/json' }, cache: 'no-store' });
      if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
      const a = await resposta.json();
      const s = a.estatisticas || {};
      const m = a.modelo || {};

      p.querySelector('.scientific-metrics').innerHTML = [
        metric('Medições', s.n ?? 0),
        metric('Média de g', numero(s.media, 4), 'm/s²'),
        metric('Desvio padrão', numero(s.desvio_padrao, 4), 'm/s²'),
        metric('Erro percentual', s.erro_percentual == null ? '—' : `${numero(s.erro_percentual, 2)}%`),
        metric('Coef. de variação', s.coeficiente_variacao == null ? '—' : `${numero(s.coeficiente_variacao, 2)}%`),
        metric('Qualidade', s.qualidade || 'Dados insuficientes')
      ].join('');

      const reg = m.regressao;
      let detalhe = `<strong>${m.titulo_grafico || 'Gráfico experimental'}</strong><p>${m.descricao_modelo || ''}</p>`;
      if (reg) detalhe += `<p>Ajuste linear: R² = <strong>${numero(reg.r2, 4)}</strong>.</p>`;
      if (m.gravidade_modelo != null) detalhe += `<p>Estimativa de g pelo modelo: <strong>${numero(m.gravidade_modelo, 4)} m/s²</strong>.</p>`;
      p.querySelector('.scientific-chart-copy').innerHTML = detalhe;

      const img = p.querySelector('.scientific-chart');
      if ((m.pontos || []).length) {
        img.src = endpointGrafico();
        img.alt = `${m.titulo_grafico || 'Gráfico experimental'}. Eixo horizontal: ${m.eixo_x || 'x'}. Eixo vertical: ${m.eixo_y || 'y'}.`;
        img.hidden = false;
      } else {
        img.hidden = true;
      }

      p.querySelector('.scientific-interpretation').innerHTML = `<h4>Interpretação</h4><p>${a.interpretacao || 'Ainda não há dados suficientes para interpretação.'}</p>`;
      status.textContent = 'Análise atualizada';
    } catch (erro) {
      status.textContent = 'Não foi possível atualizar a análise';
      console.error('Física Web — análise científica:', erro);
    }
  }

  const style = document.createElement('style');
  style.textContent = `
    .scientific-panel{margin-top:24px;padding-top:22px;border-top:1px solid var(--border)}
    .scientific-head{display:flex;justify-content:space-between;gap:14px;align-items:flex-start;margin-bottom:14px}
    .scientific-head h3{margin:3px 0;font-size:1.2rem}.scientific-kicker{font-size:.75rem;text-transform:uppercase;letter-spacing:.1em;color:var(--primary);font-weight:800}
    .scientific-live{font-size:.82rem;color:var(--muted)}
    .scientific-metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;margin-bottom:14px}
    .metric{border:1px solid var(--border);border-radius:12px;padding:12px;background:var(--surface2)}.metric small{display:block;color:var(--muted);font-weight:700}.metric strong{display:block;font-size:1.08rem;margin-top:3px}.metric span{font-size:.78rem;color:var(--muted)}
    .scientific-chart-card{border:1px solid var(--border);border-radius:14px;padding:14px;background:var(--surface)}.scientific-chart-copy p{margin:5px 0;color:var(--muted)}.scientific-chart{display:block;width:100%;height:auto;margin-top:12px;border-radius:10px}
    .scientific-interpretation{margin-top:12px;padding:14px;border-radius:12px;background:var(--surface2)}.scientific-interpretation h4{margin:0 0 5px}.scientific-interpretation p{margin:0!important;color:var(--text)!important}
    .catalog-mode .scientific-panel,.catalog-mode .acquisition-panel{display:none!important}
    .experiment-focus-mode .flow{display:none!important}
    .experiment-focus-mode .flow-section-hidden{display:none!important}
    @media(max-width:600px){.scientific-head{display:block}.scientific-live{display:block;margin-top:4px}.scientific-metrics{grid-template-columns:repeat(2,minmax(0,1fr))}.metric{padding:10px}.scientific-chart-card{padding:11px}}
  `;
  document.head.appendChild(style);

  const flowSection = document.querySelector('.flow')?.closest('.section');
  if (flowSection) flowSection.classList.add('flow-section-hidden');

  atualizar();
  document.addEventListener('fisicaweb:experiment-updated', atualizar);
})();

(() => {
  if (!document.querySelector('script[data-fisica-acquisition]')) {
    const script = document.createElement('script');
    script.src = '/static/acquisition-layer.js?v=2';
    script.defer = true;
    script.dataset.fisicaAcquisition = '1';
    document.head.appendChild(script);
  }
  if (!document.querySelector('script[data-fisica-montage]')) {
    const script = document.createElement('script');
    script.src = '/static/experiment-montage.js?v=1';
    script.defer = true;
    script.dataset.fisicaMontage = '1';
    document.head.appendChild(script);
  }
})();