"""
CashFlow Fluxo de Caixa · Backend Flask

API REST para o dashboard de fluxo de caixa.

Uso:
    pip install flask flask-cors mysql-connector-python python-dotenv
    python backend/app.py
"""

import os
from datetime import date, timedelta
from decimal import Decimal

import mysql.connector
from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# DB 
def get_db():
    return mysql.connector.connect(
        host     = os.getenv("DB_HOST", "localhost"),
        port     = int(os.getenv("DB_PORT", 3306)),
        user     = os.getenv("DB_USER", "root"),
        password = os.getenv("DB_PASSWORD", ""),
        database = os.getenv("DB_NAME", "cashflow_db"),
    )

def query(sql, params=None, one=False):
    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(sql, params or ())
    rows = cur.fetchone() if one else cur.fetchall()
    cur.close(); conn.close()
    # Decimal → float para JSON
    def fix(row):
        if not row: return row
        return {k: (float(v) if isinstance(v, Decimal) else v) for k, v in row.items()}
    return fix(rows) if one else [fix(r) for r in rows]

def execute(sql, params=None):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(sql, params or ())
    last_id = cur.lastrowid
    conn.commit()
    cur.close(); conn.close()
    return last_id

# DASHBOARD
@app.route("/api/dashboard/resumo")
def dashboard_resumo():
    """KPIs principais para a tela inicial."""
    hoje = date.today().isoformat()

    # Saldo total em bancos hoje (último registro disponível)
    saldo_bancos = query("""
        SELECT COALESCE(SUM(s.saldo), 0) AS total
        FROM saldo_banco s
        WHERE s.data = (SELECT MAX(data) FROM saldo_banco)
    """, one=True)

    # Total a receber (recebíveis pendentes)
    a_receber = query("""
        SELECT COALESCE(SUM(vlr_liquido), 0) AS total
        FROM recebiveis WHERE recebido = 0
    """, one=True)

    # Total a pagar hoje
    a_pagar_hoje = query("""
        SELECT COALESCE(SUM(valor), 0) AS total
        FROM pagamentos WHERE data = %s AND status = 'pendente'
    """, (hoje,), one=True)

    # Saldo projetado para os próximos 30 dias
    saldo_30d = query("""
        SELECT data, saldo FROM fluxo_saldo
        WHERE data >= %s
        ORDER BY data LIMIT 30
    """, (hoje,))

    # Pendências de e-mail
    email_pendencias = query("""
        SELECT COUNT(*) AS total, COALESCE(SUM(valor_detectado), 0) AS valor
        FROM email_pendencias WHERE status = 'novo'
    """, one=True)

    # Saldo por banco (último dia)
    saldo_por_banco = query("""
        SELECT b.nome, s.saldo
        FROM saldo_banco s
        JOIN bancos b ON b.id = s.banco_id
        WHERE s.data = (SELECT MAX(data) FROM saldo_banco)
        ORDER BY s.saldo DESC
    """)

    return jsonify({
        "saldo_bancos":      saldo_bancos["total"],
        "a_receber":         a_receber["total"],
        "a_pagar_hoje":      a_pagar_hoje["total"],
        "saldo_30d":         saldo_30d,
        "email_pendencias":  email_pendencias,
        "saldo_por_banco":   saldo_por_banco,
    })

# FLUXO
@app.route("/api/fluxo/saldo")
def fluxo_saldo():
    """Saldo projetado por período."""
    inicio = request.args.get("inicio", date.today().isoformat())
    fim    = request.args.get("fim",    (date.today() + timedelta(days=60)).isoformat())
    rows = query("""
        SELECT data, total_entradas, total_saidas, saldo
        FROM fluxo_saldo WHERE data BETWEEN %s AND %s ORDER BY data
    """, (inicio, fim))
    return jsonify(rows)

@app.route("/api/fluxo/saidas-por-categoria")
def fluxo_saidas_categoria():
    """Total de saídas agrupadas por categoria no período."""
    inicio = request.args.get("inicio", date.today().isoformat())
    fim    = request.args.get("fim",    (date.today() + timedelta(days=30)).isoformat())
    rows = query("""
        SELECT c.nome AS categoria, SUM(s.valor) AS total
        FROM fluxo_saidas s
        JOIN categoria_saida c ON c.id = s.categoria_id
        WHERE s.data BETWEEN %s AND %s
        GROUP BY c.id ORDER BY total DESC
    """, (inicio, fim))
    return jsonify(rows)

# BANCOS
@app.route("/api/bancos")
def listar_bancos():
    return jsonify(query("SELECT id, nome, conta FROM bancos WHERE ativo = 1 ORDER BY nome"))

@app.route("/api/bancos/saldo-historico/<int:banco_id>")
def saldo_historico(banco_id):
    rows = query("""
        SELECT data, saldo FROM saldo_banco
        WHERE banco_id = %s ORDER BY data DESC LIMIT 90
    """, (banco_id,))
    return jsonify(rows)

# ENDIVIDAMENTO
@app.route("/api/endividamento")
def endividamento():
    rows = query("""
        SELECT b.nome AS banco, e.valor_tomado, e.data_ref
        FROM endividamento e JOIN bancos b ON b.id = e.banco_id
        WHERE e.data_ref = (SELECT MAX(data_ref) FROM endividamento)
        ORDER BY e.valor_tomado DESC
    """)
    return jsonify(rows)

# KGIRO
@app.route("/api/kgiro/contratos")
def kgiro_contratos():
    rows = query("""
        SELECT k.id, b.nome AS banco, k.no_contrato, k.tipo_operacao,
               k.taxa, k.data_contrato, k.valor_original, k.prazo_parcelas
        FROM kgiro_contrato k JOIN bancos b ON b.id = k.banco_id
        WHERE k.ativo = 1 ORDER BY b.nome, k.data_contrato
    """)
    return jsonify(rows)

@app.route("/api/kgiro/parcelas-vencendo")
def kgiro_parcelas_vencendo():
    """Parcelas a vencer nos próximos 30 dias."""
    hoje = date.today()
    fim  = hoje + timedelta(days=30)
    rows = query("""
        SELECT b.nome AS banco, k.no_contrato, p.vencimento, p.principal, p.valor_parcela
        FROM kgiro_parcela p
        JOIN kgiro_contrato k ON k.id = p.contrato_id
        JOIN bancos b ON b.id = k.banco_id
        WHERE p.pago = 0 AND p.vencimento BETWEEN %s AND %s
        ORDER BY p.vencimento
    """, (hoje, fim))
    return jsonify(rows)

# DUPLICATAS
@app.route("/api/duplicatas")
def listar_duplicatas():
    pagina  = int(request.args.get("pagina", 1))
    por_pag = int(request.args.get("por_pagina", 50))
    banco   = request.args.get("banco", "")
    inicio  = request.args.get("inicio", "")
    fim     = request.args.get("fim", "")
    offset  = (pagina - 1) * por_pag

    where = ["1=1"]
    params = []
    if banco:
        where.append("banco = %s"); params.append(banco)
    if inicio:
        where.append("vencimento >= %s"); params.append(inicio)
    if fim:
        where.append("vencimento <= %s"); params.append(fim)

    cond = " AND ".join(where)
    total = query(f"SELECT COUNT(*) AS n FROM duplicatas WHERE {cond}", params, one=True)
    rows  = query(f"""
        SELECT * FROM duplicatas WHERE {cond}
        ORDER BY vencimento LIMIT %s OFFSET %s
    """, params + [por_pag, offset])
    return jsonify({"total": total["n"], "dados": rows})

@app.route("/api/duplicatas/resumo-banco")
def duplicatas_por_banco():
    rows = query("""
        SELECT banco, COUNT(*) AS qtd, SUM(vlr_titulo) AS total
        FROM duplicatas WHERE banco != ''
        GROUP BY banco ORDER BY total DESC
    """)
    return jsonify(rows)

# RECEBIVEIS
@app.route("/api/recebiveis")
def listar_recebiveis():
    pagina  = int(request.args.get("pagina", 1))
    por_pag = int(request.args.get("por_pagina", 50))
    offset  = (pagina - 1) * por_pag
    recebido = request.args.get("recebido", "0")

    rows = query("""
        SELECT * FROM recebiveis WHERE recebido = %s
        ORDER BY vencimento LIMIT %s OFFSET %s
    """, (recebido, por_pag, offset))
    total = query("SELECT COUNT(*) AS n FROM recebiveis WHERE recebido = %s", (recebido,), one=True)
    return jsonify({"total": total["n"], "dados": rows})

@app.route("/api/recebiveis/<int:rec_id>/receber", methods=["POST"])
def marcar_recebido(rec_id):
    dados = request.get_json()
    execute("""
        UPDATE recebiveis SET recebido = 1, dt_recebimento = %s WHERE id = %s
    """, (dados.get("data", date.today()), rec_id))
    return jsonify({"ok": True})

@app.route("/api/recebiveis/<int:rec_id>/desfazer", methods=["POST"])
def desfazer_recebido(rec_id):
    execute("""
        UPDATE recebiveis SET recebido = 0, dt_recebimento = NULL WHERE id = %s
    """, (rec_id,))
    return jsonify({"ok": True})

# PAGAMENTOS
@app.route("/api/pagamentos")
def listar_pagamentos():
    data_ref = request.args.get("data", date.today().isoformat())
    rows = query("""
        SELECT p.*, b.nome AS nome_banco, c.nome AS nome_categoria
        FROM pagamentos p
        LEFT JOIN bancos b ON b.id = p.banco_id
        LEFT JOIN categoria_saida c ON c.id = p.categoria_id
        WHERE p.data = %s ORDER BY p.criado_em
    """, (data_ref,))
    return jsonify(rows)

@app.route("/api/pagamentos", methods=["POST"])
def criar_pagamento():
    d = request.get_json()
    valor_pago = float(d.get("valor", 0)) - float(d.get("desconto", 0))
    last_id = execute("""
        INSERT INTO pagamentos
          (data, descricao, favorecido, valor, banco_id, desconto, valor_pago,
           observacao, categoria_id, status, origem)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        d.get("data", date.today().isoformat()),
        d["descricao"],
        d.get("favorecido", ""),
        d["valor"],
        d.get("banco_id"),
        d.get("desconto", 0),
        valor_pago,
        d.get("observacao", ""),
        d.get("categoria_id"),
        d.get("status", "pendente"),
        d.get("origem", "manual"),
    ))
    return jsonify({"id": last_id, "ok": True}), 201

@app.route("/api/pagamentos/<int:pag_id>", methods=["PUT"])
def atualizar_pagamento(pag_id):
    d = request.get_json()
    campos = []
    valores = []
    for campo in ["data","descricao","favorecido","valor","banco_id","desconto","valor_pago","observacao","categoria_id","status"]:
        if campo in d:
            campos.append(f"{campo} = %s")
            valores.append(d[campo])
    if not campos:
        return jsonify({"erro": "Nenhum campo para atualizar"}), 400
    execute(f"UPDATE pagamentos SET {', '.join(campos)} WHERE id = %s", valores + [pag_id])
    return jsonify({"ok": True})

@app.route("/api/pagamentos/<int:pag_id>", methods=["DELETE"])
def excluir_pagamento(pag_id):
    execute("DELETE FROM pagamentos WHERE id = %s", (pag_id,))
    return jsonify({"ok": True})

@app.route("/api/pagamentos/<int:pag_id>/pagar", methods=["POST"])
def confirmar_pagamento(pag_id):
    d = request.get_json() or {}
    execute("UPDATE pagamentos SET status = 'pago', banco_id = COALESCE(%s, banco_id) WHERE id = %s",
            (d.get("banco_id"), pag_id))
    return jsonify({"ok": True})

@app.route("/api/pagamentos/resumo-dia")
def resumo_dia():
    """Total de pagamentos por dia dos últimos 30 dias."""
    inicio = (date.today() - timedelta(days=30)).isoformat()
    rows = query("""
        SELECT data, COUNT(*) AS qtd, SUM(valor_pago) AS total
        FROM pagamentos WHERE data >= %s AND status = 'pago'
        GROUP BY data ORDER BY data
    """, (inicio,))
    return jsonify(rows)

# E-MAIL PENDENCIAS 
@app.route("/api/emails/pendencias")
def listar_pendencias():
    status = request.args.get("status", "novo")
    rows = query("""
        SELECT * FROM email_pendencias WHERE status = %s ORDER BY data_email DESC
    """, (status,))
    return jsonify(rows)

@app.route("/api/emails/pendencias/<int:email_id>/vincular", methods=["POST"])
def vincular_pendencia(email_id):
    """Converte uma pendência de e-mail em pagamento."""
    d = request.get_json()
    # Cria o pagamento
    valor_pago = float(d.get("valor", 0)) - float(d.get("desconto", 0))
    pag_id = execute("""
        INSERT INTO pagamentos
          (data, descricao, favorecido, valor, banco_id, desconto, valor_pago,
           observacao, categoria_id, status, origem, email_ref)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'pendente','outlook',%s)
    """, (
        d.get("data_vencimento", date.today().isoformat()),
        d.get("descricao", ""),
        d.get("favorecido", ""),
        d.get("valor", 0),
        d.get("banco_id"),
        d.get("desconto", 0),
        valor_pago,
        d.get("observacao", ""),
        d.get("categoria_id"),
        d.get("email_ref", ""),
    ))
    # Atualiza o status da pendência
    execute("""
        UPDATE email_pendencias SET status = 'vinculado', pagamento_id = %s WHERE id = %s
    """, (pag_id, email_id))
    return jsonify({"pagamento_id": pag_id, "ok": True}), 201

@app.route("/api/emails/pendencias/<int:email_id>/ignorar", methods=["POST"])
def ignorar_pendencia(email_id):
    execute("UPDATE email_pendencias SET status = 'ignorado' WHERE id = %s", (email_id,))
    return jsonify({"ok": True})

# CATEGORIAS 
@app.route("/api/categorias")
def listar_categorias():
    return jsonify(query("SELECT id, nome FROM categoria_saida ORDER BY nome"))

@app.route("/api/categorias", methods=["POST"])
def criar_categoria():
    d = request.get_json()
    last_id = execute("INSERT IGNORE INTO categoria_saida (nome) VALUES (%s)", (d["nome"],))
    return jsonify({"id": last_id, "ok": True}), 201

@app.route("/api/categorias/<int:cat_id>", methods=["DELETE"])
def excluir_categoria(cat_id):
    execute("DELETE FROM categoria_saida WHERE id = %s", (cat_id,))
    return jsonify({"ok": True})

# BANCOS (extras) 
@app.route("/api/bancos", methods=["POST"])
def criar_banco():
    d = request.get_json()
    last_id = execute(
        "INSERT INTO bancos (nome, conta) VALUES (%s, %s)",
        (d["nome"], d.get("conta", ""))
    )
    if d.get("saldo_inicial") and d.get("data"):
        execute("""
            INSERT INTO saldo_banco (banco_id, data, saldo)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE saldo = VALUES(saldo)
        """, (last_id, d["data"], d["saldo_inicial"]))
    return jsonify({"id": last_id, "ok": True}), 201

@app.route("/api/bancos/<int:banco_id>", methods=["DELETE"])
def excluir_banco(banco_id):
    try:
        execute("DELETE FROM saldo_banco WHERE banco_id = %s", (banco_id,))
        execute("DELETE FROM bancos WHERE id = %s", (banco_id,))
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "erro": str(e)}), 400

@app.route("/api/bancos/saldo", methods=["POST"])
def atualizar_saldo_banco():
    d = request.get_json()
    execute("""
        INSERT INTO saldo_banco (banco_id, data, saldo)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE saldo = VALUES(saldo)
    """, (d["banco_id"], d["data"], d["saldo"]))
    return jsonify({"ok": True})

@app.route("/api/kgiro/contratos", methods=["POST"])
def criar_contrato():
    d = request.get_json()
    contrato_id = execute("""
        INSERT INTO kgiro_contrato
          (banco_id, no_contrato, tipo_operacao, taxa, garantia,
           data_contrato, valor_original, prazo_parcelas)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        d["banco_id"], d["no_contrato"], d.get("tipo_operacao",""),
        d.get("taxa",""), d.get("garantia",""),
        d["data_contrato"], d["valor_original"], d.get("prazo_parcelas",0)
    ))
    for p in d.get("parcelas", []):
        execute("""
            INSERT INTO kgiro_parcela
              (contrato_id, vencimento, principal, valor_parcela, pago)
            VALUES (%s,%s,%s,%s,0)
        """, (contrato_id, p["vencimento"], p.get("principal",0), p["valor_parcela"]))
    return jsonify({"id": contrato_id, "ok": True}), 201

@app.route("/api/kgiro/contratos/<int:contrato_id>/parcelas")
def listar_parcelas_contrato(contrato_id):
    rows = query("""
        SELECT * FROM kgiro_parcela
        WHERE contrato_id = %s ORDER BY vencimento
    """, (contrato_id,))
    return jsonify(rows)

@app.route("/api/kgiro/parcelas/<int:parcela_id>/pagar", methods=["POST"])
def pagar_parcela(parcela_id):
    d = request.get_json() or {}
    execute("""
        UPDATE kgiro_parcela SET pago = 1, dt_pagamento = %s WHERE id = %s
    """, (d.get("data", date.today()), parcela_id))
    return jsonify({"ok": True})

# KGIRO (extras)
@app.route("/api/kgiro/contratos/<int:contrato_id>/desativar", methods=["POST"])
def desativar_contrato(contrato_id):
    execute("UPDATE kgiro_contrato SET ativo = 0 WHERE id = %s", (contrato_id,))
    return jsonify({"ok": True})

# SAÚDE 
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "versao": "1.0.0"})

# START 
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    app.run(host="0.0.0.0", port=port, debug=debug)
