# src/database.py
import sqlite3
import os

# Reutiliza o banco SQLite do protótipo (não precisa criar do zero)
# O caminho pode ser sobrescrito pelo .env para facilitar uso com Docker
_PADRAO = os.path.join(os.path.dirname(__file__), "..", "data", "app.db")
DB_FILE = os.getenv("DB_PATH") or _PADRAO

def get_connection():
    """Retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Permite acessar colunas por nome (como dicionário)
    return conn
