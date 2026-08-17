(() => {
  'use strict';

  const HIDDEN = 'fw-a11y-science-description';

  function visible(el) {
    if (!el || el.hidden) return false;
    const s = getComputedStyle(el);
    return s.display !== 'none' && s.visibility !== 'hidden';
  }

  function text(value) {
    return String(value || '').replace(/\s+/g, ' ').trim();
  }

  function nearestHeading(el) {
    const container = el.closest('section,article,main,form,fieldset,div') || document.body;
    const heading = container.querySelector('h1,h2,h3,h4,legend');
    return text(heading?.innerText || document.title || 'conteúdo científico');
  }

  function hiddenDescription(id, content) {
    let node = document.getElementById(id);
    if (!node) {
      node = document.createElement('div');
      node.id = id;
      node.className = HIDDEN;
      node.setAttribute('aria-hidden', 'false');
      document.body.appendChild(node);
    }
    node.textContent = content;
    return node.id;
  }

  function makeTablesAccessible() {
    document.querySelectorAll('table').forEach((table, index) => {
      if (!visible(table)) return;
      table.setAttribute('role', 'table');
      const caption = table.querySelector('caption');
      if (!caption) {
        const firstHeading = nearestHeading(table);
        const cap = document.createElement('caption');
        cap.textContent = `Tabela de dados: ${firstHeading}.`;
        table.insertBefore(cap, table.firstChild);
      }

      const headers = table.querySelectorAll('thead th');
      headers.forEach(th => th.setAttribute('scope', 'col'));
      if (!headers.length) {
        const firstRow = table.querySelector('tr');
        firstRow?.querySelectorAll('th').forEach(th => th.setAttribute('scope', 'col'));
      }

      const rows = table.querySelectorAll('tbody tr');
      const cells = table.querySelectorAll('tbody td');
      if (cells.length && !table.hasAttribute('aria-describedby')) {
        const captionText = text(table.querySelector('caption')?.innerText || nearestHeading(table));
        const description = `${captionText}. A tabela contém ${rows.length || table.querySelectorAll('tr').length} linhas de dados e ${headers.length || table.querySelectorAll('tr:first-child th, tr:first-child td').length} colunas.`;
        const id = hiddenDescription(`fw-table-description-${index}-${Date.now()}`, description);
        table.setAttribute('aria-describedby', id);
      }
    });
  }

  function makeChartsAccessible() {
    document.querySelectorAll('canvas, svg').forEach((chart, index) => {
      if (!visible(chart)) return;
      const heading = nearestHeading(chart);
      chart.setAttribute('role', 'img');
      if (!chart.getAttribute('aria-label')) {
        chart.setAttribute('aria-label', `Gráfico ou visualização científica: ${heading}.`);
      }

      const table = chart.closest('section,article,main,div')?.querySelector('table');
      if (table) {
        const id = table.id || `fw-chart-data-${index}`;
        table.id = id;
        chart.setAttribute('aria-describedby', id);
      } else if (!chart.hasAttribute('aria-describedby')) {
        const id = hiddenDescription(`fw-chart-description-${index}-${Date.now()}`, `Gráfico científico relacionado a ${heading}. Se os dados tabulares estiverem disponíveis, utilize a tabela de dados para consultar os valores individualmente.`);
        chart.setAttribute('aria-describedby', id);
      }
    });
  }

  function makeFormsAccessible() {
    document.querySelectorAll('input,select,textarea').forEach((field, index) => {
      if (!visible(field)) return;
      let label = '';
      if (field.id) label = text(document.querySelector(`label[for="${CSS.escape(field.id)}"]`)?.innerText);
      if (!label) label = text(field.closest('label')?.innerText);
      if (!label) label = text(field.getAttribute('aria-label') || field.placeholder || field.name);
      if (!label) return;

      if (!field.getAttribute('aria-label') && !field.getAttribute('aria-labelledby')) {
        field.setAttribute('aria-label', label);
      }

      const unit = text(field.closest('.field,.form-group,.input-group,.control')?.querySelector('.unit,.unidade,[data-unit]')?.innerText);
      if (unit && !field.getAttribute('aria-describedby')) {
        const id = hiddenDescription(`fw-field-unit-${index}-${Date.now()}`, `Unidade: ${unit}.`);
        field.setAttribute('aria-describedby', id);
      }
    });
  }

  function makeLiveRegionsAccessible() {
    document.querySelectorAll('.resultado,.resultados,.mensagem,.erro,.alert,[data-result],[data-output]').forEach(el => {
      if (!visible(el)) return;
      if (!el.getAttribute('role') && /erro|alert/i.test(el.className || '')) el.setAttribute('role', 'alert');
      else if (!el.getAttribute('aria-live')) el.setAttribute('aria-live', 'polite');
    });
  }

  function run() {
    makeTablesAccessible();
    makeChartsAccessible();
    makeFormsAccessible();
    makeLiveRegionsAccessible();
  }

  function init() {
    run();
    const observer = new MutationObserver(() => {
      window.clearTimeout(init.timer);
      init.timer = window.setTimeout(run, 120);
    });
    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['hidden', 'class', 'aria-label', 'value'] });
    window.addEventListener('load', run, { once: true });
    window.addEventListener('hashchange', () => window.setTimeout(run, 150));
    window.FisicaWebAccessibility = Object.assign(window.FisicaWebAccessibility || {}, { refresh: run });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
