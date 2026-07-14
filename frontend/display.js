// ═══════════════════════════════════════════════════════
// DADOS – editados pelo admin.html ou pelo servidor
// ═══════════════════════════════════════════════════════

// Migração: converte formato antigo {slides,ticker} para novo {grades,rodapes,tvs}
function migrateData(raw) {
  if (raw.grades && raw.tvs && raw.rodapes) return raw;
  const nd = JSON.parse(JSON.stringify(DEFAULT_CONTENT));
  if (raw.slides)  nd.grades[0].slides           = raw.slides;
  if (raw.ticker)  nd.rodapes[0].messages        = raw.ticker;
  if (raw.config)  nd.config                     = { ...nd.config, ...raw.config };
  return nd;
}

const DEFAULT_CONTENT = {
  config: { company_name: "GRUPO FLEXÍVEL", slide_duration: 12 },
  tvs: [{ id:"tv-001", slug:"principal", name:"TV Principal", description:"", grade_id:"grade-001", rodape_id:"rodape-001", active:true }],
  grades: [{
    id: "grade-001", name: "Grade Principal", slide_duration: 12,
    slides: [
      { id:1, type:"announcement", active:true, icon:"📣", badge:"Comunicado",
        title:"Bem-vindos à TV Corporativa!",
        body:"Este sistema foi desenvolvido para manter todos informados sobre os acontecimentos, metas e agenda da empresa.",
        author:"Equipe de TI" },
      { id:2, type:"kpi", active:true, title:"Indicadores do Mês", subtitle:"Atualizado em tempo real",
        metrics:[
          {label:"Produção Hoje",value:"1.247",unit:" un",trend:"+8%",dir:"up",color:"green",icon:"🏭"},
          {label:"Meta do Mês",value:"94",unit:"%",trend:"+2%",dir:"up",color:"blue",icon:"🎯"},
          {label:"Eficiência",value:"98,3",unit:"%",trend:"–0.5%",dir:"down",color:"amber",icon:"⚙️"},
          {label:"Qualidade",value:"99,1",unit:"%",trend:"+0.3%",dir:"up",color:"green",icon:"✅"},
          {label:"Colaboradores",value:"342",unit:"",trend:"estável",dir:"neu",color:"blue",icon:"👥"},
          {label:"NPS Interno",value:"87",unit:"",trend:"+5 pts",dir:"up",color:"green",icon:"⭐"}
        ]},
      { id:3, type:"announcement", active:true, icon:"⚠️", badge:"Aviso",
        title:"Uso Obrigatório de EPI",
        body:"O uso correto dos EPIs é obrigatório em todas as áreas de produção. Segurança em primeiro lugar!",
        author:"SSMA" }
    ]
  }],
  rodapes: [{ id:"rodape-001", name:"Rodapé Padrão", ticker_speed:40,
    messages:["Bem-vindos ao sistema de TV Corporativa","Configure o conteúdo pelo painel de administração"] }]
};

// Resolve qual grade e rodapé usar com base no parâmetro ?tv=SLUG
function resolveContent() {
  const raw = (() => {
    try { const r = localStorage.getItem('tv_content'); if (r) return migrateData(JSON.parse(r)); } catch(e) {}
    return JSON.parse(JSON.stringify(DEFAULT_CONTENT));
  })();

  const params = new URLSearchParams(location.search);
  const slug   = params.get('tv');

  let tv     = slug ? raw.tvs?.find(t => t.slug === slug) : null;
  if (!tv)    tv = raw.tvs?.[0];       // fallback: primeira TV

  const grade   = (raw.grades||[]).find(g => g.id === tv?.grade_id)   || raw.grades?.[0];
  const rodape  = (raw.rodapes||[]).find(r => r.id === tv?.rodape_id) || raw.rodapes?.[0];

  const gradeDefaultDur = grade?.slide_duration || raw.config?.slide_duration || 12;

  return {
    config:       raw.config || {},
    slides:       grade?.slides || [],
    ticker:       rodape?.messages || [],
    ticker_speed: rodape?.ticker_speed || raw.config?.ticker_speed || 40,
    slide_duration: gradeDefaultDur,
    tv, grade, rodape,
  };
}

// ═══════════════════════════════════════════════════════
// RENDERIZAÇÃO DOS SLIDES
// ═══════════════════════════════════════════════════════
function buildAnnouncementSlide(s) {
  return `
    <div class="slide slide-announcement" id="slide-${s.id}">
      <div class="ann-badge">${s.badge || 'Comunicado'}</div>
      <div class="ann-icon">${s.icon || '📢'}</div>
      <h1 class="ann-title">${s.title}</h1>
      <p class="ann-body">${s.body}</p>
      ${s.author ? `<div class="ann-author">— ${s.author}</div>` : ''}
    </div>`;
}

function buildCalendarSlide(s) {
  const events = s.events.map(e => `
    <div class="cal-event ${e.type==='urgent'?'urgent':''}">
      <div class="cal-date-box">
        <div class="cal-day">${e.day}</div>
        <div class="cal-month">${e.month}</div>
      </div>
      <div class="cal-info">
        <div class="cal-title">${e.title}</div>
        <div class="cal-meta">
          <span>🕐 ${e.time}</span>
          <span>📍 ${e.local}</span>
        </div>
      </div>
      ${e.type==='urgent'?'<div class="cal-badge">⚡ Destaque</div>':''}
    </div>`).join('');
  return `
    <div class="slide slide-calendar" id="slide-${s.id}">
      <div class="cal-header">
        <span class="cal-header-icon">📅</span>
        <div>
          <div class="cal-header-title">${s.title}</div>
          <div class="cal-header-month">${s.month || ''}</div>
        </div>
      </div>
      <div class="cal-events">${events}</div>
    </div>`;
}

function buildIntegrationSlide(s) {
  const img = s.integration_id ? `/uploads/captures/intg-${s.integration_id}.png` : '';
  return `
    <div class="slide slide-media slide-integration" id="slide-${s.id}">
      ${img ? `<img class="media-fg" id="iimg-${s.id}" src="${img}" alt="" onerror="this.style.display='none'">`
            : `<div class="news-loading">Integração não configurada</div>`}
    </div>`;
}

function refreshIntegration(slide) {
  if (!slide.integration_id) return;
  const src = `/uploads/captures/intg-${slide.integration_id}.png?t=${Date.now()}`;
  const img = document.getElementById('iimg-' + slide.id);
  const bg = document.getElementById('ibg-' + slide.id);
  if (img) { img.src = src; img.style.display = ''; }
  if (bg) bg.style.backgroundImage = `url('${src}')`;
}
// Enquanto um slide de integração estiver na tela, recarrega o print (acompanha a playlist)
setInterval(() => {
  const s = slides[current];
  if (s && s.type === 'integration') refreshIntegration(s);
}, 10000);

function buildUrlshotSlide(s) {
  const url = s.url || '';
  const zoom = s.zoom || 80;
  const z = zoom / 100;
  const sizePct = (100 / zoom * 100).toFixed(2);   // viewport maior p/ caber mais conteúdo
  const st = `width:${sizePct}%;height:${sizePct}%;transform:scale(${z});transform-origin:0 0;`;
  return `
    <div class="slide slide-embed" id="slide-${s.id}">
      ${url ? `<iframe src="${url}" style="${st}" referrerpolicy="no-referrer" loading="eager"></iframe>`
            : `<div class="news-loading">URL não definida</div>`}
      ${s.title ? `<div class="media-caption">${s.title}</div>` : ''}
    </div>`;
}

function buildNewsSlide(s) {
  const interval = (s.duration && s.count) ? Math.max(4, Math.floor(s.duration / s.count)) : 7;
  return `
    <div class="slide slide-news" id="slide-${s.id}">
      <div class="news-stage" id="news-${s.id}"
           data-cat="${s.category || 'TOP'}" data-count="${s.count || 6}"
           data-interval="${interval}" data-label="${s.label || 'Notícias'}">
        <div class="news-loading">Carregando notícias...</div>
      </div>
    </div>`;
}

function youtubeId(url) {
  if (!url) return null;
  const m = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/|v\/)|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  return m ? m[1] : null;
}

function buildMediaSlide(s) {
  const isVideo = s.url && s.url.match(/\.(mp4|webm|ogg)$/i);
  const ytId = youtubeId(s.url);
  const isPdf = s.url && /\.pdf(\?|#|$)/i.test(s.url);
  // Ajuste por mídia (configurável no admin): fit = cover (preenche/corta) ou
  // contain (inteira, sem corte) — vale quando os eixos estão em 100%.
  // zoomX/zoomY ≠ 100 definem o TAMANHO da caixa do conteúdo na tela
  // (largura % × altura %, centralizada) e o conteúdo é esticado exatamente
  // para ela (object-fit:fill) → muda a proporção SEM cortar. Acima de 100%
  // a caixa passa da tela e aí sim as bordas saem do quadro.
  const fit = s.fit === 'contain' ? 'contain' : 'cover';
  const clamp = v => Math.max(25, Math.min(300, parseInt(v) || 100));
  const zx = clamp(s.zoomX || s.zoom);
  const zy = clamp(s.zoomY || s.zoom);
  const fitStyle = (zx === 100 && zy === 100)
    ? `object-fit:${fit};`
    : `position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);` +
      `width:${zx}%;height:${zy}%;object-fit:fill;z-index:1;`;
  let media;
  if (!s.url) {
    media = `<div style="font-size:80px;opacity:.3">🖼️</div>`;
  } else if (isVideo) {
    // Vídeo: sem loop, avança automaticamente ao terminar
    media = `<video id="vid-${s.id}" src="${s.url}" autoplay muted playsinline
               style="${fitStyle}"
               onended="onVideoEnded(${s.id})"
               onerror="onVideoError(${s.id})"></video>`;
  } else if (ytId) {
    // YouTube: o player é criado via API ao exibir o slide (avança no fim do vídeo)
    media = `<div class="yt-wrap"><div id="ytm-${s.id}"></div></div>`;
  } else if (isPdf) {
    // PDF: exibe em tela cheia, sem a barra de ferramentas do leitor.
    // O zoom redimensiona a caixa do PDF (centralizada), sem cortar.
    const pdfZoom = (zx !== 100 || zy !== 100)
      ? `position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);width:${zx}%;height:${zy}%;`
      : 'width:100%;height:100%;';
    media = `<iframe src="${s.url}#toolbar=0&navpanes=0&scrollbar=0&view=FitH"
               style="${pdfZoom}border:none;background:#fff;"></iframe>`;
  } else {
    const u = s.url.replace(/'/g, '%27');
    media = `<div class="media-bg" style="background-image:url('${u}')"></div>
             <img class="media-fg" src="${s.url}" alt="${s.caption||''}" style="${fitStyle}">`;
  }
  return `
    <div class="slide slide-media" id="slide-${s.id}" data-is-video="${isVideo?'1':'0'}">
      ${media}
      ${s.caption ? `<div class="media-caption">${s.caption}</div>` : ''}
    </div>`;
}

// ── Galeria ──────────────────────────────────────────────
// Galeria: múltiplas imagens dentro de um único slide,
// rotacionando com crossfade suave.
const galleryTimers = {};

function buildGallerySlide(s) {
  const imgs = (s.images || []);
  const items = imgs.map((img, i) => `
    <div class="gallery-item ${i===0?'active':''}" data-idx="${i}">
      <div class="media-bg" style="background-image:url('${(img.url||'').replace(/'/g, '%27')}')"></div>
      <img class="media-fg" src="${img.url}" alt="${img.caption||''}">
      ${img.caption ? `<div class="media-caption">${img.caption}</div>` : ''}
    </div>`).join('');
  return `
    <div class="slide slide-gallery" id="slide-${s.id}">
      <div class="gallery-wrap">${items || '<div style="font-size:60px;opacity:.3">🖼️</div>'}</div>
      ${s.title ? `<div class="gallery-title">${s.title}</div>` : ''}
    </div>`;
}

function startGallery(slideId, intervalSec) {
  stopGallery(slideId);
  const wrap = document.querySelector(`#slide-${slideId} .gallery-wrap`);
  if (!wrap) return;
  const items = wrap.querySelectorAll('.gallery-item');
  if (items.length <= 1) return;
  let idx = 0;
  galleryTimers[slideId] = setInterval(() => {
    items[idx].classList.remove('active');
    idx = (idx + 1) % items.length;
    items[idx].classList.add('active');
  }, (intervalSec || 4) * 1000);
}

function stopGallery(slideId) {
  clearInterval(galleryTimers[slideId]);
  delete galleryTimers[slideId];
}

// ═══════════════════════════════════════════════════════
// CONTROLE DE SLIDES
// ═══════════════════════════════════════════════════════
let slides = [], current = 0, timer = null, progress_timer = null;
let _resolvedContent = null;  // cache de resolveContent()

function getContent() { return _resolvedContent || resolveContent(); }

// ── Agendamento: o slide só entra na rotação se a data/hora atual bater com a regra ──
function _localYMD(d) {
  return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
}
function _hm(d) {
  return String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0');
}
function scheduleMatches(s, now) {
  const sc = s.schedule;
  if (!sc || !sc.mode || sc.mode === 'always') return true;
  now = now || new Date();
  if (sc.mode === 'range') {
    const ymd = _localYMD(now);
    if (sc.start && ymd < sc.start) return false;
    if (sc.end && ymd > sc.end) return false;
    return true;
  }
  if (sc.mode === 'recurring') {
    const month = now.getMonth() + 1, dom = now.getDate(), dow = now.getDay(), hm = _hm(now);
    if (sc.months && sc.months.length && !sc.months.includes(month)) return false;
    if (sc.dom_from && dom < sc.dom_from) return false;
    if (sc.dom_to && dom > sc.dom_to) return false;
    if (sc.weekdays && sc.weekdays.length && !sc.weekdays.includes(dow)) return false;
    if (sc.time_from && sc.time_to) {
      if (sc.time_from <= sc.time_to) { if (hm < sc.time_from || hm > sc.time_to) return false; }
      else { if (hm < sc.time_from && hm > sc.time_to) return false; }  // faixa que vira a meia-noite
    } else if (sc.time_from && hm < sc.time_from) { return false; }
    else if (sc.time_to && hm > sc.time_to) { return false; }
    return true;
  }
  return true;
}
function activeSlides(content) {
  return (content.slides || []).filter(s => s.active && s.type !== 'kpi' && scheduleMatches(s));
}

let _lastVisibleKey = '';

function init() {
  _resolvedContent = resolveContent();
  const content = _resolvedContent;
  newsBlockGlobal = (content.config && content.config.news_blocklist) || '';
  slides = activeSlides(content);
  _lastVisibleKey = slides.map(s => s.id).join(',');
  console.log('%c[TV] init() — reconstruindo slides:', 'color:#F46800;font-weight:bold', slides.length, 'slides @', new Date().toLocaleTimeString());
  const container = document.getElementById('slides-container');
  const dotsEl = document.getElementById('dots');

  // barra inferior configurável (logo, data/hora, ticker, moedas)
  renderFooter(content);

  // build slides
  container.innerHTML = '';
  dotsEl.innerHTML = '';

  // Nenhum slide programado para agora → tela neutra (a barra inferior continua)
  if (slides.length === 0) {
    clearTimeout(timer);
    document.getElementById('slides-container').classList.remove('fullbleed');
    container.innerHTML = '<div class="slide active" style="background:#0C3B38;align-items:center;justify-content:center;">'
      + '<div style="color:rgba(255,255,255,.55);font-size:24px;">Sem conteúdo programado no momento</div></div>';
    const pbw = document.getElementById('progress-bar-wrap'); if (pbw) pbw.style.display = 'none';
    return;
  }

  slides.forEach((s, i) => {
    let html = '';
    if      (s.type === 'announcement') html = buildAnnouncementSlide(s);
    else if (s.type === 'calendar')     html = buildCalendarSlide(s);
    else if (s.type === 'media')        html = buildMediaSlide(s);
    else if (s.type === 'gallery')      html = buildGallerySlide(s);
    else if (s.type === 'news')         html = buildNewsSlide(s);
    else if (s.type === 'urlshot')      html = buildUrlshotSlide(s);
    else if (s.type === 'integration')  html = buildIntegrationSlide(s);
    container.insertAdjacentHTML('beforeend', html);

    const dot = document.createElement('div');
    dot.className = 'dot';
    dot.onclick = () => goTo(i);
    dotsEl.appendChild(dot);
  });

  prefetchNews();   // pré-carrega as notícias dos slides
  goTo(0);
}

// Reavalia o agendamento a cada minuto: vira o dia/hora → slide entra ou sai sozinho da rotação
setInterval(() => {
  if (!_resolvedContent) return;
  const key = activeSlides(_resolvedContent).map(s => s.id).join(',');
  if (key !== _lastVisibleKey) init();
}, 60 * 1000);

// Duração individual de cada slide (usa slide.duration se definido, senão o padrão da grade)
function getDuration(idx) {
  const content = getContent();
  const defaultDur = content.slide_duration || content.config?.slide_duration || 12;
  const slide = slides[idx];
  if (slide?.duration && slide.duration > 0) return slide.duration;
  if (slide?.type === 'integration') return 120;  // playlist: permanece mais tempo
  return defaultDur;
}

// Verifica se o slide atual é um vídeo sem duração forçada
function currentIsVideo() {
  const slide = slides[current];
  if (!slide || slide.type !== 'media') return false;
  if (slide.duration && slide.duration > 0) return false; // duração forçada → trata como imagem
  return !!(slide.url && (slide.url.match(/\.(mp4|webm|ogg)$/i) || youtubeId(slide.url)));
}

// Chamado quando o vídeo termina naturalmente
function onVideoEnded(slideId) {
  const idx = slides.findIndex(s => s.id === slideId);
  if (idx === current) goTo(current + 1);
}

// ── YouTube IFrame API (avança no fim do vídeo) ──────────
let _ytPlayer = null, _ytApiLoading = false, _ytReadyCbs = [];
window.onYouTubeIframeAPIReady = function () { _ytReadyCbs.forEach(c => c()); _ytReadyCbs = []; };
function ensureYTApi(cb) {
  if (window.YT && window.YT.Player) { cb(); return; }
  _ytReadyCbs.push(cb);
  if (_ytApiLoading) return;
  _ytApiLoading = true;
  const tag = document.createElement('script');
  tag.src = 'https://www.youtube.com/iframe_api';
  document.head.appendChild(tag);
}
function destroyYTPlayer() {
  if (_ytPlayer) { try { _ytPlayer.destroy(); } catch (e) {} _ytPlayer = null; }
}
function playYouTubeFor(slide) {
  const ytId = youtubeId(slide.url);
  const wrap = document.querySelector(`#slide-${slide.id} .yt-wrap`);
  if (!ytId || !wrap) return;
  ensureYTApi(() => {
    if (slides[current] !== slide) return;   // já mudou de slide enquanto a API carregava
    destroyYTPlayer();
    wrap.innerHTML = '<div id="ytm-' + slide.id + '"></div>';
    _ytPlayer = new YT.Player('ytm-' + slide.id, {
      width: '100%', height: '100%', videoId: ytId,
      playerVars: { autoplay: 1, mute: 1, controls: 0, rel: 0, modestbranding: 1, playsinline: 1, fs: 0, disablekb: 1 },
      events: {
        onReady: e => { try { e.target.mute(); e.target.playVideo(); } catch (x) {} },
        onStateChange: e => { if (e.data === YT.PlayerState.ENDED && currentIsVideo()) onVideoEnded(slide.id); },
        onError: () => onVideoError(slide.id)
      }
    });
  });
}

// Chamado se o vídeo falhar ao carregar → usa duração padrão
function onVideoError(slideId) {
  const idx = slides.findIndex(s => s.id === slideId);
  if (idx === current) {
    console.warn('Vídeo falhou ao carregar, avançando após duração padrão.');
    scheduleNext(true); // força modo timer
  }
}

function goTo(idx) {
  const all = document.querySelectorAll('.slide');
  const dots = document.querySelectorAll('.dot');

  // Pausar vídeo/galeria do slide anterior
  if (all[current]) {
    const prevVid = all[current].querySelector('video');
    if (prevVid) { prevVid.pause(); prevVid.currentTime = 0; }
    const prevSlide = slides[current];
    if (prevSlide?.type === 'gallery') stopGallery(prevSlide.id);
    if (prevSlide?.type === 'media' && youtubeId(prevSlide.url)) destroyYTPlayer();
    all[current].classList.remove('active');
    all[current].classList.add('exit');
    setTimeout(() => all[current]?.classList.remove('exit'), 800);
  }

  current = (idx + slides.length) % slides.length;

  if (all[current]) {
    all[current].classList.add('active');
    // Iniciar vídeo do novo slide — reinicia do começo; se o play falhar, recarrega e tenta de novo
    const vid = all[current].querySelector('video');
    if (vid) {
      try { vid.currentTime = 0; } catch (e) {}
      const pr = vid.play();
      if (pr && pr.catch) pr.catch(() => { try { vid.load(); vid.play().catch(() => {}); } catch (e) {} });
    }
    // Iniciar rotação de galeria
    const curSlide = slides[current];
    if (curSlide?.type === 'gallery') {
      startGallery(curSlide.id, curSlide.image_interval || 4);
    }
    if (curSlide?.type === 'media' && youtubeId(curSlide.url)) playYouTubeFor(curSlide);
    if (curSlide?.type === 'news') { const st = document.getElementById('news-' + curSlide.id); if (st) advanceNews(st); }
    if (curSlide?.type === 'integration') refreshIntegration(curSlide);
  }
  dots.forEach((d,i) => d.classList.toggle('active', i===current));

  // Integração (playlist) = modo aplicação: sem barra de progresso visível
  const pbw = document.getElementById('progress-bar-wrap');
  if (pbw) pbw.style.display = (slides[current]?.type === 'integration') ? 'none' : '';

  // Mídia visual preenche a tela inteira (a barra fica por cima); PDF e demais ficam acima da barra
  const curT = slides[current];
  let fullbleed = false;
  if (curT) {
    if (curT.type === 'gallery') fullbleed = true;
    else if (curT.type === 'media') fullbleed = !/\.pdf(\?|#|$)/i.test(curT.url || '');
  }
  document.getElementById('slides-container').classList.toggle('fullbleed', fullbleed);

  scheduleNext();
}

let countdownInterval = null;

function setTimeRemaining(text) {
  const el = document.getElementById('time-remaining');
  if (el) el.textContent = text;
}

function startCountdown(seconds) {
  clearInterval(countdownInterval);
  let remaining = Math.round(seconds);
  setTimeRemaining(remaining + 's');
  countdownInterval = setInterval(() => {
    remaining--;
    if (remaining <= 0) {
      clearInterval(countdownInterval);
      setTimeRemaining('');
    } else {
      setTimeRemaining(remaining + 's');
    }
  }, 1000);
}

function scheduleNext(forceTimer = false) {
  clearTimeout(timer);
  clearInterval(countdownInterval);
  const bar = document.getElementById('progress-bar');

  // Integração (Grafana): fica fixa, sem timer — a própria playlist alterna sozinha
  if (slides[current]?.type === 'integration') {
    setTimeRemaining('');
    return;
  }

  if (!forceTimer && currentIsVideo()) {
    // Vídeo sem duração forçada: barra indeterminada, avança pelo evento 'ended'
    bar.style.transition = 'none';
    bar.style.width = '0%';
    setTimeout(() => {
      bar.style.transition = 'width 999s linear';
      bar.style.width = '99%'; // nunca chega a 100% – vídeo decide
    }, 60);
    setTimeRemaining('▶ vídeo');
    // Fallback: se após 10 min o vídeo não terminar, avança
    timer = setTimeout(() => goTo(current + 1), 10 * 60 * 1000);
    return;
  }

  // Slide normal ou duração forçada: usa timer
  const dur = getDuration(current);
  bar.style.transition = 'none';
  bar.style.width = '0%';
  setTimeout(() => {
    bar.style.transition = `width ${dur}s linear`;
    bar.style.width = '100%';
  }, 60);

  startCountdown(dur);

  timer = setTimeout(() => {
    goTo(current + 1);
  }, dur * 1000);
}

// ═══════════════════════════════════════════════════════
// BARRA INFERIOR CONFIGURÁVEL (logo, data/hora, ticker, moedas)
// ═══════════════════════════════════════════════════════
const DEFAULT_FOOTER_WIDGETS = [
  { type:'logo',     enabled:true,  position:'left', transparent:true },
  { type:'ticker',   enabled:true,  position:'center' },
  { type:'datetime', enabled:true,  position:'right', timezone:'America/Sao_Paulo' },
  { type:'currency', enabled:true,  position:'right' },
  { type:'weather',  enabled:false, position:'right', city:'São Paulo' }
];

let _latestRates = null;

function renderFooter(content) {
  const footer = document.getElementById('footer');
  if (!footer) return;
  const rod = content.rodape || {};
  footer.style.background = rod.bg_color || '';
  footer.style.color = rod.text_color || '';

  // Altura configurável da barra (e ajusta o espaço dos slides)
  const barH = Math.min(200, Math.max(40, parseInt(rod.bar_height) || 56));
  footer.style.height = barH + 'px';
  const sc = document.getElementById('slides-container');
  if (sc) sc.style.bottom = barH + 'px';

  const widgets = (rod.widgets && rod.widgets.length) ? rod.widgets : DEFAULT_FOOTER_WIDGETS;
  footer.innerHTML = '';

  // Três zonas de posicionamento: esquerda, centro, direita
  const zones = {
    left:   Object.assign(document.createElement('div'), { className: 'fw-zone fw-zone-left' }),
    center: Object.assign(document.createElement('div'), { className: 'fw-zone fw-zone-center' }),
    right:  Object.assign(document.createElement('div'), { className: 'fw-zone fw-zone-right' }),
  };

  widgets.filter(w => w.enabled !== false).forEach(w => {
    let el = null;
    if      (w.type === 'logo')     el = buildLogoWidget(w);
    else if (w.type === 'datetime') el = buildDateTimeWidget(w);
    else if (w.type === 'ticker')   el = buildTickerWidget(content);
    else if (w.type === 'currency') el = buildCurrencyWidget(w);
    else if (w.type === 'weather')  el = buildWeatherWidget(w);
    if (el) (zones[w.position] || zones.center).appendChild(el);
  });

  footer.appendChild(zones.left);
  footer.appendChild(zones.center);
  footer.appendChild(zones.right);

  // Escala o logo conforme a altura da barra
  const logoH = Math.max(24, barH - 18);
  footer.querySelectorAll('.fw-logo img').forEach(img => img.style.height = logoH + 'px');

  updateFooterClocks();
  refreshRates();
  refreshWeather();
}

function buildLogoWidget(w) {
  const d = document.createElement('div');
  d.className = 'fw fw-logo';
  if (w && w.transparent === false) d.classList.add('fw-logo--solid');
  const url = (w && w.url) ? w.url : '/assets/logo.png';
  d.innerHTML = `<img src="${url}" alt="Logo">`;
  return d;
}

function buildDateTimeWidget(w) {
  const d = document.createElement('div');
  d.className = 'fw fw-datetime';
  d.dataset.tz = w.timezone || 'America/Sao_Paulo';
  d.innerHTML = `<div><div class="fw-time">--:--:--</div><div class="fw-date">—</div></div>`;
  return d;
}

function buildTickerWidget(content) {
  const d = document.createElement('div');
  d.className = 'fw fw-ticker';
  const msgs = content.ticker || [];
  const spd = content.ticker_speed || 40;
  const inner = document.createElement('div');
  inner.className = 'ticker-scroll';
  inner.style.animationDuration = spd + 's';
  inner.innerHTML = msgs.map(m => `<span>${m}</span>`).join('');
  d.appendChild(inner);
  return d;
}

function buildCurrencyWidget(w) {
  const d = document.createElement('div');
  d.className = 'fw fw-currency';
  d.innerHTML =
    `<span class="cur cur-usd" data-cur="USD"><span class="cur-sym">$</span><span class="cur-val">—</span></span>` +
    `<span class="cur cur-eur" data-cur="EUR"><span class="cur-sym">€</span><span class="cur-val">—</span></span>`;
  return d;
}

function buildWeatherWidget(w) {
  const d = document.createElement('div');
  d.className = 'fw fw-weather';
  d.dataset.city = w.city || '';
  d.dataset.lat = (w.lat != null) ? w.lat : '';
  d.dataset.lon = (w.lon != null) ? w.lon : '';
  d.innerHTML = `<span class="wx-icon">🌡️</span><span class="wx-temp">—</span>` +
    `<span class="wx-minmax"><span class="wx-min">▼ —</span><span class="wx-max">▲ —</span></span>`;
  return d;
}

function updateFooterClocks() {
  document.querySelectorAll('.fw-datetime').forEach(el => {
    const tz = el.dataset.tz || 'America/Sao_Paulo';
    const now = new Date();
    const t = el.querySelector('.fw-time');
    const dt = el.querySelector('.fw-date');
    try {
      t.textContent  = now.toLocaleTimeString('pt-BR', { timeZone: tz, hour:'2-digit', minute:'2-digit', second:'2-digit' });
      dt.textContent = now.toLocaleDateString('pt-BR', { timeZone: tz, weekday:'long', day:'2-digit', month:'long' });
    } catch (e) {
      t.textContent = now.toLocaleTimeString('pt-BR');
      dt.textContent = now.toLocaleDateString('pt-BR', { weekday:'long', day:'2-digit', month:'long' });
    }
  });
}
setInterval(updateFooterClocks, 1000);

function applyRates() {
  if (!_latestRates) return;
  document.querySelectorAll('.fw-currency .cur').forEach(span => {
    const c = span.dataset.cur;
    const v = _latestRates[c];
    const valEl = span.querySelector('.cur-val');
    if (valEl) valEl.textContent = v != null ? ('R$ ' + Number(v).toFixed(2).replace('.', ',')) : '—';
  });
}

async function refreshRates() {
  if (!document.querySelector('.fw-currency')) return;
  try {
    const r = await fetch('/api/rates', { cache: 'no-store' });
    _latestRates = await r.json();
    applyRates();
  } catch (e) {}
}
// O servidor cacheia 1x/dia; o display reconsulta de hora em hora.
setInterval(refreshRates, 60 * 60 * 1000);

// ── Previsão do tempo ──────────────────────────────────
function refreshWeather() {
  document.querySelectorAll('.fw-weather').forEach(async el => {
    const { city, lat, lon } = el.dataset;
    let url;
    if (lat && lon) url = `/api/weather?lat=${encodeURIComponent(lat)}&lon=${encodeURIComponent(lon)}&label=${encodeURIComponent(city || '')}`;
    else if (city)  url = `/api/weather?city=${encodeURIComponent(city)}`;
    else { el.style.display = 'none'; return; }
    try {
      const r = await fetch(url, { cache: 'no-store' });
      const w = await r.json();
      if (w && w.ok) {
        el.style.display = '';
        el.querySelector('.wx-icon').textContent = w.icon || '🌡️';
        el.querySelector('.wx-temp').textContent = Math.round(w.temp) + '°';
        el.querySelector('.wx-min').textContent  = '▼ ' + Math.round(w.tmin) + '°';
        el.querySelector('.wx-max').textContent  = '▲ ' + Math.round(w.tmax) + '°';
        el.title = w.city || city;
      } else {
        el.style.display = 'none';   // sem dados (cidade inválida ou servidor sem internet): oculta
      }
    } catch (e) { el.style.display = 'none'; }
  });
}
// Clima é cacheado no servidor (~3h); o display reconsulta de hora em hora.
setInterval(refreshWeather, 60 * 60 * 1000);

// ── Notícias: 1 por vez, e a cada volta da grade mostra a PRÓXIMA ──
const newsData = {};    // stageId -> { items, ts }
const newsCursor = {};  // stageId -> próximo índice a exibir
let newsBlockGlobal = '';  // lista global de palavras proibidas (Configurações)

function _renderNewsCard(stage, n, label) {
  stage.innerHTML = `
    <div class="news-card active">
      <div class="news-img"${n.image ? ` style="background-image:url('${n.image.replace(/'/g, '%27')}')"` : ''}>${n.image ? '' : '📰'}</div>
      <div class="news-info">
        <div class="news-source">${n.source ? n.source + ' · ' : ''}${label}</div>
        <div class="news-headline">${n.title}</div>
      </div>
    </div>`;
}

// Pré-carrega as notícias (sem avançar), para a 1ª exibição ser instantânea
function prefetchNews() {
  document.querySelectorAll('.news-stage').forEach(async stage => {
    const cat = stage.dataset.cat || 'TOP';
    try {
      const r = await fetch('/api/news?category=' + encodeURIComponent(cat), { cache: 'no-store' });
      const data = await r.json();
      newsData[stage.id] = { items: (data && data.ok && data.items) ? data.items : [], ts: Date.now() };
      if (newsCursor[stage.id] === undefined) newsCursor[stage.id] = 0;
    } catch (e) {}
  });
}

// Remove notícias que contenham qualquer palavra proibida (no título ou fonte)
function filterBlocked(items, blockStr) {
  const words = (blockStr || '').split(',').map(w => w.trim().toLowerCase()).filter(Boolean);
  if (!words.length) return items;
  return items.filter(n => {
    const text = ((n.title || '') + ' ' + (n.source || '')).toLowerCase();
    return !words.some(w => text.includes(w));
  });
}

// Chamado toda vez que o slide de notícia entra em cena → mostra a próxima
async function advanceNews(stage) {
  const id = stage.id;
  const cat = stage.dataset.cat || 'TOP';
  const label = stage.dataset.label || 'Notícias';
  const count = parseInt(stage.dataset.count) || 6;
  const block = newsBlockGlobal;
  const now = Date.now();
  let entry = newsData[id];
  let cursor = newsCursor[id] || 0;

  // Monta a lista exibível: aplica palavras proibidas, prefere as com imagem, limita à quantidade
  function buildPool(e) {
    let arr = filterBlocked(e ? (e.items || []) : [], block);
    const withImg = arr.filter(n => n.image);
    if (withImg.length >= 1) arr = withImg;
    return arr.slice(0, count);
  }

  const stale = !entry || (now - entry.ts > 30 * 60 * 1000);
  let pool = buildPool(entry);
  const exhausted = entry && cursor >= pool.length;
  if (stale || exhausted) {  // recarrega ao esgotar a lista ou após 30 min (notícias frescas)
    try {
      const r = await fetch('/api/news?category=' + encodeURIComponent(cat), { cache: 'no-store' });
      const data = await r.json();
      entry = { items: (data && data.ok && data.items) ? data.items : [], ts: now };
    } catch (e) { entry = entry || { items: [], ts: now }; }
    newsData[id] = entry;
    cursor = 0;
    pool = buildPool(entry);
  }

  if (!pool.length) { stage.innerHTML = '<div class="news-loading">Sem notícias disponíveis no momento.</div>'; return; }
  const n = pool[cursor % pool.length];
  newsCursor[id] = cursor + 1;   // próxima volta da grade mostra a seguinte
  _renderNewsCard(stage, n, label);
}

// ═══════════════════════════════════════════════════════
// ATUALIZAÇÃO AUTOMÁTICA (ouve mudanças do admin)
// ═══════════════════════════════════════════════════════
window.addEventListener('storage', e => {
  if (e.key === 'tv_content') {
    _resolvedContent = null; // invalida cache
    clearInterval(timer);
    init();
  }
});

// ═══════════════════════════════════════════════════════
// SINCRONIZAÇÃO COM SERVIDOR (server.py)
// ═══════════════════════════════════════════════════════
const SERVER_URL = (() => {
  // Se a página for servida pelo server.py, usa a mesma origem
  if (location.protocol === 'http:' && location.port === '8080')
    return location.origin;
  return null; // modo arquivo local
})();

let _lastSyncStr = null;   // conteúdo rastreado EM MEMÓRIA (não depende de o localStorage persistir)
async function syncFromServer() {
  if (!SERVER_URL) return;
  try {
    const r = await fetch(SERVER_URL + '/api/content', { cache: 'no-store' });
    if (!r.ok) throw new Error('HTTP ' + r.status);
    const data = await r.json();
    const next = JSON.stringify(data);
    if (_lastSyncStr === null) {           // 1ª sincronização: parte do que já está salvo/exibido
      _lastSyncStr = localStorage.getItem('tv_content');
    }
    if (_lastSyncStr !== next) {           // só reconstrói se o conteúdo REALMENTE mudou
      _lastSyncStr = next;
      try { localStorage.setItem('tv_content', next); } catch (e) {}
      _resolvedContent = null; // invalida cache
      clearInterval(timer);
      init();
    }
    setOnlineStatus(true);
  } catch(e) {
    setOnlineStatus(false);
  }
}

// ═══════════════════════════════════════════════════════
// INDICADOR DE STATUS ONLINE / OFFLINE
// ═══════════════════════════════════════════════════════
function setOnlineStatus(online) {
  let dot = document.getElementById('status-dot');
  if (!dot) {
    dot = document.createElement('div');
    dot.id = 'status-dot';
    dot.style.cssText = `
      position:fixed;bottom:65px;right:10px;width:8px;height:8px;
      border-radius:50%;z-index:200;transition:background .5s;
      box-shadow:0 0 4px rgba(0,0,0,.4);
    `;
    document.body.appendChild(dot);
  }
  dot.style.background = online ? '#4caf50' : '#e06c75';
  dot.title = online ? 'Conectado ao servidor' : 'Offline – exibindo último conteúdo salvo';
}

// ═══════════════════════════════════════════════════════
// WATCHDOG – recarrega a página se travar por > 2 min
// ═══════════════════════════════════════════════════════
let lastActivity = Date.now();
setInterval(() => { lastActivity = Date.now(); }, 30000);
setInterval(() => {
  if (Date.now() - lastActivity > 130000) location.reload();
}, 10000);

// Sync a cada 60 segundos com o servidor
setInterval(syncFromServer, 60 * 1000);
// Reload completo a cada 4 horas (limpa memória)
setInterval(() => location.reload(), 4 * 60 * 60 * 1000);

// ── START ──
init();
syncFromServer();

// ═══════════════════════════════════════════════════════
// ANTI-STANDBY – impede a TV/browser de dormir, em 2 camadas:
// 1) Wake Lock API (Chrome, Android TV, webOS/Tizen recentes)
// 2) Vídeo mudo invisível em loop — o browser da TV entende como
//    "mídia em reprodução" e não entra em standby (técnica NoSleep)
// ═══════════════════════════════════════════════════════
(function keepAwake() {
  // Camada 1: Wake Lock API
  let wakeLock = null;
  async function requestWakeLock() {
    if (!('wakeLock' in navigator)) return;
    try {
      wakeLock = await navigator.wakeLock.request('screen');
      wakeLock.addEventListener('release', () => { wakeLock = null; });
    } catch (e) { wakeLock = null; }  // sem suporte/permissão: segue na camada 2
  }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && !wakeLock) requestWakeLock();
  });
  setInterval(() => { if (!wakeLock) requestWakeLock(); }, 60 * 1000);
  requestWakeLock();

  // Camada 2: vídeo keepalive (2s, 1,6 KB, mudo, fora da tela)
  const v = document.createElement('video');
  v.muted = true;
  v.loop = true;
  v.setAttribute('muted', '');        // atributo explícito: exigido p/ autoplay em algumas TVs
  v.setAttribute('playsinline', '');
  v.src = '/assets/keepawake.mp4';
  v.style.cssText = 'position:fixed;left:-9999px;top:-9999px;width:2px;height:2px;opacity:0;pointer-events:none;';
  document.body.appendChild(v);
  const play = () => { v.play().catch(() => {}); };
  v.addEventListener('pause', play);   // se a TV pausar, retoma
  v.addEventListener('error', () => setTimeout(() => { v.load(); play(); }, 5000));
  setInterval(play, 30 * 1000);        // garantia periódica
  play();
})();
