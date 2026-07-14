// ═══════════════════════════════════════════════════════════
// DATA MODEL
// ═══════════════════════════════════════════════════════════
const DEFAULT = {
  config: { company_name: "GRUPO FLEXÍVEL", slide_duration: 12 },
  tvs: [
    {
      id: "tv-001", slug: "principal", name: "TV Principal",
      description: "Tela principal da empresa",
      grade_id: "grade-001", rodape_id: "rodape-001", active: true
    }
  ],
  grades: [
    {
      id: "grade-001", name: "Grade Principal", slide_duration: 12,
      slides: [
        {id:1,type:"announcement",active:true,icon:"📣",badge:"Comunicado",title:"Bem-vindos à TV Corporativa!",body:"Este sistema foi desenvolvido para manter todos informados sobre os acontecimentos, metas e agenda da empresa. Configure o conteúdo pelo painel de administração.",author:"Equipe de TI"},
        {id:3,type:"announcement",active:true,icon:"🏆",badge:"Reconhecimento",title:"Destaque do Mês",body:"Parabéns à equipe de Produção pelo excelente resultado alcançado! Meta superada em 6% graças ao comprometimento de todos.",author:"Diretoria"},
        {id:4,type:"calendar",active:true,title:"Agenda Corporativa",month:"Junho / Julho 2026",events:[
          {day:"23",month:"Jun",title:"Treinamento de Segurança do Trabalho",time:"14:00",local:"Auditório",type:"urgent"},
          {day:"25",month:"Jun",title:"Apresentação de Resultados Q2",time:"16:00",local:"Online / Teams",type:"urgent"},
          {day:"30",month:"Jun",title:"Encerramento do Mês – Checklist",time:"10:00",local:"Todos os setores",type:"normal"},
          {day:"07",month:"Jul",title:"Início do Inventário Anual",time:"08:00",local:"Almoxarifado",type:"normal"}
        ]},
        {id:5,type:"announcement",active:true,icon:"⚠️",badge:"Aviso Importante",title:"Uso Obrigatório de EPI",body:"Reforçamos: o uso correto dos EPIs é obrigatório em todas as áreas de produção. Segurança em primeiro lugar!",author:"SSMA"}
      ]
    }
  ],
  rodapes: [
    {
      id: "rodape-001", name: "Rodapé Padrão", ticker_speed: 40,
      messages: [
        "Bem-vindos ao sistema de TV Corporativa",
        "Acesse o painel de administração para personalizar o conteúdo",
        "Sistema desenvolvido para o Grupo Flexível"
      ]
    }
  ]
};

// ── Migração de formato antigo ──────────────────────────
function migrateData(raw) {
  // Se já é o novo formato, retorna direto
  if (raw.grades && raw.tvs && raw.rodapes) return raw;
  // Migra do formato antigo (slides + ticker diretos)
  console.info('[TV] Migrando dados para novo formato (v2)...');
  const nd = JSON.parse(JSON.stringify(DEFAULT));
  if (raw.slides) nd.grades[0].slides = raw.slides;
  if (raw.ticker) nd.rodapes[0].messages = raw.ticker;
  if (raw.config) nd.config = { ...nd.config, ...raw.config };
  return nd;
}

function load() {
  try {
    const r = localStorage.getItem('tv_content');
    if (r) return migrateData(JSON.parse(r));
  } catch(e) {}
  return JSON.parse(JSON.stringify(DEFAULT));
}
// Salva no servidor central (fonte da verdade) e mantém cópia local como cache offline.
function save(data) {
  localStorage.setItem('tv_content', JSON.stringify(data)); // cache local
  fetch('/api/content', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  }).then(r => {
    if (r.status === 401) { location.href = '/login?next=/admin'; return; }
    if (!r.ok) throw new Error('HTTP ' + r.status);
  }).catch(() => {
    toast && toast('⚠️ Sem conexão com o servidor — alterações salvas apenas localmente.');
  });
}

// Busca o conteúdo central do servidor; cai para cache/local em caso de falha.
async function loadFromServer() {
  try {
    const r = await fetch('/api/content', { cache: 'no-store' });
    if (r.status === 401) { location.href = '/login?next=/admin'; return null; }
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return migrateData(await r.json());
  } catch (e) {
    return load(); // fallback: cache local ou DEFAULT
  }
}

let DATA = load();

// Garante IDs únicos entre todas as grades
function nextSlideId() {
  const all = DATA.grades.flatMap(g => g.slides || []);
  return (Math.max(...all.map(s => s.id || 0), 0) + 1);
}
function nextEntityId(arr) {
  return (Math.max(...arr.map(x => parseInt(x.id?.replace(/\D/g,'') || 0) || 0), 0) + 1);
}

// Grade ativa (para edição de conteúdo)
let activeGradeId = DATA.grades[0]?.id || 'grade-001';

function getActiveGrade() {
  return DATA.grades.find(g => g.id === activeGradeId) || DATA.grades[0];
}
function activeSlides() { return getActiveGrade()?.slides || []; }
function setActiveSlides(slides) { getActiveGrade().slides = slides; }

function switchActiveGrade(gradeId) {
  activeGradeId = gradeId;
  renderAll();
  updateGradePill();
}

function updateGradePill() {
  const g = getActiveGrade();
  const pill = document.getElementById('sidebar-grade-pill');
  const nameEl = document.getElementById('sidebar-grade-name');
  if (g) { pill.style.display='block'; nameEl.textContent = g.name; }
  else    { pill.style.display='none'; }
  // update grade context bars
  ['ann','kpi','cal','media','gallery','tl'].forEach(key => {
    const el = document.getElementById(`ctx-grade-name-${key}`);
    if (el) el.textContent = g?.name || '–';
  });
  // update grade selectors in context bars
  document.querySelectorAll('.grade-ctx-bar select').forEach(sel => {
    sel.innerHTML = DATA.grades.map(g => `<option value="${g.id}" ${g.id===activeGradeId?'selected':''}>${g.name}</option>`).join('');
  });
}

// ═══════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════
const CONTENT_PANELS = ['announcements','calendar','media','gallery','timeline'];
const PANEL_TITLES = {
  dashboard:'Dashboard', tvs:'TVs', grades:'Grades de Programação',
  announcements:'Avisos', calendar:'Agenda',
  media:'Mídia', gallery:'Galeria', timeline:'Grade de Programação',
  biblioteca:'Biblioteca de Arquivos', rodapes:'Barra inferior',
  users:'Usuários', profiles:'Perfis de Acesso',
  integrations:'Integrações', smtp:'Servidor de E-mail (SMTP)',
  backup:'Backup do Banco', config:'Configurações'
};

// Permissões do usuário logado (preenchido em loadCurrentUser)
let MY_PERMS = null;          // null = ainda não carregado (não restringe)
const PANEL_AREA = {
  tvs:'grade', grades:'grade', timeline:'grade',
  biblioteca:'biblioteca', rodapes:'rodape',
  users:'sistema', profiles:'sistema', integrations:'sistema', smtp:'sistema',
  backup:'sistema', config:'sistema',
};

function hasPerm(area) { return !MY_PERMS || MY_PERMS.includes(area); }

// Esconde da navegação as áreas sem permissão
function applyPermGating() {
  if (!MY_PERMS) return;
  document.querySelectorAll('nav [data-area]').forEach(el => {
    const area = el.getAttribute('data-area');
    el.style.display = MY_PERMS.includes(area) ? '' : 'none';
  });
}

function showPanel(id, ev) {
  const area = PANEL_AREA[id];
  if (area && !hasPerm(area)) { toast('🔒 Você não tem acesso a esta área.'); return; }
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('panel-' + id)?.classList.add('active');
  if (ev?.currentTarget) ev.currentTarget.classList.add('active');
  document.getElementById('topbar-title').textContent = PANEL_TITLES[id] || id;
  if (id === 'profiles') loadProfiles();
  if (id === 'smtp') loadSmtp();
  if (id === 'users') loadUsers();
  if (id === 'integrations') loadIntegrations();
  // Show grade pill for content panels
  const inContent = CONTENT_PANELS.includes(id);
  document.getElementById('sidebar-grade-pill').style.display = inContent ? 'block' : 'none';
  renderAll();
  updateGradePill();
}

// ═══════════════════════════════════════════════════════════
// RENDER ALL
// ═══════════════════════════════════════════════════════════
function renderAll() {
  renderDashboard();
  renderTvs();
  renderGrades();
  renderAnnouncements();
  renderCalendar();
  renderMedia();
  renderGallery();
  renderTimeline();
  renderRodapes();
  renderConfig();
  updateSlideCountBadge();
}

function updateSlideCountBadge() {
  const total = DATA.grades.reduce((s, g) => s + (g.slides||[]).filter(x => x.active).length, 0);
  document.getElementById('slide-count-badge').textContent =
    `${DATA.tvs.length} TVs · ${DATA.grades.length} grades · ${total} slides ativos`;
}

const typeLabels = {announcement:'Aviso',kpi:'KPI',calendar:'Agenda',media:'Mídia',gallery:'Galeria'};

// ── Dashboard ─────────────────────────────────────────────
function renderDashboard() {
  // TVs
  const tvTbody = document.getElementById('dash-tv-tbody');
  if (tvTbody) {
    tvTbody.innerHTML = DATA.tvs.map(tv => {
      const g = DATA.grades.find(x => x.id === tv.grade_id);
      const r = DATA.rodapes.find(x => x.id === tv.rodape_id);
      const link = `display.html?tv=${tv.slug}`;
      return `<tr>
        <td><b>${tv.name}</b><br><small style="color:var(--dim)">${tv.description||''}</small></td>
        <td>${g?.name||'–'}</td>
        <td>${r?.name||'–'}</td>
        <td><span class="status-dot ${tv.active?'on':'off'}"></span>${tv.active?'Ativa':'Inativa'}</td>
        <td>
          <div class="tv-link-box" style="max-width:280px;">
            <span>${link}</span>
            <button class="tv-link-copy" onclick="copyTvLink('${link}')" title="Copiar link">📋</button>
            <a href="${link}" target="_blank" style="color:var(--blue-light);text-decoration:none;font-size:13px;" title="Abrir TV">↗</a>
          </div>
        </td>
      </tr>`;
    }).join('') || '<tr><td colspan="5" style="color:var(--dim);text-align:center;padding:20px">Nenhuma TV cadastrada</td></tr>';
  }
  // Grades
  const gradeTbody = document.getElementById('dash-grade-tbody');
  if (gradeTbody) {
    gradeTbody.innerHTML = DATA.grades.map(g => {
      const active = (g.slides||[]).filter(s => s.active).length;
      const total  = (g.slides||[]).length;
      return `<tr>
        <td><b>${g.name}</b></td>
        <td>${active} / ${total}</td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="editGradeContent('${g.id}')">✏️ Editar Conteúdo</button>
        </td>
      </tr>`;
    }).join('') || '<tr><td colspan="3" style="color:var(--dim);text-align:center;padding:20px">Nenhuma grade cadastrada</td></tr>';
  }
}

// ── TVs ───────────────────────────────────────────────────
function renderTvs() {
  const tbody = document.getElementById('tv-tbody');
  if (!tbody) return;
  tbody.innerHTML = DATA.tvs.map(tv => {
    const g = DATA.grades.find(x => x.id === tv.grade_id);
    const r = DATA.rodapes.find(x => x.id === tv.rodape_id);
    const link = `display.html?tv=${tv.slug}`;
    return `<tr>
      <td><b>${tv.name}</b><br><small style="color:var(--dim)">${tv.description||''}</small></td>
      <td><code style="font-size:12px;">${tv.slug}</code></td>
      <td>${g?.name||'<span style="color:var(--red)">Sem grade</span>'}</td>
      <td>${r?.name||'<span style="color:var(--red)">Sem rodapé</span>'}</td>
      <td><span class="status-dot ${tv.active?'on':'off'}"></span>${tv.active?'Ativa':'Inativa'}</td>
      <td>
        <div class="tv-link-box">
          <span>${link}</span>
          <button class="tv-link-copy" onclick="copyTvLink('${link}')" title="Copiar">📋</button>
          <a href="${link}" target="_blank" style="color:var(--blue-light);font-size:13px;" title="Abrir">↗</a>
        </div>
      </td>
      <td class="action-row">
        <button class="btn btn-outline btn-sm" onclick="openTvModal('${tv.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="deleteTv('${tv.id}')">🗑️</button>
      </td>
    </tr>`;
  }).join('') || '<tr><td colspan="7" style="color:var(--dim);text-align:center;padding:20px">Nenhuma TV cadastrada. Clique em "+ Nova TV" para começar.</td></tr>';
}

// ── Grades ────────────────────────────────────────────────
function renderGrades() {
  const tbody = document.getElementById('grade-tbody');
  if (!tbody) return;
  tbody.innerHTML = DATA.grades.map(g => {
    const active = (g.slides||[]).filter(s => s.active).length;
    const total  = (g.slides||[]).length;
    const tvCount = DATA.tvs.filter(t => t.grade_id === g.id).length;
    return `<tr>
      <td>
        <b>${g.name}</b>
        ${tvCount > 0 ? `<span style="margin-left:8px;font-size:11px;color:var(--blue-light);">${tvCount} TV(s)</span>` : ''}
      </td>
      <td>${active} ativos / ${total} total</td>
      <td>${g.slide_duration}s</td>
      <td class="action-row">
        <button class="btn btn-primary btn-sm" onclick="editGradeContent('${g.id}')">🎞️ Editar Conteúdo</button>
        <button class="btn btn-outline btn-sm" onclick="openGradeModal('${g.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="deleteGrade('${g.id}')">🗑️</button>
      </td>
    </tr>`;
  }).join('') || '<tr><td colspan="4" style="color:var(--dim);text-align:center;padding:20px">Nenhuma grade cadastrada</td></tr>';
}

// ── Rodapés ───────────────────────────────────────────────
function renderRodapes() {
  const tbody = document.getElementById('rodape-tbody');
  if (!tbody) return;
  tbody.innerHTML = DATA.rodapes.map(r => {
    const tvCount = DATA.tvs.filter(t => t.rodape_id === r.id).length;
    return `<tr>
      <td>
        <b>${r.name}</b>
        ${tvCount > 0 ? `<span style="margin-left:8px;font-size:11px;color:var(--blue-light);">${tvCount} TV(s)</span>` : ''}
      </td>
      <td>${(r.messages||[]).length} mensagem(ns)</td>
      <td>${r.ticker_speed||40}s por ciclo</td>
      <td class="action-row">
        <button class="btn btn-outline btn-sm" onclick="openRodapeModal('${r.id}')">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="deleteRodape('${r.id}')">🗑️</button>
      </td>
    </tr>`;
  }).join('') || '<tr><td colspan="4" style="color:var(--dim);text-align:center;padding:20px">Nenhum rodapé cadastrado</td></tr>';
}

// ── Avisos ────────────────────────────────────────────────
function renderAnnouncements() {
  const anns = activeSlides().filter(s => s.type === 'announcement');
  const tbody = document.getElementById('ann-tbody');
  if (!tbody) return;
  tbody.innerHTML = anns.map(s => `
    <tr>
      <td>${s.icon||''} <b>${s.title}</b></td>
      <td>${s.author||'–'}</td>
      <td><span class="type-badge announcement">${s.badge||'Comunicado'}</span></td>
      <td><span class="status-dot ${s.active?'on':'off'}"></span>${s.active?'Ativo':'Inativo'}</td>
      <td class="action-row">
        <button class="btn btn-outline btn-sm" onclick="editAnn(${s.id})">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="deleteSlide(${s.id})">🗑️</button>
      </td>
    </tr>`).join('') || '<tr><td colspan="5" style="color:var(--dim);text-align:center;padding:20px">Nenhum aviso cadastrado</td></tr>';
}

// ── KPI ──────────────────────────────────────────────────
function renderKpi() {
  const kpiSlide = activeSlides().find(s => s.type === 'kpi');
  const ed = document.getElementById('kpi-editor');
  if (!ed) return;
  if (!kpiSlide) { ed.innerHTML='<p style="color:var(--dim)">Nenhum slide de KPI nesta grade. Adicione um via Gerenciar Slides.</p>'; return; }
  const colors = ['green','blue','amber','red'];
  ed.innerHTML = `
    <div class="form-row" style="margin-bottom:14px;">
      <div class="form-group">
        <label class="form-label">Título do Slide KPI</label>
        <input class="form-input" id="kpi-slide-title" value="${kpiSlide.title}">
      </div>
      <div class="form-group">
        <label class="form-label">Subtítulo</label>
        <input class="form-input" id="kpi-slide-sub" value="${kpiSlide.subtitle||''}">
      </div>
      <div class="form-group">
        <label class="form-label">⏱️ Duração (segundos)</label>
        <input class="form-input" type="number" id="kpi-slide-dur" min="3" max="120"
          value="${kpiSlide.duration||''}" placeholder="Padrão da grade se vazio">
      </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;">
    ${kpiSlide.metrics.map((m,i) => `
      <div class="card" style="padding:16px;margin:0;">
        <div style="display:flex;gap:8px;align-items:center;margin-bottom:10px;">
          <input class="form-input" style="width:50px;font-size:20px;" value="${m.icon}" id="kpi-icon-${i}">
          <input class="form-input" value="${m.label}" id="kpi-label-${i}" placeholder="Label">
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Valor</label>
            <input class="form-input" value="${m.value}" id="kpi-val-${i}">
          </div>
          <div class="form-group">
            <label class="form-label">Unidade</label>
            <input class="form-input" value="${m.unit}" id="kpi-unit-${i}" placeholder="%, un...">
          </div>
        </div>
        <div class="form-row">
          <div class="form-group">
            <label class="form-label">Tendência</label>
            <input class="form-input" value="${m.trend}" id="kpi-trend-${i}">
          </div>
          <div class="form-group">
            <label class="form-label">Direção</label>
            <select class="form-select" id="kpi-dir-${i}">
              <option value="up" ${m.dir==='up'?'selected':''}>↑ Alta</option>
              <option value="down" ${m.dir==='down'?'selected':''}>↓ Baixa</option>
              <option value="neu" ${m.dir==='neu'?'selected':''}>→ Estável</option>
            </select>
          </div>
        </div>
        <div class="form-group">
          <label class="form-label">Cor</label>
          <select class="form-select" id="kpi-color-${i}">
            ${colors.map(c=>`<option value="${c}" ${m.color===c?'selected':''}>${c}</option>`).join('')}
          </select>
        </div>
      </div>`).join('')}
    </div>`;
}

// ── Agenda ────────────────────────────────────────────────
function renderCalendar() {
  const calSlide = activeSlides().find(s => s.type === 'calendar');
  const tbody = document.getElementById('cal-tbody');
  if (!tbody) return;
  if (!calSlide) { tbody.innerHTML='<tr><td colspan="6" style="color:var(--dim);text-align:center">Nenhum slide de agenda nesta grade.</td></tr>'; return; }
  tbody.innerHTML = (calSlide.events||[]).map((e,i) => `
    <tr>
      <td>${e.day} ${e.month}</td>
      <td><b>${e.title}</b></td>
      <td>${e.time}</td>
      <td>${e.local}</td>
      <td><span class="type-badge ${e.type==='urgent'?'kpi':'announcement'}">${e.type==='urgent'?'Destaque':'Normal'}</span></td>
      <td class="action-row">
        <button class="btn btn-outline btn-sm" onclick="editEvent(${i})">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="deleteEvent(${i})">🗑️</button>
      </td>
    </tr>`).join('') || '<tr><td colspan="6" style="color:var(--dim);text-align:center;padding:20px">Nenhum evento cadastrado</td></tr>';
}

// ── Mídia ─────────────────────────────────────────────────
function renderMedia() {
  const medias = activeSlides().filter(s => s.type === 'media');
  const tbody = document.getElementById('media-tbody');
  if (!tbody) return;
  tbody.innerHTML = medias.map(s => `
    <tr>
      <td>${s.caption||'–'}</td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px;color:var(--dim)">${s.url||'–'}</td>
      <td>${(s.url||'').match(/\.(mp4|webm|ogg)$/i)?'🎬 Vídeo':'🖼️ Imagem'}</td>
      <td><span class="status-dot ${s.active?'on':'off'}"></span>${s.active?'Ativo':'Inativo'}</td>
      <td class="action-row">
        <button class="btn btn-outline btn-sm" onclick="editMedia(${s.id})">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="deleteSlide(${s.id})">🗑️</button>
      </td>
    </tr>`).join('') || '<tr><td colspan="5" style="color:var(--dim);text-align:center;padding:20px">Nenhuma mídia cadastrada</td></tr>';
}

// ── Galeria ───────────────────────────────────────────────
function renderGallery() {
  const galleries = activeSlides().filter(s => s.type === 'gallery');
  const tbody = document.getElementById('gallery-tbody');
  if (!tbody) return;
  tbody.innerHTML = galleries.map(s => `
    <tr>
      <td>${s.title||'–'}</td>
      <td>${(s.images||[]).length} imagem(ns)</td>
      <td>${s.image_interval||4}s por imagem</td>
      <td><span class="status-dot ${s.active?'on':'off'}"></span>${s.active?'Ativo':'Inativo'}</td>
      <td class="action-row">
        <button class="btn btn-outline btn-sm" onclick="openGalleryModal(${s.id})">✏️</button>
        <button class="btn btn-danger btn-sm" onclick="deleteSlide(${s.id})">🗑️</button>
      </td>
    </tr>`).join('') || '<tr><td colspan="5" style="color:var(--dim);text-align:center;padding:20px">Nenhuma galeria cadastrada</td></tr>';
}

// ── Config ────────────────────────────────────────────────
function renderConfig() {
  const cfg = DATA.config || {};
  const el1 = document.getElementById('cfg-company');
  const el2 = document.getElementById('cfg-slide-dur');
  const el3 = document.getElementById('cfg-news-block');
  if (el1) el1.value = cfg.company_name||'';
  if (el2) el2.value = cfg.slide_duration||12;
  if (el3) el3.value = cfg.news_blocklist||'';
}

// ═══════════════════════════════════════════════════════════
// TV CRUD
// ═══════════════════════════════════════════════════════════
function autoSlug(name) {
  const slug = name.toLowerCase()
    .normalize('NFD').replace(/[̀-ͯ]/g,'')
    .replace(/[^a-z0-9\s-]/g,'').trim()
    .replace(/\s+/g,'-').replace(/-+/g,'-');
  document.getElementById('tv-slug').value = slug;
  const id = document.getElementById('tv-edit-id').value;
  if (!id && slug) {
    const prev = document.getElementById('tv-link-preview');
    document.getElementById('tv-link-preview-url').textContent = `display.html?tv=${slug}`;
    prev.style.display = 'block';
  }
}

function openTvModal(id=null) {
  document.getElementById('tv-edit-id').value = id||'';
  document.getElementById('tv-modal-title').textContent = id ? 'Editar TV' : 'Nova TV';
  const tv = id ? DATA.tvs.find(x => x.id === id) : null;
  document.getElementById('tv-name').value = tv?.name||'';
  document.getElementById('tv-slug').value = tv?.slug||'';
  document.getElementById('tv-desc').value = tv?.description||'';
  document.getElementById('tv-active-toggle').classList.toggle('on', tv ? !!tv.active : true);
  // Grade select
  document.getElementById('tv-grade-id').innerHTML = DATA.grades.map(g =>
    `<option value="${g.id}" ${g.id===(tv?.grade_id)? 'selected':''}>${g.name}</option>`
  ).join('');
  // Rodapé select
  document.getElementById('tv-rodape-id').innerHTML = DATA.rodapes.map(r =>
    `<option value="${r.id}" ${r.id===(tv?.rodape_id)? 'selected':''}>${r.name}</option>`
  ).join('');
  // Link preview for edit
  const prev = document.getElementById('tv-link-preview');
  if (tv?.slug) {
    document.getElementById('tv-link-preview-url').textContent = `display.html?tv=${tv.slug}`;
    prev.style.display = 'block';
  } else {
    prev.style.display = 'none';
  }
  openModal('modal-tv');
}

function saveTv() {
  const id     = document.getElementById('tv-edit-id').value;
  const name   = document.getElementById('tv-name').value.trim();
  const slug   = document.getElementById('tv-slug').value.trim();
  const active = document.getElementById('tv-active-toggle').classList.contains('on');
  if (!name || !slug) { toast('⚠️ Nome e slug são obrigatórios.'); return; }
  // Check slug uniqueness
  const dup = DATA.tvs.find(t => t.slug === slug && t.id !== id);
  if (dup) { toast('⚠️ Slug já está em uso por outra TV.'); return; }
  const obj = {
    id:       id || `tv-${String(nextEntityId(DATA.tvs)).padStart(3,'0')}`,
    slug, name,
    description: document.getElementById('tv-desc').value.trim(),
    grade_id:    document.getElementById('tv-grade-id').value,
    rodape_id:   document.getElementById('tv-rodape-id').value,
    active,
  };
  if (id) {
    const idx = DATA.tvs.findIndex(t => t.id === id);
    if (idx >= 0) DATA.tvs[idx] = obj;
  } else {
    DATA.tvs.push(obj);
  }
  save(DATA); renderAll(); closeModal('modal-tv'); toast('TV salva!');
}

function deleteTv(id) {
  if (!confirm('Remover esta TV?')) return;
  DATA.tvs = DATA.tvs.filter(t => t.id !== id);
  save(DATA); renderAll(); toast('TV removida');
}

function copyTvLink(link) {
  navigator.clipboard.writeText(window.location.origin + '/' + link)
    .then(() => toast('📋 Link copiado!'))
    .catch(() => {
      // Fallback
      const ta = document.createElement('textarea');
      ta.value = link; document.body.appendChild(ta);
      ta.select(); document.execCommand('copy');
      document.body.removeChild(ta);
      toast('📋 Link copiado!');
    });
}

// ═══════════════════════════════════════════════════════════
// GRADE CRUD
// ═══════════════════════════════════════════════════════════
function openGradeModal(id=null) {
  document.getElementById('grade-edit-id').value = id||'';
  document.getElementById('grade-modal-title').textContent = id ? 'Editar Grade' : 'Nova Grade';
  const g = id ? DATA.grades.find(x => x.id === id) : null;
  document.getElementById('grade-name').value = g?.name||'';
  document.getElementById('grade-slide-dur').value = g?.slide_duration||12;
  openModal('modal-grade');
}

function saveGrade() {
  const id   = document.getElementById('grade-edit-id').value;
  const name = document.getElementById('grade-name').value.trim();
  if (!name) { toast('⚠️ Nome da grade é obrigatório.'); return; }
  const dur = parseInt(document.getElementById('grade-slide-dur').value) || 12;
  if (id) {
    const g = DATA.grades.find(x => x.id === id);
    if (g) { g.name = name; g.slide_duration = dur; }
  } else {
    const newId = `grade-${String(nextEntityId(DATA.grades)).padStart(3,'0')}`;
    DATA.grades.push({ id: newId, name, slide_duration: dur, slides: [] });
  }
  save(DATA); renderAll(); closeModal('modal-grade'); toast('Grade salva!');
}

function deleteGrade(id) {
  if (DATA.grades.length === 1) { toast('⚠️ Você precisa de ao menos uma grade.'); return; }
  const tvsUsing = DATA.tvs.filter(t => t.grade_id === id);
  if (tvsUsing.length > 0) {
    if (!confirm(`Esta grade está sendo usada por ${tvsUsing.length} TV(s). Remover mesmo assim?`)) return;
  }
  if (!confirm('Remover esta grade e todos os seus slides?')) return;
  DATA.grades = DATA.grades.filter(g => g.id !== id);
  if (activeGradeId === id) activeGradeId = DATA.grades[0]?.id;
  save(DATA); renderAll(); toast('Grade removida');
}

function editGradeContent(gradeId) {
  activeGradeId = gradeId;
  showPanel('announcements', null);
  // Activate the nav button
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => {
    if (b.textContent.includes('Avisos')) b.classList.add('active');
  });
}

// ═══════════════════════════════════════════════════════════
// RODAPÉ CRUD
// ═══════════════════════════════════════════════════════════
// ── Construtor da barra (rodapé) ──────────────────────────
const RODAPE_WIDGET_LABELS = {
  logo:'🏷️ Logo', datetime:'🕐 Data e hora', ticker:'📢 Mensagens (ticker)', currency:'💱 Dólar e Euro (USD/BRL, EUR/BRL)', weather:'🌦️ Previsão do tempo'
};
const RODAPE_TIMEZONES = [
  ['America/Sao_Paulo','Brasília (GMT-3)'],
  ['America/Manaus','Manaus (GMT-4)'],
  ['America/Rio_Branco','Rio Branco (GMT-5)'],
  ['America/Noronha','F. de Noronha (GMT-2)'],
  ['America/New_York','Nova York (GMT-5/-4)'],
  ['Europe/Lisbon','Lisboa (GMT+0/+1)'],
  ['UTC','UTC']
];
const RODAPE_DEFAULT_WIDGETS = [
  {type:'logo',enabled:true,position:'left',transparent:true},
  {type:'ticker',enabled:true,position:'center'},
  {type:'datetime',enabled:true,position:'right',timezone:'America/Sao_Paulo'},
  {type:'currency',enabled:true,position:'right'},
  {type:'weather',enabled:false,position:'right',city:'São Paulo'}
];

// Converte "#rrggbb", "#rgb" ou "rgb(r,g,b)" para "#rrggbb" (para o seletor de cor)
function colorToHex(str) {
  if (!str) return null;
  str = str.trim();
  let m = str.match(/^#([0-9a-f]{3})$/i);
  if (m) return '#' + m[1].split('').map(c => c + c).join('').toLowerCase();
  if (/^#[0-9a-f]{6}$/i.test(str)) return str.toLowerCase();
  m = str.match(/rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)/i);
  if (m) {
    const h = n => Math.max(0, Math.min(255, +n)).toString(16).padStart(2, '0');
    return '#' + h(m[1]) + h(m[2]) + h(m[3]);
  }
  return null;
}

function syncRodapeColor(which, source) {
  const picker = document.getElementById('rodape-' + which);
  const text   = document.getElementById('rodape-' + which + '-hex');
  if (source === 'picker') {
    text.value = picker.value;
  } else {
    const hex = colorToHex(text.value);
    if (hex) picker.value = hex;
  }
}

function renderRodapeWidgets(widgets) {
  const box = document.getElementById('rodape-widgets');
  box.innerHTML = '';
  // Garante que todos os tipos apareçam (na ordem salva; o que faltar vai ao fim)
  const order = widgets.slice();
  Object.keys(RODAPE_WIDGET_LABELS).forEach(t => {
    if (!order.find(w => w.type === t)) order.push({ type: t, enabled: false });
  });
  order.forEach(w => box.appendChild(buildRodapeWidgetRow(w)));
}

function buildRodapeWidgetRow(w) {
  const row = document.createElement('div');
  row.className = 'rw-row';
  row.dataset.type = w.type;
  row.style.cssText = 'display:flex;align-items:center;gap:10px;flex-wrap:wrap;background:var(--gray);border:1px solid #e0e7f0;border-radius:8px;padding:8px 10px;';
  let extra = '';
  if (w.type === 'datetime') {
    const opts = RODAPE_TIMEZONES.map(([v, l]) =>
      `<option value="${v}" ${v === (w.timezone || 'America/Sao_Paulo') ? 'selected' : ''}>${l}</option>`).join('');
    extra = `<select class="rw-tz form-select" style="width:auto;font-size:12px;" title="Fuso horário">${opts}</select>`;
  } else if (w.type === 'weather') {
    const located = !!(w.lat && w.lon);
    extra = `
      <input class="rw-city form-input" style="width:130px;font-size:12px;" placeholder="Cidade" value="${(w.city || '').replace(/"/g, '&quot;')}">
      <button type="button" class="btn btn-outline btn-sm rw-geo-btn" style="font-size:12px;" onclick="geocodeRodapeCity(this)">🔍 Localizar</button>
      <select class="rw-geo-results form-select" style="display:none;font-size:12px;max-width:240px;" onchange="pickRodapeCity(this)"></select>
      <input type="hidden" class="rw-lat" value="${w.lat || ''}">
      <input type="hidden" class="rw-lon" value="${w.lon || ''}">
      <span class="rw-geo-status" style="font-size:11px;color:${located ? 'var(--green)' : 'var(--dim)'};">${located ? '✓ ' + (w.city || 'local definido') : 'digite e clique em Localizar'}</span>`;
  } else if (w.type === 'logo') {
    const hasUrl = !!(w.url);
    extra = `
      <input type="file" class="rw-logo-file" accept=".png,.jpg,.jpeg" style="display:none" onchange="uploadRodapeLogo(this)">
      <input type="hidden" class="rw-logo-url" value="${(w.url || '').replace(/"/g, '&quot;')}">
      <button type="button" class="btn btn-outline btn-sm rw-logo-btn" style="font-size:12px;" onclick="this.parentElement.querySelector('.rw-logo-file').click()">📁 ${hasUrl ? 'Trocar logo' : 'Enviar logo'}</button>
      <label style="display:flex;align-items:center;gap:5px;font-size:12px;cursor:pointer;" title="Sem fundo branco atrás do logo">
        <input type="checkbox" class="rw-logo-transparent" ${w.transparent !== false ? 'checked' : ''}> Fundo transparente
      </label>`;
  }
  const pos = w.position || 'center';
  const posSel = `<select class="rw-pos form-select" style="width:auto;font-size:12px;" title="Posição na barra">
      <option value="left" ${pos === 'left' ? 'selected' : ''}>⬅ Esquerda</option>
      <option value="center" ${pos === 'center' ? 'selected' : ''}>▦ Centro</option>
      <option value="right" ${pos === 'right' ? 'selected' : ''}>➡ Direita</option>
    </select>`;
  row.innerHTML = `
    <div style="display:flex;flex-direction:column;gap:2px;">
      <button type="button" class="btn btn-outline btn-sm" style="padding:0 7px;line-height:1.4;" onclick="moveRodapeWidget(this,-1)">↑</button>
      <button type="button" class="btn btn-outline btn-sm" style="padding:0 7px;line-height:1.4;" onclick="moveRodapeWidget(this,1)">↓</button>
    </div>
    <label style="display:flex;align-items:center;gap:8px;flex:1;cursor:pointer;">
      <input type="checkbox" class="rw-enabled" ${w.enabled !== false ? 'checked' : ''}>
      <span>${RODAPE_WIDGET_LABELS[w.type] || w.type}</span>
    </label>
    ${extra}
    ${posSel}`;
  return row;
}

function moveRodapeWidget(btn, dir) {
  const row = btn.closest('.rw-row');
  const box = row.parentElement;
  if (dir < 0 && row.previousElementSibling) box.insertBefore(row, row.previousElementSibling);
  if (dir > 0 && row.nextElementSibling) box.insertBefore(row.nextElementSibling, row);
}

async function geocodeRodapeCity(btn) {
  const row = btn.closest('.rw-row');
  const q = row.querySelector('.rw-city').value.trim();
  const sel = row.querySelector('.rw-geo-results');
  const status = row.querySelector('.rw-geo-status');
  if (!q) { toast('Digite o nome da cidade primeiro.'); return; }
  status.style.color = 'var(--dim)'; status.textContent = 'buscando...';
  try {
    const r = await fetch('/api/geocode?q=' + encodeURIComponent(q));
    if (r.status === 401) { location.href = '/login?next=/admin'; return; }
    const list = await r.json();
    if (!Array.isArray(list) || !list.length) {
      status.textContent = 'nenhuma cidade encontrada'; sel.style.display = 'none'; return;
    }
    sel.innerHTML = '<option value="">— escolha a cidade correta —</option>' + list.map(c => {
      const label = [c.name, c.admin1, c.country].filter(Boolean).join(', ');
      return `<option value="${c.lat}|${c.lon}|${label.replace(/"/g, '&quot;')}">${label}</option>`;
    }).join('');
    sel.style.display = '';
    status.style.color = 'var(--dim)';
    status.textContent = list.length + ' resultado(s) — selecione';
  } catch (e) {
    status.textContent = 'serviço indisponível (servidor sem internet?)';
    sel.style.display = 'none';
  }
}

function pickRodapeCity(sel) {
  if (!sel.value) return;
  const [lat, lon, label] = sel.value.split('|');
  const row = sel.closest('.rw-row');
  row.querySelector('.rw-lat').value = lat;
  row.querySelector('.rw-lon').value = lon;
  row.querySelector('.rw-city').value = label;
  const status = row.querySelector('.rw-geo-status');
  status.style.color = 'var(--green)';
  status.textContent = '✓ ' + label;
  sel.style.display = 'none';
}

async function uploadRodapeLogo(input) {
  const file = input.files && input.files[0];
  if (!file) return;
  const row = input.closest('.rw-row');
  const btn = row.querySelector('.rw-logo-btn');
  if (btn) btn.textContent = '⏳ Enviando...';
  try {
    const url = await uploadToServer(file, null, null);
    row.querySelector('.rw-logo-url').value = url;
    if (btn) btn.textContent = '✅ Logo enviada';
    toast('Logo da barra enviada!');
  } catch (e) {
    if (btn) btn.textContent = '📁 Enviar logo';
    toast('❌ Falha no upload. O servidor está rodando?');
  }
}

function openRodapeModal(id=null) {
  document.getElementById('rodape-edit-id').value = id||'';
  document.getElementById('rodape-modal-title').textContent = id ? 'Editar Barra' : 'Nova Barra';
  const r = id ? DATA.rodapes.find(x => x.id === id) : null;
  document.getElementById('rodape-name').value  = r?.name||'';
  document.getElementById('rodape-speed').value = r?.ticker_speed||40;
  document.getElementById('rodape-height').value = r?.bar_height||56;

  // Cores
  const bg = r?.bg_color || '#14534D';
  const fg = r?.text_color || '#FFFFFF';
  document.getElementById('rodape-bg-hex').value = bg;
  document.getElementById('rodape-bg').value = colorToHex(bg) || '#14534d';
  document.getElementById('rodape-fg-hex').value = fg;
  document.getElementById('rodape-fg').value = colorToHex(fg) || '#ffffff';

  // Widgets
  renderRodapeWidgets(r?.widgets && r.widgets.length ? r.widgets : RODAPE_DEFAULT_WIDGETS);

  // Mensagens
  const list = document.getElementById('rodape-msg-list');
  list.innerHTML = '';
  (r?.messages||[]).forEach((msg, i) => addRodapeMsgRow(msg, i));
  openModal('modal-rodape');
}

function addRodapeMsgRow(msg='', idx=null) {
  const list = document.getElementById('rodape-msg-list');
  const div = document.createElement('div');
  div.style.cssText = 'display:flex;gap:8px;align-items:center;';
  div.innerHTML = `
    <input class="form-input" style="flex:1;" placeholder="Mensagem do rodapé" value="${msg.replace(/"/g,'&quot;')}">
    <button class="btn btn-danger btn-sm" onclick="this.parentElement.remove()">🗑️</button>`;
  list.appendChild(div);
}

function addRodapeMsg() {
  const val = document.getElementById('rodape-msg-new').value.trim();
  if (!val) return;
  addRodapeMsgRow(val);
  document.getElementById('rodape-msg-new').value = '';
}

function saveRodape() {
  const id   = document.getElementById('rodape-edit-id').value;
  const name = document.getElementById('rodape-name').value.trim();
  if (!name) { toast('⚠️ Nome do rodapé é obrigatório.'); return; }
  const speed = parseInt(document.getElementById('rodape-speed').value) || 40;
  const barHeight = Math.min(200, Math.max(40, parseInt(document.getElementById('rodape-height').value) || 56));
  const msgs = Array.from(document.querySelectorAll('#rodape-msg-list input'))
    .map(i => i.value.trim()).filter(Boolean);

  // Cores (prioriza o campo de texto, que aceita hex ou rgb())
  const bg = document.getElementById('rodape-bg-hex').value.trim() || document.getElementById('rodape-bg').value;
  const fg = document.getElementById('rodape-fg-hex').value.trim() || document.getElementById('rodape-fg').value;

  // Widgets na ordem exibida
  const widgets = Array.from(document.querySelectorAll('#rodape-widgets .rw-row')).map(row => {
    const w = { type: row.dataset.type, enabled: row.querySelector('.rw-enabled').checked };
    const pos = row.querySelector('.rw-pos');
    if (pos) w.position = pos.value;
    const tz = row.querySelector('.rw-tz');
    if (tz) w.timezone = tz.value;
    const city = row.querySelector('.rw-city');
    if (city) w.city = city.value.trim();
    const lat = row.querySelector('.rw-lat');
    if (lat && lat.value) w.lat = parseFloat(lat.value);
    const lon = row.querySelector('.rw-lon');
    if (lon && lon.value) w.lon = parseFloat(lon.value);
    const logoUrl = row.querySelector('.rw-logo-url');
    if (logoUrl) w.url = logoUrl.value;
    const transp = row.querySelector('.rw-logo-transparent');
    if (transp) w.transparent = transp.checked;
    return w;
  });

  if (id) {
    const r = DATA.rodapes.find(x => x.id === id);
    if (r) { r.name = name; r.ticker_speed = speed; r.bar_height = barHeight; r.messages = msgs; r.bg_color = bg; r.text_color = fg; r.widgets = widgets; }
  } else {
    const newId = `rodape-${String(nextEntityId(DATA.rodapes)).padStart(3,'0')}`;
    DATA.rodapes.push({ id: newId, name, ticker_speed: speed, bar_height: barHeight, messages: msgs, bg_color: bg, text_color: fg, widgets });
  }
  save(DATA); renderAll(); closeModal('modal-rodape'); toast('Barra salva!');
}

function deleteRodape(id) {
  if (DATA.rodapes.length === 1) { toast('⚠️ Você precisa de ao menos um rodapé.'); return; }
  const tvs = DATA.tvs.filter(t => t.rodape_id === id);
  if (tvs.length > 0) {
    if (!confirm(`Este rodapé está sendo usado por ${tvs.length} TV(s). Remover mesmo assim?`)) return;
  }
  if (!confirm('Remover este rodapé?')) return;
  DATA.rodapes = DATA.rodapes.filter(r => r.id !== id);
  save(DATA); renderAll(); toast('Rodapé removido');
}

// ═══════════════════════════════════════════════════════════
// SLIDE CRUD (opera na grade ativa)
// ═══════════════════════════════════════════════════════════
function toggleSlide(id) {
  const s = activeSlides().find(x => x.id === id);
  if (s) s.active = !s.active;
  save(DATA); renderAll(); toast('Slide ' + (s?.active ? 'ativado' : 'desativado'));
}
function deleteSlide(id) {
  if (!confirm('Remover este slide?')) return;
  getActiveGrade().slides = activeSlides().filter(s => s.id !== id);
  save(DATA); renderAll(); toast('Slide removido');
}
function pushOrUpdateSlide(obj, id) {
  if (id) {
    const idx = activeSlides().findIndex(s => s.id === parseInt(id));
    if (idx >= 0) activeSlides()[idx] = obj;
  } else {
    activeSlides().push(obj);
  }
}

// ── Announcements ─────────────────────────────────────────
function openAnnModal(id=null) {
  document.getElementById('ann-edit-id').value = id||'';
  document.getElementById('ann-modal-title').textContent = id ? 'Editar Aviso' : 'Novo Aviso';
  const s = id ? activeSlides().find(x => x.id === id) : null;
  document.getElementById('ann-title').value    = s?.title||'';
  document.getElementById('ann-badge').value    = s?.badge||'Comunicado';
  document.getElementById('ann-icon').value     = s?.icon||'📣';
  document.getElementById('ann-body').value     = s?.body||'';
  document.getElementById('ann-author').value   = s?.author||'';
  document.getElementById('ann-duration').value = s?.duration||'';
  document.getElementById('ann-active-toggle').classList.toggle('on', s ? !!s.active : true);
  openModal('modal-ann');
}
function editAnn(id) { openAnnModal(id); }
function saveAnnouncement() {
  const id  = document.getElementById('ann-edit-id').value;
  const dur = parseInt(document.getElementById('ann-duration').value) || null;
  const obj = {
    id: id ? parseInt(id) : nextSlideId(),
    type: 'announcement',
    active: document.getElementById('ann-active-toggle').classList.contains('on'),
    title:    document.getElementById('ann-title').value,
    badge:    document.getElementById('ann-badge').value,
    icon:     document.getElementById('ann-icon').value,
    body:     document.getElementById('ann-body').value,
    author:   document.getElementById('ann-author').value,
    duration: dur,
  };
  pushOrUpdateSlide(obj, id);
  save(DATA); renderAll(); closeModal('modal-ann'); toast('Aviso salvo!');
}

// ── KPI ──────────────────────────────────────────────────
function saveKpis() {
  const kpiSlide = activeSlides().find(s => s.type === 'kpi');
  if (!kpiSlide) return;
  kpiSlide.title    = document.getElementById('kpi-slide-title')?.value || kpiSlide.title;
  kpiSlide.subtitle = document.getElementById('kpi-slide-sub')?.value || '';
  kpiSlide.duration = parseInt(document.getElementById('kpi-slide-dur')?.value) || null;
  kpiSlide.metrics.forEach((m, i) => {
    m.icon  = document.getElementById(`kpi-icon-${i}`)?.value || m.icon;
    m.label = document.getElementById(`kpi-label-${i}`)?.value || m.label;
    m.value = document.getElementById(`kpi-val-${i}`)?.value || m.value;
    m.unit  = document.getElementById(`kpi-unit-${i}`)?.value ?? m.unit;
    m.trend = document.getElementById(`kpi-trend-${i}`)?.value || m.trend;
    m.dir   = document.getElementById(`kpi-dir-${i}`)?.value || m.dir;
    m.color = document.getElementById(`kpi-color-${i}`)?.value || m.color;
  });
  save(DATA); renderAll(); toast('Indicadores salvos!');
}

// ── Calendar ──────────────────────────────────────────────
function openEventModal(idx=null) {
  document.getElementById('event-edit-id').value = idx != null ? idx : '';
  document.getElementById('event-modal-title').textContent = idx != null ? 'Editar Evento' : 'Novo Evento';
  const calSlide = activeSlides().find(s => s.type === 'calendar');
  const e = idx != null ? calSlide?.events?.[idx] : null;
  document.getElementById('event-title').value = e?.title||'';
  document.getElementById('event-day').value   = e?.day||'';
  document.getElementById('event-month').value = e?.month||'';
  document.getElementById('event-time').value  = e?.time||'';
  document.getElementById('event-local').value = e?.local||'';
  document.getElementById('event-type').value  = e?.type||'normal';
  openModal('modal-event');
}
function editEvent(idx) { openEventModal(idx); }
function deleteEvent(idx) {
  if (!confirm('Remover este evento?')) return;
  const calSlide = activeSlides().find(s => s.type === 'calendar');
  if (calSlide?.events) calSlide.events.splice(idx, 1);
  save(DATA); renderAll(); toast('Evento removido');
}
function saveEvent() {
  const calSlide = activeSlides().find(s => s.type === 'calendar');
  if (!calSlide) { toast('⚠️ Não há slide de agenda nesta grade.'); return; }
  if (!calSlide.events) calSlide.events = [];
  const idx = document.getElementById('event-edit-id').value;
  const obj = {
    title: document.getElementById('event-title').value,
    day:   document.getElementById('event-day').value,
    month: document.getElementById('event-month').value,
    time:  document.getElementById('event-time').value,
    local: document.getElementById('event-local').value,
    type:  document.getElementById('event-type').value,
  };
  if (idx !== '') calSlide.events[parseInt(idx)] = obj;
  else calSlide.events.push(obj);
  save(DATA); renderAll(); closeModal('modal-event'); toast('Evento salvo!');
}

// ── Mídia ─────────────────────────────────────────────────
function youtubeId(url) {
  if (!url) return null;
  const m = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/|v\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  return m ? m[1] : null;
}

function detectarMidia(url) {
  const hint    = document.getElementById('media-type-hint');
  const durHint = document.getElementById('media-dur-hint');
  if (!url || !url.trim()) {
    hint.innerHTML = '';
    durHint.textContent = 'Deixe em branco para usar a duração padrão da grade.';
    return;
  }
  const isVideo = /\.(mp4|webm|ogg)(\?.*)?$/i.test(url.trim());
  const isPdf = /\.pdf(\?.*)?$/i.test(url.trim());
  const isYt = !!youtubeId(url.trim());
  if (isVideo) {
    hint.innerHTML = '🎬 <b>Vídeo detectado</b> — o slide avança ao término do vídeo. Duração é opcional.';
    hint.style.color = '#f4b942';
    durHint.textContent = 'Deixe em branco para o vídeo tocar até o fim. Preencha para forçar um tempo máximo.';
  } else if (isYt) {
    hint.innerHTML = '▶️ <b>YouTube detectado</b> — toca em autoplay (mudo). Defina a duração abaixo.';
    hint.style.color = '#e02b2b';
    durHint.textContent = 'Defina por quantos segundos o vídeo do YouTube ficará na tela.';
  } else if (isPdf) {
    hint.innerHTML = '📄 <b>PDF detectado</b> — exibido em tela cheia. Defina a duração em segundos abaixo.';
    hint.style.color = '#e06c75';
    durHint.textContent = 'Deixe em branco para usar a duração padrão da grade.';
  } else {
    hint.innerHTML = '🖼️ <b>Imagem detectada</b> — defina a duração em segundos abaixo.';
    hint.style.color = '#4caf50';
    durHint.textContent = 'Deixe em branco para usar a duração padrão da grade.';
  }
}
function openMediaModal(id=null) {
  document.getElementById('media-edit-id').value = id||'';
  const s = id ? activeSlides().find(x => x.id === id) : null;
  const url = s?.url||'';
  document.getElementById('media-url').value      = url;
  document.getElementById('media-caption').value  = s?.caption||'';
  document.getElementById('media-duration').value = s?.duration||'';
  document.getElementById('media-fit').value      = s?.fit === 'contain' ? 'contain' : 'cover';
  document.getElementById('media-zoom').value     = s?.zoom || 100;
  document.getElementById('media-zoom-num').value = s?.zoom || 100;
  document.getElementById('media-active-toggle').classList.toggle('on', s ? !!s.active : true);
  // Limpa a área de upload (evita a miniatura do item anterior ficar "presa")
  const thumb = document.getElementById('media-upload-thumb');
  if (thumb) { thumb.style.display = 'none'; thumb.src = ''; }
  const nameEl = document.getElementById('media-upload-name');
  if (nameEl) nameEl.textContent = '';
  const prog = document.getElementById('media-upload-prog');
  if (prog) prog.style.display = 'none';
  const fileInput = document.getElementById('media-file-input');
  if (fileInput) fileInput.value = '';
  const libGrid = document.getElementById('media-lib-grid');
  if (libGrid) libGrid.style.display = 'none';
  detectarMidia(url);
  openModal('modal-media');
}
function editMedia(id) { openMediaModal(id); }

let mediaLibPath = '';

function toggleMediaLibrary() {
  const grid = document.getElementById('media-lib-grid');
  if (grid.style.display === 'block') { grid.style.display = 'none'; return; }
  grid.style.display = 'block';
  navMediaLib('');
}

async function navMediaLib(path) {
  mediaLibPath = path || '';
  const grid = document.getElementById('media-lib-grid');
  grid.innerHTML = '<div style="color:var(--dim);font-size:13px;">Carregando...</div>';
  try {
    const r = await fetch('/api/uploads?path=' + encodeURIComponent(mediaLibPath));
    if (r.status === 401) { location.href = '/login?next=/admin'; return; }
    const data = await r.json();
    mediaLibPath = data.path || '';
    const folders = data.folders || [], files = data.files || [];
    let inner = folders.map(f => `
      <div onclick="navMediaLib('${f.path.replace(/'/g, "\\'")}')" title="${f.name}"
           style="cursor:pointer;text-align:center;border:1px solid #e0e7f0;border-radius:8px;padding:6px;background:#fff;">
        <div style="font-size:28px;line-height:48px;">📁</div>
        <div style="font-size:10px;color:var(--dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${f.name.slice(0,14)}</div>
      </div>`).join('');
    inner += files.map(f => {
      const thumb = f.type === 'video' ? `<div style="font-size:28px;line-height:60px;">🎬</div>`
                  : f.type === 'pdf' ? `<div style="font-size:28px;line-height:60px;">📄</div>`
                  : `<img src="${f.url}" style="width:100%;height:60px;object-fit:cover;border-radius:6px;" onerror="this.style.display='none'">`;
      return `<div title="${f.filename}" style="cursor:pointer;text-align:center;border:1px solid #e0e7f0;border-radius:8px;padding:6px;background:#fff;"
                   onclick="pickMediaFromLibrary('${f.url.replace(/'/g, "\\'")}')">
                ${thumb}
                <div style="font-size:10px;color:var(--dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-top:3px;">${f.filename.slice(0, 16)}</div>
              </div>`;
    }).join('');
    if (!folders.length && !files.length)
      inner = '<div style="grid-column:1/-1;color:var(--dim);font-size:13px;">Pasta vazia.</div>';
    grid.innerHTML = `<div id="media-lib-breadcrumb" style="font-size:12px;margin-bottom:8px;color:var(--blue-light);"></div>
      <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(92px,1fr));gap:8px;">${inner}</div>`;
    renderLibBreadcrumb(mediaLibPath, 'media');
  } catch (e) {
    grid.innerHTML = '<div style="color:var(--red);font-size:13px;">Servidor indisponível.</div>';
  }
}

// Atalho "📁 Biblioteca" na montagem da grade: abre o formulário de mídia já com a biblioteca expandida
function quickAddFromLibrary() {
  openMediaModal();
  toggleMediaLibrary();
}

function pickMediaFromLibrary(url) {
  document.getElementById('media-url').value = url;
  detectarMidia(url);
  const thumb = document.getElementById('media-upload-thumb');
  if (thumb && !/\.(mp4|webm|ogg|pdf)$/i.test(url)) { thumb.src = url; thumb.style.display = 'block'; }
  document.getElementById('media-lib-grid').style.display = 'none';
  toast('📁 Arquivo selecionado da biblioteca.');
}
function syncZoom(origem) {
  const range = document.getElementById('media-zoom');
  const num   = document.getElementById('media-zoom-num');
  if (origem === 'range') {
    num.value = range.value;                 // arrastou a barra → atualiza o número
  } else {
    const v = parseInt(num.value);
    if (!isNaN(v)) range.value = Math.max(25, Math.min(300, v));  // digitou → move a barra
  }
}

function saveMedia() {
  const id  = document.getElementById('media-edit-id').value;
  const dur = parseInt(document.getElementById('media-duration').value) || null;
  // Prioriza o campo digitado (clampado 25–300); a barra é o reserva
  let zoom = parseInt(document.getElementById('media-zoom-num').value);
  if (isNaN(zoom)) zoom = parseInt(document.getElementById('media-zoom').value) || 100;
  zoom = Math.max(25, Math.min(300, zoom));
  const obj = {
    id: id ? parseInt(id) : nextSlideId(),
    type: 'media',
    active: document.getElementById('media-active-toggle').classList.contains('on'),
    url:      document.getElementById('media-url').value,
    caption:  document.getElementById('media-caption').value,
    duration: dur,
    fit:      document.getElementById('media-fit').value === 'contain' ? 'contain' : 'cover',
    zoom:     zoom === 100 ? null : zoom,   // só grava se diferente do padrão
  };
  pushOrUpdateSlide(obj, id);
  save(DATA); renderAll(); closeModal('modal-media'); toast('Mídia salva!');
}

// ── Notícias ──────────────────────────────────────────────
const NEWS_LABELS = {
  TOP:'Principais', NATION:'Brasil', WORLD:'Mundo', BUSINESS:'Economia',
  TECHNOLOGY:'Tecnologia', SPORTS:'Esportes', SCIENCE:'Ciência', HEALTH:'Saúde', ENTERTAINMENT:'Entretenimento'
};
function openNewsModal(id=null) {
  document.getElementById('news-edit-id').value = id||'';
  const s = id ? activeSlides().find(x => x.id === id) : null;
  document.getElementById('news-category').value = s?.category || 'TOP';
  document.getElementById('news-count').value    = s?.count || 6;
  document.getElementById('news-duration').value = s?.duration || '';
  document.getElementById('news-active-toggle').classList.toggle('on', s ? !!s.active : true);
  document.getElementById('news-modal-title').textContent = id ? 'Editar Notícias' : 'Notícias';
  openModal('modal-news');
}
function saveNews() {
  const id  = document.getElementById('news-edit-id').value;
  const cat = document.getElementById('news-category').value;
  const obj = {
    id: id ? parseInt(id) : nextSlideId(),
    type: 'news',
    active: document.getElementById('news-active-toggle').classList.contains('on'),
    category: cat,
    label: NEWS_LABELS[cat] || 'Notícias',
    count: parseInt(document.getElementById('news-count').value) || 6,
    duration: parseInt(document.getElementById('news-duration').value) || null,
  };
  pushOrUpdateSlide(obj, id);
  save(DATA); renderAll(); closeModal('modal-news'); toast('Notícias salvas!');
}

// ── Página da Web (URL incorporada) ───────────────────────
function openCaptureModal(id=null) {
  document.getElementById('capture-edit-id').value = id||'';
  const s = id ? activeSlides().find(x => x.id === id) : null;
  document.getElementById('capture-url').value      = s?.url || '';
  document.getElementById('capture-duration').value = s?.duration || '';
  document.getElementById('capture-zoom').value     = s?.zoom || 80;
  document.getElementById('capture-active-toggle').classList.toggle('on', s ? !!s.active : true);
  document.getElementById('capture-modal-title').textContent = id ? 'Editar Página (URL)' : 'Página da Web (URL)';
  openModal('modal-capture');
}

function saveCapture() {
  const id = document.getElementById('capture-edit-id').value;
  const url = document.getElementById('capture-url').value.trim();
  if (!/^https?:\/\//i.test(url)) { toast('❌ Informe uma URL começando com http:// ou https://'); return; }
  const obj = {
    id: id ? parseInt(id) : nextSlideId(),
    type: 'urlshot',
    active: document.getElementById('capture-active-toggle').classList.contains('on'),
    url,
    zoom: parseInt(document.getElementById('capture-zoom').value) || 80,
    duration: parseInt(document.getElementById('capture-duration').value) || null,
  };
  pushOrUpdateSlide(obj, id);
  save(DATA); renderAll(); closeModal('modal-capture'); toast('Página salva!');
}

// ── Integrações (login automático) ────────────────────────
let _grafana = null;

async function loadIntegrations() {
  const st = document.getElementById('grafana-status');
  if (!st) return;
  try {
    const r = await fetch('/api/integrations');
    if (r.status === 401) { location.href = '/login?next=/admin'; return; }
    const list = await r.json();
    _grafana = (Array.isArray(list) ? list : []).find(i => i.type === 'grafana' || i.id === 'grafana') || null;
    if (!_grafana) { st.textContent = 'não configurado'; st.style.color = 'var(--dim)'; return; }
    const s = _grafana.status || 'parado';
    const ok = s === 'ok';
    const cred = _grafana.has_password ? 'credenciais definidas' : 'sem credenciais — clique em 🔑 Credenciais';
    st.textContent = `${ok ? '🟢 ativo' : (s.startsWith('erro') ? '🔴 ' + s : '⚪ ' + s)} · ${cred}`;
    st.style.color = ok ? 'var(--green)' : (s.startsWith('erro') ? 'var(--red)' : 'var(--dim)');
  } catch (e) {
    st.textContent = '⚠️ servidor indisponível — reconstrua a imagem (docker compose up -d --build)';
    st.style.color = 'var(--red)';
  }
}

function openGrafanaModal() {
  document.getElementById('grafana-user').value = _grafana?.username || '';
  document.getElementById('grafana-pass').value = '';
  document.getElementById('grafana-interval').value = _grafana?.interval || 20;
  openModal('modal-grafana');
}

async function saveGrafanaCreds() {
  const body = {
    username: document.getElementById('grafana-user').value.trim(),
    interval: parseInt(document.getElementById('grafana-interval').value) || 20,
  };
  const pass = document.getElementById('grafana-pass').value;
  if (pass) body.password = pass;
  try {
    const r = await fetch('/api/integrations/grafana', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    if (!r.ok) { const d = await r.json(); toast('❌ ' + (d.error || 'Erro')); return; }
    closeModal('modal-grafana');
    toast('Credenciais salvas! O servidor está fazendo login...');
    setTimeout(loadIntegrations, 2000);
  } catch (e) { toast('❌ Sem conexão (o backend foi reconstruído?).'); }
}

// Adiciona o Grafana como slide na grade (direto, sem tempo fixo)
function addGrafanaSlide() {
  const obj = { id: nextSlideId(), type: 'integration', active: true,
                integration_id: 'grafana', name: 'Grafana', duration: null };
  pushOrUpdateSlide(obj, null);
  save(DATA); renderAll(); toast('📊 Grafana adicionado à grade!');
}

function openIntegrationModal(id=null) {
  const i = id ? _integrations.find(x => x.id === id) : null;
  document.getElementById('integration-edit-id').value = id || '';
  document.getElementById('integration-name').value = i?.name || '';
  document.getElementById('integration-type').value = i?.type || 'grafana';
  document.getElementById('integration-url').value = i?.url || '';
  document.getElementById('integration-user').value = i?.username || '';
  document.getElementById('integration-pass').value = '';
  document.getElementById('integration-interval').value = i?.interval || 20;
  document.getElementById('integration-modal-title').textContent = id ? 'Editar Integração' : 'Nova Integração';
  openModal('modal-integration');
}

async function saveIntegration() {
  const id = document.getElementById('integration-edit-id').value;
  const body = {
    name: document.getElementById('integration-name').value.trim(),
    type: document.getElementById('integration-type').value,
    url: document.getElementById('integration-url').value.trim(),
    username: document.getElementById('integration-user').value,
    interval: parseInt(document.getElementById('integration-interval').value) || 20,
  };
  const pass = document.getElementById('integration-pass').value;
  if (pass) body.password = pass;
  if (!body.name || !/^https?:\/\//i.test(body.url)) { toast('❌ Informe nome e URL (http/https).'); return; }
  try {
    const r = await fetch('/api/integrations' + (id ? '/' + id : ''), {
      method: id ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    const d = await r.json();
    if (!r.ok) { toast('❌ ' + (d.error || 'Erro')); return; }
    closeModal('modal-integration'); toast('Integração salva!'); loadIntegrations();
    // Se o seletor "Adicionar à grade" estiver aberto, atualiza e já seleciona a nova
    const picker = document.getElementById('modal-intgslide');
    if (picker && picker.classList.contains('open')) _fillIntgSelect(d.id);
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

async function deleteIntegration(id) {
  if (!confirm('Excluir esta integração?')) return;
  try {
    const r = await fetch('/api/integrations/' + id, { method: 'DELETE' });
    if (!r.ok) { toast('❌ Erro ao excluir'); return; }
    toast('🗑️ Integração removida.'); loadIntegrations();
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

// Adicionar uma integração como slide na grade
async function _fillIntgSelect(selectedId) {
  const sel = document.getElementById('intgslide-select');
  if (!sel) return;
  sel.innerHTML = '<option value="">Carregando...</option>';
  try {
    const r = await fetch('/api/integrations');
    if (r.status === 401) { location.href = '/login?next=/admin'; return; }
    const list = await r.json();
    sel.innerHTML = (Array.isArray(list) && list.length)
      ? list.map(i => `<option value="${i.id}">${i.name}</option>`).join('')
      : '<option value="">— nenhuma cadastrada —</option>';
    if (selectedId) sel.value = selectedId;
  } catch (e) { sel.innerHTML = '<option value="">erro ao carregar</option>'; }
}

async function openIntgSlideModal(id=null) {
  const s = id ? activeSlides().find(x => x.id === id) : null;
  await _fillIntgSelect(s?.integration_id);
  document.getElementById('intgslide-edit-id').value = id || '';
  document.getElementById('intgslide-active-toggle').classList.toggle('on', s ? !!s.active : true);
  openModal('modal-intgslide');
}

function saveIntgSlide() {
  const id = document.getElementById('intgslide-edit-id').value;
  const sel = document.getElementById('intgslide-select');
  const intgId = sel.value;
  if (!intgId) { toast('⚠️ Cadastre uma integração em Sistema → 🔌 Integrações primeiro.'); return; }
  const name = sel.options[sel.selectedIndex]?.text || 'Integração';
  const obj = {
    id: id ? parseInt(id) : nextSlideId(),
    type: 'integration',
    active: document.getElementById('intgslide-active-toggle').classList.contains('on'),
    integration_id: intgId,
    name,
    duration: null,   // sem tempo fixo — usa o padrão da grade
  };
  pushOrUpdateSlide(obj, id);
  save(DATA); renderAll(); closeModal('modal-intgslide'); toast('Integração adicionada à grade!');
}

// ── Galeria ───────────────────────────────────────────────
function addGalleryImageRow(url='', caption='') {
  const list = document.getElementById('gallery-images-list');
  const idx = list.children.length;
  const row = document.createElement('div');
  row.style.cssText = 'display:flex;gap:8px;align-items:center;margin-bottom:4px;';
  row.innerHTML = `
    <input class="form-input" style="flex:2;" placeholder="URL da imagem" value="${url.replace(/"/g,'&quot;')}" oninput="">
    <input class="form-input" style="flex:1;" placeholder="Legenda (opcional)" value="${caption.replace(/"/g,'&quot;')}">
    <label class="btn btn-outline btn-sm" title="Enviar arquivo" style="cursor:pointer;padding:6px 10px;">
      📁<input type="file" accept=".png,.jpg,.jpeg" style="display:none;" onchange="uploadGalleryRowFile(this)">
    </label>
    <button class="btn btn-danger btn-sm" onclick="this.closest('div').remove()" title="Remover">🗑️</button>`;
  list.appendChild(row);
}
function openGalleryModal(id=null) {
  document.getElementById('gallery-edit-id').value = id||'';
  const s = id ? activeSlides().find(x => x.id === id) : null;
  document.getElementById('gallery-title').value    = s?.title||'';
  document.getElementById('gallery-interval').value = s?.image_interval||4;
  document.getElementById('gallery-duration').value = s?.duration||'';
  document.getElementById('gallery-active-toggle').classList.toggle('on', s ? !!s.active : true);
  const list = document.getElementById('gallery-images-list');
  list.innerHTML = '';
  (s?.images||[]).forEach(img => addGalleryImageRow(img.url, img.caption||''));
  if (!s?.images?.length) addGalleryImageRow();
  openModal('modal-gallery');
}
function saveGallery() {
  const id       = document.getElementById('gallery-edit-id').value;
  const dur      = parseInt(document.getElementById('gallery-duration').value) || null;
  const interval = parseInt(document.getElementById('gallery-interval').value) || 4;
  const rows     = document.querySelectorAll('#gallery-images-list > div');
  const images   = [];
  rows.forEach(row => {
    const inputs = row.querySelectorAll('input');
    const url    = inputs[0]?.value.trim();
    if (url) images.push({ url, caption: inputs[1]?.value.trim()||'' });
  });
  if (!images.length) { toast('⚠️ Adicione ao menos uma imagem.'); return; }
  const obj = {
    id: id ? parseInt(id) : nextSlideId(),
    type: 'gallery',
    active: document.getElementById('gallery-active-toggle').classList.contains('on'),
    title:          document.getElementById('gallery-title').value.trim(),
    image_interval: interval, duration: dur, images,
  };
  pushOrUpdateSlide(obj, id);
  save(DATA); renderAll(); closeModal('modal-gallery'); toast('Galeria salva!');
}

// ═══════════════════════════════════════════════════════════
// CONFIG & BACKUP
// ═══════════════════════════════════════════════════════════
function saveConfig() {
  DATA.config = DATA.config || {};
  DATA.config.company_name   = document.getElementById('cfg-company').value;
  DATA.config.slide_duration = parseInt(document.getElementById('cfg-slide-dur').value) || 12;
  DATA.config.news_blocklist = document.getElementById('cfg-news-block').value.trim();
  save(DATA); renderAll(); toast('Configurações salvas!');
}
function exportContent() {
  const blob = new Blob([JSON.stringify(DATA, null, 2)], {type:'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'tv_content_backup_' + new Date().toISOString().slice(0,10) + '.json';
  a.click();
}
function importContent(input) {
  const file = input.files[0]; if (!file) return;
  const r = new FileReader();
  r.onload = e => {
    try {
      DATA = migrateData(JSON.parse(e.target.result));
      activeGradeId = DATA.grades[0]?.id;
      save(DATA); renderAll(); toast('Conteúdo importado!');
    } catch { toast('Erro ao importar JSON'); }
  };
  r.readAsText(file);
}
function resetContent() {
  if (!confirm('Redefinir todo o conteúdo para o padrão? Isso apagará suas alterações.')) return;
  DATA = JSON.parse(JSON.stringify(DEFAULT));
  activeGradeId = DATA.grades[0]?.id;
  save(DATA); renderAll(); toast('Conteúdo redefinido');
}
function saveAndNotify() {
  save(DATA); renderAll();
  toast('✅ Publicado! As TVs serão atualizadas.');
}

// ═══════════════════════════════════════════════════════════
// MODAL HELPERS
// ═══════════════════════════════════════════════════════════
function openModal(id)  { document.getElementById(id).classList.add('open'); }
function closeModal(id) { document.getElementById(id).classList.remove('open'); }
document.querySelectorAll('.modal-overlay').forEach(m => {
  m.addEventListener('click', e => { if (e.target === m) m.classList.remove('open'); });
});

// ═══════════════════════════════════════════════════════════
// TOAST
// ═══════════════════════════════════════════════════════════
let toastTimer;
function toast(msg) {
  document.getElementById('toast-msg').textContent = msg;
  const t = document.getElementById('toast');
  t.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove('show'), 3000);
}

// ═══════════════════════════════════════════════════════════
// TIMELINE
// ═══════════════════════════════════════════════════════════
let tlDragId = null, tlDragOverId = null;

function renderTimeline() {
  const slides    = activeSlides();
  const g         = getActiveGrade();
  const defDur    = g?.slide_duration || DATA.config?.slide_duration || 12;
  const barEl     = document.getElementById('tl-bar');
  const cardsEl   = document.getElementById('tl-cards');
  const totalEl   = document.getElementById('tl-total');
  const legendEl  = document.getElementById('tl-legend');
  if (!barEl || !cardsEl) return;

  const labels = {announcement:'Aviso',kpi:'KPI',calendar:'Agenda',media:'Mídia',gallery:'Galeria',news:'Notícias',urlshot:'Página',integration:'Grafana'};
  const durs   = slides.map(s => (s.duration && s.duration > 0) ? s.duration : defDur);
  const total  = durs.reduce((a,b) => a+b, 0) || 1;

  // Visual bar
  barEl.innerHTML = slides.length
    ? slides.map((s,i) => {
        const flex = Math.max((durs[i]/total)*100, 1).toFixed(1);
        return `<div class="tl-seg ${s.type} ${s.active?'':'inactive'}" style="flex:${flex}"
          title="${s.title||labels[s.type]||s.type} – ${durs[i]}s${s.active?'':' (inativo)'}"></div>`;
      }).join('')
    : '<div style="flex:1;display:flex;align-items:center;justify-content:center;font-size:12px;color:#bbb;">Nenhum slide nesta grade</div>';

  // Legend
  const types = [...new Set(slides.map(s => s.type))];
  const legendColors = {announcement:'var(--blue-light)',kpi:'var(--green)',calendar:'var(--accent)',media:'#9c27b0',gallery:'var(--red)'};
  legendEl.innerHTML = types.map(t =>
    `<span><span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:${legendColors[t]||'#ccc'};margin-right:4px;"></span>${labels[t]||t}</span>`
  ).join('');

  // Total duration
  const m = Math.floor(total/60), s2 = total%60;
  totalEl.textContent = slides.length
    ? `Duração total: ${m>0?m+'min ':''}${s2}s  ·  ${slides.filter(s=>s.active).length} ativos de ${slides.length} slides`
    : '';

  // Draggable cards
  cardsEl.innerHTML = slides.length ? '' : '<div style="text-align:center;padding:30px;color:var(--dim);font-size:14px;">Nenhum slide nesta grade. Use os botões acima para adicionar.</div>';

  slides.forEach((s, i) => {
    const title = s.title || (s.type==='media' ? (s.caption||'Mídia') : (labels[s.type]||s.type));
    const card = document.createElement('div');
    card.className = `tl-card${s.active?'':' tl-inactive'}`;
    card.draggable = true;
    card.dataset.id = s.id;
    card.innerHTML = `
      <div class="gp-preview"><span class="gp-num">${i+1}</span>${slidePreview(s)}</div>
      <div class="gp-body">
        <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
          <span class="type-badge ${s.type}">${labels[s.type]||s.type}</span>
          ${scheduleBadge(s)}
        </div>
        <div class="gp-title" title="${title.replace(/"/g,'&quot;')}">${title}</div>
        <div class="gp-dur">⏱
          <input type="number" min="1" max="3600" value="${s.duration||''}" placeholder="${defDur}"
                 onchange="setSlideDuration(${s.id}, this.value)" onmousedown="event.stopPropagation()" title="Tempo de exibição (segundos)"> s
        </div>
        <div class="gp-acts">
          <button class="btn btn-outline btn-sm" onclick="editSlide(${s.id})" title="Editar conteúdo">✏️</button>
          <button class="btn btn-outline btn-sm" onclick="openScheduleModal(${s.id})" title="Agendar exibição (período)">⏰</button>
          <button class="btn btn-outline btn-sm" onclick="tlToggle(${s.id})" title="${s.active?'Desativar':'Ativar'}">${s.active?'👁':'🚫'}</button>
          <button class="btn btn-danger btn-sm" onclick="deleteSlide(${s.id})" title="Remover">🗑️</button>
          <span class="gp-drag" title="Arraste para reordenar">⠿</span>
        </div>
      </div>`;
    card.addEventListener('dragstart', e => {
      tlDragId = s.id;
      setTimeout(() => card.classList.add('dragging'), 0);
      e.dataTransfer.effectAllowed = 'move';
    });
    card.addEventListener('dragend', () => {
      card.classList.remove('dragging');
      document.querySelectorAll('.tl-card').forEach(c => c.classList.remove('drag-over'));
      tlDragId = null; tlDragOverId = null;
    });
    cardsEl.appendChild(card);
  });
}

function slidePreview(s) {
  if (s.type === 'media') {
    const url = s.url || '';
    const yt = youtubeId(url);
    if (/\.(mp4|webm|ogg)(\?|#|$)/i.test(url)) return `<video src="${url}" muted></video><span class="gp-play">🎬 vídeo</span>`;
    if (yt) return `<img src="https://img.youtube.com/vi/${yt}/hqdefault.jpg" alt="" onerror="this.style.display='none'"><span class="gp-play">▶️ YouTube</span>`;
    if (/\.pdf(\?|#|$)/i.test(url)) return `<span class="gp-ico">📄</span>`;
    if (url) return `<img src="${url}" alt="" onerror="this.style.display='none'">`;
    return `<span class="gp-ico">🖼️</span>`;
  }
  if (s.type === 'gallery') {
    const first = (s.images && s.images[0] && s.images[0].url) || '';
    return first ? `<img src="${first}" alt="" onerror="this.style.display='none'">` : `<span class="gp-ico">🗂️</span>`;
  }
  if (s.type === 'announcement') {
    return `<div class="gp-ann" style="background:linear-gradient(135deg,var(--blue-light),var(--blue-mid));">
      <span style="font-size:32px;">${s.icon || '📣'}</span>
      <span style="font-size:10px;opacity:.9;text-transform:uppercase;letter-spacing:1px;">${s.badge || 'Aviso'}</span></div>`;
  }
  if (s.type === 'calendar') {
    return `<div class="gp-ann" style="background:linear-gradient(135deg,#e0a300,#b97e00);">
      <span style="font-size:32px;">📅</span>
      <span style="font-size:10px;">${(s.events||[]).length} evento(s)</span></div>`;
  }
  if (s.type === 'news') {
    return `<div class="gp-ann" style="background:linear-gradient(135deg,#2e5b8a,#16324f);">
      <span style="font-size:32px;">📰</span>
      <span style="font-size:10px;">${s.label || 'Notícias'}</span></div>`;
  }
  if (s.type === 'urlshot') {
    const host = (s.url || 'Página').replace(/^https?:\/\//, '');
    return `<div class="gp-ann" style="background:linear-gradient(135deg,#5a3a8a,#33215c);">
      <span style="font-size:32px;">🌐</span>
      <span style="font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:160px;">${host.slice(0,24)}</span></div>`;
  }
  if (s.type === 'integration') {
    return `<div class="gp-ann" style="background:linear-gradient(135deg,#0f6e64,#0c3b38);">
      <span style="font-size:32px;">🔌</span>
      <span style="font-size:10px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:160px;">${s.name || 'Integração'}</span></div>`;
  }
  return `<span class="gp-ico">🎬</span>`;
}

// ── Agendamento de exibição (período / recorrente) ──────────────────────────
const SCHED_MONTHS = [['Jan',1],['Fev',2],['Mar',3],['Abr',4],['Mai',5],['Jun',6],
                      ['Jul',7],['Ago',8],['Set',9],['Out',10],['Nov',11],['Dez',12]];
const SCHED_WD = [['Dom',0],['Seg',1],['Ter',2],['Qua',3],['Qui',4],['Sex',5],['Sáb',6]];
const _MN_ABBR = ['','Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
const _WD_ABBR = ['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];

function _brDate(ymd){ const p=(ymd||'').split('-'); return p.length===3?`${p[2]}/${p[1]}`:ymd; }

function scheduleBadge(s) {
  const sc = s.schedule;
  if (!sc || !sc.mode || sc.mode === 'always') return '';
  let txt = '';
  if (sc.mode === 'range') {
    txt = `${sc.start?_brDate(sc.start):'…'} – ${sc.end?_brDate(sc.end):'…'}`;
  } else {
    const parts = [];
    if (sc.months && sc.months.length) parts.push(sc.months.slice().sort((a,b)=>a-b).map(m=>_MN_ABBR[m]).join('/'));
    if (sc.dom_from || sc.dom_to) parts.push('dia ' + (sc.dom_from||1) + '–' + (sc.dom_to||31));
    if (sc.weekdays && sc.weekdays.length) parts.push(sc.weekdays.slice().sort((a,b)=>a-b).map(d=>_WD_ABBR[d]).join('/'));
    if (sc.time_from || sc.time_to) parts.push((sc.time_from||'00:00') + '–' + (sc.time_to||'23:59'));
    txt = parts.join(' · ') || 'recorrente';
  }
  return `<span class="type-badge" style="background:#fff3e0;color:#b9842b;" title="Exibição agendada">⏰ ${txt}</span>`;
}

function schedModeChanged() {
  const m = document.getElementById('sched-mode').value;
  document.getElementById('sched-range').style.display = m === 'range' ? '' : 'none';
  document.getElementById('sched-recurring').style.display = m === 'recurring' ? '' : 'none';
}

function _chip(cls, val, label, checked) {
  return `<label style="display:inline-flex;align-items:center;gap:5px;font-size:13px;font-weight:400;background:var(--gray-light,#e8eef5);padding:5px 9px;border-radius:7px;cursor:pointer;">
    <input type="checkbox" class="${cls}" value="${val}" ${checked?'checked':''}> ${label}</label>`;
}

function openScheduleModal(id) {
  const s = activeSlides().find(x => x.id === id);
  if (!s) return;
  const sc = s.schedule || {};
  document.getElementById('sched-slide-id').value = id;
  document.getElementById('sched-mode').value = sc.mode || 'always';
  document.getElementById('sched-start').value = sc.start || '';
  document.getElementById('sched-end').value = sc.end || '';
  document.getElementById('sched-domfrom').value = sc.dom_from || '';
  document.getElementById('sched-domto').value = sc.dom_to || '';
  document.getElementById('sched-timefrom').value = sc.time_from || '';
  document.getElementById('sched-timeto').value = sc.time_to || '';
  document.getElementById('sched-months').innerHTML =
    SCHED_MONTHS.map(([lb,v]) => _chip('sched-month', v, lb, (sc.months||[]).includes(v))).join('');
  document.getElementById('sched-weekdays').innerHTML =
    SCHED_WD.map(([lb,v]) => _chip('sched-wd', v, lb, (sc.weekdays||[]).includes(v))).join('');
  schedModeChanged();
  openModal('modal-schedule');
}

function saveSchedule() {
  const id = parseInt(document.getElementById('sched-slide-id').value);
  const s = activeSlides().find(x => x.id === id);
  if (!s) return;
  const mode = document.getElementById('sched-mode').value;
  if (mode === 'always') {
    delete s.schedule;
  } else if (mode === 'range') {
    const start = document.getElementById('sched-start').value || null;
    const end = document.getElementById('sched-end').value || null;
    if (start && end && end < start) { toast('❌ A data final é antes da inicial.'); return; }
    s.schedule = { mode:'range', start, end };
  } else {
    s.schedule = {
      mode: 'recurring',
      months: [...document.querySelectorAll('.sched-month:checked')].map(c => parseInt(c.value)),
      weekdays: [...document.querySelectorAll('.sched-wd:checked')].map(c => parseInt(c.value)),
      dom_from: parseInt(document.getElementById('sched-domfrom').value) || null,
      dom_to: parseInt(document.getElementById('sched-domto').value) || null,
      time_from: document.getElementById('sched-timefrom').value || null,
      time_to: document.getElementById('sched-timeto').value || null,
    };
  }
  save(DATA);
  renderTimeline();
  closeModal('modal-schedule');
  toast('✅ Agendamento salvo!');
}

function setSlideDuration(id, val) {
  const s = activeSlides().find(x => x.id === id);
  if (!s) return;
  const n = parseInt(val);
  s.duration = (n && n > 0) ? n : null;
  save(DATA);
  renderTimeline();
}

function editSlide(id) {
  const s = activeSlides().find(x => x.id === id);
  if (!s) return;
  if (s.type === 'announcement') openAnnModal(id);
  else if (s.type === 'media') openMediaModal(id);
  else if (s.type === 'gallery') openGalleryModal(id);
  else if (s.type === 'news') openNewsModal(id);
  else if (s.type === 'urlshot') openCaptureModal(id);
  else if (s.type === 'integration') { showPanel('integrations'); toast('Gerencie o Grafana (credenciais) aqui.'); }
  else if (s.type === 'calendar') { showPanel('calendar'); toast('Gerencie os eventos da agenda. Volte em "Montar Grade".'); }
}

function tlDragOver(e) {
  e.preventDefault();
  const card = e.target.closest('.tl-card');
  if (!card || card.dataset.id == tlDragId) return;
  document.querySelectorAll('.tl-card').forEach(c => c.classList.remove('drag-over'));
  card.classList.add('drag-over');
  tlDragOverId = parseInt(card.dataset.id);
}
function tlDragLeave(e) {
  if (!e.currentTarget.contains(e.relatedTarget))
    document.querySelectorAll('.tl-card').forEach(c => c.classList.remove('drag-over'));
}
function tlDrop(e) {
  e.preventDefault();
  if (tlDragId == null || tlDragOverId == null || tlDragId === tlDragOverId) return;
  const slides = activeSlides();
  const fi = slides.findIndex(s => s.id === tlDragId);
  const ti = slides.findIndex(s => s.id === tlDragOverId);
  if (fi < 0 || ti < 0) return;
  const [moved] = slides.splice(fi, 1);
  slides.splice(ti, 0, moved);
  setActiveSlides(slides);
  save(DATA); renderAll(); toast('✅ Ordem atualizada!');
}
function tlMoveUp(id) {
  const slides = activeSlides();
  const i = slides.findIndex(s => s.id === id);
  if (i <= 0) return;
  [slides[i-1], slides[i]] = [slides[i], slides[i-1]];
  setActiveSlides(slides); save(DATA); renderAll(); toast('Slide movido para cima');
}
function tlMoveDown(id) {
  const slides = activeSlides();
  const i = slides.findIndex(s => s.id === id);
  if (i < 0 || i >= slides.length-1) return;
  [slides[i], slides[i+1]] = [slides[i+1], slides[i]];
  setActiveSlides(slides); save(DATA); renderAll(); toast('Slide movido para baixo');
}
function tlToggle(id) {
  const s = activeSlides().find(x => x.id === id);
  if (s) { s.active = !s.active; save(DATA); renderAll(); }
}

// Quick-add from timeline
function quickAdd(type) {
  if (type === 'announcement') openAnnModal();
  else if (type === 'media')   openMediaModal();
  else if (type === 'gallery') openGalleryModal();
  else if (type === 'calendar') openEventModal();
}

// ═══════════════════════════════════════════════════════════
// UPLOAD DE ARQUIVOS
// ═══════════════════════════════════════════════════════════
const SERVER_BASE = (() => {
  if (location.protocol === 'http:' && location.port === '8080') return location.origin;
  if (location.hostname !== '') return location.origin; // any server context
  return null; // file:// mode
})();

// Tipos aceitos para envio: PNG, JPG, JPEG, MP4 e PDF
const ALLOWED_UPLOAD_EXT = ['png', 'jpg', 'jpeg', 'mp4', 'pdf'];
function uploadExt(file) { return (file.name.split('.').pop() || '').toLowerCase(); }
function isAllowedUpload(file) { return ALLOWED_UPLOAD_EXT.includes(uploadExt(file)); }

async function uploadToServer(file, progressBarEl, progressWrapEl, path = '') {
  const form = new FormData();
  form.append('file', file);
  if (path) form.append('path', path);
  if (progressWrapEl) progressWrapEl.style.display = 'block';
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', '/api/upload');
    xhr.upload.onprogress = e => {
      if (progressBarEl && e.lengthComputable)
        progressBarEl.style.width = (e.loaded/e.total*100).toFixed(0) + '%';
    };
    xhr.onload = () => {
      if (progressWrapEl) progressWrapEl.style.display = 'none';
      if (xhr.status === 201) {
        const r = JSON.parse(xhr.responseText);
        resolve(r.url);
      } else {
        reject(new Error('Upload falhou: ' + xhr.status));
      }
    };
    xhr.onerror = () => reject(new Error('Erro de rede no upload'));
    xhr.send(form);
  });
}

// Drag-and-drop helpers para zonas de upload genéricas
function dzOver(e, zoneId) {
  e.preventDefault();
  document.getElementById(zoneId)?.classList.add('dz-over');
}
function dzLeave(zoneId) {
  document.getElementById(zoneId)?.classList.remove('dz-over');
}
function dzDrop(e, target) {
  e.preventDefault();
  dzLeave(target === 'media' ? 'media-upload-zone' : target + '-upload-zone');
  const file = e.dataTransfer.files?.[0];
  if (!file) return;
  if (target === 'media') uploadMediaFile(file);
}

// Upload para o modal de mídia
async function uploadMediaFile(file) {
  if (!file) return;
  if (!isAllowedUpload(file)) { toast('❌ Tipo não permitido. Aceitos: PNG, JPG, JPEG, MP4, PDF.'); return; }
  const nameEl  = document.getElementById('media-upload-name');
  const thumbEl = document.getElementById('media-upload-thumb');
  const progW   = document.getElementById('media-upload-prog');
  const progB   = document.getElementById('media-upload-bar');
  nameEl.textContent = '⏳ Enviando ' + file.name + '...';
  thumbEl.style.display = 'none';
  try {
    const url = await uploadToServer(file, progB, progW);
    document.getElementById('media-url').value = url;
    detectarMidia(url);
    nameEl.textContent = '✅ ' + file.name;
    if (file.type.startsWith('image/')) {
      thumbEl.src = url; thumbEl.style.display = 'block';
    }
    toast('📁 Arquivo enviado!');
  } catch(err) {
    // Fallback: base64 para imagens pequenas
    if (file.type.startsWith('image/') && file.size < 2*1024*1024) {
      const reader = new FileReader();
      reader.onload = e2 => {
        document.getElementById('media-url').value = e2.target.result;
        detectarMidia(e2.target.result);
        thumbEl.src = e2.target.result; thumbEl.style.display = 'block';
        nameEl.textContent = '⚠️ Imagem incorporada (sem servidor)';
      };
      reader.readAsDataURL(file);
    } else {
      nameEl.textContent = '❌ Erro: servidor não disponível. Inicie server.py.';
      toast('❌ Servidor não encontrado. Inicie server.py para upload de arquivos.');
    }
  }
}

// Upload por linha de galeria
async function uploadGalleryRowFile(input) {
  const file = input.files?.[0]; if (!file) return;
  const row   = input.closest('div');
  const urlInput = row.querySelector('input[type=text], input:not([type])');
  const btn   = input.parentElement;
  btn.textContent = '⏳';
  try {
    const url = await uploadToServer(file, null, null);
    if (urlInput) urlInput.value = url;
    btn.textContent = '✅';
    setTimeout(() => { btn.innerHTML = '📁<input type="file" accept=".png,.jpg,.jpeg" style="display:none;" onchange="uploadGalleryRowFile(this)">'; }, 2000);
    toast('Imagem enviada!');
  } catch(err) {
    if (file.type.startsWith('image/') && file.size < 1*1024*1024) {
      const reader = new FileReader();
      reader.onload = e2 => { if (urlInput) urlInput.value = e2.target.result; btn.textContent = '✅'; };
      reader.readAsDataURL(file);
    } else {
      btn.textContent = '❌';
      toast('❌ Servidor não disponível. Inicie server.py.');
    }
  }
}

// ═══════════════════════════════════════════════════════════
// BIBLIOTECA DE ARQUIVOS
// ═══════════════════════════════════════════════════════════
let libPath = '';

function renderLibBreadcrumb(path, scope) {
  const el = document.getElementById(scope === 'media' ? 'media-lib-breadcrumb' : 'lib-breadcrumb');
  if (!el) return;
  const nav = scope === 'media' ? 'navMediaLib' : 'loadLibrary';
  // No painel Biblioteca, os níveis também recebem arquivos arrastados
  const drop = scope === 'lib'
    ? (p) => ` ondragover="libFolderDragOver(event)" ondragleave="libFolderDragLeave(event)" ondrop="libFolderDrop(event,'${p.replace(/'/g, "\\'")}')"`
    : () => '';
  let acc = '', html = `<a href="#" onclick="event.preventDefault();${nav}('')"${drop('')} style="text-decoration:none;font-weight:600;padding:2px 5px;border-radius:5px;">📁 Biblioteca</a>`;
  if (path) path.split('/').forEach(seg => {
    acc = (acc ? acc + '/' : '') + seg;
    html += ` <span style="color:var(--dim)">/</span> <a href="#" onclick="event.preventDefault();${nav}('${acc.replace(/'/g, "\\'")}')"${drop(acc)} style="text-decoration:none;padding:2px 5px;border-radius:5px;">${seg}</a>`;
  });
  el.innerHTML = html;
}

async function loadLibrary(path) {
  if (path !== undefined) libPath = path;
  const grid   = document.getElementById('lib-grid');
  const status = document.getElementById('lib-status');
  if (!grid) return;
  grid.innerHTML = '<div style="color:var(--dim);font-size:13px;grid-column:1/-1;">Carregando...</div>';
  try {
    const r = await fetch('/api/uploads?path=' + encodeURIComponent(libPath));
    if (r.status === 401) { location.href = '/login?next=/admin'; return; }
    if (!r.ok) throw new Error('Servidor indisponível');
    const data = await r.json();
    libPath = data.path || '';
    renderLibBreadcrumb(libPath, 'lib');
    const folders = data.folders || [], files = data.files || [];
    status.textContent = `${folders.length} pasta(s) · ${files.length} arquivo(s)`;
    let html = folders.map(f => `
      <div class="lib-item lib-folder" title="${f.name}" onclick="loadLibrary('${f.path.replace(/'/g, "\\'")}')"
           ondragover="libFolderDragOver(event)" ondragleave="libFolderDragLeave(event)" ondrop="libFolderDrop(event,'${f.path.replace(/'/g, "\\'")}')">
        <span class="lib-icon">📁</span>
        <div class="lib-name">${f.name.slice(0,16)}</div>
        <div style="font-size:10px;color:var(--dim);">${f.count} item(ns)</div>
        <button class="lib-del" title="Excluir pasta" onclick="event.stopPropagation();deleteLibFolder('${f.path.replace(/'/g, "\\'")}')">🗑️</button>
      </div>`).join('');
    html += files.map(f => `
      <div class="lib-item" title="${f.filename} (${f.size_mb}MB) — arraste para uma pasta" draggable="true"
           ondragstart="libDragFile(event,'${f.path.replace(/'/g, "\\'")}')"
           onclick="libSelectFile('${f.url}','${f.type}')">
        ${f.type==='video' ? `<span class="lib-icon">🎬</span>` : f.type==='pdf' ? `<span class="lib-icon">📄</span>` : `<img src="${f.url}" alt="" onerror="this.style.display='none'">`}
        <div class="lib-name">${f.filename.slice(0,16)}</div>
        <div style="font-size:10px;color:var(--dim);">${f.size_mb}MB</div>
        <button class="lib-del" title="Excluir arquivo" onclick="event.stopPropagation();deleteLibFile('${f.path.replace(/'/g, "\\'")}')">🗑️</button>
      </div>`).join('');
    if (!folders.length && !files.length)
      html = '<div style="color:var(--dim);font-size:13px;grid-column:1/-1;">Pasta vazia. Crie uma subpasta ou envie arquivos.</div>';
    grid.innerHTML = html;
  } catch(e) {
    status.textContent = '⚠️ Servidor não disponível.';
    grid.innerHTML = '<div style="color:var(--dim);font-size:13px;grid-column:1/-1;">Sem conexão com o servidor.</div>';
  }
}

async function createLibFolder() {
  const name = prompt('Nome da nova pasta:');
  if (!name || !name.trim()) return;
  try {
    const r = await fetch('/api/library/folder', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: libPath, name: name.trim() })
    });
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Erro ao criar pasta')); return; }
    toast('📁 Pasta criada!');
    loadLibrary();
  } catch(e) { toast('❌ Sem conexão com o servidor.'); }
}

async function deleteLibFolder(path) {
  if (!confirm('Excluir a pasta "' + path + '" e TODO o seu conteúdo?')) return;
  try {
    const r = await fetch('/api/library/folder?path=' + encodeURIComponent(path), { method: 'DELETE' });
    if (!r.ok) { const d = await r.json(); toast('❌ ' + (d.error || 'Erro')); return; }
    toast('🗑️ Pasta excluída.');
    loadLibrary();
  } catch(e) { toast('❌ Sem conexão com o servidor.'); }
}

async function deleteLibFile(path) {
  if (!confirm('Excluir o arquivo "' + path.split('/').pop() + '"?')) return;
  try {
    const r = await fetch('/api/library/' + path.split('/').map(encodeURIComponent).join('/'), { method: 'DELETE' });
    if (!r.ok) { const d = await r.json(); toast('❌ ' + (d.error || 'Erro')); return; }
    toast('🗑️ Arquivo excluído.');
    loadLibrary();
  } catch(e) { toast('❌ Sem conexão com o servidor.'); }
}

function libSelectFile(url, type) {
  document.querySelectorAll('.lib-item').forEach(el => el.classList.remove('selected'));
  event.currentTarget.classList.add('selected');
  toast(`📋 URL copiada: ${url}`);
  navigator.clipboard?.writeText(url).catch(() => {});
}

// ── Mover arquivos entre pastas (arrastar e soltar) ──────
let _libDragFile = null;
function libDragFile(e, path) {
  _libDragFile = path;
  e.dataTransfer.effectAllowed = 'move';
  e.dataTransfer.setData('text/plain', path);
}
function libFolderDragOver(e) { e.preventDefault(); e.currentTarget.classList.add('lib-drop'); }
function libFolderDragLeave(e) { e.currentTarget.classList.remove('lib-drop'); }
function libFolderDrop(e, folderPath) {
  e.preventDefault();
  e.currentTarget.classList.remove('lib-drop');
  const from = _libDragFile || e.dataTransfer.getData('text/plain');
  _libDragFile = null;
  if (from) moveLibFile(from, folderPath);
}
async function moveLibFile(from, to) {
  if (from === to) return;
  try {
    const r = await fetch('/api/library/move', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from, to })
    });
    const d = await r.json();
    if (!r.ok) { toast('❌ ' + (d.error || 'Erro ao mover')); return; }
    toast('✅ Movido para ' + (to || 'Biblioteca') + '.');
    loadLibrary();
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

async function libUploadFiles(files) {
  if (!files?.length) return;
  const prog = document.getElementById('lib-progress');
  const bar  = document.getElementById('lib-progress-bar');
  const status = document.getElementById('lib-status');
  prog.style.display = 'block';
  let done = 0;
  for (const file of files) {
    if (!isAllowedUpload(file)) { toast('❌ ' + file.name + ': tipo não permitido (aceitos: PNG, JPG, JPEG, MP4, PDF).'); continue; }
    status.textContent = `Enviando ${file.name}...`;
    try {
      await uploadToServer(file, bar, null, libPath);   // envia para a pasta atual
      done++;
      bar.style.width = (done/files.length*100) + '%';
    } catch(e) {
      toast('❌ Falha ao enviar ' + file.name);
    }
  }
  prog.style.display = 'none';
  bar.style.width = '0%';
  status.textContent = `✅ ${done} arquivo(s) enviado(s)`;
  loadLibrary();
}
function libDragOver(e) { e.preventDefault(); document.getElementById('lib-upload-zone')?.classList.add('dz-over'); }
function libDragLeave()  { document.getElementById('lib-upload-zone')?.classList.remove('dz-over'); }
function libDropFile(e) {
  e.preventDefault(); libDragLeave();
  libUploadFiles(e.dataTransfer.files);
}

// ═══════════════════════════════════════════════════════════
// SESSÃO: usuário atual, trocar senha e sair
// ═══════════════════════════════════════════════════════════
async function loadCurrentUser() {
  try {
    const r = await fetch('/api/session');
    const s = await r.json();
    if (s.authenticated) {
      const el = document.getElementById('current-user');
      if (el) el.textContent = '👤 ' + (s.name || s.user) + (s.profile_name ? ' · ' + s.profile_name : '');
      MY_PERMS = Array.isArray(s.perms) ? s.perms : null;
      applyPermGating();
    }
  } catch (e) {}
}

async function logout() {
  if (!confirm('Deseja sair do painel?')) return;
  try { await fetch('/api/logout', { method: 'POST' }); } catch (e) {}
  location.href = '/login';
}

function openChangePassword() {
  document.getElementById('cp-current').value = '';
  document.getElementById('cp-new').value = '';
  document.getElementById('cp-confirm').value = '';
  openModal('modal-changepass');
}

async function saveOwnPassword() {
  const current = document.getElementById('cp-current').value;
  const nw = document.getElementById('cp-new').value;
  const confirmPw = document.getElementById('cp-confirm').value;
  if (nw.length < 6) { toast('❌ A nova senha deve ter ao menos 6 caracteres.'); return; }
  if (nw !== confirmPw) { toast('❌ A confirmação não confere.'); return; }
  try {
    const r = await fetch('/api/change-password', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ current_password: current, new_password: nw })
    });
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Erro ao trocar senha')); return; }
    closeModal('modal-changepass');
    toast('✅ Senha alterada com sucesso!');
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

// ═══════════════════════════════════════════════════════════
// USUÁRIOS (logins do painel)
// ═══════════════════════════════════════════════════════════
let _usersCache = [];
let _profilesCache = [];
let _permAreas = { grade:'Montar grade / TVs / grades', biblioteca:'Biblioteca e mídias',
                   rodape:'Barra inferior (rodapé)', sistema:'Usuários, perfis, SMTP e integrações' };

async function loadUsers() {
  const tb = document.getElementById('user-tbody');
  if (!tb) return;
  tb.innerHTML = '<tr><td colspan="5" style="color:var(--dim);">Carregando...</td></tr>';
  try {
    // garante perfis em cache para o select e para a coluna
    if (!_profilesCache.length) await loadProfilesCache();
    const r = await fetch('/api/users');
    if (r.status === 401) { location.href = '/login?next=/admin'; return; }
    if (r.status === 403) { tb.innerHTML = '<tr><td colspan="5" style="color:var(--dim);">Sem permissão.</td></tr>'; return; }
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const users = await r.json();
    _usersCache = users;
    if (!users.length) {
      tb.innerHTML = '<tr><td colspan="5" style="color:var(--dim);">Nenhum usuário.</td></tr>';
      return;
    }
    tb.innerHTML = users.map(u => `
      <tr>
        <td style="font-family:monospace;">${u.username}</td>
        <td>${u.name || ''}</td>
        <td>${u.email || '<span style="color:var(--red);">— sem e-mail —</span>'}</td>
        <td>${u.profile_name || u.profile || ''}</td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="openUserModal('${u.username}')">✏️ Editar</button>
          <button class="btn btn-danger btn-sm" onclick="deleteUser('${u.username}')">🗑️</button>
        </td>
      </tr>`).join('');
  } catch (e) {
    tb.innerHTML = '<tr><td colspan="5" style="color:var(--red);">Erro ao carregar usuários.</td></tr>';
  }
}

function _fillProfileSelect(selectedId) {
  const sel = document.getElementById('user-profile');
  if (!sel) return;
  sel.innerHTML = _profilesCache.map(p =>
    `<option value="${p.id}" ${p.id === selectedId ? 'selected' : ''}>${p.name}</option>`).join('');
}

async function openUserModal(username = '') {
  const isEdit = !!username;
  const u = isEdit ? (_usersCache.find(x => x.username === username) || {}) : {};
  document.getElementById('user-modal-title').textContent = isEdit ? 'Editar Usuário' : 'Novo Usuário';
  document.getElementById('user-edit-username').value = username;
  const userInput = document.getElementById('user-username');
  userInput.value = username;
  userInput.disabled = isEdit;            // login não muda depois de criado
  document.getElementById('user-name').value = u.name || '';
  document.getElementById('user-email').value = u.email || '';
  document.getElementById('user-password').value = '';
  document.getElementById('user-pass-label').textContent = isEdit ? 'Nova senha (vazio = manter)' : 'Senha';
  document.getElementById('user-username-hint').style.display = isEdit ? 'none' : 'block';
  if (!_profilesCache.length) await loadProfilesCache();
  _fillProfileSelect(u.profile || 'administrador');
  openModal('modal-user');
}

async function saveUser() {
  const editUser = document.getElementById('user-edit-username').value;
  const isEdit = !!editUser;
  const username = document.getElementById('user-username').value.trim().toLowerCase();
  const name = document.getElementById('user-name').value.trim();
  const email = document.getElementById('user-email').value.trim().toLowerCase();
  const profile = document.getElementById('user-profile').value;
  const password = document.getElementById('user-password').value;
  const emailOk = /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email);
  if (!isEdit && !emailOk) { toast('❌ Informe um e-mail válido.'); return; }   // e-mail obrigatório só na criação
  if (isEdit && email && !emailOk) { toast('❌ E-mail inválido.'); return; }     // ao editar, valida só se preenchido
  if (!isEdit && password.length < 6) { toast('❌ A senha deve ter ao menos 6 caracteres.'); return; }
  try {
    let r;
    if (isEdit) {
      r = await fetch('/api/users/' + encodeURIComponent(editUser), {
        method: 'PUT', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, profile, password: password || undefined })
      });
    } else {
      r = await fetch('/api/users', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, name, email, profile, password })
      });
    }
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Erro ao salvar')); return; }
    closeModal('modal-user');
    toast('✅ Usuário salvo!');
    loadUsers();
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

async function deleteUser(username) {
  if (!confirm('Remover o usuário "' + username + '"?')) return;
  try {
    const r = await fetch('/api/users/' + encodeURIComponent(username), { method: 'DELETE' });
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Erro ao remover')); return; }
    toast('🗑️ Usuário removido.');
    loadUsers();
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

// ═══════════════════════════════════════════════════════════
// PERFIS DE ACESSO
// ═══════════════════════════════════════════════════════════
async function loadProfilesCache() {
  try {
    const [pr, ar] = await Promise.all([fetch('/api/profiles'), fetch('/api/perm-areas')]);
    if (pr.ok) _profilesCache = await pr.json();
    if (ar.ok) _permAreas = await ar.json();
  } catch (e) {}
}

async function loadProfiles() {
  const tb = document.getElementById('profile-tbody');
  if (!tb) return;
  tb.innerHTML = '<tr><td colspan="4" style="color:var(--dim);">Carregando...</td></tr>';
  await loadProfilesCache();
  if (!_profilesCache.length) {
    tb.innerHTML = '<tr><td colspan="4" style="color:var(--dim);">Nenhum perfil.</td></tr>';
    return;
  }
  tb.innerHTML = _profilesCache.map(p => {
    const areas = (p.perms || []).map(a => _permAreas[a] || a).join(', ') || '<span style="color:var(--dim);">nenhuma</span>';
    const del = p.locked
      ? '<button class="btn btn-danger btn-sm" disabled title="Perfil fixo">🗑️</button>'
      : `<button class="btn btn-danger btn-sm" onclick="deleteProfile('${p.id}')">🗑️</button>`;
    return `
      <tr>
        <td><b>${p.name}</b>${p.locked ? ' 🔒' : ''}</td>
        <td style="font-size:13px;">${areas}</td>
        <td style="text-align:center;">${p.in_use || 0}</td>
        <td>
          <button class="btn btn-outline btn-sm" onclick="openProfileModal('${p.id}')">✏️ Editar</button>
          ${del}
        </td>
      </tr>`;
  }).join('');
}

function openProfileModal(id = '') {
  const isEdit = !!id;
  const p = isEdit ? (_profilesCache.find(x => x.id === id) || {}) : { perms: [] };
  document.getElementById('profile-modal-title').textContent = isEdit ? 'Editar Perfil' : 'Novo Perfil';
  document.getElementById('profile-edit-id').value = id;
  document.getElementById('profile-name').value = p.name || '';
  const locked = !!p.locked;
  document.getElementById('profile-locked-hint').style.display = locked ? 'block' : 'none';
  const box = document.getElementById('profile-perms');
  box.innerHTML = Object.keys(_permAreas).map(a => {
    const checked = locked || (p.perms || []).includes(a) ? 'checked' : '';
    return `<label style="display:flex;align-items:center;gap:8px;font-weight:400;cursor:pointer;">
      <input type="checkbox" class="profile-perm" value="${a}" ${checked} ${locked ? 'disabled' : ''}>
      <span>${_permAreas[a]}</span></label>`;
  }).join('');
  openModal('modal-profile');
}

async function saveProfile() {
  const id = document.getElementById('profile-edit-id').value;
  const isEdit = !!id;
  const name = document.getElementById('profile-name').value.trim();
  if (!name) { toast('❌ Informe o nome do perfil.'); return; }
  const perms = Array.from(document.querySelectorAll('.profile-perm:checked')).map(c => c.value);
  try {
    const r = await fetch(isEdit ? '/api/profiles/' + encodeURIComponent(id) : '/api/profiles', {
      method: isEdit ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, perms })
    });
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Erro ao salvar')); return; }
    closeModal('modal-profile');
    toast('✅ Perfil salvo!');
    loadProfiles();
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

async function deleteProfile(id) {
  if (!confirm('Remover o perfil "' + id + '"?')) return;
  try {
    const r = await fetch('/api/profiles/' + encodeURIComponent(id), { method: 'DELETE' });
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Erro ao remover')); return; }
    toast('🗑️ Perfil removido.');
    loadProfiles();
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

// ═══════════════════════════════════════════════════════════
// SMTP (envio de e-mail)
// ═══════════════════════════════════════════════════════════
async function loadSmtp() {
  const st = document.getElementById('smtp-status');
  try {
    const r = await fetch('/api/smtp');
    if (r.status === 403) { if (st) st.textContent = 'Sem permissão.'; return; }
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const c = await r.json();
    document.getElementById('smtp-host').value = c.host || '';
    document.getElementById('smtp-port').value = c.port || 587;
    document.getElementById('smtp-security').value = c.security || 'starttls';
    document.getElementById('smtp-username').value = c.username || '';
    document.getElementById('smtp-password').value = '';
    document.getElementById('smtp-from-email').value = c.from_email || '';
    document.getElementById('smtp-from-name').value = c.from_name || 'TV Corporativa';
    if (st) {
      st.innerHTML = c.configured
        ? '🟢 Configurado' + (c.has_password ? ' · senha definida' : ' · sem senha')
        : '⚪ Ainda não configurado';
      st.style.color = c.configured ? 'var(--green)' : 'var(--dim)';
    }
  } catch (e) { if (st) { st.textContent = '⚠️ Erro ao carregar.'; st.style.color = 'var(--red)'; } }
}

async function saveSmtp() {
  const body = {
    host: document.getElementById('smtp-host').value.trim(),
    port: parseInt(document.getElementById('smtp-port').value) || 587,
    security: document.getElementById('smtp-security').value,
    username: document.getElementById('smtp-username').value.trim(),
    from_email: document.getElementById('smtp-from-email').value.trim(),
    from_name: document.getElementById('smtp-from-name').value.trim() || 'TV Corporativa',
  };
  const pass = document.getElementById('smtp-password').value;
  if (pass) body.password = pass;
  try {
    const r = await fetch('/api/smtp', {
      method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Erro ao salvar')); return; }
    toast('✅ SMTP salvo!');
    loadSmtp();
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

async function testSmtp() {
  const to = prompt('Enviar e-mail de teste para qual endereço?\n(vazio = seu próprio e-mail)');
  if (to === null) return;
  toast('📨 Enviando teste...');
  try {
    const r = await fetch('/api/smtp/test', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ to: (to || '').trim() })
    });
    const data = await r.json();
    if (!r.ok) { toast('❌ ' + (data.error || 'Falha no teste')); return; }
    toast('✅ E-mail de teste enviado para ' + (data.sent_to || ''));
  } catch (e) { toast('❌ Sem conexão com o servidor.'); }
}

// ═══════════════════════════════════════════════════════════
// BACKUP / RESTAURAÇÃO DO BANCO
// ═══════════════════════════════════════════════════════════
async function downloadBackup() {
  const st = document.getElementById('backup-status');
  st.textContent = 'Gerando backup...'; st.style.color = 'var(--dim)';
  try {
    const r = await fetch('/api/backup');
    if (r.status === 403) { st.textContent = 'Sem permissão.'; st.style.color = 'var(--red)'; return; }
    if (!r.ok) { const d = await r.json().catch(()=>({})); throw new Error(d.error || ('HTTP ' + r.status)); }
    const blob = await r.blob();
    const cd = r.headers.get('Content-Disposition') || '';
    const m = cd.match(/filename="([^"]+)"/);
    const name = m ? m[1] : 'tvcorporativa-backup.dump';
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = name; a.click();
    URL.revokeObjectURL(a.href);
    st.textContent = '✅ Backup baixado.'; st.style.color = 'var(--green)';
  } catch (e) { st.textContent = '❌ ' + e.message; st.style.color = 'var(--red)'; }
}

async function restoreBackup() {
  const inp = document.getElementById('restore-file');
  const st = document.getElementById('restore-status');
  if (!inp.files || !inp.files[0]) { st.textContent = 'Selecione um arquivo.'; st.style.color = 'var(--red)'; return; }
  if (!confirm('Tem certeza? Restaurar vai SUBSTITUIR todos os dados atuais pelo conteúdo do arquivo. Esta ação não pode ser desfeita.')) return;
  st.textContent = 'Restaurando... (pode demorar)'; st.style.color = 'var(--dim)';
  const fd = new FormData(); fd.append('file', inp.files[0]);
  try {
    const r = await fetch('/api/restore', { method: 'POST', body: fd });
    const d = await r.json().catch(()=>({}));
    if (!r.ok) { st.textContent = '❌ ' + (d.error || ('HTTP ' + r.status)); st.style.color = 'var(--red)'; return; }
    st.textContent = '✅ Banco restaurado! Recarregando...'; st.style.color = 'var(--green)';
    setTimeout(() => location.reload(), 1500);
  } catch (e) { st.textContent = '❌ Sem conexão com o servidor.'; st.style.color = 'var(--red)'; }
}

// ═══════════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════════
async function boot() {
  loadCurrentUser();                         // mostra o nome do usuário logado
  const remote = await loadFromServer();
  if (remote) DATA = remote;                 // servidor é a fonte da verdade
  activeGradeId = DATA.grades[0]?.id;
  renderAll();
  updateGradePill();
}

// Carrega biblioteca quando o painel for exibido
document.querySelectorAll('.nav-btn').forEach(b => {
  if (b.textContent.includes('Biblioteca')) b.addEventListener('click', () => setTimeout(loadLibrary, 100));
  if (b.textContent.includes('Usuários'))   b.addEventListener('click', () => setTimeout(loadUsers, 100));
  if (b.textContent.includes('Integrações')) b.addEventListener('click', () => setTimeout(loadIntegrations, 100));
});

boot();  // build: perfis de acesso, e-mail obrigatorio, SMTP, esqueci a senha
