# src/database.py
import sqlite3
import os

# FISC-MOD5-02: Caminho do banco configurável via ambiente para facilitar o uso com Docker.
# O padrão recai para a pasta data/app.db se a variável não estiver definida.
_PADRAO = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
DB_FILE = os.environ.get("DATABASE_URL") or _PADRAO

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return conn
