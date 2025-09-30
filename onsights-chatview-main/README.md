## ONSights - Documentação Didática do Projeto

Bem-vindo à documentação do ONSights! Aqui você encontra um guia passo a passo de como foi construída a solução, desde a arquitetura até a integração dos componentes.

---

### 1. Visão Geral

ONSights é uma plataforma inteligente para consulta e análise de dados do setor elétrico, integrando backend (FastAPI, n8n, Redis) e frontend (React/Vite, Streamlit) em uma interface conversacional moderna.

---

### 2. Arquitetura da Solução

**Componentes principais:**

- **Frontend React/Vite:** Interface de chat, visual, responsiva, com sugestões inteligentes e integração visual da marca.
- **Backend FastAPI:** API que recebe requisições do chat, processa dados, integra com n8n e Redis.
- **n8n:** Orquestrador de workflows, recebe payloads do backend e executa automações.
- **Redis:** Cache e compartilhamento de dados entre backend e frontend.
- **Streamlit:** Dashboards e visualização de dados (opcional).

**Fluxo resumido:**
Usuário interage no chat → Frontend envia requisição → Backend processa e consulta n8n/Redis → Resposta exibida no chat.

---

### 3. Passo a Passo de Implementação

#### 3.1. Frontend (React/Vite)

1. **Criação do projeto:**
  - Utilizamos Vite para scaffolding rápido: `npm create vite@latest onsights-chatview-main -- --template react-ts`
2. **Configuração do Tailwind CSS:**
  - Instalado via `npm install -D tailwindcss postcss autoprefixer`
  - Configurado em `tailwind.config.ts` e `postcss.config.js`.
3. **Componentização:**
  - Criados componentes em `src/components/chat/ChatInterface.tsx` para o chat, sugestões, input, logo, etc.
4. **Tema visual:**
  - Aplicado tema escuro, paleta laranja/amarelo, cantos arredondados, sombra suave.
  - Logo integrada via `src/assets/logo.jpg`.
5. **Sugestões inteligentes:**
  - Array de perguntas sugeridas, renderizadas como botões para facilitar interação.
6. **Scroll e UX:**
  - Scroll automático para última mensagem, input otimizado, loading animado.
7. **Integração com backend:**
  - Requisições simuladas via `fetch` ou `axios` para endpoints FastAPI.

#### 3.2. Backend (FastAPI)

1. **Criação do projeto:**
  - Arquivo principal: `backend_api.py`.
  - Instalação: `pip install fastapi uvicorn redis pandas numpy httpx websockets`
2. **Modelagem dos dados:**
  - Utilização de Pydantic para validação dos modelos (EnergyData, N8nTrigger, WebhookPayload).
3. **Configuração do Redis:**
  - Conexão e fallback para memória local se Redis indisponível.
4. **Endpoints principais:**
  - `/n8n/webhook/{workflow_name}`: Recebe payloads do frontend/chat e encaminha para n8n.
  - `/docs`: Documentação automática via Swagger.
5. **Integração n8n:**
  - Envio de payloads para URLs de webhook do n8n (test/prod).
  - Recebimento e tratamento de respostas JSON.
6. **Tratamento de erros:**
  - Validação de campos obrigatórios, logging detalhado, respostas padronizadas.

#### 3.3. n8n (Orquestrador)

1. **Configuração do workflow:**
  - Criado workflow com node Webhook para receber dados do backend.
  - URL configurada: `http://localhost:8000/n8n/webhook/{workflow_name}`
2. **Processamento dos dados:**
  - Nodes para análise, enriquecimento, automação e resposta.
3. **Retorno ao backend:**
  - Resposta JSON enviada de volta ao FastAPI, que repassa ao frontend.

#### 3.4. Redis

1. **Execução via Docker:**
  - `docker run -p 6379:6379 redis:7-alpine`
2. **Uso no backend:**
  - Cache de dados, compartilhamento entre APIs, persistência temporária.

#### 3.5. Streamlit (Opcional)

1. **Dashboards interativos:**
  - Visualização de dados, gráficos, análises complementares.
2. **Execução:**
  - `streamlit run streamlit_app.py`

---

### 4. Instalação e Execução

**Pré-requisitos:** Node.js, Python 3.10+, Docker, Redis

**Backend:**
```sh
pip install -r requirements.txt
uvicorn backend_api:app --reload --port 8000
```

**Frontend:**
```sh
cd onsights-chatview-main
npm install
npm run dev
```

**Redis:**
```sh
docker run -p 6379:6379 redis:7-alpine
```

**n8n:**
```sh
docker run -p 5678:5678 n8nio/n8n
```

**Streamlit:**
```sh
streamlit run streamlit_app.py
```

---

### 5. Fluxo de Dados

1. Usuário envia mensagem no chat (frontend)
2. Frontend faz requisição para FastAPI
3. FastAPI processa, consulta Redis/n8n
4. n8n executa workflow e retorna dados
5. FastAPI responde ao frontend
6. Mensagem e dados exibidos no chat

---

### 6. Dicas para Desenvolvedores

- Use o Swagger (`/docs`) para testar endpoints do backend
- Customize o tema do chat em `ChatInterface.tsx`
- Adicione novos workflows no n8n para expandir funcionalidades
- Use Redis para cache de dados pesados
- Consulte os arquivos Dockerfile para deploy automatizado

---

### 7. Contato e Suporte

- Para dúvidas técnicas, abra uma issue ou envie e-mail para o mantenedor
- Documentação adicional nos arquivos de cada subdiretório

---
# ONSights - Plataforma Inteligente de Dados do Setor Elétrico

## Sumário

- [ONSights - Plataforma Inteligente de Dados do Setor Elétrico](#onsights---plataforma-inteligente-de-dados-do-setor-elétrico)
  - [Sumário](#sumário)
  - [Visão Geral](#visão-geral)
  - [Estrutura do Projeto](#estrutura-do-projeto)
  - [Frontend (React/Vite)](#frontend-reactvite)
  - [Backend (FastAPI, n8n, Redis, Streamlit)](#backend-fastapi-n8n-redis-streamlit)
  - [Instalação e Execução](#instalação-e-execução)
    - [1. Pré-requisitos](#1-pré-requisitos)
    - [2. Instalação Local](#2-instalação-local)
    - [3. Execução via Docker](#3-execução-via-docker)
  - [Integração com n8n](#integração-com-n8n)
  - [Scripts e Dependências](#scripts-e-dependências)
  - [Contato e Suporte](#contato-e-suporte)

---

## Visão Geral

ONSights é uma plataforma para consulta, análise e visualização de dados do setor elétrico brasileiro, integrando múltiplas fontes (ONS, n8n, dados manuais) e oferecendo uma interface conversacional inteligente.

---

## Estrutura do Projeto

```
├── onsights-chatview-main/      # Frontend React/Vite
│   ├── src/
│   │   ├── components/
│   │   ├── assets/
│   │   ├── pages/
│   │   └── ...
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── backend_api.py               # FastAPI principal
├── backend_n8n.py               # FastAPI para integração n8n
├── backend_n8n_new.py           # Versão alternativa n8n
├── analisar.py                  # Scripts de análise
├── requirements.txt             # Dependências Python
├── Dockerfile.api               # Docker backend
├── Dockerfile.streamlit         # Docker frontend Streamlit
└── ...
```

---

## Frontend (React/Vite)

- **Tecnologias:** React, Vite, TypeScript, Tailwind CSS, shadcn-ui, Lucide Icons
- **Principais arquivos:** `onsights-chatview-main/src/components/chat/ChatInterface.tsx`
- **Funcionalidades:**
  - Chat inteligente com sugestões de perguntas
  - Integração visual com a marca ONSights (tema escuro, logo, paleta laranja/amarelo)
  - Layout responsivo e moderno
- **Scripts principais:**
  - `npm run dev` - inicia servidor de desenvolvimento
  - `npm run build` - gera build de produção

---

## Backend (FastAPI, n8n, Redis, Streamlit)

- **FastAPI:** API principal (`backend_api.py`) e integração n8n (`backend_n8n.py`)
- **Redis:** Cache e compartilhamento de dados entre backend e frontend
- **n8n:** Orquestração de workflows, integração via webhooks
- **Streamlit:** Visualização de dados e dashboards interativos
- **Principais endpoints:**
  - `/n8n/webhook/{workflow_name}` - recebe e encaminha payloads para n8n
  - `/docs` - documentação automática da API

---

## Instalação e Execução

### 1. Pré-requisitos

- Node.js (para frontend)
- Python 3.10+ (para backend)
- Docker (opcional, recomendado)
- Redis (pode ser via Docker)

### 2. Instalação Local

**Backend:**
```sh
pip install -r requirements.txt
uvicorn backend_api:app --reload --port 8000
```

**Frontend:**
```sh
cd onsights-chatview-main
npm install
npm run dev
```

**Streamlit:**
```sh
streamlit run streamlit_app.py
```

**Redis:**
```sh
docker run -p 6379:6379 redis:7-alpine
```

### 3. Execução via Docker

```sh
docker-compose up
```
- `Dockerfile.api` para backend
- `Dockerfile.streamlit` para frontend Streamlit
- `onsights-chatview-main/Dockerfile` para React/Vite

---

## Integração com n8n

- Configure workflow no n8n com node Webhook
- Use endpoint: `http://localhost:8000/n8n/webhook/{workflow_name}`
- Payloads do chat são encaminhados para n8n, que pode processar, enriquecer e retornar dados

---

## Scripts e Dependências

- **Frontend:** Veja `package.json` para dependências React, Tailwind, Radix UI, etc.
- **Backend:** Veja `requirements.txt` para FastAPI, Redis, Pandas, etc.

---

## Contato e Suporte

- Para dúvidas técnicas, abra uma issue ou envie e-mail para o mantenedor do projeto.
- Documentação adicional pode ser encontrada nos arquivos `README.md` de cada subdiretório.

---
