# 💰 CashFlow Dashboard

Dashboard financeiro completo desenvolvido com **Python + Flask + MySQL + HTML/CSS/JS**.

## Funcionalidades

- 📊 **Visão geral** — KPIs, saldo projetado e gráficos
- 📅 **Fluxo diário** — entradas, saídas e saldo por data
- 💳 **Pagamentos** — registro e controle diário com exportação CSV
- 🏦 **KGIRO** — contratos de capital de giro e parcelas
- 📄 **Duplicatas** — títulos a pagar com filtros
- 💰 **Recebíveis** — títulos a receber com marcação de recebimento
- 📈 **Endividamento** — saldo devedor por banco
- ⚙️ **Configurações** — bancos, categorias, KGIRO e senha

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3 + Flask |
| Banco de dados | MySQL |
| Frontend | HTML + CSS + JavaScript + Chart.js |
| Importação | openpyxl (Excel → MySQL) |

## Como instalar

### 1. Clonar o repositório
```bash
git clone https://github.com/seu-usuario/CashFlow-Dashboard.git
cd CashFlow-Dashboard
```

### 2. Instalar dependências
```bash
pip install -r backend/requirements.txt
```

### 3. Configurar banco de dados
```bash
# Criar banco
mysql -u root -p < database/schema.sql

# Copiar e preencher variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais
```

### 4. Importar planilha (opcional)
```bash
python scripts/importar_planilha.py caminho/para/planilha.xlsx
```

### 5. Iniciar servidor
```bash
python backend/app.py
```

Acesse `http://localhost:5000/api/health` para verificar se está funcionando.

### 6. Abrir o dashboard
No VS Code, clique com o botão direito em `frontend/index.html` e escolha **Open with Live Server**.

## Estrutura do projeto

```
CashFlow-Dashboard/
├── backend/
│   ├── app.py              ← API Flask com todas as rotas
│   └── requirements.txt
├── database/
│   └── schema.sql          ← Criação das tabelas MySQL
├── frontend/
│   └── index.html          ← Dashboard completo (single page)
├── scripts/
│   └── importar_planilha.py ← Importação de Excel para MySQL
├── .env.example            ← Modelo de configuração
├── .gitignore
└── README.md
```

## Licença

MIT
