/**
 * Regressão: a TV precisa sincronizar com o servidor em QUALQUER origem HTTP(S),
 * não só em http://host:8080.
 *
 * Contexto: o display é publicado atrás de proxy reverso (HAProxy) em
 * tv.grupoflexivel.com.br, sem porta explícita. Quando SERVER_URL exige a porta
 * 8080 literal, syncFromServer() aborta na primeira linha, a grade nunca é
 * buscada e a TV exibe o DEFAULT_CONTENT de demonstração.
 *
 * Uso:  node tests/test_display_sync.js
 * (precisa só do node, não sobe servidor nem banco)
 */
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const DISPLAY_JS = path.join(__dirname, '..', 'frontend', 'display.js');
const src = fs.readFileSync(DISPLAY_JS, 'utf8');
const lines = src.split(/\r?\n/);

function fatia(deIdx, ateFn, oque) {
  if (deIdx < 0) throw new Error(oque + ' não encontrado em display.js');
  for (let i = deIdx + 1; i < lines.length; i++) {
    if (ateFn(lines[i])) return lines.slice(0, i + 1);
  }
  throw new Error('fim de ' + oque + ' não encontrado em display.js');
}

// migrateData + DEFAULT_CONTENT + resolveContent
const contentBlock = fatia(
  lines.findIndex(l => l.includes('function resolveContent()')),
  l => l === '}', 'resolveContent'
).join('\n');

// o IIFE do SERVER_URL
const suStart = lines.findIndex(l => l.includes('const SERVER_URL'));
if (suStart < 0) throw new Error('SERVER_URL não encontrado em display.js');
let suEnd = -1;
for (let i = suStart; i < lines.length; i++) {
  if (lines[i].trim() === '})();') { suEnd = i; break; }
}
const serverUrlBlock = lines.slice(suStart, suEnd + 1).join('\n');

// 'const' declarado no vm não vira propriedade do sandbox: exporta explicitamente
const EXPORTA = '\n__out.SERVER_URL = SERVER_URL;\n__out.resolveContent = resolveContent;';

// Conteúdo de servidor fixo — a TV "producao" usa uma grade que NÃO é a primeira,
// para que o fallback silencioso de resolveContent() não passe por acidente.
const CONTEUDO_SERVIDOR = {
  config: { company_name: 'GRUPO FLEXÍVEL', slide_duration: 12 },
  tvs: [
    { id: 'tv-001', slug: 'principal', name: 'Principal', grade_id: 'grade-001', rodape_id: 'rodape-001', active: true },
    { id: 'tv-002', slug: 'producao',  name: 'Produção',  grade_id: 'grade-002', rodape_id: 'rodape-001', active: true },
  ],
  grades: [
    { id: 'grade-001', name: 'Grade Principal', slide_duration: 12, slides: [{ id: 101, type: 'announcement', active: true, title: 'A' }] },
    { id: 'grade-002', name: 'Grade Produção',  slide_duration: 12, slides: [{ id: 202, type: 'announcement', active: true, title: 'B' }] },
  ],
  rodapes: [{ id: 'rodape-001', name: 'Rodapé', ticker_speed: 40, messages: ['oi'] }],
};

function abrirTV(urlStr, { localStorageInicial = null } = {}) {
  const u = new URL(urlStr);
  const store = {};
  if (localStorageInicial) store['tv_content'] = JSON.stringify(localStorageInicial);
  const sandbox = {
    location: {
      protocol: u.protocol, port: u.port, hostname: u.hostname,
      origin: u.origin, search: u.search, href: u.href,
    },
    localStorage: {
      getItem: k => (k in store ? store[k] : null),
      setItem: (k, v) => { store[k] = String(v); },
    },
    URLSearchParams, JSON, console, __out: {},
  };
  vm.createContext(sandbox);
  vm.runInContext(contentBlock + '\n' + serverUrlBlock + EXPORTA, sandbox);
  const { SERVER_URL, resolveContent } = sandbox.__out;
  // Reproduz syncFromServer(): só grava o conteúdo do servidor se houver SERVER_URL
  if (SERVER_URL) store['tv_content'] = JSON.stringify(CONTEUDO_SERVIDOR);
  return { SERVER_URL, conteudo: resolveContent() };
}

let falhas = 0;
function verifica(nome, fn) {
  try { fn(); console.log('  ok   ' + nome); }
  catch (e) { falhas++; console.log('  FALHA ' + nome + '\n        ' + e.message); }
}
function igual(obtido, esperado, oque) {
  if (obtido !== esperado) throw new Error(`${oque}: esperado ${JSON.stringify(esperado)}, obtido ${JSON.stringify(obtido)}`);
}

console.log('\nsincronização do display em diferentes origens\n');

const origens = [
  ['porta 8080 direta',        'http://192.168.0.50:8080/display.html?tv=producao'],
  ['proxy reverso em http',    'http://tv.grupoflexivel.com.br/display.html?tv=producao'],
  ['proxy reverso em https',   'https://tv.grupoflexivel.com.br/display.html?tv=producao'],
  ['porta alternativa',        'http://192.168.0.50:9090/display.html?tv=producao'],
];

for (const [nome, url] of origens) {
  verifica(`${nome}: sincroniza e exibe a grade vinculada`, () => {
    const { SERVER_URL, conteudo } = abrirTV(url);
    if (!SERVER_URL) throw new Error('SERVER_URL veio null — a TV não vai sincronizar com o servidor');
    igual(conteudo.grade?.name, 'Grade Produção', 'grade exibida');
    igual((conteudo.slides || []).map(s => s.id).join(','), '202', 'slides exibidos');
  });
}

verifica('file:// (sem servidor) continua em modo local, sem tentar sincronizar', () => {
  const { SERVER_URL } = abrirTV('file:///C:/tv/display.html?tv=producao');
  igual(SERVER_URL, null, 'SERVER_URL em file://');
});

verifica('TV nova atrás de proxy não cai no conteúdo de demonstração', () => {
  const { conteudo } = abrirTV('https://tv.grupoflexivel.com.br/display.html?tv=producao');
  const titulos = (conteudo.slides || []).map(s => s.title).join('|');
  if (/Bem-vindos à TV Corporativa/.test(titulos) || /EPI/.test(titulos)) {
    throw new Error('a TV está exibindo o DEFAULT_CONTENT embutido no código');
  }
});

console.log(falhas ? `\n${falhas} falha(s)\n` : '\ntudo ok\n');
process.exit(falhas ? 1 : 0);
