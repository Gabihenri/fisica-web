(() => {
  'use strict';

  const BASE = '/static/img/experimentos/';
  const EXPERIMENTS = {
    'Queda Livre': ['queda-livre.svg', 'Esquema de queda livre: uma esfera cai verticalmente de uma altura h.'],
    'Pêndulo Simples': ['pendulo.svg', 'Esquema de um pêndulo simples: uma esfera suspensa por um fio de comprimento L oscila.'],
    'Plano Inclinado': ['plano-inclinado.svg', 'Esquema de um plano inclinado: um bloco está sobre uma rampa com ângulo theta.'],
    'MRU': ['mru.svg', 'Esquema de movimento retilíneo uniforme, com um objeto percorrendo uma trajetória em velocidade constante.'],
    'MRUV': ['mruv.svg', 'Esquema de movimento retilíneo uniformemente variado, com posições sucessivas e aceleração não nula.'],
    'Lançamento': ['lancamento.svg', 'Esquema de lançamento de um objeto com trajetória parabólica.'],
    'Leis de Newton': ['newton.svg', 'Esquema de um bloco submetido a forças, ilustrando a relação F igual a m vezes a.'],
    'Energia': ['energia.svg', 'Esquema de transformação de energia potencial e cinética ao longo de uma trajetória.'],
    'Atrito': ['atrito.svg', 'Esquema de um bloco sobre uma superfície com força aplicada e força de atrito em sentido oposto.'],
    'Movimento Circular': ['circular.svg', 'Esquema de movimento circular, mostrando o raio e a aceleração centrípeta.'],
    'Som': ['som.svg', 'Representação de uma onda sonora periódica, relacionada à frequência e ao período.'],
    'Elevador': ['elevador.svg', 'Esquema de uma cabine de elevador com forças verticais e aceleração.'],
    'Sensores': ['sensores.svg', 'Esquema de um smartphone apoiado, com os eixos X, Y e Z do acelerômetro e o vetor da gravidade.'],
    'Laboratório Móvel': ['movel.svg', 'Esquema do laboratório móvel usando sensores integrados ao dispositivo.']
  };

  const PATHS = {
    '/laboratorio-pendulo': 'Pêndulo Simples',
    '/laboratorio-plano-inclinado': 'Plano Inclinado',
    '/laboratorio-som': 'Som',
    '/laboratorio-mru': 'MRU',
    '/laboratorio-mruv': 'MRUV',
    '/laboratorio-queda-livre': 'Queda Livre',
    '/laboratorio-lancamento': 'Lançamento',
    '/laboratorio-newton': 'Leis de Newton',
    '/laboratorio-energia': 'Energia',
    '/laboratorio-atrito': 'Atrito',
    '/laboratorio-circular': 'Movimento Circular',
    '/laboratorio-elevador': 'Elevador',
    '/laboratorio-sensores': 'Sensores',
    '/laboratorio-movel': 'Laboratório Móvel'
  };

  function normalize(value) {
    return String(value || '').replace(/\s+/g, ' ').trim();
  }

  function styleOnce() {
    if (document.getElementById('fw-experiment-illustrations-style')) return;
    const style = document.createElement('style');
    style.id = 'fw-experiment-illustrations-style';
    style.textContent = `
      .fw-experiment-figure{margin:0 0 14px;border:1px solid rgba(80,151,255,.28);border-radius:14px;overflow:hidden;background:rgba(2,15,42,.62)}
      .fw-experiment-figure img{display:block;width:100%;height:auto;aspect-ratio:300/280;object-fit:cover}
      .fw-experiment-figure figcaption{padding:8px 10px;color:#aebfdd;font-size:.78rem;line-height:1.45}
      @media (max-width:600px){.fw-experiment-figure{margin-bottom:12px}.fw-experiment-figure figcaption{font-size:.76rem}}
    `;
    document.head.appendChild(style);
  }

  function addFigure(container, title) {
    if (!container || container.querySelector(':scope > .fw-experiment-figure')) return;
    const data = EXPERIMENTS[title];
    if (!data) return;

    const figure = document.createElement('figure');
    figure.className = 'fw-experiment-figure';
    figure.setAttribute('aria-label', `Ilustração do experimento ${title}.`);

    const img = document.createElement('img');
    img.src = BASE + data[0];
    img.alt = data[1];
    img.loading = 'lazy';
    img.decoding = 'async';

    const caption = document.createElement('figcaption');
    caption.textContent = `Esquema do experimento: ${data[1]}`;

    figure.append(img, caption);
    container.prepend(figure);
  }

  function enhanceHomeCards() {
    document.querySelectorAll('.experiment').forEach(card => {
      const title = normalize(card.querySelector('h3')?.textContent);
      addFigure(card, title);
    });
  }

  function enhanceLaboratoryPage() {
    const path = window.location.pathname;
    const title = path.startsWith('/laboratorio-sensores') ? 'Sensores' : PATHS[path];
    if (!title) return;

    const heading = [...document.querySelectorAll('h1,h2,h3')].find(h => normalize(h.textContent) === title);
    const container = heading?.closest('.card, article, section, main') || document.querySelector('main') || document.body;
    addFigure(container, title);
  }

  function run() {
    styleOnce();
    enhanceHomeCards();
    enhanceLaboratoryPage();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, { once: true });
  else run();
  window.addEventListener('load', run, { once: true });
})();
