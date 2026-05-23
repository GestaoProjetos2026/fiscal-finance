# src/invoice.py
# FISC-MOD5: Nota Fiscal — Endpoints REST
# FISC-22: POST /v1/fisc/invoice/intent    → calcula nota sem salvar
# FISC-23: POST /v1/fisc/invoice/confirm   → confirma nota, baixa estoque, registra no caixa
# FISC-24: GET  /v1/fisc/invoice/<numero>  → busca nota por número

from flask import Blueprint, request
from utils import standard_response
from database import get_connection
from datetime import datetime

invoice_bp = Blueprint("invoice", __name__)


# ─────────────────────────────────────────────────────────
# FISC-22 — POST /invoice/intent (calcular intenção de nota)
# ─────────────────────────────────────────────────────────
@invoice_bp.route("/invoice/intent", methods=["POST"])
def calcular_intencao():
    """
    Calcula os valores de uma nota fiscal SEM salvar no banco.
    Body: { "itens": [{ "sku": "PROD-001", "quantidade": 2 }] }
    """
    dados = request.get_json()
    if not dados or "itens" not in dados:
        return standard_response(success=False, message="Corpo inválido. Envie: { \"itens\": [{\"sku\": ..., \"quantidade\": ...}] }", data=None, status_code=400)

    itens_req = dados["itens"]
    if not itens_req:
        return standard_response(success=False, message="A lista de itens não pode ser vazia.", data=None, status_code=400)

    conn = get_connection()
    cursor = conn.cursor()

    itens_calculados = []
    skus_invalidos   = []
    total_bruto      = 0.0
    total_imposto    = 0.0
    total_lucro      = 0.0
    total_final      = 0.0

    markup = float(dados.get("markup", 0.0))

    for item in itens_req:
        sku = str(item.get("sku", "")).strip()
        qtd = item.get("quantidade", 0)

        if not sku or qtd <= 0:
            skus_invalidos.append({"sku": sku, "motivo": "SKU ou quantidade inválidos."})
            continue

        cursor.execute("SELECT * FROM produtos WHERE sku = ?", (sku,))
        produto = cursor.fetchone()

        if not produto:
            skus_invalidos.append({"sku": sku, "motivo": "Produto não encontrado no cadastro."})
            continue

        p         = dict(produto)
        aliquota  = p.get("aliquota", p.get("aliquota_imposto", 0))
        
        # Aplica o markup sobre o preço de custo para definir o preço de venda
        preco_venda = p["preco_base"] * (1 + (markup / 100.0))
        lucro_unitario = preco_venda - p["preco_base"]
        
        vb        = preco_venda * qtd
        vi        = vb * aliquota
        vt        = vb + vi
        vl        = lucro_unitario * qtd

        total_bruto   += vb
        total_imposto += vi
        total_lucro   += vl
        total_final   += vt

        itens_calculados.append({
            "sku":            sku,
            "nome":           p["nome"],
            "quantidade":     qtd,
            "preco_unitario": p["preco_base"],
            "aliquota":       aliquota,
            "valor_bruto":    round(vb, 2),
            "valor_imposto":  round(vi, 2),
            "valor_lucro":    round(vl, 2),
            "valor_total":    round(vt, 2)
        })

    conn.close()

    if skus_invalidos and not itens_calculados:
        return standard_response(success=False, message="Nenhum item válido encontrado.", data={"skus_invalidos": skus_invalidos}, status_code=422)

    return standard_response(success=True, message="Intenção calculada. Use /invoice/confirm para confirmar.", data={
            "itens":           itens_calculados,
            "skus_invalidos":  skus_invalidos,
            "totais": {
                "total_bruto":    round(total_bruto,   2),
                "total_imposto":  round(total_imposto, 2),
                "total_lucro":    round(total_lucro, 2),
                "total_final":    round(total_final,   2)
            }
        }, status_code=200)


# ─────────────────────────────────────────────────────────
# FISC-23 — POST /invoice/confirm (confirmar nota)
# ─────────────────────────────────────────────────────────
@invoice_bp.route("/invoice/confirm", methods=["POST"])
def confirmar_nota():
    """
    Confirma a nota fiscal: valida estoque, baixa estoque, salva nota e registra no caixa.
    Operação atômica — usa transação única.
    Body: { "numero": "NF-2026-001", "descricao": "Venda loja", "itens": [...] }
    """
    dados = request.get_json()
    if not dados:
        return standard_response(success=False, message="Corpo da requisição inválido.", data=None, status_code=400)

    numero    = str(dados.get("numero", "")).strip()
    descricao = str(dados.get("descricao", "Nota confirmada via API")).strip()
    itens_req = dados.get("itens", [])

    if not numero:
        return standard_response(success=False, message="Campo 'numero' é obrigatório.", data=None, status_code=400)
    if not itens_req:
        return standard_response(success=False, message="A lista de itens não pode ser vazia.", data=None, status_code=400)

    conn = get_connection()
    cursor = conn.cursor()

    # Verifica se número já existe
    cursor.execute("SELECT id FROM notas_fiscais WHERE numero_nota = ?", (numero,))
    if cursor.fetchone():
        conn.close()
        return standard_response(success=False, message=f"Nota '{numero}' já existe.", data=None, status_code=409)

    markup = float(dados.get("markup", 0.0))

    # Valida e calcula todos os itens
    itens_validos = []
    skus_invalidos = []

    for item in itens_req:
        sku = str(item.get("sku", "")).strip()
        qtd = item.get("quantidade", 0)

        cursor.execute("SELECT * FROM produtos WHERE sku = ?", (sku,))
        produto = cursor.fetchone()
        if not produto:
            skus_invalidos.append({"sku": sku, "motivo": "Produto não encontrado."})
            continue

        p = dict(produto)
        estoque_atual = p.get("estoque", 0)
        if estoque_atual < qtd:
            conn.close()
            return standard_response(success=False, message=f"Estoque insuficiente para SKU '{sku}'. Disponível: {estoque_atual}, necessário: {qtd}.", data=None, status_code=422)

        aliquota = p.get("aliquota", p.get("aliquota_imposto", 0))
        
        # Aplica o markup
        preco_venda = p["preco_base"] * (1 + (markup / 100.0))
        
        vb = preco_venda * qtd
        vi = vb * aliquota
        vt = vb + vi
        itens_validos.append({**p, "quantidade": qtd, "aliquota": aliquota,
                               "vb": vb, "vi": vi, "vt": vt, "preco_venda": preco_venda})

    if skus_invalidos:
        conn.close()
        return standard_response(success=False, message="Existem SKUs inválidos. Corrija e tente novamente.", data={"skus_invalidos": skus_invalidos}, status_code=422)

    # Operação atômica
    try:
        agora = datetime.now().isoformat()

        # Como é um projeto acadêmico, geramos um DANFE simulado direto no frontend
        dummy_pdf_url = f"danfe.html?numero={numero}"

        # 1. Cria a nota
        cursor.execute(
            "INSERT INTO notas_fiscais (numero_nota, descricao, status, pdf_url, data_criacao) VALUES (?, ?, 'emitida', ?, ?)",
            (numero, descricao, dummy_pdf_url, agora)
        )
        cursor.execute("SELECT id FROM notas_fiscais WHERE numero_nota = ?", (numero,))
        nota_row = cursor.fetchone()
        if nota_row:
            try:
                nota_id = nota_row["id"]
            except Exception:
                nota_id = nota_row[0]
        else:
            nota_id = cursor.lastrowid

        total_final = 0.0
        for item in itens_validos:
            # 2. Insere itens
            cursor.execute("""
                INSERT INTO itens_nota
                    (nota_id, sku, quantidade, preco_base, aliquota, valor_bruto, valor_imposto, valor_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (nota_id, item["sku"], item["quantidade"], item["preco_venda"],
                  item["aliquota"], item["vb"], item["vi"], item["vt"]))

            # 3. Baixa o estoque
            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE sku = ?",
                (item["quantidade"], item["sku"])
            )
            cursor.execute("""
                INSERT INTO estoque_mov (sku, tipo, quantidade, motivo, data_mov)
                VALUES (?, 'saida', ?, ?, ?)
            """, (item["sku"], item["quantidade"], f"Emissão NF {numero}", agora))

            total_final += item["vt"]

        # 4. Registra entrada no caixa
        cursor.execute(
            "INSERT INTO caixa (tipo, descricao, valor_liquido, data_registro) VALUES ('entrada', ?, ?, ?)",
            (f"Receita NF {numero}", total_final, agora)
        )

        conn.commit()
        conn.close()

        return standard_response(success=True, message=f"Nota '{numero}' emitida com sucesso!", data={
                "nota_id":     nota_id,
                "numero":      numero,
                "status":      "emitida",
                "pdf_url":     dummy_pdf_url,
                "total_final": round(total_final, 2),
                "itens":       len(itens_validos)
            }, status_code=201)

    except Exception as e:
        conn.rollback()
        conn.close()
        return standard_response(success=False, message=f"Erro interno ao confirmar nota: {str(e)}", data=None, status_code=500)


# ─────────────────────────────────────────────────────────
# FISC-24 — GET /invoice/<numero> (buscar nota por número)
# ─────────────────────────────────────────────────────────
@invoice_bp.route("/invoice/<string:numero>", methods=["GET"])
def buscar_nota(numero):
    """
    Retorna uma nota fiscal com todos os seus itens e totais.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM notas_fiscais WHERE numero_nota = ?", (numero,))
    nota = cursor.fetchone()

    if not nota:
        conn.close()
        return standard_response(success=False, message=f"Nota '{numero}' não encontrada.", data=None, status_code=404)

    nota_dict = dict(nota)

    cursor.execute("""
        SELECT i.*, p.nome
        FROM itens_nota i
        JOIN produtos p ON i.sku = p.sku
        WHERE i.nota_id = ?
        ORDER BY i.id ASC
    """, (nota_dict["id"],))
    itens = [dict(row) for row in cursor.fetchall()]

    cursor.execute("""
        SELECT COALESCE(SUM(valor_total), 0) AS total FROM itens_nota WHERE nota_id = ?
    """, (nota_dict["id"],))
    total = cursor.fetchone()["total"]

    conn.close()

    return standard_response(success=True, message="Nota encontrada.", data={
            "nota":   nota_dict,
            "itens":  itens,
            "totais": {"total_final": round(total, 2), "num_itens": len(itens)}
        }, status_code=200)
