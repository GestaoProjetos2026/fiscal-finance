# 🧾 Fiscal Finance · Conexus ERP
> **Squad FISC** · O núcleo inteligente de faturamento fiscal, controle de caixa atômico e rastreabilidade física de estoque do Conexus ERP.

---

[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?logo=docker&logoColor=white)](https://www.docker.com/)
[![Flask](https://img.shields.io/badge/Flask-v3.0-lightgrey?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLite](https://img.shields.io/badge/SQLite-v3-blue?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![UI Nativo](https://img.shields.io/badge/UI-Vanilla_HTML5_/_CSS3_/_JS-orange?logo=javascript&logoColor=white)]()
[![GitHub version](https://img.shields.io/badge/version-v1.1.1-brightgreen)](https://github.com/GestaoProjetos2026/fiscal-finance)
[![Licença](https://img.shields.io/badge/license-Academic_ERP-green)](https://github.com/GestaoProjetos2026/fiscal-finance)

O **Fiscal Finance** é um módulo de alta performance web projetado para gerenciar de forma atômica e integrada as operações fiscais, financeiras e de logística de estoque de pequenas e médias empresas dentro do ecossistema Conexus ERP. 

Desenvolvido sob uma arquitetura de microsserviços desacoplada, o sistema realiza simulações fiscais, processamento de Notas Fiscais (DANFE), controle de estoque físico e fluxo de caixa de forma 100% transacional e automatizada.

---

## 🗺️ Visão Geral do Produto (Conexus ERP)

Dentro do ecossistema Conexus ERP, o Fiscal Finance atua como a **fonte centralizadora da verdade fiscal e financeira**, realizando integrações inter-squads via APIs de microsserviços:

* **Faturamento de Vendas (CRM - Squad 3):** Recebe intenções de nota (`/invoice/intent`) e confirmações de faturamento (`/invoice/confirm`) para calcular impostos em tempo real, diminuir saldo físico no estoque e gerar o documento auxiliar de nota fiscal (DANFE).
* **Auditoria e Service Desk (Squad 4):** Exibe logs históricos completos de movimentações físicas de estoque (`/public/fisc/history/<sku>`) para ajudar analistas de suporte a auditar devoluções e rastrear extravios.
* **Segurança e Conformidade IAM (Core - Squad 1):** Realiza autenticação centralizada por Single Sign-On (SSO) baseada em JWT, bloqueando de forma rígida (403) o papel `suporte` (Service Desk) de visualizar faturamento financeiro.

---

## 🎨 Diagrama de Arquitetura e Fluxo de Rede

O Fiscal Finance é executado de forma totalmente containerizada e isolada no mesmo cluster Docker que os outros módulos do ERP, utilizando uma rede comum compartilhada de alto desempenho:

```mermaid
flowchart TB
    subgraph Portal [Portal Conexus & Roteamento - Squad 5]
        Gateway[Nginx Gateway\nlocalhost:80 / 8080]
    end

    subgraph Core [Identity & Central IAM - Squad 1]
        CoreBackend[erp-backend\nlocalhost:3000]
        CorePostgres[(PostgreSQL\nerp_core)]
        CoreBackend <--> CorePostgres
    end

    subgraph Fiscal [Módulo Fiscal Finance - Squad 2]
        FiscFront[container-fisc-frontend\nlocalhost:8080]
        FiscBack[container-fisc-backend\nlocalhost:5000]
        FiscSQLite[(SQLite Local\ndata/app.db)]
        FiscBack <--> FiscSQLite
    end

    subgraph CRM [CRM & Vendas - Squad 3]
        CRM_App[CRM App\nlocalhost:80]
    end

    subgraph Support [Service Desk - Squad 4]
        Desk_App[Support App\nlocalhost:80]
    end

    %% Roteamento do Gateway
    Gateway -->|/v1/auth & /v1/integration| CoreBackend
    Gateway -->|/v1/fisc| FiscBack
    Gateway -->|Servir SPA Fiscal| FiscFront

    %% Comunicações e APIs
    FiscBack -->|1. Autenticar SSO REST| CoreBackend
    FiscBack -->|2. Identidade M2M X-Tenant-Id| CoreBackend
    CRM_App -->|Consultar Estoque X-API-KEY| FiscBack
    CRM_App -->|Confirmar Venda /invoice| FiscBack
    Desk_App -->|Auditar Movimentações X-API-KEY| FiscBack

    classDef fiscStyle fill:#2b5c8f,stroke:#1a365d,color:#ffffff,stroke-width:2px;
    classDef coreStyle fill:#4b3a6f,stroke:#2d2242,color:#ffffff;
    classDef otherStyle fill:#1b4d3e,stroke:#0d2b1f,color:#ffffff;
    
    class FiscFront,FiscBack,FiscSQLite fiscStyle;
    class CoreBackend,CorePostgres coreStyle;
    class CRM_App,Desk_App otherStyle;
```

### O Segredo de Ouro: Transacionalidade Atômica
Toda confirmação de nota fiscal (`/v1/fisc/invoice/confirm`) é protegida por uma transação lógica rigorosa: se a baixa no estoque físico de qualquer SKU falhar, a inserção correspondente no fluxo de caixa é cancelada imediatamente, eliminando qualquer risco de divergência contábil.

---

## 🛠️ Pré-requisitos de Instalação

Para rodar o Fiscal Finance em uma máquina limpa em menos de **10 minutos**, certifique-se de possuir:

1. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** (v20+ com Docker Compose habilitado).
2. **Git** para clonar o repositório.
3. **[Requisito Externo do ERP] Rede Compartilhada Docker:** O ecossistema Conexus ERP exige uma rede Docker em ponte externa pré-criada para permitir que as squads se enxerguem por hostname. Crie-a no terminal com o seguinte comando:
   ```bash
   docker network create core-engine-main_erp-network
   ```

---

## 🚀 Guia de Execução Rápida (Step-by-Step)

### Passo 1: Clonar o Repositório
```bash
git clone https://github.com/GestaoProjetos2026/fiscal-finance.git
cd fiscal-finance
```

### Passo 2: Configurar o Arquivo `.env`
O projeto necessita de um arquivo de configuração de variáveis na raiz. Duplique o arquivo de exemplo e crie o `.env`:
* **Linux/macOS:** `cp .env.example .env`
* **Windows (PowerShell):** `Copy-Item .env.example .env`
* **Windows (CMD):** `copy .env.example .env`

> [!NOTE]
> As variáveis padrão contidas em `.env.example` estão otimizadas para rodar localmente no Docker sem necessidade de nenhuma alteração!

### Passo 3: Executar a Aplicação

#### Opção A: Execução via docker-compose (Recomendado/Universal)
Execute o comando abaixo para realizar o build e subir os contêineres em segundo plano:
```bash
docker compose up -d --build
```

#### Opção B: Execução via Script Assistente (Windows - Recomendado)
Se você estiver rodando em ambiente Windows com o Docker Desktop aberto, basta dar um **duplo clique** no arquivo assistente:
* **[run_docker.bat](run_docker.bat)**: Ele verifica as portas, valida se a rede externa existe (e a cria silenciosamente se necessário) e inicia os contêineres abrindo a SPA automaticamente no seu navegador.


## 🌐 Acesso ao Ambiente de Produção (Nuvem / Kubernetes)

O sistema está totalmente implantado e orquestrado no cluster Kubernetes de Produção. Utilize os links oficiais abaixo para acessar e monitorar:

### 📱 Sistema Fiscal Finance (Interface Web em Produção)
* **URL de Produção:** [https://app.fiscal-finance.40.82.176.176.nip.io/index.html](https://app.fiscal-finance.40.82.176.176.nip.io/index.html)
* **Opções de Acesso:** O sistema suporta dois tipos de autenticação (Local ou Federada integrada ao Core):
  1. **Autenticação Federada (Core Engine SSO):**
     * **E-mail:** `fiscal@example.com`
     * **Senha:** `Fiscal123!`
  2. **Autenticação Local (SQLite do Fiscal):**
     * **E-mail:** `admin@fiscal.com`
     * **Senha:** `admin123`

### 📊 Observabilidade e Logs (Grafana + Loki)
* **Painel Grafana (Dashboard Conexus):** [http://grafana.40.82.176.176.nip.io/d/e678880d-2ab5-4bd1-9819-311beda19b14/conexus?orgId=1](http://grafana.40.82.176.176.nip.io/d/e678880d-2ab5-4bd1-9819-311beda19b14/conexus?orgId=1)
  > [!TIP]
  > Caso a rede local (como o FortiGuard da Unisanta) bloqueie o tráfego HTTP para domínios `.nip.io`, acesse de forma segura via HTTPS: [https://grafana.40.82.176.176.nip.io/d/e678880d-2ab5-4bd1-9819-311beda19b14/conexus?orgId=1](https://grafana.40.82.176.176.nip.io/d/e678880d-2ab5-4bd1-9819-311beda19b14/conexus?orgId=1)
* **Credenciais de Acesso:**
  * **Usuário:** `admin`
  * **Senha:** `admin123`

---

## 🔑 Acesso ao Sistema Local (Ambiente de Desenvolvimento)

Assim que o contêiner subir localmente, as seguintes URLs estarão imediatamente disponíveis em localhost:

* **Painel Web (Frontend SPA Local):** [http://localhost:8080](http://localhost:8080)
* **API Swagger UI (Backend docs):** [http://localhost:5000/docs](http://localhost:5000/docs)
* **Especificação OpenAPI Raw:** [http://localhost:5000/apispec.json](http://localhost:5000/apispec.json)

### Credenciais para Testes Locais e Demos:

#### A. Administrador Local Standalone (Exclusivo do Módulo Fiscal)
* **Usuário:** `admin@fiscal.com`
* **Senha:** `admin123`
* *Acesso:* Libera todas as abas, incluindo o **API Tester** e a **Gestão de Usuários** local.

#### B. Administrador Central do Core (SSO SSO)
* **Usuário:** `admin@example.com`
* **Senha:** `Password123!`
* *Acesso:* Login autenticado de forma híbrida contra o banco PostgreSQL do Core Engine.

#### C. Agente de Suporte (Demonstração de Bloqueio - Squad 4)
* **Usuário:** `suporte@example.com`
* **Senha:** `Suporte123!`
* *Acesso:* Login via SSO. Demonstra o **bloqueio visual e lógico**: a aba de Gestão de Usuários fica oculta e qualquer requisição às telas restritas do Fiscal retorna **`403 Forbidden`**.

---

## ⚙️ Guia de Variáveis de Ambiente (`.env`)

| Chave | Padrão no Docker | Descrição |
|---|---|---|
| `SECRET_KEY` | `sua_chave_secreta_super_segura_aqui` | Chave criptográfica usada para assinar e garantir a integridade de JWTs locais. |
| `DB_PATH` | `/app/data/app.db` | Diretório de persistência do banco de dados SQLite dentro do volume montado. |
| `CORE_BACKEND_URL` | `http://erp-backend:3000` | URL/Host DNS do back-end do Core Engine utilizado para chamadas de login e M2M. |
| `CORE_ENGINE_URL` | `http://erp-backend:3000` | Alias do hostname do Core Engine (fallback). |
| `DATABASE_URL` | `postgresql://admin:admin123@erp-postgres:5432/erp_core` | String de conexão opcional com o Postgres central para fins de debug e seeds integrados. |

---

## 🔌 Integração de APIs com Outros Módulos (Inter-Squads)

Os outros módulos interagem com o Fiscal Finance de duas formas principais:

### 1. Autenticação Central por SSO (OAuth2 - Password Grant)
Qualquer usuário humano autenticado no Core Engine pode logar no Fiscal. O Fiscal troca as credenciais no Core e emite seu próprio JWT local.
* **Endpoint:** `POST /v1/fisc/oauth/token`
* **Payload:**
  ```json
  {
    "grant_type": "password",
    "username": "kevin@fiscal.com",
    "password": "SenhaDoCore123!"
  }
  ```
* **Retorno Importante (`user.tipo`):** O JSON de sucesso retorna `"tipo": "externo"` (autenticado no Core) ou `"tipo": "local"`. O frontend consome essa flag para ocultar a aba "Gestão de Usuários" para usuários externos, redirecionando o fluxo IAM para o Core.

### 2. Leitura Rápida e Auditoria Física (APIs Públicas com `X-API-KEY`)
Endpoints somente leitura (`GET`) que exigem a passagem da chave de API acordada no Header da requisição:
```http
X-API-KEY: FISC-PUBLIC-2026-SQUAD3
```

* **`GET /v1/public/fisc/stock/<sku>`**: Consulta saldo e última data de movimentação de um produto.
* **`GET /v1/public/fisc/products/<sku>`**: Consulta catálogo básico de produtos (sem dados de custo/margem).
* **`GET /v1/public/fisc/history/<sku>`**: Histórico físico detalhado de entradas e saídas (para auditoria da Squad 4).
* **`GET /v1/public/fisc/cashflow/summary`**: Resumo consolidado do fluxo de caixa e impostos.

---

## 🔧 Troubleshooting (Solução de Problemas Comuns)

#### 1. Erro `network core-engine-main_erp-network not found` ao subir contêineres
* **Causa:** O Docker Compose tenta se ligar à rede externa de integração das squads, mas a rede não foi criada na sua máquina.
* **Solução:** Crie a rede executando no seu terminal:
  ```bash
  docker network create core-engine-main_erp-network
  ```

#### 2. Porta 5000 ou 8080 já em uso
* **Causa:** Outro serviço (como o macOS AirPlay Receiver na porta 5000 ou um container Tomcat/Web na 8080) já está ouvindo.
* **Solução:** Pare o serviço conflitante ou edite as portas mapeadas do host em `docker-compose.yml` (seção `ports` sob os serviços `backend` ou `frontend`).

#### 3. Usuário logado aparece como "Usuário Core" na sidebar
* **Causa:** O front-end carrega o perfil de usuário armazenado em `localStorage`. Caso a sincronização da API M2M com o Core tenha falhado temporariamente no primeiro login ou o cache local esteja antigo, ele exibe o placeholder padrão.
* **Solução:** Clique no botão de sair (**⏻**) no rodapé da sidebar para invalidar a sessão atual e logue novamente. O sistema irá disparar uma nova query M2M e atualizar seu nome real automaticamente.

---

## 👥 Contribuição e Licença

Este projeto é desenvolvido para fins acadêmicos e de portfólio tecnológico sob a licença **Academic ERP Conexus**. PRs de otimização de consultas SQL e segurança de headers de proxy são bem-vindos!

**Squad FISC — Gestão de Projetos 2026**
