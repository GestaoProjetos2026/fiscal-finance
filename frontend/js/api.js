// ============================================================
// api.js — Camada de comunicação com a API Flask
// Todas as chamadas HTTP do sistema passam por aqui
// ============================================================

const API_BASE = '/v1/fisc';

// ─── Token JWT (localStorage) ────────────────────────────────
function getToken() {
  return localStorage.getItem('fisc_token');
}

function setToken(token) {
  localStorage.setItem('fisc_token', token);
}

function clearToken() {
  localStorage.removeItem('fisc_token');
  localStorage.removeItem('fisc_user');
}

function getUser() {
  try { return JSON.parse(localStorage.getItem('fisc_user')); }
  catch { return null; }
}

function setUser(user) {
  localStorage.setItem('fisc_user', JSON.stringify(user));
}

// ─── Fetch base com headers automáticos ──────────────────────
async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': token.startsWith('Bearer ') ? token : `Bearer ${token}` } : {}),
    ...(options.headers || {})
  };

  let res;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      ...options,
      headers
    });
  } catch (err) {
    console.error('Erro de conexão:', err);
    if (!options.silent) {
      if (window.toast) {
        window.toast('Falha de conexão com o servidor. Verifique se os contêineres estão ativos.', 'error');
      }
    }
    return { ok: false, status: 503, body: { message: 'Servidor indisponível no momento.' } };
  }

  let json = {};
  try {
    json = await res.json();
  } catch (e) {
    json = { message: 'Erro ao processar resposta do servidor.' };
  }

  if (!res.ok && !options.silent) {
    const errMsg = json.message || json.error || `Erro na requisição (${res.status})`;
    if (window.toast) {
      window.toast(errMsg, 'error');
    }
    // Se o token for inválido ou expirado, desloga automaticamente
    if (res.status === 401) {
      clearToken();
      window.location.href = 'index.html';
    }
  }

  return { ok: res.ok, status: res.status, body: json };
}

// ─── AUTH ─────────────────────────────────────────────────────
const Auth = {
  // LOGIN ANTIGO (Desativado)
  // async login(email, senha) {
  //   return apiFetch('/auth/login', {
  //     method: 'POST',
  //     body: JSON.stringify({ email, senha })
  //   });
  // },
  
  // LOGIN OAUTH2 (Novo)
  async login(email, senha) {
    const params = new URLSearchParams();
    params.append('grant_type', 'password');
    params.append('username', email);
    params.append('password', senha);

    return apiFetch('/oauth/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: params.toString()
    });
  },
  async logout() {
    const r = await apiFetch('/auth/logout', { method: 'POST' });
    clearToken();
    return r;
  },
  async me() {
    return apiFetch('/auth/me');
  }
};

// ─── USUÁRIOS (Admin) ─────────────────────────────────────────
const Usuarios = {
  async listar() {
    return apiFetch('/usuarios');
  },
  async criar(dados) {
    return apiFetch('/usuarios', {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },
  async editarPapel(id, papel) {
    return apiFetch(`/usuarios/${id}/role`, {
      method: 'PUT',
      body: JSON.stringify({ papel })
    });
  },
  async remover(id) {
    return apiFetch(`/usuarios/${id}`, {
      method: 'DELETE'
    });
  }
};

// ─── PRODUTOS ─────────────────────────────────────────────────
const Produtos = {
  async listar(nome = '') {
    const q = nome ? `?nome=${encodeURIComponent(nome)}` : '';
    return apiFetch(`/products${q}`);
  },
  async buscar(sku) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`);
  },
  async criar(dados) {
    return apiFetch('/products', {
      method: 'POST',
      body: JSON.stringify(dados)
    });
  },
  async editar(sku, dados) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`, {
      method: 'PUT',
      body: JSON.stringify(dados)
    });
  },
  async remover(sku) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`, {
      method: 'DELETE'
    });
  }
};

// ─── ESTOQUE ──────────────────────────────────────────────
// Saldo via products (saldo_estoque = produtos.estoque)
// Entradas: POST /stock/entry (FISC-19)
// Saídas:   via invoice/confirm (baixa automática)
const Estoque = {
  async listar() {
    return apiFetch('/products');
  },
  async buscar(sku) {
    return apiFetch(`/products/${encodeURIComponent(sku)}`);
  },
  async registrarEntrada(sku, quantidade, motivo) {
    return apiFetch('/stock/entry', {
      method: 'POST',
      body: JSON.stringify({ sku, quantidade, motivo })
    });
  }
};

// ─── NOTA FISCAL ──────────────────────────────────────────────
const Notas = {
  async calcularIntencao(itens, markup = 0) {
    return apiFetch('/invoice/intent', {
      method: 'POST',
      body: JSON.stringify({ itens, markup })
    });
  },
  async confirmar(numero, descricao, itens, markup = 0) {
    return apiFetch('/invoice/confirm', {
      method: 'POST',
      body: JSON.stringify({ numero, descricao, itens, markup })
    });
  },
  async buscar(numero) {
    return apiFetch(`/invoice/${encodeURIComponent(numero)}`);
  }
};

// ─── CAIXA ────────────────────────────────────────────────────
const Caixa = {
  async saldo() {
    return apiFetch('/cashflow/balance');
  },
  async extrato(from, to) {
    return apiFetch(`/cashflow/statement?from=${from}&to=${to}`);
  },
  async registrarDespesa(descricao, valor, data = null) {
    const body = { descricao, valor };
    if (data) body.data = data;
    return apiFetch('/cashflow/expense', {
      method: 'POST',
      body: JSON.stringify(body)
    });
  }
};

// ─── Exporta globalmente ──────────────────────────────────────
window.API = { Auth, Usuarios, Produtos, Estoque, Notas, Caixa };
window.getToken = getToken;
window.setToken = setToken;
window.clearToken = clearToken;
window.getUser = getUser;
window.setUser = setUser;
