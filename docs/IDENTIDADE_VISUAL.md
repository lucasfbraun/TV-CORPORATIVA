# 🎨 Identidade Visual — TV Corporativa | Grupo Flexível

Guia de identidade visual do projeto **TV Corporativa**, derivado da marca
**Grupo Flexível**. A paleta é **híbrida**: as cores principais vêm do logo
oficial (verdes da marca) e mantemos um acento laranja para alertas, herdado do
padrão Material Design de referência.

> Documento adaptado do guia de identidade de outro projeto (dashboard Microsoft),
> reaproveitando a estrutura e a tipografia, mas com a paleta da marca Flexível.

---

## 🟢 Paleta de Cores

### Cores da marca (extraídas do logo)

| Função / Uso | Nome | Hex | RGB | Onde aparece |
|---|---|---|---|---|
| **Verde-petróleo** (primária escura) | `--brand-petrol` | `#0C3B38` | `rgb(12, 59, 56)` | Sidebar do admin, fundo das TVs, cabeçalhos |
| **Teal** (primária de ação) | `--brand-teal` | `#0F7C70` | `rgb(15, 124, 112)` | Botões principais, links, KPI, destaques |
| **Verde-limão** (acento da marca) | `--brand-lime` | `#76C043` | `rgb(118, 192, 67)` | Badges, realces, selo do logo, pílulas |
| **Verde-petróleo médio** | `--blue-mid` | `#14534D` | `rgb(20, 83, 77)` | Gradientes, fundos intermediários |

### Cores funcionais

| Função | Nome | Hex | Uso |
|---|---|---|---|
| **Sucesso** | `--green` | `#4CAF50` | Status ativo, confirmações |
| **Alerta** (herdado do doc de referência) | `--amber` | `#FFAB40` | Avisos, vencimentos, atenção |
| **Erro / Perigo** | `--red` | `#E06C75` | Erros, remoções, status off |
| **Branco** | `--white` | `#FFFFFF` | Cards, selo do logo, texto sobre verde |
| **Cinza de fundo** | `--gray` | `#F0F4F8` | Fundo geral do painel |
| **Texto** | `--text` | `#2D3A4A` | Texto padrão |
| **Texto suave** | `--dim` | `#7A8FA6` | Legendas, descrições |

---

## 🎯 Variáveis CSS (já aplicadas nas telas)

As três telas (`login.html`, `admin.html`, `display.html`) compartilham este
bloco `:root`. Os nomes `--blue-*` foram **mantidos por compatibilidade**, mas
agora carregam os valores verdes da marca:

```css
:root {
  /* Marca Grupo Flexível */
  --brand-petrol:#0C3B38;
  --brand-teal:#0F7C70;
  --brand-lime:#76C043;
  --amber:#FFAB40;            /* acento de alerta (Material Design) */

  /* Tema aplicado na UI */
  --blue-dark:#0C3B38;        /* verde-petróleo */
  --blue-mid:#14534D;
  --blue-light:#0F7C70;       /* teal — ações/links */
  --accent:#76C043;           /* verde-limão */
  --green:#4CAF50;
  --red:#E06C75;
  --white:#fff; --gray:#f0f4f8; --text:#2d3a4a; --dim:#7a8fa6;
}
```

---

## 🖼️ Logo

- **Arquivo:** `frontend/assets/logo.png` (servido em `/assets/logo.png`).
- **Fundo:** transparente — pode ser sobreposto a qualquer cor.
- **Regra de legibilidade:** o logo tem texto verde-escuro, que **some em fundos
  escuros**. Por isso, sobre fundos verdes/escuros ele é sempre exibido dentro de
  um **selo branco arredondado** (`border-radius:10px; padding:6–12px`).
  - Tela de login (fundo claro): logo direto, sem selo.
  - Sidebar do admin e cabeçalho das TVs (fundo escuro): logo dentro do selo branco.
- **Não** distorcer, recolorir ou rotacionar o logo. Manter a proporção original.

---

## 🎨 Aplicação por componente

### Sidebar / Cabeçalhos (fundo escuro)
```css
background: var(--brand-petrol);   /* #0C3B38 */
color: var(--white);
```

### Botões principais
```css
background: var(--brand-teal);     /* #0F7C70 */
color: #fff;
border-radius: 8px;
```

### Badges / Pílulas / Realces
```css
background: var(--brand-lime);     /* #76C043 */
color: var(--brand-petrol);
```

### Cards
```css
background: #fff;
border-radius: 12px;
box-shadow: 0 2px 12px rgba(0,0,0,.1);
```

### Alertas (agenda / vencimentos)
```css
/* Atenção */
border-left: 4px solid var(--amber);   /* #FFAB40 */
/* Erro / vencido */
border-left: 4px solid var(--red);     /* #E06C75 */
```

---

## 🔤 Tipografia

```css
font-family: 'Roboto', 'Segoe UI', Arial, sans-serif;
```

A fonte **Roboto** é carregada via Google Fonts em cada tela, com fallback para
**Segoe UI** (importante para as TVs sem internet, onde o Roboto pode não carregar):

```html
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
```

### Pesos
- **300 (Light)** — subtítulos, descrições
- **400 (Regular)** — texto padrão
- **500 (Medium)** — labels, badges
- **700 (Bold)** — títulos, KPIs, números grandes

---

## ✅ Checklist de consistência

- [x] Paleta principal derivada do logo (verdes da marca)
- [x] Acento laranja (`--amber`) reservado para alertas
- [x] Logo em `frontend/assets/` (não na raiz)
- [x] Logo com selo branco sobre fundos escuros
- [x] Fonte Roboto com fallback Segoe UI nas 3 telas
- [x] Mesmas variáveis `:root` em login, admin e display
- [x] Texto branco sobre verde; texto escuro sobre claro

---

**Projeto:** TV Corporativa — Grupo Flexível
**Versão da identidade:** 1.0 (paleta híbrida verde)
**Base:** cores do logo oficial + estrutura/typografia do guia Material Design de referência
