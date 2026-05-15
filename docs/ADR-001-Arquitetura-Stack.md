# ADR 001: Decisão da Stack Tecnológica e Arquitetura Web

**Data:** Maio de 2026
**Status:** Aceito
**Autores:** Squad FISC

## Contexto

Inicialmente, o sistema Fiscal Finance foi idealizado como uma aplicação Desktop (utilizando interfaces Qt/PyQt). No entanto, ao longo do desenvolvimento e diante dos requisitos de integração com outros sistemas de negócio (outros Squads), escalabilidade e facilidade de deploy, a abordagem Desktop demonstrou-se limitante. Precisávamos de uma arquitetura que pudesse ser acessada em qualquer lugar, integrada facilmente via rede e que não exigisse instalação pesada nos clientes.

## Decisão

Pivotamos a arquitetura do projeto para uma arquitetura **Web (Client-Server)** com API RESTful. As seguintes escolhas de stack foram adotadas:

1. **Frontend: Single Page Application (SPA) com Vanilla JS, HTML5 e CSS3 Nativo**
   - **Por que:** Evitamos a complexidade de frameworks pesados (React/Angular) ou bundlers (Webpack/Vite) para focar na entrega rápida de valor. A utilização de Vanilla JS e Fetch API mantém o frontend extremamente leve e reduz a curva de aprendizado, permitindo que a equipe foque nas regras de negócio.
   - **Estilização:** CSS3 nativo foi utilizado em vez de frameworks como Tailwind para manter o controle absoluto sobre o layout, que possui temática escura (Dark Mode) profissional e responsiva.

2. **Backend: Python 3 com Flask**
   - **Por que:** Python é a linguagem principal do projeto e possui excelente legibilidade. Flask foi escolhido por ser um microframework flexível e leve, ideal para expor a API RESTful e implementar as calculadoras fiscais sem a sobrecarga de frameworks robustos (como Django).
   - **Segurança:** O Flask nos permitiu implementar nossa própria camada de autenticação com JWT e também a proteção baseada em `X-API-KEY` para os endpoints públicos.

3. **Banco de Dados: SQLite**
   - **Por que:** A simplicidade era o principal requisito. O SQLite é embutido em um arquivo (`app.db`), dispensando a configuração de servidores separados de banco de dados (como PostgreSQL ou MySQL). Para a nossa escala atual, atende perfeitamente e facilita a execução local e as demonstrações.

4. **Containerização: Docker e Docker Compose**
   - **Por que:** Ao distribuir o sistema, a instalação de dependências locais (Python, PIP, variáveis de ambiente) tornava a execução frágil. A containerização garantiu consistência total entre o ambiente de desenvolvimento, de demonstração e de deploy (produção).

## Consequências

- **Positivas:** 
  - A separação entre Frontend e Backend permitiu a criação de uma API Pública que pode ser consumida por outros Squads.
  - O deploy foi altamente simplificado (1 único comando Docker).
  - Experiência do usuário (UX) aprimorada através da SPA, que não exige o reload de páginas a cada ação.

- **Negativas/Trade-offs:** 
  - O uso do SQLite limita a escalabilidade de escrita concorrente em um cenário de altíssimo tráfego, algo que precisará ser reavaliado no futuro (migração possível para PostgreSQL).
  - O uso de Vanilla JS e manipulação manual do DOM pode se tornar verboso caso a interface cresça de maneira desproporcional nos próximos módulos.
