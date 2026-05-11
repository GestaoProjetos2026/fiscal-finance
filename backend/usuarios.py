import hashlib
from flask import Blueprint, request, jsonify, g
from database import get_connection
from auth import requer_auth

usuarios_bp = Blueprint("usuarios", __name__)

def apenas_admin(f):
    """Decorator adicional para garantir que apenas admins acessem as rotas de usuarios."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'usuario') or g.usuario.get('papel') != 'admin':
            return jsonify({
                "status": "error", "data": None,
                "message": "Acesso negado. Apenas administradores podem gerenciar usuários."
            }), 403
        return f(*args, **kwargs)
    return wrapper

@usuarios_bp.route("/usuarios", methods=["GET"])
@requer_auth
@apenas_admin
def listar_usuarios():
    """Retorna todos os usuários cadastrados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome, email, papel, criado_em FROM usuarios ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    
    lista = [dict(r) for r in rows]
    return jsonify({
        "status": "success",
        "data": lista,
        "message": "Lista de usuários."
    }), 200

@usuarios_bp.route("/usuarios", methods=["POST"])
@requer_auth
@apenas_admin
def criar_usuario():
    """Cria um novo usuário."""
    dados = request.get_json()
    if not dados:
        return jsonify({"status": "error", "data": None, "message": "Corpo inválido."}), 400
        
    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")
    papel = dados.get("papel", "usuario")
    
    if not nome or not email or not senha:
        return jsonify({"status": "error", "data": None, "message": "Nome, email e senha são obrigatórios."}), 400
        
    senha_hash = hashlib.sha256(senha.encode()).hexdigest()
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, papel)
            VALUES (?, ?, ?, ?)
        """, (nome, email, senha_hash, papel))
        conn.commit()
        novo_id = cursor.lastrowid
    except Exception as e:
        conn.close()
        return jsonify({"status": "error", "data": None, "message": f"Erro ao criar usuário: {str(e)}"}), 500
    finally:
        conn.close()
        
    return jsonify({
        "status": "success",
        "data": {"id": novo_id},
        "message": "Usuário criado com sucesso."
    }), 201

@usuarios_bp.route("/usuarios/<int:usuario_id>/role", methods=["PUT"])
@requer_auth
@apenas_admin
def editar_papel(usuario_id):
    """Edita o papel (nível de acesso) de um usuário."""
    dados = request.get_json()
    novo_papel = dados.get("papel", "").strip() if dados else ""
    
    if not novo_papel:
        return jsonify({"status": "error", "data": None, "message": "O papel é obrigatório."}), 400
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET papel = ? WHERE id = ?", (novo_papel, usuario_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"status": "error", "data": None, "message": "Usuário não encontrado."}), 404
        
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "success",
        "data": None,
        "message": "Papel do usuário atualizado com sucesso."
    }), 200

@usuarios_bp.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
@requer_auth
@apenas_admin
def excluir_usuario(usuario_id):
    """Exclui um usuário do sistema."""
    # Impede auto-exclusão
    if g.usuario.get("id") == usuario_id:
        return jsonify({"status": "error", "data": None, "message": "Você não pode excluir sua própria conta."}), 400
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({"status": "error", "data": None, "message": "Usuário não encontrado."}), 404
        
    conn.commit()
    conn.close()
    
    return jsonify({
        "status": "success",
        "data": None,
        "message": "Usuário excluído com sucesso."
    }), 200
