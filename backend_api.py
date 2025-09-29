# ============================================================================
# ARQUIVO 1: backend_api.py - FastAPI para n8n
# ============================================================================

"""
SALVAR COMO: backend_api.py
EXECUTAR: uvicorn backend_api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
import redis
import numpy as np
import pandas as pd
from enum import Enum

# ============================================================================
# CONFIGURAÇÃO FASTAPI
# ============================================================================

app = FastAPI(
    title="AIDE v2 - API para n8n",
    description="API do Sistema Inteligente do Setor Elétrico com integração n8n",
    version="2.0.0"
)

# CORS para n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar o domínio do n8n
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis para compartilhar dados com Streamlit
try:
    redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
    redis_client.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    print("⚠️ Redis não disponível - usando memória local")

# ============================================================================
# MODELOS DE DADOS
# ============================================================================

class DataSource(str, Enum):
    ONS_API = "ons_api"
    N8N_WEBHOOK = "n8n_webhook"
    MANUAL = "manual"
    SCHEDULED = "scheduled"

class EnergyData(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    source: DataSource
    consumption_mw: float
    generation_mw: float
    subsystem: str
    metadata: Optional[Dict] = {}

class N8nTrigger(BaseModel):
    workflow_name: str
    trigger_type: str  # data_update, alert, report, analysis
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)

class WebhookPayload(BaseModel):
    event: str
    data: Dict
    source: str = "n8n"
    workflow_id: Optional[str] = None

class AlertConfig(BaseModel):
    alert_type: str  # consumption_high, price_spike, reservoir_low
    threshold: float
    subsystems: List[str]
    notify_n8n: bool = True

# ============================================================================
# GERENCIADOR DE WEBSOCKET
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.n8n_subscribers: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Envia mensagem para todos os clientes conectados"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

    async def send_to_n8n_subscribers(self, workflow: str, data: dict):
        """Envia dados específicos para subscribers de workflows n8n"""
        if workflow in self.n8n_subscribers:
            for connection in self.n8n_subscribers[workflow]:
                try:
                    await connection.send_json(data)
                except:
                    pass

manager = ConnectionManager()

# ============================================================================
# SIMULADOR DE DADOS ONS
# ============================================================================

class ONSDataService:
    @staticmethod
    def get_current_metrics() -> Dict:
        """Retorna métricas atuais do sistema"""
        base_load = 65000
        hour = datetime.now().hour
        hour_factor = 1 + 0.3 * np.sin((hour - 14) * np.pi / 12)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_load_mw": base_load * hour_factor * (1 + np.random.normal(0, 0.02)),
            "generation_mix": {
                "hydro": 42850 + np.random.normal(0, 1000),
                "thermal": 8750 + np.random.normal(0, 500),
                "wind": 12300 + np.random.normal(0, 800),
                "solar": 4200 * max(0, np.sin((hour - 6) * np.pi / 12)),
                "nuclear": 1990,
                "import": 890 + np.random.normal(0, 100)
            },
            "reservoir_levels": {
                "SE_CO": 68.5 + np.random.normal(0, 2),
                "S": 82.3 + np.random.normal(0, 2),
                "NE": 54.7 + np.random.normal(0, 2),
                "N": 91.2 + np.random.normal(0, 2)
            },
            "pld_prices": {
                "SE_CO": 145.32 + np.random.normal(0, 10),
                "S": 142.18 + np.random.normal(0, 10),
                "NE": 89.45 + np.random.normal(0, 10),
                "N": 78.92 + np.random.normal(0, 10)
            }
        }

    @staticmethod
    def check_alerts(data: Dict) -> List[Dict]:
        """Verifica condições de alerta"""
        alerts = []
        
        # Alerta de consumo alto
        if data["total_load_mw"] > 70000:
            alerts.append({
                "type": "high_consumption",
                "severity": "warning",
                "value": data["total_load_mw"],
                "message": f"Consumo elevado: {data['total_load_mw']:.0f} MW"
            })
        
        # Alerta de reservatório baixo
        for region, level in data["reservoir_levels"].items():
            if level < 60:
                alerts.append({
                    "type": "low_reservoir",
                    "severity": "critical" if level < 50 else "warning",
                    "region": region,
                    "value": level,
                    "message": f"Reservatório {region} em {level:.1f}%"
                })
        
        # Alerta de preço PLD alto
        for region, price in data["pld_prices"].items():
            if price > 200:
                alerts.append({
                    "type": "high_pld",
                    "severity": "warning",
                    "region": region,
                    "value": price,
                    "message": f"PLD {region}: R$ {price:.2f}/MWh"
                })
        
        return alerts

# ============================================================================
# ENDPOINTS PARA N8N
# ============================================================================

@app.get("/")
async def root():
    return {
        "name": "AIDE v2 API",
        "status": "online",
        "version": "2.0.0",
        "endpoints": {
            "n8n_webhook": "/n8n/webhook/{workflow_name}",
            "metrics": "/api/metrics/current",
            "trigger": "/api/trigger/n8n",
            "websocket": "ws://localhost:8000/ws"
        }
    }

# ============================================================================
# WEBHOOK PRINCIPAL DO N8N
# ============================================================================

@app.post("/n8n/webhook/{workflow_name}")
async def n8n_webhook(
    workflow_name: str,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Endpoint principal para receber dados do n8n
    O n8n pode enviar dados de diferentes workflows aqui
    """
    try:
        # Log do webhook recebido
        webhook_data = {
            "timestamp": datetime.now().isoformat(),
            "workflow": workflow_name,
            "payload": payload
        }
        
        # Salvar no Redis ou memória
        if REDIS_AVAILABLE:
            redis_client.set(f"n8n:webhook:{workflow_name}", json.dumps(webhook_data))
            redis_client.expire(f"n8n:webhook:{workflow_name}", 3600)
        
        # Processar baseado no tipo de workflow
        if workflow_name == "data_ingestion":
            # Workflow de ingestão de dados
            processed_data = await process_data_ingestion(payload)
            
            # Broadcast para WebSocket
            await manager.broadcast({
                "type": "data_update",
                "source": "n8n",
                "workflow": workflow_name,
                "data": processed_data
            })
            
        elif workflow_name == "alert_monitoring":
            # Workflow de monitoramento
            alerts = await process_alerts(payload)
            
            # Notificar subscribers
            await manager.broadcast({
                "type": "alert",
                "source": "n8n",
                "alerts": alerts
            })
            
        elif workflow_name == "report_generation":
            # Workflow de geração de relatórios
            background_tasks.add_task(generate_report, payload)
            
        elif workflow_name == "ml_prediction":
            # Workflow de predição ML
            prediction = await process_ml_prediction(payload)
            
            # Salvar predição
            if REDIS_AVAILABLE:
                redis_client.set("latest_prediction", json.dumps(prediction))
        
        # Resposta para o n8n
        return {
            "status": "success",
            "workflow": workflow_name,
            "timestamp": datetime.now().isoformat(),
            "message": f"Webhook {workflow_name} processado com sucesso"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# TRIGGER PARA N8N (AIDE -> N8N)
# ============================================================================

@app.post("/api/trigger/n8n")
async def trigger_n8n_workflow(trigger: N8nTrigger):
    """
    Permite que o AIDE dispare workflows no n8n
    Útil para automatizações bidirecionais
    """
    try:
        # Aqui você configuraria a URL do seu n8n
        n8n_webhook_url = f"http://localhost:5678/webhook/{trigger.workflow_name}"
        
        # Preparar dados para n8n
        n8n_payload = {
            "trigger_type": trigger.trigger_type,
            "timestamp": trigger.timestamp.isoformat(),
            "aide_data": trigger.data,
            "metadata": {
                "source": "AIDE_v2",
                "version": "2.0.0"
            }
        }
        
        # Em produção, fazer chamada HTTP real para n8n
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(n8n_webhook_url, json=n8n_payload)
        
        # Simulação de resposta
        response = {
            "status": "triggered",
            "workflow": trigger.workflow_name,
            "n8n_response": "Workflow iniciado com sucesso"
        }
        
        # Log no Redis
        if REDIS_AVAILABLE:
            redis_client.lpush("n8n_triggers", json.dumps({
                "workflow": trigger.workflow_name,
                "timestamp": trigger.timestamp.isoformat(),
                "type": trigger.trigger_type
            }))
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# ENDPOINTS DE DADOS
# ============================================================================

@app.get("/api/metrics/current")
async def get_current_metrics():
    """Retorna métricas atuais do sistema"""
    metrics = ONSDataService.get_current_metrics()
    
    # Verificar alertas
    alerts = ONSDataService.check_alerts(metrics)
    
    # Se houver alertas críticos, notificar n8n
    critical_alerts = [a for a in alerts if a["severity"] == "critical"]
    if critical_alerts:
        await trigger_n8n_workflow(N8nTrigger(
            workflow_name="critical_alert_handler",
            trigger_type="alert",
            data={"alerts": critical_alerts}
        ))
    
    return {
        "status": "success",
        "data": metrics,
        "alerts": alerts,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/metrics/historical")
async def get_historical_metrics(hours: int = 24, subsystem: Optional[str] = None):
    """Retorna dados históricos"""
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Simular dados históricos
    timestamps = pd.date_range(start=start_time, end=end_time, freq='H')
    data = []
    
    for ts in timestamps:
        hour = ts.hour
        base = 60000
        hour_factor = 1 + 0.3 * np.sin((hour - 14) * np.pi / 12)
        
        data.append({
            "timestamp": ts.isoformat(),
            "consumption": base * hour_factor * (1 + np.random.normal(0, 0.02)),
            "generation": base * hour_factor * (1 + np.random.normal(0, 0.02)),
            "price": 145 + np.random.normal(0, 20)
        })
    
    return {
        "status": "success",
        "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
        "data": data
    }

@app.post("/api/data/ingest")
async def ingest_data(data: EnergyData):
    """Endpoint para ingestão manual de dados"""
    try:
        # Validar dados
        if data.consumption_mw < 0 or data.generation_mw < 0:
            raise ValueError("Valores negativos não permitidos")
        
        # Salvar no Redis
        if REDIS_AVAILABLE:
            key = f"energy_data:{data.subsystem}:{data.timestamp.isoformat()}"
            redis_client.set(key, data.json())
            redis_client.expire(key, 86400)  # 24 horas
        
        # Broadcast via WebSocket
        await manager.broadcast({
            "type": "data_ingestion",
            "data": data.dict()
        })
        
        return {"status": "success", "message": "Dados ingeridos com sucesso"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================================
# WEBSOCKET PARA TEMPO REAL
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket para comunicação em tempo real com Streamlit e n8n"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Enviar métricas a cada 5 segundos
            metrics = ONSDataService.get_current_metrics()
            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics
            })
            
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ============================================================================
# FUNÇÕES AUXILIARES DE PROCESSAMENTO
# ============================================================================

async def process_data_ingestion(payload: Dict) -> Dict:
    """Processa dados recebidos do n8n"""
    # Extrair e validar dados
    processed = {
        "timestamp": datetime.now().isoformat(),
        "records_processed": len(payload.get("data", [])),
        "status": "processed"
    }
    
    # Aqui você processaria os dados reais
    # Por exemplo, salvar no banco, calcular métricas, etc.
    
    return processed

async def process_alerts(payload: Dict) -> List[Dict]:
    """Processa alertas do n8n"""
    alerts = []
    
    for alert_data in payload.get("alerts", []):
        alerts.append({
            "id": alert_data.get("id"),
            "type": alert_data.get("type"),
            "severity": alert_data.get("severity", "info"),
            "message": alert_data.get("message"),
            "timestamp": datetime.now().isoformat()
        })
    
    return alerts

async def process_ml_prediction(payload: Dict) -> Dict:
    """Processa predições ML do n8n"""
    # Simular processamento de ML
    return {
        "prediction_type": payload.get("type", "demand_forecast"),
        "horizon_hours": payload.get("horizon", 24),
        "confidence": 0.85 + np.random.uniform(-0.05, 0.05),
        "values": [np.random.uniform(60000, 70000) for _ in range(24)]
    }

async def generate_report(payload: Dict):
    """Gera relatório em background"""
    # Simular geração de relatório
    await asyncio.sleep(5)
    
    report = {
        "id": f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "type": payload.get("report_type", "daily"),
        "status": "completed",
        "url": f"/reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    }
    
    # Notificar via WebSocket
    await manager.broadcast({
        "type": "report_ready",
        "report": report
    })

# ============================================================================
# ENDPOINTS DE MONITORAMENTO
# ============================================================================

@app.get("/api/health")
async def health_check():
    """Health check para n8n monitorar"""
    return {
        "status": "healthy",
        "services": {
            "api": "online",
            "redis": "online" if REDIS_AVAILABLE else "offline",
            "websocket": "online"
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/stats")
async def get_stats():
    """Estatísticas do sistema"""
    stats = {
        "active_connections": len(manager.active_connections),
        "redis_available": REDIS_AVAILABLE,
        "last_webhook": None,
        "total_triggers": 0
    }
    
    if REDIS_AVAILABLE:
        stats["total_triggers"] = redis_client.llen("n8n_triggers")
    
    return stats
