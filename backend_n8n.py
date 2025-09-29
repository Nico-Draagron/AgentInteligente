from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json

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
# Para teste, use o webhookId do node Webhook

N8N_MAIN_URL_TEST = "https://lobatofranca.app.n8n.cloud/webhook/af615c3e-1131-492d-8c03-b5f4a01cb0c6"
N8N_MAIN_URL_PROD = "https://lobatofranca.app.n8n.cloud/webhook/954a7292-a859-4c57-bcfd-e8de2a4905f1"


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
    body = payload.get("body")
    chat_input = payload.get("chatInput") or payload.get("message")
    session_id = payload.get("sessionId")

    n8n_payload = {}
    if chat_input:
        n8n_payload["chatInput"] = chat_input
    if session_id:
        n8n_payload["sessionId"] = session_id
    if not chat_input:
        raise HTTPException(status_code=400, detail="Campo 'chatInput' ou 'message' obrigatório")

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
        print(f"📡 Response Headers: {dict(n8n_response.headers)}")
        print(f"📡 Response Content: {n8n_response.text[:500]}...")

        n8n_response.raise_for_status()

        # Retorna resposta como JSON se possível
        try:
            response_data = n8n_response.json()
            print(f"✅ Resposta JSON: {json.dumps(response_data, indent=2, ensure_ascii=False)}")
            return response_data
        except ValueError:
            print(f"✅ Resposta texto: {n8n_response.text}")
            return {"text": n8n_response.text}

    except requests.exceptions.Timeout:
        print(f"❌ Timeout ao aguardar resposta do n8n")
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


# Endpoint para testar conectividade
@app.post("/test/n8n")
async def test_n8n():
    test_payload = {
        "message": "Teste de conectividade",
        "chatInput": "Teste de conectividade"
    }
    
    # Testa apenas a URL principal
    if N8N_ENV == "prod":
        urls_to_test = [N8N_MAIN_URL_PROD]
    else:
        urls_to_test = [N8N_MAIN_URL_TEST]
    
    results = []
    
    for url in urls_to_test:
        try:
            response = requests.post(url, json=test_payload, timeout=30)
            results.append({
                "url": url,
                "status": "success" if response.status_code == 200 else "error",
                "status_code": response.status_code,
                "response_preview": response.text[:200] + "..." if len(response.text) > 200 else response.text
            })
        except Exception as e:
            results.append({
                "url": url,
                "status": "error",
                "error": str(e)
            })
    
    return {
        "environment": N8N_ENV,
        "results": results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)