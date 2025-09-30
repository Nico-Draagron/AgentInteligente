from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

app = FastAPI()

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ajuste para seu domínio em produção
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Use variável de ambiente para alternar entre produção e teste
N8N_ENV = os.getenv("N8N_ENV", "test")  # "test" ou "prod"

# URLs corretas baseadas no webhook ID do seu workflow
N8N_MAIN_URL_TEST = "https://lobatofranca.app.n8n.cloud/webhook/af615c3e-1131-492d-8c03-b5f4a01cb0c6"
N8N_MAIN_URL_PROD = "https://lobatofranca.app.n8n.cloud/webhook/954a7292-a859-4c57-bcfd-e8de2a4905f1"

# Modelo para resposta estruturada
class ChatResponse(BaseModel):
    text: str
    tables: Optional[list] = []
    columns: Optional[list] = []
    sql_query: Optional[str] = ""
    visualization: Optional[Dict[str, Any]] = None

@app.post("/n8n/webhook/{workflow_name}")
async def n8n_webhook(workflow_name: str, request: Request):
    payload = await request.json()
    print(f"📩 Payload recebido para {workflow_name}:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    # Seleciona a URL correta
    if N8N_ENV == "prod":
        n8n_url = N8N_MAIN_URL_PROD
    else:
        n8n_url = N8N_MAIN_URL_TEST

    # Extrai campos do body se existirem
    chat_input = payload.get("chatInput") or payload.get("message")
    session_id = payload.get("sessionId", "default")

    if not chat_input:
        raise HTTPException(status_code=400, detail="Campo 'chatInput' ou 'message' obrigatório")

    n8n_payload = {
        "chatInput": chat_input,
        "sessionId": session_id
    }

    # Headers adequados para n8n
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        print(f"🚀 Enviando para n8n:")
        print(f"   URL: {n8n_url}")
        print(f"   Payload: {json.dumps(n8n_payload, indent=2, ensure_ascii=False)}")

        n8n_response = requests.post(
            n8n_url,
            json=n8n_payload,
            headers=headers,
            timeout=60
        )

        print(f"📡 Status Code: {n8n_response.status_code}")
        n8n_response.raise_for_status()

        # Parse da resposta
        try:
            response_data = n8n_response.json()
            print(f"✅ Resposta JSON recebida: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            
            # Estrutura a resposta para o frontend
            structured_response = {
                "text": response_data.get("text", ""),
                "tables": response_data.get("tables", []),
                "columns": response_data.get("columns", []),
                "sql_query": response_data.get("query", response_data.get("sql_query", "")),
                "visualization": None
            }
            
            # Parse do campo visualization se existir
            if "visualization" in response_data:
                try:
                    # Se visualization já for um dict, usa direto
                    if isinstance(response_data["visualization"], dict):
                        structured_response["visualization"] = response_data["visualization"]
                    # Se for uma string JSON, faz parse
                    elif isinstance(response_data["visualization"], str):
                        structured_response["visualization"] = json.loads(response_data["visualization"])
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"⚠️ Erro ao processar visualization: {e}")
                    # Ignora visualization se houver erro
            
            print(f"📊 Resposta estruturada: {json.dumps(structured_response, indent=2, ensure_ascii=False)}")
            return structured_response
            
        except ValueError as e:
            print(f"⚠️ Resposta não é JSON válido: {n8n_response.text[:500]}")
            return {
                "text": n8n_response.text,
                "tables": [],
                "columns": [],
                "sql_query": "",
                "visualization": None
            }

    except requests.exceptions.Timeout:
        print(f"⌚ Timeout ao aguardar resposta do n8n")
        raise HTTPException(status_code=504, detail="Timeout ao aguardar resposta do n8n")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Erro de conexão com n8n: {e}")
        raise HTTPException(status_code=502, detail=f"Erro de conexão com n8n: {str(e)}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro ao consultar n8n: {e}")
        raise HTTPException(status_code=502, detail=f"Erro ao consultar n8n: {str(e)}")

@app.get("/health")
def health():
    return {"status": "ok", "n8n_env": N8N_ENV}

@app.post("/test/n8n")
async def test_n8n():
    """Endpoint para testar conectividade com n8n"""
    test_payload = {
        "chatInput": "Qual a geração total de energia hoje?",
        "sessionId": "test-session"
    }
    
    # Testa apenas a URL principal
    if N8N_ENV == "prod":
        url = N8N_MAIN_URL_PROD
    else:
        url = N8N_MAIN_URL_TEST
    
    try:
        response = requests.post(url, json=test_payload, timeout=30)
        
        result = {
            "url": url,
            "status": "success" if response.status_code == 200 else "error",
            "status_code": response.status_code
        }
        
        # Tenta parsear a resposta
        try:
            response_json = response.json()
            result["response_structure"] = {
                "has_text": "text" in response_json,
                "has_visualization": "visualization" in response_json,
                "has_tables": "tables" in response_json,
                "has_sql": "query" in response_json or "sql_query" in response_json
            }
        except:
            result["response_preview"] = response.text[:200] + "..." if len(response.text) > 200 else response.text
            
    except Exception as e:
        result = {
            "url": url,
            "status": "error",
            "error": str(e)
        }
    
    return {
        "environment": N8N_ENV,
        "test_result": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)