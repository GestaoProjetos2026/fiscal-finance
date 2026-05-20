# src/auth.py
# FISC-MOD2 Sprint 2 — Autenticação JWT
# Adaptado de auth_handler.py (feat/auth-security) por kaua-silva09
# Integrado como Flask Blueprint por Kevin para src/
#
# FISC-12: POST /v1/fisc/auth/login
# FISC-13: Middleware JWT (middleware_jwt)
# FISC-14: Tabela usuarios + seed admin
# FISC-15: GET  /v1/fisc/auth/me  |  POST /v1/fisc/auth/logout

import hashlib
import datetime
from flask import Blueprint, request, g
import jwt
import bcrypt
from utils import standard_response

from database import get_connection

auth_bp = Blueprint("auth", __name__)

# ── Configuração ────────────────────────────────────────────────
import os
SECRET_KEY = os.getenv("SECRET_KEY", "fiscal_finance_squad_2026_secret")   # >= 32 bytes para HS256


# ── Inicialização da tabela de usuários (FISC-14) ───────────────
def init_db_auth():
    """Cria a tabela 'usuarios' e insere o admin padrão se não existir."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT    NOT NULL,
            email      TEXT    UNIQUE NOT NULL,
            senha_hash TEXT    NOT NULL,
            papel      TEXT    NOT NULL DEFAULT 'usuario',
            criado_em  DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Seed legado (comentado a pedido do usuário - conflito com bcrypt)
    # senha_hash_old = hashlib.sha256("admin123".encode()).hexdigest()
    # cursor.execute("""
    #     INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel)
    #     VALUES (?, ?, ?, ?)
    # """, ("Administrador", "admin@fiscal.com", senha_hash_old, "admin"))

    # Novo seed: admin inicial com bcrypt
    senha_hash_bcrypt = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode('utf-8')
    
    # Inserir se não existir
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel)
        VALUES (?, ?, ?, ?)
    """, ("Administrador", "admin@fiscal.com", senha_hash_bcrypt, "admin"))

    # Forçar a atualização da senha caso o banco antigo já exista (para não quebrar o login)
    cursor.execute("UPDATE usuarios SET senha_hash = ? WHERE email = 'admin@fiscal.com'", (senha_hash_bcrypt,))

    conn.commit()
    conn.close()


# ── Helpers JWT (FISC-13) ────────────────────────────────────────
def gerar_token(usuario_id: int, papel: str) -> str:
    payload = {
        "id":    usuario_id,
        "papel": papel,
        "exp":   datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def validar_token(auth_header: str):
    """Retorna o payload decodificado ou None se inválido/expirado."""
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ", 1)[1]
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def requer_auth(f):
    """Decorator — protege qualquer rota com JWT."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        payload = validar_token(request.headers.get("Authorization", ""))
        if not payload:
            return standard_response(
                success=False,
                message="Não autorizado. Faça login e use o header Authorization: Bearer <token>.",
                data=None,
                status_code=401
            )
        g.usuario = payload   # disponível para a rota
        return f(*args, **kwargs)
    return wrapper


# ── Rota Legada (FISC-12) ────────────────────────────────────────
# @auth_bp.route("/auth/login", methods=["POST"])
# def login():
#     """ Rota de login antiga baseada em SHA-256 e JSON no body. Desativada para usar OAuth2. """
#     pass

# ── Rota OAuth2 (Password Grant) ─────────────────────────────────
@auth_bp.route("/oauth/token", methods=["POST"])
def oauth_token():
    """
    Realiza o login e retorna um token JWT (Padrão OAuth 2.0).
    Espera formato application/x-www-form-urlencoded
    Campos: grant_type=password, username=..., password=...
    """
    grant_type = request.form.get("grant_type")
    username = request.form.get("username", "").strip().lower()
    password = request.form.get("password", "")

    if grant_type != "password":
        return standard_response(success=False, message="grant_type deve ser 'password'.", data=None, status_code=400)

    if not username or not password:
        return standard_response(success=False, message="Campos 'username' e 'password' são obrigatórios.", data=None, status_code=400)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, papel, senha_hash FROM usuarios WHERE email = ?",
        (username,)
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        return standard_response(success=False, message="Credenciais inválidas.", data=None, status_code=401)

    u = dict(usuario)
    
    # Verifica a senha com bcrypt
    senha_valida = False
    try:
        senha_valida = bcrypt.checkpw(password.encode(), u["senha_hash"].encode('utf-8'))
    except ValueError:
        # Fallback caso a senha do banco não seja um hash bcrypt válido
        senha_valida = False

    if not senha_valida:
        return standard_response(success=False, message="Credenciais inválidas.", data=None, status_code=401)

    token = gerar_token(u["id"], u["papel"])

    return standard_response(
        success=True,
        message="Login OAuth2 realizado com sucesso.",
        data={
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 86400,
            "user": {
                "id": u["id"],
                "nome": u["nome"],
                "papel": u["papel"]
            }
        },
        status_code=200
    )


# ── FISC-15a — GET /auth/me ──────────────────────────────────────
@auth_bp.route("/auth/me", methods=["GET"])
@requer_auth
def me():
    """Retorna os dados do usuário logado a partir do token JWT."""
    payload = g.usuario

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, nome, email, papel, criado_em FROM usuarios WHERE id = ?",
        (payload["id"],)
    )
    usuario = cursor.fetchone()
    conn.close()

    if not usuario:
        return standard_response(success=False, message="Usuário não encontrado.", data=None, status_code=404)

    return standard_response(
        success=True,
        message="Dados do usuário logado.",
        data=dict(usuario),
        status_code=200
    )


# ── FISC-15b — POST /auth/logout ────────────────────────────────
@auth_bp.route("/auth/logout", methods=["POST"])
@requer_auth
def logout():
    """
    Logout stateless: JWT não tem invalidação server-side.
    O cliente deve descartar o token localmente.
    """
    return standard_response(
        success=True,
        message="Logout realizado. Descarte o token no cliente.",
        data=None,
        status_code=200
    )
