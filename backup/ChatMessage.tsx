import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { User, Zap, Download, Share2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  chartUrl?: string;
  data?: any;
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.type === 'user';

  return (
    <div className={`flex gap-3 message-enter ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-primary shadow-md">
          <Zap className="h-5 w-5 text-primary-foreground" />
        </div>
      )}
      <div className={`max-w-2xl ${isUser ? 'order-1' : ''}`}>
        <div className={`rounded-2xl px-4 py-3 shadow-sm ${
          isUser 
            ? 'bg-chat-user text-chat-user-foreground ml-12' 
            : 'bg-chat-assistant text-chat-assistant-foreground mr-12'
        }`}>
          <div className="space-y-3">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
            {/* Chart Display */}
            {message.chartUrl && (
              <Card className="p-4 bg-card border-2 border-primary/10">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 pb-2 border-b">
                    <div className="h-2 w-2 bg-primary rounded-full"></div>
                    <h4 className="text-sm font-medium text-primary">Gráfico Gerado</h4>
                  </div>
                  <div className="rounded-lg overflow-hidden">
                    <img 
                      src={message.chartUrl} 
                      alt="Gráfico gerado" 
                      className="w-full h-auto"
                    />
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button variant="outline" size="sm" className="hover:bg-primary/5">
                      <Download className="h-3 w-3 mr-1" />
                      Baixar PNG
                    </Button>
                    <Button variant="outline" size="sm" className="hover:bg-primary/5">
                      <Share2 className="h-3 w-3 mr-1" />
                      Compartilhar
                    </Button>
                  </div>
                </div>
              </Card>
            )}
            {/* Data Table - renderiza como tabela se for array de objetos */}
            {message.data && (
              <Card className="p-4 bg-muted/30 border border-muted">
                <div className="flex items-center gap-2 pb-2 mb-2 border-b border-muted">
                  <div className="h-2 w-2 bg-secondary rounded-full"></div>
                  <h4 className="text-sm font-medium text-secondary">Dados Consultados</h4>
                </div>
                <div className="overflow-x-auto">
                  {Array.isArray(message.data) && message.data.length > 0 && typeof message.data[0] === 'object' ? (
                    <table className="min-w-full text-xs">
                      <thead>
                        <tr>
                          {Object.keys(message.data[0]).map((col) => (
                            <th key={col} className="px-2 py-1 border-b">{col}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {message.data.map((row: any, idx: number) => (
                          <tr key={idx}>
                            {Object.values(row).map((val, i) => (
                              <td key={i} className="px-2 py-1 border-b">{String(val)}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <pre className="text-xs text-muted-foreground">
                      {JSON.stringify(message.data, null, 2)}
                    </pre>
                  )}
                </div>
              </Card>
            )}
          </div>
        </div>
        <div className={`mt-1 text-xs text-muted-foreground ${isUser ? 'text-right' : 'text-left'}`}>
          {format(message.timestamp, 'HH:mm', { locale: ptBR })}
        </div>
      </div>
      {isUser && (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-muted to-muted/70 shadow-md">
          <User className="h-5 w-5 text-muted-foreground" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;