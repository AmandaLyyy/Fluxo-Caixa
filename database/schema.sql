-- ============================================================
--  CashFlow Dashboard · Schema MySQL
--  Execute: mysql -u root -p cashflow_db < schema.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS cashflow_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE cashflow_db;

-- ============================================================
-- TABELA: bancos
-- Cadastro dos bancos cadastrados no sistema
-- ============================================================
CREATE TABLE IF NOT EXISTS bancos (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  nome          VARCHAR(100) NOT NULL,
  ativo         TINYINT(1) DEFAULT 1,
  criado_em     DATETIME DEFAULT NOW()
);

-- ============================================================
-- TABELA: saldo_banco
-- Saldo diário por banco (linha "BANCOS" da planilha Fluxo)
-- ============================================================
CREATE TABLE IF NOT EXISTS saldo_banco (
  id        INT AUTO_INCREMENT PRIMARY KEY,
  banco_id  INT NOT NULL,
  data      DATE NOT NULL,
  saldo     DECIMAL(18,2) NOT NULL DEFAULT 0,
  UNIQUE KEY uq_banco_data (banco_id, data),
  FOREIGN KEY (banco_id) REFERENCES bancos(id)
);

-- ============================================================
-- TABELA: fluxo_entradas
-- Entradas do fluxo: duplicatas, recebíveis, empréstimo homemade
-- ============================================================
CREATE TABLE IF NOT EXISTS fluxo_entradas (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  data        DATE NOT NULL,
  duplicatas  DECIMAL(18,2) DEFAULT 0,
  recebiveis  DECIMAL(18,2) DEFAULT 0,
  homemade    DECIMAL(18,2) DEFAULT 0,
  total       DECIMAL(18,2) DEFAULT 0,
  criado_em   DATETIME DEFAULT NOW()
);

-- ============================================================
-- TABELA: categoria_saida
-- Categorias de saída (fornecedores, câmbio, fretes, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS categoria_saida (
  id    INT AUTO_INCREMENT PRIMARY KEY,
  nome  VARCHAR(150) NOT NULL UNIQUE
);

-- ============================================================
-- TABELA: fluxo_saidas
-- Saídas diárias do fluxo por categoria
-- ============================================================
CREATE TABLE IF NOT EXISTS fluxo_saidas (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  data          DATE NOT NULL,
  categoria_id  INT NOT NULL,
  valor         DECIMAL(18,2) NOT NULL DEFAULT 0,
  observacao    TEXT,
  FOREIGN KEY (categoria_id) REFERENCES categoria_saida(id)
);

-- ============================================================
-- TABELA: fluxo_saldo
-- Saldo líquido projetado por dia (linha SALDO da planilha)
-- ============================================================
CREATE TABLE IF NOT EXISTS fluxo_saldo (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  data        DATE NOT NULL UNIQUE,
  total_entradas DECIMAL(18,2) DEFAULT 0,
  total_saidas   DECIMAL(18,2) DEFAULT 0,
  saldo          DECIMAL(18,2) DEFAULT 0,
  atualizado_em  DATETIME DEFAULT NOW() ON UPDATE NOW()
);

-- ============================================================
-- TABELA: duplicatas
-- Títulos a pagar (aba Duplicatas)
-- ============================================================
CREATE TABLE IF NOT EXISTS duplicatas (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  no_titulo     VARCHAR(30),
  parcela       VARCHAR(10),
  portador      VARCHAR(100),
  cod_cliente   VARCHAR(20),
  nome_cliente  VARCHAR(200),
  dt_emissao    DATE,
  vencimento    DATE,
  vencto_real   DATE,
  vlr_titulo    DECIMAL(18,2),
  situacao      VARCHAR(50),
  banco         VARCHAR(100),
  criado_em     DATETIME DEFAULT NOW()
);

-- ============================================================
-- TABELA: recebiveis
-- Títulos a receber (aba Recebiveis)
-- ============================================================
CREATE TABLE IF NOT EXISTS recebiveis (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  no_titulo       VARCHAR(30),
  parcela         VARCHAR(10),
  tipo            VARCHAR(10),
  portador        VARCHAR(100),
  cod_cliente     VARCHAR(20),
  nome_cliente    VARCHAR(200),
  dt_emissao      DATE,
  vencimento      DATE,
  vencto_real     DATE,
  vlr_titulo      DECIMAL(18,2),
  desconto_pct    DECIMAL(10,4) DEFAULT 0,
  vlr_liquido     DECIMAL(18,2),
  recebido        TINYINT(1) DEFAULT 0,
  dt_recebimento  DATE,
  criado_em       DATETIME DEFAULT NOW()
);

-- ============================================================
-- TABELA: kgiro_contrato
-- Contratos de capital de giro (aba KGIRO)
-- ============================================================
CREATE TABLE IF NOT EXISTS kgiro_contrato (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  banco_id        INT,
  no_contrato     VARCHAR(60),
  tipo_operacao   VARCHAR(100),
  taxa            VARCHAR(100),
  data_contrato   DATE,
  valor_original  DECIMAL(18,2),
  prazo_parcelas  INT,
  garantia        VARCHAR(200),
  ativo           TINYINT(1) DEFAULT 1,
  criado_em       DATETIME DEFAULT NOW(),
  FOREIGN KEY (banco_id) REFERENCES bancos(id)
);

-- ============================================================
-- TABELA: kgiro_parcela
-- Parcelas de cada contrato de KGIRO
-- ============================================================
CREATE TABLE IF NOT EXISTS kgiro_parcela (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  contrato_id   INT NOT NULL,
  vencimento    DATE,
  valor_parcela DECIMAL(18,2),
  valor_juros   DECIMAL(18,2) DEFAULT 0,
  principal     DECIMAL(18,2) DEFAULT 0,
  pago          TINYINT(1) DEFAULT 0,
  dt_pagamento  DATE,
  FOREIGN KEY (contrato_id) REFERENCES kgiro_contrato(id) ON DELETE CASCADE
);

-- ============================================================
-- TABELA: endividamento
-- Saldo devedor total por banco (aba Endividamento Principal)
-- ============================================================
CREATE TABLE IF NOT EXISTS endividamento (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  banco_id      INT NOT NULL,
  data_ref      DATE NOT NULL,
  valor_tomado  DECIMAL(18,2) DEFAULT 0,
  UNIQUE KEY uq_banco_data_ref (banco_id, data_ref),
  FOREIGN KEY (banco_id) REFERENCES bancos(id)
);

-- ============================================================
-- TABELA: pagamentos
-- Relação diária de pagamentos realizados (planilha separada)
-- ============================================================
CREATE TABLE IF NOT EXISTS pagamentos (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  data          DATE NOT NULL,
  descricao     VARCHAR(300) NOT NULL,
  favorecido    VARCHAR(200),
  valor         DECIMAL(18,2) NOT NULL,
  banco_id      INT,
  desconto      DECIMAL(18,2) DEFAULT 0,
  valor_pago    DECIMAL(18,2),
  observacao    TEXT,
  categoria_id  INT,
  status        ENUM('pendente','pago','cancelado') DEFAULT 'pendente',
  origem        ENUM('manual','outlook','importacao') DEFAULT 'manual',
  email_ref     VARCHAR(500),
  criado_em     DATETIME DEFAULT NOW(),
  atualizado_em DATETIME DEFAULT NOW() ON UPDATE NOW(),
  FOREIGN KEY (banco_id) REFERENCES bancos(id),
  FOREIGN KEY (categoria_id) REFERENCES categoria_saida(id)
);

-- ============================================================
-- TABELA: email_pendencias
-- E-mails do Outlook capturados como pendências
-- ============================================================
CREATE TABLE IF NOT EXISTS email_pendencias (
  id              INT AUTO_INCREMENT PRIMARY KEY,
  outlook_id      VARCHAR(200) UNIQUE,
  assunto         VARCHAR(500),
  remetente       VARCHAR(200),
  data_email      DATETIME,
  corpo_resumo    TEXT,
  valor_detectado DECIMAL(18,2),
  favorecido      VARCHAR(200),
  data_vencimento DATE,
  status          ENUM('novo','vinculado','ignorado') DEFAULT 'novo',
  pagamento_id    INT,
  criado_em       DATETIME DEFAULT NOW(),
  FOREIGN KEY (pagamento_id) REFERENCES pagamentos(id)
);

-- ============================================================
-- SEEDS: categorias de saída padrão
-- ============================================================
INSERT IGNORE INTO categoria_saida (nome) VALUES
  ('Pagamento a fornecedores / contas de consumo'),
  ('Fornecedor peixe e equipamentos'),
  ('Diversos e empréstimos'),
  ('Câmbio antecipações'),
  ('Câmbios previstos'),
  ('Câmbios efetivamente fechados'),
  ('Desembaraço / fretes'),
  ('Sodexo – cessão Safra'),
  ('Modelez – cessão Safra'),
  ('KGIRO – parcela'),
  ('Outros');
  
USE cashflow_db;
ALTER TABLE duplicatas MODIFY cod_cliente VARCHAR(50);

USE cashflow_db;
ALTER TABLE bancos ADD COLUMN conta VARCHAR(100) AFTER nome;

