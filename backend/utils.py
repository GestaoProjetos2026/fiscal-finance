from flask import jsonify, request
import datetime

def standard_response(success: bool, message: str, data: dict = None, status_code: int = 200):
    """
    Gera o envelope de resposta padrão da API (Core Engine).
    Formato exigido:
    {
      "success": true/false,
      "message": "...",
      "data": {...} ou null,
      "timestamp": "ISO-8601",
      "path": "/caminho/da/requisicao"
    }
    """
    response_body = {
        "success": success,
        "message": message,
        "data": data,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "path": request.path
    }
    return jsonify(response_body), status_code
