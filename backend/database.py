# src/database.py
import sqlite3
import os

# Reutiliza o banco SQLite do protótipo (não precisa criar do zero)
# O caminho pode ser sobrescrito pelo .env para facilitar uso com Docker
_PADRAO = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
DB_FILE = os.getenv("DB_PATH") or _PADRAO

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome (como dicionário)
        return conn
    except sqlite3.Error as e:
        print(f"\n[ERRO DE SISTEMA] Falha ao conectar ao banco de dados: {e}")
        raise

def init_db():
    # Verifica se o diretório data/ existe
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True)
    
    banco_existe = os.path.exists(DB_FILE) and os.path.getsize(DB_FILE) > 0

    if not banco_existe:
        print("\n================================================================")
        print("  AVISO: BANCO DE DADOS NAO ENCONTRADO OU VAZIO.")
        print("  Criando um novo banco de dados do zero...")
        print("  AVISO: Nao ha nenhum dado disponivel (banco limpo).")
        print("================================================================\n")

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            sku TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            preco_base REAL NOT NULL,
            aliquota REAL NOT NULL,
            estoque INTEGER DEFAULT 0
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT NOT NULL,
            tipo TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            data_movimentacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(sku) REFERENCES produtos(sku)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS caixa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor_liquido REAL NOT NULL,
            data_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS estoque_mov (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT,
            tipo TEXT,
            quantidade INTEGER,
            data_mov TEXT, 
            motivo TEXT,
            FOREIGN KEY(sku) REFERENCES produtos(sku)
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas_fiscais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_nota TEXT NOT NULL UNIQUE,
            descricao TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'rascunho',
            data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
        )""")

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_nota (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nota_id INTEGER NOT NULL,
            sku TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_base REAL NOT NULL,
            aliquota REAL NOT NULL,
            valor_bruto REAL NOT NULL,
            valor_imposto REAL NOT NULL,
            valor_total REAL NOT NULL,
            FOREIGN KEY(nota_id) REFERENCES notas_fiscais(id),
            FOREIGN KEY(sku) REFERENCES produtos(sku)
        )""")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"\n[ERRO DE SISTEMA] Falha ao criar tabelas no banco de dados: {e}")
