(() => {
  'use strict';

  const EXPERIMENTS = {
    'Queda Livre': 'Esquema de queda livre: esfera em queda vertical a partir de uma altura h, com sensor de tempo na base.',
    'Pêndulo Simples': 'Esquema de pêndulo simples: esfera suspensa por fio de comprimento L, oscilando em torno da posição de equilíbrio.',
    'Plano Inclinado': 'Esquema de plano inclinado: bloco sobre uma rampa com ângulo theta e forças atuantes.',
    'MRU': 'Esquema de movimento retilíneo uniforme: objeto percorrendo uma trajetória com velocidade constante.',
    'MRUV': 'Esquema de movimento retilíneo uniformemente variado: posições sucessivas de um objeto com aceleração.',
    'Lançamento': 'Esquema de lançamento oblíquo com trajetória parabólica, velocidade inicial e altura.',
    'Leis de Newton': 'Esquema de bloco submetido a forças, ilustrando a relação entre força, massa e aceleração.',
    'Energia': 'Esquema de transformação entre energia potencial e energia cinética ao longo de uma trajetória.',
    'Atrito': 'Esquema de bloco sobre superfície horizontal, com força aplicada e força de atrito em sentido oposto.',
    'Movimento Circular': 'Esquema de movimento circular mostrando raio, velocidade tangencial e aceleração centrípeta.',
    'Som': 'Representação de uma onda sonora periódica, destacando comprimento de onda, amplitude e propagação.',
    'Elevador': 'Esquema de cabine de elevador com forças verticais e indicação da aceleração.',
    'Sensores': 'Esquema de smartphone com eixos X, Y e Z do acelerômetro e indicação do vetor gravidade.',
    'Laboratório Móvel': 'Esquema de laboratório móvel utilizando sensores integrados ao dispositivo.'
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

  const normalize = value => String(value || '').replace(/\s+/g, ' ').trim();

  function speak(text, button) {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.lang = 'pt-BR';
    u.rate = .92;
    u.pitch = 1;
    u.onend = () => button?.removeAttribute('aria-busy');
    button?.setAttribute('aria-busy', 'true');
    window.speechSynthesis.speak(u);
  }

  function styleOnce() {
    if (document.getElementById('fw-experiment-illustrations-style')) return;
    const style = document.createElement('style');
    style.id = 'fw-experiment-illustrations-style';
    style.textContent = `
      .fw-experiment-figure{
        margin:0 auto 14px;
        max-width:760px;
        border:1px solid #c9d8e8;
        border-radius:16px;
        overflow:hidden;
        background:#fff;
        box-shadow:0 6px 20px rgba(9,47,85,.08)
      }
      .fw-experiment-diagram{
        display:block;
        width:100%;
        height:auto;
        min-height:220px;
        background:#fff
      }
      .fw-experiment-figure figcaption{
        padding:10px 14px 5px;
        color:#24384e;
        font-size:.88rem;
        line-height:1.45;
        font-weight:650
      }
      .fw-experiment-figure .fw-figure-actions{
        display:flex;
        gap:8px;
        flex-wrap:wrap;
        padding:7px 14px 12px
      }
      .fw-experiment-figure .fw-figure-speak{
        min-height:40px;
        border:1px solid #15558f;
        border-radius:10px;
        padding:8px 12px;
        background:#15558f;
        color:#fff;
        font:inherit;
        font-weight:800;
        cursor:pointer
      }
      .fw-experiment-figure .fw-figure-speak:focus-visible{
        outline:3px solid #35b779;
        outline-offset:2px
      }
      @media(max-width:700px){
        .fw-experiment-figure{margin:0 auto 12px;max-width:100%;border-radius:13px}
        .fw-experiment-diagram{min-height:190px}
        .fw-experiment-figure figcaption{font-size:.84rem}
      }
    `;
    document.head.appendChild(style);
  }

  function svgShell(title, body, legend) {
    return `<svg class="fw-experiment-diagram" viewBox="0 0 760 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Esquema do experimento ${title}">
      <rect width="760" height="300" fill="#ffffff"/>
      <rect x="18" y="18" width="724" height="264" rx="18" fill="#fbfdff" stroke="#d5e2ee" stroke-width="2"/>
      <text x="44" y="52" fill="#17324d" font-family="Arial,sans-serif" font-size="20" font-weight="800">Esquema de montagem</text>
      ${body}
      ${legend ? `<g font-family="Arial,sans-serif" font-size="15" fill="#24435f">${legend}</g>` : ''}
    </svg>`;
  }

  function diagram(title) {
    const navy = '#173b59', blue = '#1267b1', cyan = '#1689d5', light = '#eaf4fb', green = '#2f8f62', orange = '#d9822b';
    if (title === 'Queda Livre') return svgShell(title, `
      <g stroke-linecap="round" stroke-linejoin="round">
        <path d="M130 230V92h150" fill="none" stroke="#5b6f82" stroke-width="12"/>
        <rect x="255" y="72" width="48" height="34" rx="7" fill="${navy}"/>
        <circle cx="279" cy="128" r="21" fill="#d8e3ed" stroke="#5b6f82" stroke-width="4"/>
        <path d="M279 153V218m0 0-13-17m13 17 13-17" fill="none" stroke="${cyan}" stroke-width="6"/>
        <rect x="245" y="218" width="68" height="30" rx="7" fill="${navy}"/>
        <rect x="263" y="225" width="32" height="13" rx="2" fill="#fff"/>
        <line x1="75" y1="128" x2="75" y2="218" stroke="${blue}" stroke-width="4"/>
        <path d="M67 128h16M67 218h16" stroke="${blue}" stroke-width="4"/>
        <text x="51" y="177" fill="${blue}" font-family="Arial" font-size="22" font-weight="800">h</text>
      </g>`, `<circle cx="530" cy="108" r="7" fill="${blue}"/><text x="548" y="113">Liberação da esfera</text><circle cx="530" cy="145" r="7" fill="${cyan}"/><text x="548" y="150">Queda livre</text><circle cx="530" cy="182" r="7" fill="${navy}"/><text x="548" y="187">Sensor de tempo</text><rect x="510" y="208" width="188" height="46" rx="12" fill="${light}"/><text x="526" y="236" fill="${navy}" font-weight="700">Altura h e tempo t</text>`);

    if (title === 'Pêndulo Simples') return svgShell(title, `
      <g stroke-linecap="round">
        <line x1="150" y1="78" x2="350" y2="78" stroke="${navy}" stroke-width="10"/>
        <circle cx="250" cy="78" r="8" fill="${blue}"/>
        <line x1="250" y1="78" x2="315" y2="190" stroke="#5b6f82" stroke-width="5"/>
        <circle cx="315" cy="190" r="25" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>
        <line x1="250" y1="78" x2="250" y2="190" stroke="#b6c7d7" stroke-dasharray="8 7" stroke-width="3"/>
        <path d="M250 112 A42 42 0 0 1 274 104" fill="none" stroke="${cyan}" stroke-width="3"/>
        <text x="268" y="119" fill="${cyan}" font-family="Arial" font-size="18" font-weight="800">θ</text>
        <line x1="265" y1="88" x2="304" y2="156" stroke="${blue}" stroke-width="2"/>
        <text x="304" y="120" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">L</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Ponto de suspensão</text><circle cx="510" cy="145" r="7" fill="${cyan}"/><text x="528" y="150">Comprimento L</text><circle cx="510" cy="182" r="7" fill="${green}"/><text x="528" y="187">Posição de equilíbrio</text>`);

    if (title === 'Plano Inclinado') return svgShell(title, `
      <g stroke-linecap="round" stroke-linejoin="round">
        <path d="M95 225H390L275 125Z" fill="#eef5fa" stroke="${navy}" stroke-width="5"/>
        <rect x="235" y="157" width="52" height="38" rx="6" transform="rotate(-41 261 176)" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>
        <path d="M262 174l38-30" stroke="${cyan}" stroke-width="5"/>
        <path d="M300 144l-12 2m12-2-2 12" stroke="${cyan}" stroke-width="4"/>
        <path d="M260 176v55" stroke="${orange}" stroke-width="4"/>
        <path d="M260 231l-8-13m8 13 8-13" stroke="${orange}" stroke-width="4"/>
        <path d="M95 225h48" stroke="${blue}" stroke-width="4"/>
        <path d="M145 225 A50 50 0 0 0 129 193" fill="none" stroke="${blue}" stroke-width="3"/>
        <text x="142" y="204" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">θ</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Plano com ângulo θ</text><circle cx="510" cy="145" r="7" fill="${cyan}"/><text x="528" y="150">Aceleração</text><circle cx="510" cy="182" r="7" fill="${orange}"/><text x="528" y="187">Componente do peso</text>`);

    if (title === 'MRU' || title === 'MRUV') return svgShell(title, `
      <g stroke-linecap="round">
        <line x1="80" y1="220" x2="410" y2="220" stroke="${navy}" stroke-width="5"/>
        <path d="M110 220h260" stroke="${cyan}" stroke-width="4"/>
        <path d="M370 220l-16-9m16 9-16 9" stroke="${cyan}" stroke-width="4"/>
        <circle cx="135" cy="190" r="17" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>
        ${title === 'MRU' ? `<circle cx="230" cy="190" r="17" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/><circle cx="325" cy="190" r="17" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>` : `<circle cx="215" cy="190" r="17" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/><circle cx="315" cy="190" r="17" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/><circle cx="380" cy="190" r="17" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>`}
        <text x="105" y="145" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">t₁</text><text x="205" y="145" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">t₂</text><text x="305" y="145" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">t₃</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Posições sucessivas</text><circle cx="510" cy="145" r="7" fill="${cyan}"/><text x="528" y="150">${title === 'MRU' ? 'Velocidade constante' : 'Aceleração constante'}</text>`);

    if (title === 'Lançamento') return svgShell(title, `
      <g fill="none" stroke-linecap="round">
        <path d="M90 220 Q240 65 410 220" stroke="${cyan}" stroke-width="5"/>
        <circle cx="90" cy="220" r="12" fill="${blue}" stroke="none"/><circle cx="250" cy="130" r="11" fill="#d8e3ed" stroke="${navy}" stroke-width="3"/><circle cx="410" cy="220" r="12" fill="${green}" stroke="none"/>
        <path d="M90 220l65-40" stroke="${orange}" stroke-width="4"/><path d="M155 180l-12 1m12-1-3 12" stroke="${orange}" stroke-width="3"/>
        <line x1="250" y1="220" x2="250" y2="130" stroke="#b6c7d7" stroke-dasharray="7 7" stroke-width="3"/>
        <text x="265" y="180" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">h</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Velocidade inicial</text><circle cx="510" cy="145" r="7" fill="${cyan}"/><text x="528" y="150">Trajetória</text><circle cx="510" cy="182" r="7" fill="${green}"/><text x="528" y="187">Alcance</text>`);

    if (title === 'Leis de Newton') return svgShell(title, `
      <g stroke-linecap="round">
        <rect x="210" y="150" width="100" height="65" rx="8" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>
        <path d="M125 182h85" stroke="${blue}" stroke-width="6"/><path d="M210 182l-16-10m16 10-16 10" stroke="${blue}" stroke-width="5"/>
        <path d="M310 182h90" stroke="${orange}" stroke-width="6"/><path d="M400 182l-16-10m16 10-16 10" stroke="${orange}" stroke-width="5"/>
        <path d="M260 150V105" stroke="${green}" stroke-width="6"/><path d="M260 105l-10 16m10-16 10 16" stroke="${green}" stroke-width="5"/>
        <text x="248" y="190" fill="${navy}" font-family="Arial" font-size="18" font-weight="800">m</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Força aplicada</text><circle cx="510" cy="145" r="7" fill="${orange}"/><text x="528" y="150">Força resultante</text><circle cx="510" cy="182" r="7" fill="${green}"/><text x="528" y="187">Aceleração</text>`);

    if (title === 'Energia') return svgShell(title, `
      <g stroke-linecap="round">
        <path d="M90 220 Q220 60 420 220" fill="none" stroke="${navy}" stroke-width="6"/>
        <circle cx="110" cy="210" r="17" fill="${blue}"/><circle cx="250" cy="112" r="17" fill="#d8e3ed" stroke="${navy}" stroke-width="3"/><circle cx="410" cy="210" r="17" fill="${green}"/>
        <path d="M130 195l70-60" stroke="${cyan}" stroke-width="4"/><path d="M335 135l60 60" stroke="${cyan}" stroke-width="4"/>
        <text x="105" y="260" fill="${blue}" font-family="Arial" font-size="17" font-weight="800">Eₚ</text><text x="400" y="260" fill="${green}" font-family="Arial" font-size="17" font-weight="800">E𝚌</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Energia potencial</text><circle cx="510" cy="145" r="7" fill="${green}"/><text x="528" y="150">Energia cinética</text>`);

    if (title === 'Atrito') return svgShell(title, `
      <g stroke-linecap="round">
        <line x1="90" y1="220" x2="430" y2="220" stroke="${navy}" stroke-width="8"/>
        <rect x="220" y="150" width="95" height="65" rx="8" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>
        <path d="M315 182h95" stroke="${blue}" stroke-width="6"/><path d="M410 182l-16-10m16 10-16 10" stroke="${blue}" stroke-width="5"/>
        <path d="M220 195h-95" stroke="${orange}" stroke-width="6"/><path d="M125 195l16-10m-16 10 16 10" stroke="${orange}" stroke-width="5"/>
        <path d="M267 150V105" stroke="${green}" stroke-width="5"/><path d="M267 105l-9 15m9-15 9 15" stroke="${green}" stroke-width="4"/>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Força aplicada</text><circle cx="510" cy="145" r="7" fill="${orange}"/><text x="528" y="150">Força de atrito</text><circle cx="510" cy="182" r="7" fill="${green}"/><text x="528" y="187">Normal e peso</text>`);

    if (title === 'Movimento Circular') return svgShell(title, `
      <g stroke-linecap="round">
        <circle cx="250" cy="170" r="80" fill="#f5f9fc" stroke="${navy}" stroke-width="5"/>
        <circle cx="250" cy="170" r="8" fill="${navy}"/>
        <circle cx="250" cy="90" r="15" fill="#d8e3ed" stroke="${blue}" stroke-width="4"/>
        <line x1="250" y1="170" x2="250" y2="90" stroke="${blue}" stroke-width="4"/>
        <path d="M250 90l-18 18m18-18 18 18" stroke="${cyan}" stroke-width="4"/>
        <path d="M280 95 A80 80 0 0 1 330 145" fill="none" stroke="${green}" stroke-width="5"/>
        <text x="260" y="132" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">r</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Raio r</text><circle cx="510" cy="145" r="7" fill="${green}"/><text x="528" y="150">Velocidade tangencial</text><circle cx="510" cy="182" r="7" fill="${cyan}"/><text x="528" y="187">Aceleração centrípeta</text>`);

    if (title === 'Som') return svgShell(title, `
      <g stroke-linecap="round">
        <path d="M75 175 C110 105 145 245 180 175 S250 105 285 175 S355 245 390 175" fill="none" stroke="${cyan}" stroke-width="5"/>
        <line x1="75" y1="175" x2="390" y2="175" stroke="#b6c7d7" stroke-width="2"/>
        <line x1="120" y1="125" x2="120" y2="175" stroke="${blue}" stroke-width="3"/>
        <line x1="120" y1="125" x2="120" y2="145" stroke="${blue}" stroke-width="3"/>
        <text x="128" y="135" fill="${blue}" font-family="Arial" font-size="18" font-weight="800">A</text>
        <line x1="75" y1="255" x2="180" y2="255" stroke="${navy}" stroke-width="3"/><path d="M75 255l10-6m-10 6 10 6M180 255l-10-6m10 6-10 6" stroke="${navy}" stroke-width="3"/><text x="120" y="278" fill="${navy}" font-family="Arial" font-size="17" font-weight="800">λ</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${cyan}"/><text x="528" y="113">Amplitude A</text><circle cx="510" cy="145" r="7" fill="${blue}"/><text x="528" y="150">Comprimento de onda λ</text>`);

    if (title === 'Elevador') return svgShell(title, `
      <g stroke-linecap="round">
        <rect x="170" y="70" width="150" height="155" rx="10" fill="#f5f9fc" stroke="${navy}" stroke-width="6"/>
        <circle cx="245" cy="150" r="28" fill="#d8e3ed" stroke="${navy}" stroke-width="4"/>
        <path d="M245 118V82" stroke="${blue}" stroke-width="5"/><path d="M245 82l-10 14m10-14 10 14" stroke="${blue}" stroke-width="4"/>
        <path d="M245 182v35" stroke="${orange}" stroke-width="5"/><path d="M245 217l-10-14m10 14 10-14" stroke="${orange}" stroke-width="4"/>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Tensão / normal</text><circle cx="510" cy="145" r="7" fill="${orange}"/><text x="528" y="150">Peso</text><circle cx="510" cy="182" r="7" fill="${green}"/><text x="528" y="187">Aceleração</text>`);

    if (title === 'Sensores' || title === 'Laboratório Móvel') return svgShell(title, `
      <g stroke-linecap="round" stroke-linejoin="round">
        <rect x="125" y="65" width="150" height="170" rx="20" fill="#f5f9fc" stroke="${navy}" stroke-width="6"/>
        <rect x="145" y="92" width="110" height="105" rx="8" fill="#fff" stroke="#c9d8e8" stroke-width="3"/>
        <circle cx="200" cy="212" r="7" fill="${navy}"/>
        <path d="M200 145V105" stroke="${blue}" stroke-width="5"/><path d="M200 105l-9 13m9-13 9 13" stroke="${blue}" stroke-width="4"/>
        <path d="M200 145l42 0" stroke="${green}" stroke-width="5"/><path d="M242 145l-13-9m13 9-13 9" stroke="${green}" stroke-width="4"/>
        <path d="M200 145l-28 30" stroke="${orange}" stroke-width="5"/><path d="M172 175l4-15m-4 15 15-4" stroke="${orange}" stroke-width="4"/>
        <text x="185" y="100" fill="${blue}" font-family="Arial" font-size="15" font-weight="800">Z</text><text x="247" y="138" fill="${green}" font-family="Arial" font-size="15" font-weight="800">X</text><text x="160" y="193" fill="${orange}" font-family="Arial" font-size="15" font-weight="800">Y</text>
      </g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Eixo Z</text><circle cx="510" cy="145" r="7" fill="${green}"/><text x="528" y="150">Eixo X</text><circle cx="510" cy="182" r="7" fill="${orange}"/><text x="528" y="187">Eixo Y</text>`);

    return svgShell(title, `<g><circle cx="250" cy="160" r="65" fill="#f5f9fc" stroke="${navy}" stroke-width="5"/><circle cx="250" cy="160" r="13" fill="${blue}"/><path d="M250 95v-28m0 158v-28M185 160h-28m158 0h-28" stroke="${cyan}" stroke-width="4"/></g>`, `<circle cx="510" cy="108" r="7" fill="${blue}"/><text x="528" y="113">Grandeza física</text><circle cx="510" cy="145" r="7" fill="${cyan}"/><text x="528" y="150">Medição</text>`);
  }

  function addFigure(container, title) {
    if (!container || container.querySelector(':scope > .fw-experiment-figure')) return;
    const description = EXPERIMENTS[title];
    if (!description) return;

    const figure = document.createElement('figure');
    figure.className = 'fw-experiment-figure';
    figure.setAttribute('aria-label', `Ilustração do experimento ${title}.`);
    figure.innerHTML = diagram(title);

    const caption = document.createElement('figcaption');
    caption.textContent = `Esquema do experimento: ${description}`;

    const actions = document.createElement('div');
    actions.className = 'fw-figure-actions';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'fw-figure-speak';
    button.textContent = '🔊 Ouvir descrição';
    button.setAttribute('aria-label', `Ouvir descrição da ilustração de ${title}`);
    button.addEventListener('click', () => speak(`${title}. ${description}`, button));
    actions.append(button);

    figure.append(caption, actions);
    container.prepend(figure);
  }

  function enhanceHomeCards() {
    document.querySelectorAll('.experiment').forEach(card => {
      addFigure(card, normalize(card.querySelector('h3')?.textContent));
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

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run, {once:true});
  else run();
  window.addEventListener('load', run, {once:true});
})();
