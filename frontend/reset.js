function qs(name){ return new URLSearchParams(location.search).get(name); }
const TOKEN = qs('token') || '';

if (!TOKEN) {
  document.getElementById('form-fields').style.display = 'none';
  const e = document.getElementById('err');
  e.textContent = 'Link inválido. Solicite uma nova redefinição na tela de login.';
  e.style.display = 'block';
}

async function doReset(e){
  e.preventDefault();
  const err = document.getElementById('err');
  const ok  = document.getElementById('ok');
  err.style.display = 'none'; ok.style.display = 'none';
  const p1 = document.getElementById('pass').value;
  const p2 = document.getElementById('pass2').value;
  if (p1.length < 6) { err.textContent = 'A senha deve ter ao menos 6 caracteres.'; err.style.display='block'; return false; }
  if (p1 !== p2)     { err.textContent = 'As senhas não conferem.'; err.style.display='block'; return false; }
  const btn = document.getElementById('btn');
  btn.disabled = true; btn.textContent = 'Salvando...';
  try {
    const r = await fetch('/api/reset-password', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ token: TOKEN, new_password: p1 })
    });
    const data = await r.json();
    if (r.ok) {
      document.getElementById('form-fields').style.display = 'none';
      ok.innerHTML = 'Senha redefinida com sucesso! Você já pode <a href="/login">entrar</a>.';
      ok.style.display = 'block';
    } else {
      err.textContent = data.error || 'Não foi possível redefinir.';
      err.style.display = 'block';
    }
  } catch(ex) {
    err.textContent = 'Não foi possível conectar ao servidor.';
    err.style.display = 'block';
  } finally {
    btn.disabled = false; btn.textContent = 'Redefinir senha';
  }
  return false;
}
