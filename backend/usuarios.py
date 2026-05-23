import bcrypt
from flask import Blueprint, request, g
from utils import standard_response
from database import get_connection
from auth import requer_auth

usuarios_bp = Blueprint("usuarios", __name__)

def apenas_admin(f):
    """Decorator adicional para garantir que apenas admins acessem as rotas de usuarios."""
    from functools import wraps
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not hasattr(g, 'usuario') or g.usuario.get('papel') != 'admin':
            return standard_response(success=False, message="Acesso negado. Apenas administradores podem gerenciar usuários.", data=None, status_code=403)
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
    return standard_response(success=True, message="Lista de usuários.", data=lista, status_code=200)

@usuarios_bp.route("/usuarios", methods=["POST"])
@requer_auth
@apenas_admin
def criar_usuario():
    """Cria um novo usuário."""
    dados = request.get_json()
    if not dados:
        return standard_response(success=False, message="Corpo inválido.", data=None, status_code=400)
        
    nome = dados.get("nome", "").strip()
    email = dados.get("email", "").strip().lower()
    senha = dados.get("senha", "")
    papel = dados.get("papel", "usuario")
    
    if not nome or not email or not senha:
        return standard_response(success=False, message="Nome, email e senha são obrigatórios.", data=None, status_code=400)
        
    senha_hash = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode('utf-8')
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha_hash, papel)
            VALUES (?, ?, ?, ?)
        """, (nome, email, senha_hash, papel))
        
        cursor.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
        usuario_row = cursor.fetchone()
        if usuario_row:
            try:
                novo_id = usuario_row["id"]
            except Exception:
                novo_id = usuario_row[0]
        else:
            novo_id = cursor.lastrowid
            
        conn.commit()
    except Exception as e:
        conn.close()
        return standard_response(success=False, message=f"Erro ao criar usuário: {str(e)}", data=None, status_code=500)
    finally:
        conn.close()
        
    return standard_response(success=True, message="Usuário criado com sucesso.", data={"id": novo_id}, status_code=201)

@usuarios_bp.route("/usuarios/<int:usuario_id>/role", methods=["PUT"])
@requer_auth
@apenas_admin
def editar_papel(usuario_id):
    """Edita o papel (nível de acesso) de um usuário."""
    dados = request.get_json()
    novo_papel = dados.get("papel", "").strip() if dados else ""
    
    if not novo_papel:
        return standard_response(success=False, message="O papel é obrigatório.", data=None, status_code=400)
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE usuarios SET papel = ? WHERE id = ?", (novo_papel, usuario_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return standard_response(success=False, message="Usuário não encontrado.", data=None, status_code=404)
        
    conn.commit()
    conn.close()
    
    return standard_response(success=True, message="Papel do usuário atualizado com sucesso.", data=None, status_code=200)

@usuarios_bp.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
@requer_auth
@apenas_admin
def excluir_usuario(usuario_id):
    """Exclui um usuário do sistema."""
    # Impede auto-exclusão
    if g.usuario.get("id") == usuario_id:
        return standard_response(success=False, message="Você não pode excluir sua própria conta.", data=None, status_code=400)
        
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        return standard_response(success=False, message="Usuário não encontrado.", data=None, status_code=404)
        
    conn.commit()
    conn.close()
    
    return standard_response(success=True, message="Usuário excluído com sucesso.", data=None, status_code=200)
