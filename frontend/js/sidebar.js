// ============================================================
// sidebar.js — Injeta a sidebar e topbar em todas as páginas
// ============================================================

function injectLayout(pageId, pageTitle) {
  const sidebarHTML = `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <div class="logo-icon">💼</div>
          <div>
            <div class="logo-text">Fiscal Finance</div>
            <div class="logo-sub">Squad FISC</div>
          </div>
        </div>
      </div>

      <nav class="sidebar-nav">
        <div class="nav-section-label">Principal</div>

        <a class="nav-item" data-page="dashboard" href="dashboard.html">
          <span class="nav-icon">📊</span> Dashboard
        </a>

        <div class="nav-section-label">Módulos</div>

        <a class="nav-item" data-page="produtos" href="produtos.html">
          <span class="nav-icon">📦</span> Produtos
        </a>

        <a class="nav-item" data-page="estoque" href="estoque.html">
          <span class="nav-icon">🏭</span> Estoque
        </a>

        <a class="nav-item" data-page="fiscal" href="fiscal.html">
          <span class="nav-icon">🧾</span> Fiscal
        </a>

        <a class="nav-item" data-page="caixa" href="caixa.html">
          <span class="nav-icon">💰</span> Fluxo de Caixa
        </a>

        <a class="nav-item" data-page="notas" href="notas.html">
          <span class="nav-icon">📄</span> Notas Fiscais
        </a>

        <div class="nav-section-label">Ferramentas</div>

        <a class="nav-item" data-page="usuarios" href="usuarios.html" id="nav-usuarios" style="display:none;">
          <span class="nav-icon">👥</span> Gestão de Usuários
        </a>

        <a class="nav-item" data-page="api-tester" href="api-tester.html" id="nav-api-tester" style="display:none;">
          <span class="nav-icon">🧪</span> API Tester
        </a>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <div class="user-avatar" id="sidebar-avatar">A</div>
          <div class="user-details">
            <div class="user-name" id="sidebar-user-name">Carregando...</div>
            <div class="user-role" id="sidebar-user-role">—</div>
          </div>
          <a href="api-tester.html" class="btn-settings" title="Opções" id="btn-sidebar-settings" style="display:none; text-decoration:none; margin-right:12px; font-size:16px; color:var(--text-light); transition:color 0.2s;" onmouseover="this.style.color='var(--primary)'" onmouseout="this.style.color='var(--text-light)'">⚙️</a>
          <button class="btn-logout" title="Sair" onclick="handleLogout()">⏻</button>
        </div>
      </div>
    </aside>

    <div class="main-content">
      <header class="topbar">
        <div class="flex-center gap-12">
          <button class="menu-toggle" id="menu-toggle" style="display:none;" onclick="toggleSidebar()">
            ☰
          </button>
          <span class="topbar-title" id="topbar-title">${pageTitle}</span>
        </div>
        <div class="topbar-right">
          <span style="font-size:12px;color:var(--text-secondary);" id="topbar-clock"></span>
        </div>
      </header>
      <div class="page-content" id="page-content">
  `;

  // Injeta antes do conteúdo existente do body
  const body = document.body;
  const existingContent = body.innerHTML;
  body.innerHTML = `
    <div class="app-layout">
      ${sidebarHTML}
        ${existingContent}
      </div>
    </div>
  `;

  // Adiciona toast container
  const toastDiv = document.createElement('div');
  toastDiv.id = 'toast-container';
  document.body.appendChild(toastDiv);

  // Marca nav ativo
  setActiveNav(pageId);

  // Preenche dados do user
  fillUserSidebar();

  // Regras de controle de acesso visual (IAM / Frontend)
  const _u = getUser();
  if (_u) {
    // Identificar Chefe e Admin Local
    const isChefe = _u.email === 'chefe@fiscal.com' || (_u.nome && _u.nome.toLowerCase().includes('chefe'));
    const isLocalAdmin = _u.papel === 'admin' && !isChefe && _u.tipo === 'local';

    // 1. Mostrar Gestão de Usuários apenas para o Admin Local standalone (não Chefe, não Externo)
    const navUsuarios = document.getElementById('nav-usuarios');
    if (navUsuarios) {
      if (isLocalAdmin) {
        navUsuarios.style.display = '';
      } else {
        navUsuarios.style.display = 'none';
      }
    }

    // 2. Exibição da aba API Tester na sidebar principal (apenas para Admin Local principal, não Chefe)
    const navTester = document.getElementById('nav-api-tester');
    if (navTester) {
      if (isLocalAdmin) {
        navTester.style.display = '';
      } else {
        navTester.style.display = 'none';
      }
    }

    // 3. Exibição da engrenagem de Opções no rodapé (para Chefe e Admin Local)
    const btnSettings = document.getElementById('btn-sidebar-settings');
    if (btnSettings) {
      if (_u.papel === 'admin') {
        btnSettings.style.display = 'inline-block';
      } else {
        btnSettings.style.display = 'none';
      }
    }
  }

  // Relógio no topbar
  function updateClock() {
    const el = document.getElementById('topbar-clock');
    if (el) el.textContent = new Date().toLocaleTimeString('pt-BR');
  }
  updateClock();
  setInterval(updateClock, 1000);
}

// ─── Toggle Sidebar (Responsive) ──────────────────────────────
function toggleSidebar() {
  const sb = document.getElementById('sidebar');
  if (sb) sb.classList.toggle('open');
}

window.injectLayout = injectLayout;
window.toggleSidebar = toggleSidebar;
