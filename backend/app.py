# src/app.py
# Ponto de entrada da API REST — Squad FISC
# Para rodar: python app.py (dentro da pasta src/)

import json
import os
from dotenv import load_dotenv
load_dotenv()  # Carrega as variaveis do arquivo .env (se existir)

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flasgger import Swagger

from products   import products_bp
from cashflow   import cashflow_bp
from invoice    import invoice_bp
from auth       import auth_bp, init_db_auth
from public_api import public_bp
from stock      import stock_bp   # FISC-19: entrada de estoque
from usuarios   import usuarios_bp
from database   import init_db
from utils      import standard_response

app = Flask(__name__)

# ── CORS — permite que o frontend web (qualquer origem local) acesse a API ──
CORS(app)

# ── Swagger UI — acessível em GET /docs ───────────────────────
_SPEC_PATH = os.path.join(os.path.dirname(__file__), "openapi.json")

if not os.path.exists(_SPEC_PATH):
    _SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "docs", "openapi.json")

try:
    with open(_SPEC_PATH, encoding="utf-8") as f:
        _openapi_spec = json.load(f)
except FileNotFoundError:
    _openapi_spec = {"info": {"title": "API FISC", "version": "1.1.0"}, "paths": {}}

app.config['SWAGGER'] = {
    'openapi': '3.0.3',
    'optional_fields': ['components']
}

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route":    "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs",
    "openapi": "3.0.3",
}

Swagger(app, config=swagger_config, template=_openapi_spec)


# ── Registra os módulos com o prefixo /v1/fisc ────────────────
app.register_blueprint(auth_bp,     url_prefix="/v1/fisc")
app.register_blueprint(products_bp, url_prefix="/v1/fisc")
app.register_blueprint(cashflow_bp, url_prefix="/v1/fisc")
app.register_blueprint(invoice_bp,  url_prefix="/v1/fisc")
app.register_blueprint(stock_bp,    url_prefix="/v1/fisc")   # FISC-19
app.register_blueprint(usuarios_bp, url_prefix="/v1/fisc")
app.register_blueprint(public_bp,   url_prefix="/v1")      # prefixo /v1 (public já inclui /public/fisc)


# ── Serve o frontend web estático em / ───────────────────────
_FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")

@app.route("/")
@app.route("/web")
@app.route("/web/")
def frontend_index():
    return send_from_directory(_FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def frontend_static(filename):
    # Evita conflito com rotas da API /v1/...
    import os as _os
    full = _os.path.join(_FRONTEND_DIR, filename)
    if _os.path.isfile(full):
        return send_from_directory(_FRONTEND_DIR, filename)
    return standard_response(success=False, message="Rota não encontrada.", data=None, status_code=404)



# ── Handler global de erros ───────────────────────────────────
@app.errorhandler(404)
def nao_encontrado(e):
    return standard_response(success=False, message="Rota não encontrada.", data=None, status_code=404)

@app.errorhandler(405)
def metodo_nao_permitido(e):
    return standard_response(success=False, message="Método HTTP não permitido.", data=None, status_code=405)

@app.errorhandler(500)
def erro_interno(e):
    return standard_response(success=False, message="Erro interno do servidor.", data=None, status_code=500)


if __name__ == "__main__":
    init_db()       # inicializa tabelas do sistema e avisa se estiver vazio
    init_db_auth()  # garante tabela usuarios + seed admin

    print("=" * 65)
    print("  API Squad FISC  —  http://0.0.0.0:5000")
    print("=" * 65)
    print()
    print("  Auth:")
    print("   POST   /v1/fisc/auth/login")
    print("   GET    /v1/fisc/auth/me           [requer JWT]")
    print("   POST   /v1/fisc/auth/logout       [requer JWT]")
    print()
    print("  Produtos:")
    print("   POST   /v1/fisc/products")
    print("   GET    /v1/fisc/products[?nome=]")
    print("   GET    /v1/fisc/products/<sku>")
    print("   PUT    /v1/fisc/products/<sku>")
    print("   DELETE /v1/fisc/products/<sku>")
    print()
    print("  Nota Fiscal:")
    print("   POST   /v1/fisc/invoice/intent")
    print("   POST   /v1/fisc/invoice/confirm")
    print("   GET    /v1/fisc/invoice/<numero>")
    print()
    print("  Estoque (FISC-19):")
    print("   POST   /v1/fisc/stock/entry")
    print()
    print("  Caixa:")
    print("   GET    /v1/fisc/cashflow/balance")
    print("   POST   /v1/fisc/cashflow/expense")
    print("   GET    /v1/fisc/cashflow/statement?from=&to=")
    print()
    print("  API Pública (X-API-KEY):")
    print("   GET    /v1/public/fisc/products/<sku>")
    print("   GET    /v1/public/fisc/stock/<sku>")
    print("   GET    /v1/public/fisc/cashflow/summary")
    print()
    print("  Swagger UI (documentação interativa):")
    print("   GET    http://0.0.0.0:5000/docs")
    print()
    print("  Frontend Web:")
    print("   GET    http://localhost:5000/web")
    print()
    print("  Pressione CTRL+C para parar.")
    print("=" * 65)

    app.run(debug=False, host="0.0.0.0", port=5000)
