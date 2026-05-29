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
import requests
from utils import standard_response

from database import get_connection

auth_bp = Blueprint("auth", __name__)

# ── Configuração ────────────────────────────────────────────────
import os
SECRET_KEY = os.getenv("SECRET_KEY", "fiscal_finance_squad_2026_secret")   # >= 32 bytes para HS256


# ── Inicialização da tabela de usuários (FISC-14) ───────────────
def init_db_auth():
    """Cria a tabela 'usuarios' e insere os usuários padrão se não existirem."""
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

    # Hashes de senhas padrão com bcrypt
    senha_hash_admin = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode('utf-8')
    senha_hash_chefe = bcrypt.hashpw("chefe123".encode(), bcrypt.gensalt()).decode('utf-8')
    senha_hash_usuario = bcrypt.hashpw("usuario123".encode(), bcrypt.gensalt()).decode('utf-8')
    
    # Inserir se não existirem
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel)
        VALUES (?, ?, ?, ?)
    """, ("Administrador Fiscal", "admin@fiscal.com", senha_hash_admin, "admin"))

    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel)
        VALUES (?, ?, ?, ?)
    """, ("Chefe Fiscal", "chefe@fiscal.com", senha_hash_chefe, "admin"))

    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (nome, email, senha_hash, papel)
        VALUES (?, ?, ?, ?)
    """, ("Funcionário Operacional", "usuario@empresa.com", senha_hash_usuario, "usuario"))

    # Forçar a atualização das senhas de seed para garantir alinhamento absoluto
    cursor.execute("UPDATE usuarios SET senha_hash = ? WHERE email = 'admin@fiscal.com'", (senha_hash_admin,))
    cursor.execute("UPDATE usuarios SET senha_hash = ? WHERE email = 'chefe@fiscal.com'", (senha_hash_chefe,))
    cursor.execute("UPDATE usuarios SET senha_hash = ? WHERE email = 'usuario@empresa.com'", (senha_hash_usuario,))

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

    # Configuração da URL do Core (Busca dinâmica e tolerante a falhas)
    CORE_BACKEND_URL = os.getenv("CORE_BACKEND_URL")
    urls_to_try = []
    if CORE_BACKEND_URL:
        urls_to_try.append(CORE_BACKEND_URL)
    else:
        urls_to_try = [
            "http://core-engine-backend-svc.core-engine.svc.cluster.local:3000",
            "http://core-engine-backend-svc:3000",
            "http://erp-backend:3000"
        ]

    # 1. Tentar autenticação contra o Core Engine via REST
    core_auth_sucesso = False
    core_user_data = None

    for url in urls_to_try:
        try:
            res_login = requests.post(
                f"{url}/v1/auth/login",
                json={"email": username, "password": password},
                timeout=2.0
            )
            if res_login.status_code in (200, 201):
                body_login = res_login.json()
                if body_login.get("success"):
                    access_token = body_login["data"]["accessToken"]
                    
                    # Obter dados do usuário no Core
                    res_me = requests.get(
                        f"{url}/v1/auth/me",
                        headers={"Authorization": f"Bearer {access_token}"},
                        timeout=2.0
                    )
                    if res_me.status_code == 200:
                        body_me = res_me.json()
                        if body_me.get("success"):
                            core_user_data = body_me["data"]
                            core_auth_sucesso = True
                            CORE_BACKEND_URL = url
                            break
        except Exception as err:
            print(f"Falha de conexão com Core Engine na URL {url}. Tentando próxima... Erro: {err}")

    if core_auth_sucesso and core_user_data:
        # Sincronizar usuário do Core localmente na tabela SQLite do Fiscal
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, papel FROM usuarios WHERE email = ?", (username,))
        usuario_local = cursor.fetchone()

        # Mapeamento do papel (role) do Core
        core_roles = core_user_data.get("roles", [])
        papel_mapeado = "usuario"
        if "admin" in core_roles:
            papel_mapeado = "admin"
        elif "viewer" in core_roles:
            papel_mapeado = "viewer"

        # Buscar o nome real do usuário no Core via M2M (/v1/integration/users/:id)
        nome_real = "Usuário Core"
        try:
            res_token = requests.post(
                f"{CORE_BACKEND_URL}/v1/integration/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": "erp-fiscal-client",
                    "client_secret": "M2mFiscal2026!Secret"
                },
                timeout=2.5
            )
            if res_token.status_code == 200:
                res_token_json = res_token.json()
                m2m_data = res_token_json.get("data", {})
                m2m_token = m2m_data.get("access_token")
                tenant_id = core_user_data.get("tenantId", "00000000-0000-4000-8000-000000000001")
                user_id = core_user_data.get("userId")
                if m2m_token and user_id:
                    res_identity = requests.get(
                        f"{CORE_BACKEND_URL}/v1/integration/users/{user_id}",
                        headers={
                            "Authorization": f"Bearer {m2m_token}",
                            "X-Tenant-Id": tenant_id
                        },
                        timeout=2.5
                    )
                    if res_identity.status_code == 200:
                        body_identity = res_identity.json()
                        if body_identity.get("success"):
                            nome_real = body_identity["data"].get("name", "Usuário Core")
        except Exception as err:
            print("Erro ao obter nome real do usuário via M2M do Core:", err)

        if not usuario_local:
            # Inserir novo usuário externo
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha_hash, papel) VALUES (?, ?, ?, ?)",
                (nome_real, username, "external_core_auth", papel_mapeado)
            )
            conn.commit()
            usuario_id = cursor.lastrowid
        else:
            # Atualizar dados do usuário externo existente
            u_local = dict(usuario_local)
            usuario_id = u_local["id"]
            cursor.execute(
                "UPDATE usuarios SET nome = ?, papel = ? WHERE id = ?",
                (nome_real, papel_mapeado, usuario_id)
            )
            conn.commit()

        conn.close()

        # Gerar o token local assinado para o Fiscal
        token = gerar_token(usuario_id, papel_mapeado)

        return standard_response(
            success=True,
            message="Login realizado com sucesso via Core Engine.",
            data={
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": 86400,
                "user": {
                    "id": usuario_id,
                    "nome": nome_real,
                    "papel": papel_mapeado,
                    "tipo": "externo"
                }
            },
            status_code=200
        )

    # 2. Fallback Local SQLite
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
    except Exception:
        senha_valida = False

    if not senha_valida:
        return standard_response(success=False, message="Credenciais inválidas.", data=None, status_code=401)

    token = gerar_token(u["id"], u["papel"])

    return standard_response(
        success=True,
        message="Login local realizado com sucesso.",
        data={
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": 86400,
            "user": {
                "id": u["id"],
                "nome": u["nome"],
                "papel": u["papel"],
                "tipo": "local"
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
