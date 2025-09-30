import { format } from "date-fns";
import { ptBR } from "date-fns/locale";
import { User, Zap, Download, Share2, Database, Code, ChartBar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Visualization from "./Visualization";

interface VisualizationData {
  type: 'line' | 'bar' | 'pie' | 'boxplot' | 'scatter' | 'histogram' | 'timeseries';
  labels: string[] | number[];
  values: number[] | number[][];
  extra?: {
    title?: string;
    xLabel?: string;
    yLabel?: string;
    colors?: string[];
    quartis?: any;
    ranges?: any;
    legendas?: string[];
  };
}

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  visualization?: VisualizationData;
  tables?: any[];
  columns?: any[];
  sql_query?: string;
  data?: any;
}

interface ChatMessageProps {
  message: Message;
}

const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.type === 'user';
  
  // Função para exportar visualização como imagem (implementação futura)
  const handleDownloadChart = () => {
    console.log("Download do gráfico - implementar export para PNG");
    // Aqui você pode implementar a lógica de export usando html2canvas ou similar
  };
  
  // Função para compartilhar (implementação futura)
  const handleShareChart = () => {
    console.log("Compartilhar gráfico - implementar compartilhamento");
    // Aqui você pode implementar a lógica de compartilhamento
  };
  
  // Verifica se há conteúdo adicional além do texto
  const hasExtras = message.visualization || message.sql_query || message.tables || message.columns || message.data;

  return (
    <div className={`flex gap-3 message-enter ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-500 to-blue-600 shadow-md">
          <Zap className="h-5 w-5 text-white" />
        </div>
      )}
      
      <div className={`max-w-3xl ${isUser ? 'order-1' : ''}`}>
        <div className={`rounded-2xl px-5 py-4 shadow-md ${
          isUser 
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white ml-12' 
            : 'bg-white text-gray-800 mr-12 border border-gray-200'
        }`}>
          <div className="space-y-3">
            {/* Conteúdo da mensagem */}
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
            
            {/* Visualização do gráfico */}
            {message.visualization && (
              <div className="mt-4">
                <Visualization data={message.visualization} />
                
                {/* Botões de ação do gráfico */}
                <div className="flex gap-2 mt-3 justify-center">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleDownloadChart}
                    className="hover:bg-blue-50 border-blue-300 text-blue-700"
                  >
                    <Download className="h-3 w-3 mr-1" />
                    Baixar PNG
                  </Button>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={handleShareChart}
                    className="hover:bg-blue-50 border-blue-300 text-blue-700"
                  >
                    <Share2 className="h-3 w-3 mr-1" />
                    Compartilhar
                  </Button>
                </div>
              </div>
            )}
            
            {/* Abas para SQL, Tabelas, Colunas e Dados */}
            {(message.sql_query || message.tables || message.columns || message.data) && (
              <Card className="mt-4 bg-gray-50 border-gray-200">
                <Tabs 
                  defaultValue={
                    message.sql_query ? "sql" : 
                    message.tables ? "tables" : 
                    message.columns ? "columns" : 
                    "data"
                  } 
                  className="w-full"
                >
                  <TabsList className="grid w-full grid-cols-auto gap-1 p-1">
                    {message.sql_query && (
                      <TabsTrigger value="sql" className="flex items-center gap-1">
                        <Code className="h-3 w-3" />
                        SQL
                      </TabsTrigger>
                    )}
                    {message.tables && message.tables.length > 0 && (
                      <TabsTrigger value="tables" className="flex items-center gap-1">
                        <Database className="h-3 w-3" />
                        Tabelas
                      </TabsTrigger>
                    )}
                    {message.columns && message.columns.length > 0 && (
                      <TabsTrigger value="columns" className="flex items-center gap-1">
                        <ChartBar className="h-3 w-3" />
                        Colunas
                      </TabsTrigger>
                    )}
                    {message.data && (
                      <TabsTrigger value="data" className="flex items-center gap-1">
                        <Database className="h-3 w-3" />
                        Dados
                      </TabsTrigger>
                    )}
                  </TabsList>
                  
                  {/* SQL Query */}
                  {message.sql_query && (
                    <TabsContent value="sql" className="mt-2">
                      <div className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto">
                        <pre className="text-xs">
                          <code className="language-sql">{message.sql_query}</code>
                        </pre>
                      </div>
                    </TabsContent>
                  )}
                  
                  {/* Tabelas */}
                  {message.tables && message.tables.length > 0 && (
                    <TabsContent value="tables" className="mt-2">
                      <div className="bg-white p-3 rounded-lg border border-gray-200">
                        <div className="space-y-2">
                          {message.tables.map((table: any, index: number) => (
                            <div key={index} className="p-2 bg-gray-50 rounded border border-gray-200">
                              <pre className="text-xs overflow-x-auto">
                                {typeof table === 'string' ? table : JSON.stringify(table, null, 2)}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    </TabsContent>
                  )}
                  
                  {/* Colunas */}
                  {message.columns && message.columns.length > 0 && (
                    <TabsContent value="columns" className="mt-2">
                      <div className="bg-white p-3 rounded-lg border border-gray-200">
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {message.columns.map((col: any, index: number) => (
                            <div key={index} className="p-2 bg-blue-50 rounded text-xs font-mono">
                              {typeof col === 'string' ? col : col.name || JSON.stringify(col)}
                            </div>
                          ))}
                        </div>
                      </div>
                    </TabsContent>
                  )}
                  
                  {/* Dados em Tabela */}
                  {message.data && (
                    <TabsContent value="data" className="mt-2">
                      <div className="bg-white p-3 rounded-lg border border-gray-200 overflow-x-auto">
                        {Array.isArray(message.data) && message.data.length > 0 && typeof message.data[0] === 'object' ? (
                          <table className="min-w-full text-xs">
                            <thead className="bg-gray-100">
                              <tr>
                                {Object.keys(message.data[0]).map((col) => (
                                  <th key={col} className="px-3 py-2 text-left font-semibold text-gray-700 border-b">
                                    {col}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {message.data.slice(0, 10).map((row: any, idx: number) => (
                                <tr key={idx} className={idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                                  {Object.values(row).map((val: any, i: number) => (
                                    <td key={i} className="px-3 py-2 border-b text-gray-600">
                                      {val !== null && val !== undefined ? String(val) : '-'}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        ) : (
                          <pre className="text-xs text-gray-600 max-h-64 overflow-y-auto">
                            {JSON.stringify(message.data, null, 2)}
                          </pre>
                        )}
                        {Array.isArray(message.data) && message.data.length > 10 && (
                          <div className="text-xs text-gray-500 mt-2 text-center">
                            Exibindo 10 de {message.data.length} registros
                          </div>
                        )}
                      </div>
                    </TabsContent>
                  )}
                </Tabs>
              </Card>
            )}
          </div>
        </div>
        
        {/* Timestamp */}
        <div className={`mt-1 text-xs text-gray-500 ${isUser ? 'text-right mr-12' : 'text-left ml-12'}`}>
          {format(message.timestamp, 'HH:mm', { locale: ptBR })}
        </div>
      </div>
      
      {isUser && (
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-gray-200 to-gray-300 shadow-md">
          <User className="h-5 w-5 text-gray-600" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;