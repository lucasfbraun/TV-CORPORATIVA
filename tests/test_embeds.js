/**
 * Teste do ciclo de vida dos <iframe> dos slides de URL (manageEmbeds).
 *
 * Roda sem navegador:  node tests/test_embeds.js
 * Usa um DOM mínimo de mentira — só o que manageEmbeds() encosta.
 *
 * O que precisa valer:
 *   - o slide em cena está sempre carregado (nunca em branco);
 *   - o próximo já vem carregado, para não piscar na troca;
 *   - os demais ficam descarregados (about:blank), sem rodar JS do site alvo;
 *   - dar a volta na grade não deixa nenhum iframe carregado para trás.
 */
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'display.js'), 'utf8');
const trecho = src.slice(src.indexOf('function manageEmbeds'),
                         src.indexOf('function buildNewsSlide'));

// ── DOM de mentira ───────────────────────────────────────────────────────────
function novoIframe(url) {
  return {
    dataset: { src: url },
    attrs: {},
    getAttribute(k) { return k in this.attrs ? this.attrs[k] : null; },
    setAttribute(k, v) { this.attrs[k] = v; },
  };
}
function novoSlide(iframe) {
  return { querySelector: sel => (sel === 'iframe[data-src]' ? iframe : null) };
}

let slides = [];
let current = 0;
let elementos = [];
const document = {
  querySelectorAll: sel => (sel === '.slide' ? elementos : []),
};

// Avalia a funcao real do display.js (eval direto: ela enxerga 'slides',
// 'current' e o 'document' de mentira declarados acima).
// eslint-disable-next-line no-eval
const manageEmbeds = eval('(' + trecho.trim() + ')');

const falhas = [];
const check = (cond, msg) => { if (!cond) falhas.push(msg); };
const srcDe = i => elementos[i].querySelector('iframe[data-src]')?.getAttribute('src') ?? null;

// ── Cenário: 5 slides, 3 deles de URL (índices 0, 2 e 4) ────────────────────
const urls = { 0: 'http://sistema/a', 2: 'http://sistema/b', 4: 'http://sistema/c' };
slides = [{ type: 'urlshot' }, { type: 'news' }, { type: 'urlshot' },
          { type: 'media' }, { type: 'urlshot' }];
elementos = slides.map((s, i) => novoSlide(urls[i] ? novoIframe(urls[i]) : null));

// 1. No slide 0: carrega o 0 (atual). O 1 é o próximo, mas não é iframe.
current = 0;
manageEmbeds();
check(srcDe(0) === urls[0], 'slide em cena nao foi carregado');
check(srcDe(2) === 'about:blank', 'iframe distante deveria estar descarregado');
check(srcDe(4) === 'about:blank', 'iframe distante deveria estar descarregado');

// 2. No slide 1: o proximo e o 2 -> pre-carrega, para nao piscar na troca.
current = 1;
manageEmbeds();
check(srcDe(2) === urls[2], 'o proximo slide de URL nao foi pre-carregado');
check(srcDe(0) === 'about:blank', 'o slide que saiu de cena continuou rodando');

// 3. No slide 2: segue carregado, sem recarregar (o src nao pode ser reescrito).
const antes = elementos[2].querySelector('iframe[data-src]');
let escritas = 0;
const setOriginal = antes.setAttribute.bind(antes);
antes.setAttribute = (k, v) => { escritas++; setOriginal(k, v); };
current = 2;
manageEmbeds();
check(escritas === 0, 'o iframe ja carregado foi reescrito (recarregaria a pagina a toa)');
check(srcDe(2) === urls[2], 'o slide em cena se perdeu');

// 4. Dando a volta na grade: no ultimo slide, o proximo e o 0.
current = 4;
manageEmbeds();
check(srcDe(4) === urls[4], 'ultimo slide nao carregou');
check(srcDe(0) === urls[0], 'a volta da grade nao pre-carregou o primeiro');
check(srcDe(2) === 'about:blank', 'sobrou iframe carregado no meio da grade');

// 5. Em nenhum momento mais de 2 iframes ficam vivos.
for (let i = 0; i < slides.length; i++) {
  current = i;
  manageEmbeds();
  const vivos = [0, 2, 4].filter(k => srcDe(k) && srcDe(k) !== 'about:blank').length;
  check(vivos <= 2, `slide ${i}: ${vivos} iframes vivos (o limite e 2: atual + proximo)`);
  const atualEhUrl = urls[i] !== undefined;
  if (atualEhUrl) check(srcDe(i) === urls[i], `slide ${i} entrou em cena em branco`);
}

// 6. Grade com um unico slide de URL: nunca pode descarregar (ele e o proximo dele mesmo).
slides = [{ type: 'urlshot' }];
elementos = [novoSlide(novoIframe('http://sistema/unico'))];
current = 0;
manageEmbeds();
manageEmbeds();
check(srcDe(0) === 'http://sistema/unico', 'grade de um slide so descarregou o proprio slide');

// 7. Grade vazia nao pode explodir.
slides = []; elementos = []; current = 0;
try { manageEmbeds(); } catch (e) { falhas.push('grade vazia quebrou: ' + e.message); }

if (falhas.length) {
  console.log('FALHOU (' + falhas.length + '):');
  falhas.forEach(f => console.log('  - ' + f));
  process.exit(1);
}
console.log('OK - iframes de URL: atual e proximo carregados, o resto descarregado.');
