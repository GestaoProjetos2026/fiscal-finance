# Endpoints da API — Squad FISC

> **Versão:** 2.0 · **Atualizado:** Maio/2026 · **Equipe:** Squad FISC
> **Base URL (local):** `http://localhost:8080`
> **Base URL (produção):** `http://<ip-servidor>:8080`
> **Documentação interativa (Swagger):** `GET /docs`

---

## Padrão de Resposta

Todos os endpoints seguem o mesmo envelope JSON:

```json
{
  "status": "success" | "error",
  "data": { ... } | null,
  "message": "Mensagem legível"
}
```

| Situação | HTTP |
|---|---|
| Sucesso | `200 OK` |
| Criado | `201 Created` |
| Dados inválidos | `400 Bad Request` |
| Não autorizado (token ausente/expirado) | `401 Unauthorized` |
| Acesso negado (permissão insuficiente) | `403 Forbidden` |
| Não encontrado | `404 Not Found` |
| Conflito (duplicado) | `409 Conflict` |
| Erro de negócio (ex: estoque insuficiente) | `422 Unprocessable Entity` |
| Erro interno | `500 Internal Server Error` |

---

## Autenticação Privada (JWT)

Rotas privadas exigem o header:
```
Authorization: Bearer <token>
```
O token é obtido via `POST /v1/fisc/auth/login`.

---

## 🔐 AUTH — `/v1/fisc/auth`

### `POST /v1/fisc/oauth/token`
Realiza o login centralizado de forma híbrida contra o Core Engine (REST API) ou com fallback local automático (SQLite + Bcrypt) caso o Core esteja offline. Retorna um token JWT do Fiscal válido por 24h.

**Headers:**
```
Content-Type: application/json  (também suporta application/x-www-form-urlencoded)
```

**Body (JSON ou Form-Data):**
```json
{
  "grant_type": "password",
  "username": "kevin@fiscal.com",
  "password": "SenhaDoCore123!"
}
```

**Resposta (`200` - Autenticação via Core):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 8,
      "nome": "Kevin",
      "papel": "viewer",
      "tipo": "externo"
    }
  },
  "message": "Login realizado com sucesso via Core Engine."
}
```

**Resposta (`200` - Fallback local offline):**
```json
{
  "status": "success",
  "data": {
    "access_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 86400,
    "user": {
      "id": 2,
      "nome": "Chefe Fiscal",
      "papel": "admin",
      "tipo": "local"
    }
  },
  "message": "Login local realizado com sucesso."
}
```

> **Nota:** O campo `user.tipo` indica se o usuário logado foi autenticado externamente via Core (`externo`) ou via banco local SQLite com Bcrypt (`local`). A rota suporta payload JSON ou Form-Data.

---

### `GET /v1/fisc/auth/me` `[JWT]`
Retorna os dados do usuário autenticado pelo token.

**Resposta (`200`):**
```json
{
  "status": "success",
  "data": { "id": 1, "nome": "Administrador", "email": "admin@fiscal.com", "papel": "admin", "criado_em": "..." },
  "message": "Dados do usuário logado."
}
```

---

### `POST /v1/fisc/auth/logout` `[JWT]`
Logout stateless — o cliente deve descartar o token localmente.

**Resposta (`200`):**
```json
{ "status": "success", "data": null, "message": "Logout realizado. Descarte o token no cliente." }
```

---

## 📦 PRODUTOS — `/v1/fisc/products`

### `GET /v1/fisc/products`
Lista todos os produtos. Aceita filtro opcional por nome.

**Query params:** `?nome=caneta` *(opcional)*

**Resposta (`200`):**
```json
{
  "status": "success",
  "data": [
    { "sku": "PROD-001", "nome": "Caneta Azul", "preco_base": 2.50, "aliquota": 0.12, "estoque": 45, "saldo_estoque": 45 }
  ],
  "message": "1 produto(s) encontrado(s)"
}
```

---

### `GET /v1/fisc/products/<sku>`
Busca um produto pelo SKU.

**Resposta (`200`):** mesmo formato do item acima.
**Resposta (`404`):** produto não encontrado.

---

### `POST /v1/fisc/products`
Cria um novo produto. SKU deve ser único.

**Body:**
```json
{ "sku": "PROD-001", "nome": "Caneta Azul", "preco_base": 2.50, "aliquota_imposto": 0.12 }
```

**Resposta (`201`):** produto criado.
**Resposta (`409`):** SKU já existe.

> **Regras:** `preco_base` > 0 | `aliquota_imposto` entre 0 e 1

---

### `PUT /v1/fisc/products/<sku>`
Atualiza nome, preço ou alíquota de um produto. **SKU é imutável.**

**Body (todos opcionais):**
```json
{ "nome": "Caneta Vermelha", "preco_base": 3.00, "aliquota_imposto": 0.15 }
```

**Resposta (`200`):** produto atualizado.

---

### `DELETE /v1/fisc/products/<sku>`
Remove um produto pelo SKU.

**Resposta (`200`):** produto removido.
**Resposta (`409`):** não é possível remover — produto possui movimentações de estoque vinculadas.

---

## 📊 ESTOQUE — `/v1/fisc/stock`

### `POST /v1/fisc/stock/entry`
Registra entrada de estoque (compra/reposição). Impacta `produtos.estoque`, registra em `estoque_mov` e lança custo de compra no caixa.

**Body:**
```json
{ "sku": "PROD-001", "quantidade": 10, "motivo": "Compra fornecedor X" }
```

**Resposta (`201`):**
```json
{
  "status": "success",
  "data": {
    "sku": "PROD-001", "nome": "Caneta Azul",
    "tipo": "entrada", "quantidade": 10,
    "motivo": "Compra fornecedor X",
    "custo_total": 25.00, "saldo_atual": 55
  },
  "message": "Entrada de 10 unidade(s) registrada. Saldo atual: 55."
}
```

> **Nota:** O SKU enviado é convertido automaticamente para maiúsculas.

---

## 🧾 NOTA FISCAL — `/v1/fisc/invoice`

### `POST /v1/fisc/invoice/intent`
Calcula os valores de uma nota fiscal **sem salvar** no banco. Útil para pré-visualização.

**Body:**
```json
{ "itens": [{ "sku": "PROD-001", "quantidade": 2 }] }
```

**Resposta (`200`):**
```json
{
  "status": "success",
  "data": {
    "itens": [{ "sku": "PROD-001", "nome": "Caneta Azul", "quantidade": 2, "preco_unitario": 2.50, "aliquota": 0.12, "valor_bruto": 5.00, "valor_imposto": 0.60, "valor_total": 5.60 }],
    "skus_invalidos": [],
    "totais": { "total_bruto": 5.00, "total_imposto": 0.60, "total_final": 5.60 }
  },
  "message": "Intenção calculada. Use /invoice/confirm para confirmar."
}
```

---

### `POST /v1/fisc/invoice/confirm`
Confirma a nota fiscal. **Operação atômica:** valida estoque, baixa estoque, salva nota e registra entrada no caixa.

**Body:**
```json
{ "numero": "NF-2026-001", "descricao": "Venda loja", "itens": [{ "sku": "PROD-001", "quantidade": 2 }] }
```

**Resposta (`201`):** nota emitida com sucesso.
**Resposta (`409`):** número de nota já existe.
**Resposta (`422`):** estoque insuficiente para algum SKU.

---

### `GET /v1/fisc/invoice/<numero>`
Busca uma nota fiscal com todos os seus itens e totais.

**Resposta (`200`):**
```json
{
  "status": "success",
  "data": {
    "nota": { "id": 1, "numero_nota": "NF-2026-001", "status": "emitida", "data_criacao": "..." },
    "itens": [...],
    "totais": { "total_final": 5.60, "num_itens": 1 }
  },
  "message": "Nota encontrada."
}
```

---

## 💰 CAIXA — `/v1/fisc/cashflow`

### `GET /v1/fisc/cashflow/balance`
Retorna o saldo atual do caixa em tempo real.

**Resposta (`200`):**
```json
{
  "status": "success",
  "data": {
    "total_entradas": 3500.00,
    "total_despesas": 1980.00,
    "saldo_liquido": 1520.00,
    "detalhamento": {
      "receita_vendas": 3500.00,
      "despesas_manuais": 800.00,
      "custo_compras": 1180.00
    }
  },
  "message": "Saldo calculado com sucesso."
}
```

---

### `POST /v1/fisc/cashflow/expense`
Registra uma despesa manual no caixa.

**Body:**
```json
{ "descricao": "Aluguel", "valor": 1200.00, "data": "2026-05-01" }
```

> `data` é opcional. Formato: `YYYY-MM-DD`.

**Resposta (`201`):** despesa registrada.

---

### `GET /v1/fisc/cashflow/statement?from=&to=`
Retorna todas as transações do caixa em um período.

**Query params obrigatórios:** `from=YYYY-MM-DD` e `to=YYYY-MM-DD`

**Resposta (`200`):**
```json
{
  "status": "success",
  "data": {
    "periodo": { "from": "2026-05-01", "to": "2026-05-31" },
    "subtotal_entradas": 3500.00,
    "subtotal_despesas": 1980.00,
    "saldo_periodo": 1520.00,
    "transacoes": [
      { "origem": "venda_estoque", "tipo": "entrada", "descricao": "Receita NF-2026-001", "valor_liquido": 5.60, "data_registro": "..." }
    ]
  },
  "message": "1 transação(ões) encontrada(s) no período."
}
```

> **Origens possíveis:** `venda_estoque` | `despesa_manual` | `compra_estoque`

---

## 👥 USUÁRIOS — `/v1/fisc/usuarios` `[JWT + Admin]`

Rotas exclusivas para usuários com `papel = admin`.

### `GET /v1/fisc/usuarios`
Lista todos os usuários cadastrados.

### `POST /v1/fisc/usuarios`
Cria um novo usuário.

**Body:**
```json
{ "nome": "João Silva", "email": "joao@empresa.com", "senha": "senha123", "papel": "usuario" }
```

> **Papéis disponíveis:** `admin` | `usuario`

### `PUT /v1/fisc/usuarios/<id>/role`
Altera o papel de um usuário.

**Body:** `{ "papel": "admin" }`

### `DELETE /v1/fisc/usuarios/<id>`
Remove um usuário. Não é possível excluir a própria conta.

---

## 🌐 API PÚBLICA — `/v1/public/fisc` `[X-API-KEY]`

Endpoints somente leitura para integração inter-squads. Exigem o header:
```
X-API-KEY: <chave>
```

| Squad | Chave |
|---|---|
| Squad 1 — Core Engine & Auth | `FISC-PUBLIC-2026-SQUAD1` |
| Squad 3 — CRM | `FISC-PUBLIC-2026-SQUAD3` |
| Squad 4 — Service Desk | `FISC-PUBLIC-2026-SQUAD4` |
| Desenvolvimento | `FISC-PUBLIC-2026-DEV` |

---

### `GET /v1/public/fisc/products/<sku>`
Consulta produto por SKU. Retorna dados básicos + saldo de estoque.

### `GET /v1/public/fisc/stock/<sku>`
Retorna saldo de estoque atual e data da última movimentação.

### `GET /v1/public/fisc/cashflow/summary`
Retorna resumo financeiro consolidado: saldo, entradas, despesas e impostos.

### `GET /v1/public/fisc/history/<sku>`
Retorna histórico completo de movimentações (entrada/saída) de um produto por SKU.

---

*Squad FISC — Gestão de Projetos 2026 | Atualizado: Maio/2026*
