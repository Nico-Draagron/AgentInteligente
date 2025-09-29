import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Dialog, DialogContent } from "@/components/ui/dialog";
import ChatMessage from "./ChatMessage";
import QuickActions from "./QuickActions";
import TypingIndicator from "./TypingIndicator";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  chartUrl?: string;
  data?: any;
}

const ChatInterface = () => {
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Olá! Eu sou o assistente do ONSights. Posso ajudá-lo a consultar dados da ONS sobre geração de energia, restrições operacionais e informações meteorológicas. O que você gostaria de saber?',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);


  // URLs do backend FastAPI
  const BACKEND_URL = "http://localhost:8000/n8n/webhook/DatathONS_Prototipo";
  const SUB_BACKEND_URL = "http://localhost:8000/n8n/webhook/SubWorkflow_SelecionarTabela";

  // Função para retornar sempre o sessionId fixo 'sessao-3'
  function getSessionId() {
    return "sessao-3";
  }

  // Função para enviar mensagem ao backend FastAPI
  async function sendToMainWorkflow(message: string) {
    const sessionId = getSessionId();
    console.log("Enviando para backend:", message, "sessionId:", sessionId);
    const response = await fetch(BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ chatInput: message, sessionId }),
    });
    return response.json();
  }

  // Função para processar resposta do workflow principal
  async function handleMainResponse(response: any) {
    console.log("Resposta do workflow principal:", response);
    if (response.tables || response.columns) {
      // Resposta do subworkflow: renderizar tabela/colunas
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          type: "assistant",
          content: "Aqui estão as tabelas/colunas encontradas:",
          timestamp: new Date(),
          data: response.tables || response.columns,
        },
      ]);
    } else if (response.text) {
      // Resposta do agente principal: texto/instrução/SQL
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          type: "assistant",
          content: response.text,
          timestamp: new Date(),
        },
      ]);
      // Se o agente indicar que precisa selecionar tabela, chame o subworkflow
      if (response.needTableSelection) {
        await callSubWorkflow();
      }
    } else {
      // Resposta genérica
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now().toString(),
          type: "assistant",
          content: "Resposta não reconhecida.",
          timestamp: new Date(),
        },
      ]);
    }
  }

  // Função para chamar o subworkflow via backend FastAPI
  async function callSubWorkflow() {
    console.log("Chamando subworkflow via backend...");
    const response = await fetch(SUB_BACKEND_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ acao: "selecionar_tabela" }),
    });
    const data = await response.json();
    console.log("Resposta do subworkflow:", data);
    // Renderize como tabela/colunas
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        type: "assistant",
        content: "Resultado do subworkflow:",
        timestamp: new Date(),
        data: data.tables || data.columns || data,
      },
    ]);
  }

  // Função principal de envio do chat
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    setIsLoading(true);
    setMessages(prev => [...prev, { id: Date.now().toString(), type: "user", content: input, timestamp: new Date() }]);
    setInput("");
    try {
      const mainResponse = await sendToMainWorkflow(input);
      await handleMainResponse(mainResponse);
    } catch (err) {
      console.error("Erro ao enviar mensagem:", err);
      setMessages(prev => [...prev, {
        id: (Date.now() + 2).toString(),
        type: "assistant",
        content: "Erro ao consultar o n8n Cloud. Tente novamente.",
        timestamp: new Date(),
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickAction = (question: string) => {
    setInput(question);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
  <div className="flex h-[calc(100vh-32px)] flex-col">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        <div className="mx-auto max-w-4xl space-y-6">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          {isLoading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Botão flutuante para perguntas sugeridas */}
      <div className="fixed bottom-8 right-8 z-50">
        <Button variant="energy-outline" size="lg" onClick={() => setShowQuickActions(true)}>
          Perguntas Sugeridas
        </Button>
      </div>

      {/* Modal de perguntas sugeridas */}
      <Dialog open={showQuickActions} onOpenChange={setShowQuickActions}>
        <DialogContent className="max-w-lg bg-blue-600">
          <QuickActions onQuickAction={(q) => { setInput(q); setShowQuickActions(false); }} />
        </DialogContent>
      </Dialog>

      {/* Input Area */}
      <div className="border-t bg-card/50 p-4">
        <div className="mx-auto max-w-4xl">
          <Card className="p-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <Textarea
                  placeholder="Faça uma pergunta sobre os dados da ONS..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="min-h-[60px] resize-none border-0 p-3 focus-visible:ring-0"
                />
              </div>
              <Button
                variant="energy"
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                size="lg"
                className="h-auto px-8"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Pressione Enter para enviar, Shift+Enter para nova linha
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;