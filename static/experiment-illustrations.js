(() => {
  'use strict';
  const BASE = '/static/img/experimentos/';
  const EXPERIMENTS = {
    'Queda Livre': ['queda-livre.svg', 'Esquema de queda livre: uma esfera cai verticalmente de uma altura h.'],
    'Pêndulo Simples': ['pendulo.svg', 'Esquema de um pêndulo simples: uma esfera suspensa por um fio de comprimento L oscila. O esquema mostra o ponto de suspensão, o comprimento L, o ângulo theta, as amplitudes máximas e a posição de equilíbrio.'],
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
    '/laboratorio-pendulo': 'Pêndulo Simples', '/laboratorio-plano-inclinado': 'Plano Inclinado',
    '/laboratorio-som': 'Som', '/laboratorio-mru': 'MRU', '/laboratorio-mruv': 'MRUV',
    '/laboratorio-queda-livre': 'Queda Livre', '/laboratorio-lancamento': 'Lançamento',
    '/laboratorio-newton': 'Leis de Newton', '/laboratorio-energia': 'Energia',
    '/laboratorio-atrito': 'Atrito', '/laboratorio-circular': 'Movimento Circular',
    '/laboratorio-elevador': 'Elevador', '/laboratorio-sensores': 'Sensores', '/laboratorio-movel': 'Laboratório Móvel'
  };
  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim();
  function speak(text, button) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'pt-BR'; u.rate = .92; u.pitch = 1;
    u.onend = () => button?.removeAttribute('aria-busy');
    button?.setAttribute('aria-busy', 'true');
    window.speechSynthesis.speak(u);
  }
  function styleOnce() {
    if (document.getElementById('fw-experiment-illustrations-style')) return;
    const style = document.createElement('style'); style.id = 'fw-experiment-illustrations-style';
    style.textContent = `
      .fw-experiment-figure{margin:0 auto 14px;max-width:460px;border:1px solid #c9d8e8;border-radius:16px;overflow:hidden;background:#fff;box-shadow:0 6px 20px rgba(9,47,85,.10)}
      .fw-experiment-figure img{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:contain;object-position:center;background:#082b55}
      .fw-experiment-figure figcaption{padding:9px 11px 4px;color:#24384e;font-size:.86rem;line-height:1.45;font-weight:600}
      .fw-experiment-figure .fw-figure-actions{display:flex;gap:8px;flex-wrap:wrap;padding:7px 11px 10px}
      .fw-experiment-figure .fw-figure-speak{min-height:40px;border:1px solid #15558f;border-radius:10px;padding:8px 12px;background:#15558f;color:#fff;font:inherit;font-weight:800;cursor:pointer}
      .fw-experiment-figure .fw-figure-speak:focus-visible{outline:3px solid #35b779;outline-offset:2px}
      @media(max-width:600px){.fw-experiment-figure{margin:0 auto 12px;max-width:92%;border-radius:13px}.fw-experiment-figure img{aspect-ratio:4/3}.fw-experiment-figure figcaption{font-size:.84rem}}
    `;
    document.head.appendChild(style);
  }
  function addFigure(container, title) {
    if (!container || container.querySelector(':scope > .fw-experiment-figure')) return;
    const data = EXPERIMENTS[title]; if (!data) return;
    const figure = document.createElement('figure'); figure.className = 'fw-experiment-figure';
    figure.setAttribute('aria-label', `Ilustração do experimento ${title}.`);
    const img = document.createElement('img'); img.src = BASE + data[0]; img.alt = data[1]; img.loading = 'lazy'; img.decoding = 'async';
    const caption = document.createElement('figcaption'); caption.textContent = `Esquema do experimento: ${data[1]}`;
    const actions = document.createElement('div'); actions.className = 'fw-figure-actions';
    const button = document.createElement('button'); button.type = 'button'; button.className = 'fw-figure-speak'; button.textContent = '🔊 Ouvir descrição';
    button.setAttribute('aria-label', `Ouvir descrição da ilustração de ${title}`);
    button.addEventListener('click', () => speak(`${title}. ${data[1]}`, button));
    actions.append(button); figure.append(img, caption, actions); container.prepend(figure);
  }
  function enhanceHomeCards(){document.querySelectorAll('.experiment').forEach(card=>addFigure(card,normalize(card.querySelector('h3')?.textContent)));}
  function enhanceLaboratoryPage(){const path=window.location.pathname;const title=path.startsWith('/laboratorio-sensores')?'Sensores':PATHS[path];if(!title)return;const heading=[...document.querySelectorAll('h1,h2,h3')].find(h=>normalize(h.textContent)===title);const container=heading?.closest('.card, article, section, main')||document.querySelector('main')||document.body;addFigure(container,title);}
  function run(){styleOnce();enhanceHomeCards();enhanceLaboratoryPage();}
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run,{once:true});else run();
  window.addEventListener('load',run,{once:true});
})();
