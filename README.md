# Fiscal Finance

Bem-vindo ao **Fiscal Finance**, um sistema web integrado para gerenciamento administrativo, desenvolvido para simplificar operações de lojas e pequenas empresas.

A aplicação fornece uma interface moderna e centralizada para gerenciar o ciclo de vida operacional, desde o cadastro do produto até a emissão da nota fiscal e o registro financeiro, tudo consumindo uma API REST robusta.

---

## 🚀 Funcionalidades

- **Dashboard:** Visão geral da operação com métricas consolidadas em tempo real.
- **Produtos:** Catálogo completo com controle de SKU, precificação e alíquotas de imposto.
- **Estoque:** Registro de entradas e saídas e acompanhamento de saldos dinâmico.
- **Fiscal:** Calculadora que cruza a venda de produtos com a alíquota cadastrada, gerando simulações exatas para Nota Fiscal.
- **Caixa:** Controle financeiro (extrato e saldo) integrado, registrando automaticamente as vendas e permitindo o lançamento manual de despesas.
- **Usuários:** Gestão de usuários com controle de acesso por perfil (RBAC) — exclusivo para administradores.
- **API Tester:** Ferramenta embutida exclusiva para administradores testarem todos os endpoints do backend.

---

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.10 + Flask. Servidor responsável pela lógica de negócios, cálculos fiscais e conexão com o banco.
- **Banco de Dados:** SQLite (leve e embutido no projeto). Criado automaticamente na primeira execução.
- **Frontend:** Single Page Application (SPA) construída em HTML5, CSS3 nativo (com tema escuro profissional) e JavaScript puro (Vanilla JS), comunicando-se com a API via *fetch*.
- **Containerização:** Docker + Docker Compose para execução padronizada em qualquer ambiente.

---

## 📁 Estrutura do Projeto

```text
Fiscal-Finance/
├── backend/             # Lógica da API Flask (rotas, validações, banco de dados)
├── frontend/            # Toda a interface do usuário (Páginas, Scripts e Estilos)
├── docs/                # Documentação técnica e planejamento do sistema
├── data/                # Banco de dados SQLite (gerado automaticamente)
├── .github/workflows/   # Pipeline de CI/CD (GitHub Actions)
├── Dockerfile           # Definição da imagem Docker
├── docker-compose.yml   # Orquestração dos containers
├── run_docker.bat       # Inicializador automático via Docker (recomendado)
└── run_web.bat          # Inicializador local sem Docker (alternativo)
```

---

## 🐳 Execução via Docker (Recomendado)

Esta é a forma **oficial e padronizada** de rodar o sistema. Funciona em qualquer máquina com Docker instalado, sem precisar configurar Python ou dependências.

### 📋 Pré-requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado e **aberto/rodando**.

### 🚀 Execução Rápida (Windows)

1. **Abra o Docker Desktop** e aguarde ele iniciar completamente.
2. **Dê um duplo-clique** no arquivo `run_docker.bat` na raiz do repositório.
3. O script vai automaticamente:
   - Remover containers anteriores para evitar conflitos.
   - Fazer o build da imagem Docker.
   - Subir o container do sistema.
   - Aguardar a API iniciar.
   - Abrir o frontend no seu navegador em **http://localhost:8080**.

> **Banco de dados:** Se não existir nenhum banco de dados, o sistema cria um automaticamente na primeira execução. Uma mensagem de aviso será exibida no terminal do container. O sistema estará funcional, porém sem dados cadastrados.

### 🛑 Para parar o sistema

```bash
docker compose down
```

---

## ⚙️ Execução Local sem Docker (Alternativo)

Para desenvolvimento ou em ambientes sem Docker.

### 📋 Pré-requisitos

- **Python 3.8+** instalado (certifique-se de marcar a opção "Add Python to PATH" durante a instalação no Windows).

### 🚀 Execução

1. Dê um duplo-clique no arquivo `run_web.bat` na raiz do repositório.
2. O script vai automaticamente:
   - Verificar a instalação do Python e instalar dependências (`flask`, `flask-cors`, etc.).
   - Subir o servidor da API Flask na porta 5000.
   - Abrir a interface web (frontend) no seu navegador padrão.

---

## 🔑 Login Padrão

Para acessar o sistema, use as credenciais padrão de administrador:

| Campo | Valor |
|---|---|
| **E-mail** | `admin@fiscal.com` |
| **Senha** | `admin123` |

---

## 🔌 API e Integração

O backend foi projetado no padrão RESTful. A documentação completa de rotas e o contrato de API estão disponíveis em:

- **Swagger UI (interativo):** http://localhost:8080/docs (com o sistema rodando)
- **Documentação em arquivo:** [`docs/`](./docs/)

### Principais Endpoints

| Módulo | Método | Rota |
|---|---|---|
| Auth | POST | `/v1/fisc/auth/login` |
| Produtos | GET/POST | `/v1/fisc/products` |
| Estoque | POST | `/v1/fisc/stock/entry` |
| Nota Fiscal | POST | `/v1/fisc/invoice/intent` |
| Caixa | GET | `/v1/fisc/cashflow/balance` |
| API Pública | GET | `/v1/public/fisc/products/<sku>` |

---

## ⚙️ CI/CD — Deploy Automático

O repositório possui um pipeline de deploy automático via **GitHub Actions** (`.github/workflows/deploy.yml`).

### Como funciona

A cada `push` nas branches `main` ou `staging`:
1. A imagem Docker é **buildada** automaticamente.
2. A imagem é **enviada (push)** para o Docker Hub.
3. Um deploy é realizado na **VM do professor via SSH**, parando o container antigo e subindo o novo.

### Secrets necessários no GitHub

Para o pipeline funcionar, os seguintes **Secrets** devem estar configurados em:  
**GitHub → Settings → Secrets and variables → Actions**

| Secret | Descrição |
|---|---|
| `DOCKERHUB_USERNAME` | Seu nome de usuário no Docker Hub |
| `DOCKERHUB_TOKEN` | Token de acesso do Docker Hub (gerado em Account Settings → Security) |
| `VM_HOST` | IP ou hostname da VM do professor |
| `VM_USER` | Usuário SSH da VM (ex: `ubuntu`, `root`) |
| `VM_SSH_KEY` | Chave SSH privada para autenticação na VM (conteúdo do arquivo `id_rsa`) |

---

*Squad FISC — Gestão de Projetos 2026*
