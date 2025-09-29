"""
AIDE v2 - Sistema Integrado com n8n
Backend FastAPI + Frontend Streamlit + n8n Workflows
"""

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

# ============================================================================
# ============================================================================
# ARQUIVO 2: streamlit_app.py - Frontend Streamlit
# ============================================================================
# ============================================================================

"""
SALVAR COMO: streamlit_app.py
EXECUTAR: streamlit run streamlit_app.py
"""

import streamlit as st
import requests
import websocket
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time

# Configuração da página
st.set_page_config(
    page_title="AIDE v2 - Dashboard n8n",
    page_icon="⚡",
    layout="wide"
)

# ============================================================================
# CONFIGURAÇÃO DA API
# ============================================================================

API_BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws"

# ============================================================================
# FUNÇÕES DE COMUNICAÇÃO COM API
# ============================================================================

def fetch_current_metrics():
    """Busca métricas atuais da API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/metrics/current")
        if response.status_code == 200:
            return response.json()
    except:
        return None

def fetch_historical_data(hours=24):
    """Busca dados históricos"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/metrics/historical?hours={hours}")
        if response.status_code == 200:
            return response.json()
    except:
        return None

def trigger_n8n_workflow(workflow_name, trigger_type, data):
    """Dispara workflow no n8n"""
    try:
        payload = {
            "workflow_name": workflow_name,
            "trigger_type": trigger_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        response = requests.post(f"{API_BASE_URL}/api/trigger/n8n", json=payload)
        return response.status_code == 200
    except:
        return False

def check_api_health():
    """Verifica saúde da API"""
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        return response.status_code == 200
    except:
        return False

# ============================================================================
# INTERFACE PRINCIPAL
# ============================================================================

st.title("⚡ AIDE v2 - Integração n8n")
st.markdown("Sistema Inteligente do Setor Elétrico com Automação n8n")

# Verificar status da API
api_status = check_api_health()

# Status bar
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("API Status", "🟢 Online" if api_status else "🔴 Offline")

with col2:
    st.metric("n8n Integration", "🟢 Ativo" if api_status else "🔴 Inativo")

with col3:
    st.metric("WebSocket", "🟡 Conectando...")

with col4:
    st.metric("Última Atualização", datetime.now().strftime("%H:%M:%S"))

# Tabs principais
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard", 
    "🔄 n8n Workflows", 
    "🚨 Alertas",
    "📡 Monitor API"
])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================

with tab1:
    if api_status:
        # Buscar métricas
        metrics = fetch_current_metrics()
        
        if metrics and "data" in metrics:
            data = metrics["data"]
            
            # Métricas principais
            st.markdown("### 📈 Métricas em Tempo Real")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Carga Total",
                    f"{data['total_load_mw']/1000:.1f} GW",
                    "↑ 2.3%"
                )
            
            with col2:
                total_gen = sum(data['generation_mix'].values())
                renewable = data['generation_mix']['hydro'] + data['generation_mix']['wind'] + data['generation_mix']['solar']
                renewable_pct = (renewable/total_gen) * 100
                st.metric(
                    "Renováveis",
                    f"{renewable_pct:.1f}%",
                    "↑ 1.2%"
                )
            
            with col3:
                avg_reservoir = sum(data['reservoir_levels'].values()) / len(data['reservoir_levels'])
                st.metric(
                    "Reservatórios",
                    f"{avg_reservoir:.1f}%",
                    "↓ 0.5%"
                )
            
            with col4:
                avg_pld = sum(data['pld_prices'].values()) / len(data['pld_prices'])
                st.metric(
                    "PLD Médio",
                    f"R$ {avg_pld:.0f}",
                    "↑ R$ 5"
                )
            
            # Gráficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Mix de geração
                fig = px.pie(
                    values=list(data['generation_mix'].values()),
                    names=list(data['generation_mix'].keys()),
                    title="Mix de Geração Atual"
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Níveis dos reservatórios
                df_res = pd.DataFrame(
                    list(data['reservoir_levels'].items()),
                    columns=['Região', 'Nível (%)']
                )
                fig = px.bar(
                    df_res,
                    x='Região',
                    y='Nível (%)',
                    title="Níveis dos Reservatórios",
                    color='Nível (%)',
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Alertas ativos
            if "alerts" in metrics and metrics["alerts"]:
                st.markdown("### 🚨 Alertas Ativos")
                for alert in metrics["alerts"]:
                    severity_icon = "🔴" if alert["severity"] == "critical" else "🟡"
                    st.warning(f"{severity_icon} {alert['message']}")
    else:
        st.error("❌ API offline - Verifique se o backend está rodando")

# ============================================================================
# TAB 2: N8N WORKFLOWS
# ============================================================================

with tab2:
    st.markdown("### 🔄 Gerenciamento de Workflows n8n")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Disparar Workflow")
        
        workflow = st.selectbox(
            "Selecione o Workflow",
            ["data_ingestion", "alert_monitoring", "report_generation", "ml_prediction"]
        )
        
        trigger_type = st.selectbox(
            "Tipo de Trigger",
            ["manual", "scheduled", "alert", "data_update"]
        )
        
        custom_data = st.text_area(
            "Dados Customizados (JSON)",
            value='{"key": "value"}',
            height=100
        )
        
        if st.button("🚀 Disparar Workflow"):
            try:
                data = json.loads(custom_data)
                if trigger_n8n_workflow(workflow, trigger_type, data):
                    st.success(f"✅ Workflow '{workflow}' disparado com sucesso!")
                else:
                    st.error("❌ Erro ao disparar workflow")
            except json.JSONDecodeError:
                st.error("❌ JSON inválido")
    
    with col2:
        st.markdown("#### Workflows Ativos")
        
        # Lista de workflows configurados
        workflows = [
            {"name": "data_ingestion", "status": "🟢 Ativo", "last_run": "10:30"},
            {"name": "alert_monitoring", "status": "🟢 Ativo", "last_run": "10:35"},
            {"name": "report_generation", "status": "🟡 Aguardando", "last_run": "09:00"},
            {"name": "ml_prediction", "status": "🟢 Ativo", "last_run": "10:20"}
        ]
        
        for wf in workflows:
            st.info(f"**{wf['name']}** {wf['status']} - Última execução: {wf['last_run']}")
    
    st.markdown("---")
    
    # Configuração de Webhooks
    st.markdown("### 🔗 Configuração de Webhooks")
    
    webhook_url = st.text_input(
        "URL do Webhook n8n",
        value="http://localhost:5678/webhook/aide-integration"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Testar Data Ingestion"):
            st.info("Enviando dados de teste para n8n...")
            # Aqui faria a chamada real
            st.success("✅ Teste concluído!")
    
    with col2:
        if st.button("🚨 Testar Alert"):
            st.info("Enviando alerta de teste...")
            st.success("✅ Alerta enviado!")
    
    with col3:
        if st.button("📈 Testar Report"):
            st.info("Solicitando relatório...")
            st.success("✅ Relatório solicitado!")

# ============================================================================
# TAB 3: ALERTAS
# ============================================================================

with tab3:
    st.markdown("### 🚨 Central de Alertas")
    
    # Configuração de alertas
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Configurar Novo Alerta")
        
        alert_type = st.selectbox(
            "Tipo de Alerta",
            ["Consumo Alto", "Preço PLD Elevado", "Reservatório Baixo", "Falha de Geração"]
        )
        
        threshold = st.number_input(
            "Threshold",
            min_value=0.0,
            max_value=100000.0,
            value=70000.0
        )
        
        subsystems = st.multiselect(
            "Subsistemas",
            ["SE/CO", "Sul", "Nordeste", "Norte"],
            default=["SE/CO"]
        )
        
        notify_n8n = st.checkbox("Notificar n8n", value=True)
        
        if st.button("➕ Criar Alerta"):
            st.success("✅ Alerta configurado com sucesso!")
    
    with col2:
        st.markdown("#### Alertas Ativos")
        
        # Simular alertas
        alerts = [
            {"type": "⚡ Consumo Alto", "value": "71.2 GW", "time": "10:35", "severity": "warning"},
            {"type": "💧 Reservatório NE", "value": "54.7%", "time": "10:30", "severity": "warning"},
            {"type": "💰 PLD SE/CO", "value": "R$ 165", "time": "10:25", "severity": "info"}
        ]
        
        for alert in alerts:
            if alert["severity"] == "critical":
                st.error(f"{alert['type']}: {alert['value']} - {alert['time']}")
            elif alert["severity"] == "warning":
                st.warning(f"{alert['type']}: {alert['value']} - {alert['time']}")
            else:
                st.info(f"{alert['type']}: {alert['value']} - {alert['time']}")
    
    # Histórico de alertas
    st.markdown("### 📜 Histórico de Alertas (24h)")
    
    history_data = pd.DataFrame({
        'Horário': pd.date_range(end=datetime.now(), periods=20, freq='H'),
        'Tipo': ['Consumo Alto'] * 10 + ['Reservatório Baixo'] * 5 + ['PLD Elevado'] * 5,
        'Severidade': ['warning'] * 15 + ['critical'] * 5
    })
    
    fig = px.scatter(
        history_data,
        x='Horário',
        y='Tipo',
        color='Severidade',
        title="Timeline de Alertas",
        color_discrete_map={'warning': 'orange', 'critical': 'red', 'info': 'blue'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# TAB 4: MONITOR API
# ============================================================================

with tab4:
    st.markdown("### 📡 Monitor da API e Integração n8n")
    
    # Status dos serviços
    st.markdown("#### 🟢 Status dos Serviços")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        api_health = check_api_health()
        st.metric(
            "FastAPI Backend",
            "Online" if api_health else "Offline",
            "✅" if api_health else "❌"
        )
    
    with col2:
        # Verificar Redis (simulado)
        redis_status = api_health  # Simplificado
        st.metric(
            "Redis Cache",
            "Connected" if redis_status else "Disconnected",
            "✅" if redis_status else "❌"
        )
    
    with col3:
        # WebSocket status (simulado)
        ws_status = api_health
        st.metric(
            "WebSocket",
            "Active" if ws_status else "Inactive",
            "✅" if ws_status else "❌"
        )
    
    # Logs em tempo real
    st.markdown("#### 📝 Logs em Tempo Real")
    
    log_container = st.empty()
    
    # Simular logs
    logs = [
        f"{datetime.now().strftime('%H:%M:%S')} - INFO: Métricas atualizadas",
        f"{datetime.now().strftime('%H:%M:%S')} - INFO: Webhook n8n recebido: data_ingestion",
        f"{datetime.now().strftime('%H:%M:%S')} - WARNING: Consumo acima do normal",
        f"{datetime.now().strftime('%H:%M:%S')} - INFO: Relatório gerado com sucesso",
        f"{datetime.now().strftime('%H:%M:%S')} - INFO: WebSocket: 2 clientes conectados"
    ]
    
    log_container.text_area("Logs", value="\n".join(logs), height=200)
    
    # Estatísticas
    st.markdown("#### 📊 Estatísticas da API")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Requisições/min", "127")
    
    with col2:
        st.metric("Latência média", "45ms")
    
    with col3:
        st.metric("Taxa de erro", "0.2%")
    
    with col4:
        st.metric("Uptime", "99.9%")
    
    # Gráfico de performance
    performance_data = pd.DataFrame({
        'Tempo': pd.date_range(end=datetime.now(), periods=60, freq='min'),
        'Latência (ms)': [45 + np.random.normal(0, 10) for _ in range(60)],
        'Requisições': [120 + np.random.normal(0, 20) for _ in range(60)]
    })
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=performance_data['Tempo'],
        y=performance_data['Latência (ms)'],
        name='Latência',
        yaxis='y'
    ))
    
    fig.add_trace(go.Scatter(
        x=performance_data['Tempo'],
        y=performance_data['Requisições'],
        name='Requisições/min',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Performance da API",
        yaxis=dict(title="Latência (ms)"),
        yaxis2=dict(title="Requisições/min", overlaying='y', side='right'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Sidebar
with st.sidebar:
    st.markdown("## 🎛️ Controle n8n")
    
    # Auto refresh
    auto_refresh = st.checkbox("Auto-refresh (5s)", value=False)
    
    if auto_refresh:
        time.sleep(5)
        st.rerun()
    
    st.markdown("---")
    
    # Ações rápidas
    st.markdown("### ⚡ Ações Rápidas")
    
    if st.button("🔄 Sincronizar Dados"):
        if trigger_n8n_workflow("data_ingestion", "manual", {"source": "streamlit"}):
            st.success("✅ Sincronizado!")
    
    if st.button("📊 Gerar Relatório"):
        if trigger_n8n_workflow("report_generation", "manual", {"type": "daily"}):
            st.success("✅ Relatório solicitado!")
    
    if st.button("🤖 Executar Predição"):
        if trigger_n8n_workflow("ml_prediction", "manual", {"horizon": 24}):
            st.success("✅ Predição iniciada!")
    
    st.markdown("---")
    
    st.markdown("### 📚 Documentação")
    st.markdown("""
    **Endpoints Principais:**
    - `/n8n/webhook/{workflow}` - Webhook n8n
    - `/api/metrics/current` - Métricas atuais
    - `/api/trigger/n8n` - Disparar workflow
    - `/ws` - WebSocket real-time
    
    **Workflows Disponíveis:**
    - `data_ingestion` - Ingestão de dados
    - `alert_monitoring` - Monitoramento
    - `report_generation` - Relatórios
    - `ml_prediction` - Predições ML
    """)

# ============================================================================
# ============================================================================
# ARQUIVO 3: docker-compose.yml - Orquestração
# ============================================================================
# ============================================================================

"""
SALVAR COMO: docker-compose.yml
"""

docker_compose = '''
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - aide_network

  fastapi:
    build:
      context: .
      dockerfile: Dockerfile.api
    ports:
      - "8000:8000"
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    networks:
      - aide_network
    volumes:
      - ./backend_api.py:/app/main.py

  streamlit:
    build:
      context: .
      dockerfile: Dockerfile.streamlit
    ports:
      - "8501:8501"
    environment:
      - API_URL=http://fastapi:8000
    depends_on:
      - fastapi
    networks:
      - aide_network
    volumes:
      - ./streamlit_app.py:/app/streamlit_app.py

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=false
      - N8N_WEBHOOK_URL=http://localhost:5678/
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - aide_network

networks:
  aide_network:
    driver: bridge

volumes:
  redis_data:
  n8n_data:
'''

# ============================================================================
# ARQUIVO 4: requirements.txt
# ============================================================================

requirements = '''
# FastAPI Backend
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
redis==5.0.1
pandas==2.1.3
numpy==1.24.3
httpx==0.25.1
websockets==12.0

# Streamlit Frontend
streamlit==1.28.2
plotly==5.18.0
requests==2.31.0
websocket-client==1.6.4
'''

# ============================================================================
# ARQUIVO 5: Dockerfile.api
# ============================================================================

dockerfile_api = '''
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend_api.py main.py

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
'''

# ============================================================================
# ARQUIVO 6: Dockerfile.streamlit
# ============================================================================

dockerfile_streamlit = '''
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY streamlit_app.py .

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
'''

print("""
============================================================================
INSTRUÇÕES DE INSTALAÇÃO E EXECUÇÃO
============================================================================

1. CRIAR ESTRUTURA DE ARQUIVOS:
   aide_n8n/
   ├── backend_api.py       (Arquivo 1 acima)
   ├── streamlit_app.py     (Arquivo 2 acima)
   ├── docker-compose.yml   (Arquivo 3 acima)
   ├── requirements.txt     (Arquivo 4 acima)
   ├── Dockerfile.api       (Arquivo 5 acima)
   └── Dockerfile.streamlit (Arquivo 6 acima)

2. OPÇÃO A - EXECUTAR COM DOCKER (RECOMENDADO):
   cd aide_n8n
   docker-compose up

3. OPÇÃO B - EXECUTAR LOCALMENTE:
   # Terminal 1 - Redis
   docker run -p 6379:6379 redis:7-alpine
   
   # Terminal 2 - FastAPI
   pip install -r requirements.txt
   uvicorn backend_api:app --reload --port 8000
   
   # Terminal 3 - Streamlit
   streamlit run streamlit_app.py
   
   # Terminal 4 - n8n
   docker run -p 5678:5678 n8nio/n8n

4. ACESSAR:
   - Streamlit: http://localhost:8501
   - FastAPI Docs: http://localhost:8000/docs
   - n8n: http://localhost:5678
   - Redis: localhost:6379

5. CONFIGURAR N8N:
   a) Criar novo workflow
   b) Adicionar node "Webhook"
   c) URL: http://fastapi:8000/n8n/webhook/{workflow_name}
   d) Método: POST
   e) Adicionar nodes de processamento
   f) Ativar workflow

6. TESTAR INTEGRAÇÃO:
   - No Streamlit, vá para aba "n8n Workflows"
   - Clique em "Disparar Workflow"
   - Verifique logs no n8n

============================================================================
""")