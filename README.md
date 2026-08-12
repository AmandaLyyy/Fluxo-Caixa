# CashFlow Dashboard

Sistema web de controle de fluxo de caixa desenvolvido para centralizar e automatizar a gestão financeira empresarial, substituindo planilhas Excel por uma interface visual interativa e um banco de dados relacional.

## Sobre o sistema

O CashFlow Dashboard consolida em uma única aplicação o controle de saldos bancários, projeção de caixa, registro de pagamentos, gestão de títulos a pagar e a receber, contratos de capital de giro e endividamento por banco. Os dados são inseridos via importação de planilha Excel ou diretamente pela interface, e persistidos em banco MySQL com atualização em tempo real via API REST.

A aplicação possui autenticação por senha com sessão de 30 minutos, exportação de dados em CSV e uma seção de configurações que permite gerenciar bancos, categorias de saída e contratos sem necessidade de acesso ao banco de dados.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3 · Flask · Flask-CORS |
| Banco de dados | MySQL · mysql-connector-python |
| Frontend | HTML5 · CSS3 · JavaScript · Chart.js |
| Importação | openpyxl |
| Autenticação futura | Microsoft Graph API (Outlook) |

## Arquitetura

```
CashFlow-Dashboard/
├── backend/
│   └── app.py              ← API REST (Flask) com 25+ endpoints
├── database/
│   └── schema.sql          ← 11 tabelas relacionais MySQL
├── frontend/
│   └── index.html          ← SPA com roteamento client-side
├── scripts/
│   └── importar_planilha.py ← ETL: Excel → MySQL via openpyxl
└── .env.example
```

## Módulos

**Visão geral** — KPIs em tempo real: saldo consolidado em bancos, total a receber, pagamentos do dia e saldo projetado para os próximos 30 dias. Gráficos de linha (projeção de caixa), rosca (saídas por categoria) e barras horizontais (saldo por banco).

**Fluxo diário** — Projeção de entradas e saídas por data com visualização em gráfico de barras agrupadas e tabela detalhada. Filtros por período de 7 a 90 dias.

**Pagamentos** — CRUD completo de pagamentos diários com campos de descrição, favorecido, banco, valor, desconto e observação. Cálculo automático do valor líquido, filtros por status (pendente/pago/cancelado) e exportação em CSV.

**KGIRO** — Gestão de contratos de capital de giro: cadastro de contratos com parcelas, taxa e garantia; alertas de vencimento em 30 dias; confirmação de pagamento de parcelas individuais.

**Duplicatas e Recebíveis** — Listagem paginada de títulos com filtros por banco e período. Recebíveis com marcação de recebimento e reversão de status.

**Endividamento** — Saldo devedor consolidado por banco com visualização em gráfico e data de referência.

**Configurações** — Gerenciamento de bancos (com saldo e conta), categorias de saída e contratos de KGIRO. Troca de senha de acesso.

## Variáveis de ambiente

```env
DB_HOST=
DB_PORT=3306
DB_USER=
DB_PASSWORD=
DB_NAME=cashflow_db
PORT=5000
SECRET_KEY=
```

## Licença

MIT
