function qs(name){ return new URLSearchParams(location.search).get(name); }

const loginForm = document.getElementById('login-form');
const forgotForm = document.getElementById('forgot-form');
document.getElementById('forgot-link').addEventListener('click', (e) => {
  e.preventDefault(); loginForm.style.display = 'none'; forgotForm.style.display = '';
  document.getElementById('forgot-id').focus();
});
document.getElementById('back-login').addEventListener('click', (e) => {
  e.preventDefault(); forgotForm.style.display = 'none'; loginForm.style.display = '';
});

const restoreForm = document.getElementById('restore-form');
document.getElementById('restore-link').addEventListener('click', (e) => {
  e.preventDefault(); loginForm.style.display = 'none'; restoreForm.style.display = '';
});
document.getElementById('restore-back').addEventListener('click', (e) => {
  e.preventDefault(); restoreForm.style.display = 'none'; loginForm.style.display = '';
});

async function doRestore(e){
  e.preventDefault();
  const err = document.getElementById('restore-err');
  const ok  = document.getElementById('restore-ok');
  const btn = document.getElementById('restore-btn');
  err.style.display = 'none'; ok.style.display = 'none';
  const file = document.getElementById('restore-file').files[0];
  if (!file) { err.textContent = 'Selecione o arquivo de backup.'; err.style.display = 'block'; return false; }
  if (!confirm('Restaurar vai SUBSTITUIR todos os dados atuais. Continuar?')) return false;
  btn.disabled = true; btn.textContent = 'Restaurando...';
  const fd = new FormData();
  fd.append('file', file);
  try {
    const r = await fetch('/api/restore-login', { method:'POST', body: fd });
    const data = await r.json().catch(()=>({}));
    if (r.ok) {
      ok.textContent = 'Banco restaurado! Você já pode entrar com os usuários do backup.';
      ok.style.display = 'block';
    } else {
      err.textContent = data.error || 'Não foi possível restaurar.';
      err.style.display = 'block';
    }
  } catch(ex) {
    err.textContent = 'Não foi possível conectar ao servidor.';
    err.style.display = 'block';
  } finally {
    btn.disabled = false; btn.textContent = 'Restaurar agora';
  }
  return false;
}

async function doForgot(e){
  e.preventDefault();
  const err = document.getElementById('forgot-err');
  const ok  = document.getElementById('forgot-ok');
  const btn = document.getElementById('forgot-btn');
  err.style.display = 'none'; ok.style.display = 'none';
  btn.disabled = true; btn.textContent = 'Enviando...';
  try {
    const r = await fetch('/api/forgot-password', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ identifier: document.getElementById('forgot-id').value })
    });
    const data = await r.json();
    if (r.ok) {
      ok.textContent = data.message || 'Se o usuário existir, enviaremos um link de redefinição.';
      ok.style.display = 'block';
    } else {
      err.textContent = data.error || 'Não foi possível enviar.';
      err.style.display = 'block';
    }
  } catch(ex) {
    err.textContent = 'Não foi possível conectar ao servidor.';
    err.style.display = 'block';
  } finally {
    btn.disabled = false; btn.textContent = 'Enviar link de redefinição';
  }
  return false;
}

async function doLogin(e){
  e.preventDefault();
  const btn = document.getElementById('btn');
  const err = document.getElementById('error-msg');
  err.style.display = 'none';
  btn.disabled = true; btn.textContent = 'Entrando...';
  try {
    const r = await fetch('/api/login', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({
        username: document.getElementById('username').value,
        password: document.getElementById('password').value
      })
    });
    const data = await r.json();
    if (r.ok) {
      const next = qs('next') || '/admin';
      location.href = next;
    } else {
      err.textContent = data.error || 'Falha no login.';
      err.style.display = 'block';
    }
  } catch(ex) {
    err.textContent = 'Não foi possível conectar ao servidor.';
    err.style.display = 'block';
  } finally {
    btn.disabled = false; btn.textContent = 'Entrar';
  }
  return false;
}
