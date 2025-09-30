import React, { useState, useRef, useEffect } from "react";
import logo from "../../assets/logo.jpg";
import { Send, Sparkles, TrendingUp, BarChart3, Zap, Database, Cloud, Activity } from "lucide-react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, BarChart, Bar, PieChart, Pie, Cell, Legend } from "recharts";

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      type: 'assistant',
      content: 'Olá! Eu sou o assistente do ONSights. Posso ajudá-lo a consultar dados da ONS sobre geração de energia, restrições operacionais e informações meteorológicas. Como posso ajudar você hoje?',
      timestamp: new Date(),
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Adiciona a fonte Inter do Google Fonts
  useEffect(() => {
    const link = document.createElement('link');
    link.href = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap';
    link.rel = 'stylesheet';
    document.head.appendChild(link);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const suggestedQuestions = [
    { icon: <TrendingUp className="w-4 h-4" />, text: "Qual foi a geração de energia solar hoje?" },
    { icon: <BarChart3 className="w-4 h-4" />, text: "Compare a geração eólica dos últimos 7 dias" },
    { icon: <Zap className="w-4 h-4" />, text: "Mostre as restrições operacionais atuais" },
    { icon: <Database className="w-4 h-4" />, text: "Análise da demanda de energia por região" },
    { icon: <Cloud className="w-4 h-4" />, text: "Previsão meteorológica para geração renovável" },
    { icon: <Activity className="w-4 h-4" />, text: "Status dos reservatórios hidrelétricos" }
  ];

  const teamMembers = [
    "Anna",
    "Daniel",
    "Sandra",
    "Nicolas",
  
  ];

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/n8n/webhook/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chatInput: userMessage.content })
      });
      const data = await response.json();
      let formatted = '';
      if (typeof data === 'string') {
        formatted = data;
      } else if (data.answer) {
        formatted = data.answer;
      } else if (data.text) {
        formatted = data.text;
      } else {
        formatted = JSON.stringify(data, null, 2);
      }
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: formatted,
        visualization: data.visualization || null,
        timestamp: new Date()
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: 'Erro ao consultar o backend.',
        timestamp: new Date()
      }]);
    }
    setIsLoading(false);
  };

  const handleQuestionClick = (question) => {
    setInput(question);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex h-screen bg-[#1C1C1C] text-[#F5F5F5]" style={{ fontFamily: 'Inter, sans-serif' }}>
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Chat Messages Area */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6">
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] px-5 py-3 rounded-2xl shadow-lg ${
                    message.type === 'user'
                      ? 'bg-gradient-to-r from-gray-700 to-gray-600 text-white'
                      : 'bg-gradient-to-r from-[#FFA500]/20 to-[#FFB300]/20 border border-[#FFA500]/30 text-[#F5F5F5]'
                  }`}
                  style={{ borderRadius: '16px' }}
                >
                  <p className="text-sm leading-relaxed">{message.content}</p>
                  <p className="text-xs mt-2 opacity-60">
                    {message.timestamp.toLocaleTimeString('pt-BR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </p>
                  {/* Renderiza gráfico se houver visualização */}
                  {message.visualization && Array.isArray(message.visualization.labels) && Array.isArray(message.visualization.values) && message.visualization.labels.length > 0 && message.visualization.values.length > 0 && (
                    <div className="mt-4 bg-gray-900 rounded-xl p-4">
                      {message.visualization.type === 'line' && (
                        <ResponsiveContainer width="100%" height={240}>
                          <LineChart
                            data={message.visualization.labels.map((label, i) => ({
                              hora: label,
                              valor: message.visualization.values[i]
                            }))}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="hora" tick={{ fill: '#FFA500', fontSize: 12 }} angle={-45} textAnchor="end" height={60} />
                            <YAxis tick={{ fill: '#FFA500', fontSize: 12 }} />
                            <Tooltip />
                            <Line type="monotone" dataKey="valor" stroke="#FFA500" strokeWidth={3} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      )}
                      {message.visualization.type === 'bar' && (
                        <ResponsiveContainer width="100%" height={240}>
                          <BarChart
                            data={message.visualization.labels.map((label, i) => ({
                              categoria: label,
                              valor: message.visualization.values[i]
                            }))}
                          >
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="categoria" tick={{ fill: '#FFA500', fontSize: 12 }} angle={-45} textAnchor="end" height={60} />
                            <YAxis tick={{ fill: '#FFA500', fontSize: 12 }} />
                            <Tooltip />
                            <Bar dataKey="valor" fill="#FFA500" />
                          </BarChart>
                        </ResponsiveContainer>
                      )}
                      {message.visualization.type === 'pie' && (
                        <ResponsiveContainer width="100%" height={240}>
                          <PieChart>
                            <Pie
                              data={message.visualization.labels.map((label, i) => ({
                                categoria: label,
                                valor: message.visualization.values[i]
                              }))}
                              dataKey="valor"
                              nameKey="categoria"
                              cx="50%"
                              cy="50%"
                              outerRadius={80}
                              label
                            >
                              {(message.visualization.labels || []).map((_, i) => (
                                <Cell key={`cell-${i}`} fill={message.visualization.extra?.colors?.[i] || ["#FFA500", "#FFB300", "#FFC107"][i % 3]} />
                              ))}
                            </Pie>
                            <Tooltip />
                            <Legend />
                          </PieChart>
                        </ResponsiveContainer>
                      )}
                      <div className="text-xs text-gray-400 mt-2 text-center">
                        {message.visualization.extra?.title || "Gráfico de dados"}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-gradient-to-r from-[#FFA500]/20 to-[#FFB300]/20 border border-[#FFA500]/30 px-5 py-3 rounded-2xl">
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-[#FFA500] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-[#FFB300] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-[#FFC107] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-t border-gray-800 bg-[#1C1C1C]/95 backdrop-blur-sm p-4 md:p-6">
          <div className="max-w-3xl mx-auto">
            <div className="flex gap-3">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Digite sua pergunta sobre dados de energia..."
                className="flex-1 bg-gray-800/50 border border-gray-700 rounded-2xl px-4 py-3 text-[#F5F5F5] placeholder-gray-500 focus:outline-none focus:border-[#FFA500] focus:ring-2 focus:ring-[#FFA500]/20 resize-none"
                rows={2}
                disabled={isLoading}
                style={{ borderRadius: '16px' }}
              />
              <button
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
                className="px-6 py-3 bg-gradient-to-r from-[#FFA500] to-[#FFC107] hover:from-[#FFB300] hover:to-[#FFA500] text-white font-semibold rounded-2xl transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg hover:shadow-xl hover:scale-105"
                style={{ borderRadius: '16px' }}
              >
                {isLoading ? (
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Pressione Enter para enviar • Shift+Enter para nova linha
            </p>
          </div>
        </div>
      </div>

      {/* Right Sidebar */}
      <div className="w-80 bg-gradient-to-b from-gray-900 to-[#121212] border-l border-gray-800 p-6 overflow-y-auto hidden lg:block">
        {/* Logo Section */}
        <div className="mb-8 text-center">
          <div className="bg-gradient-to-r from-[#FFA500] to-[#FFC107] p-1 rounded-2xl mb-4">
            <div className="bg-gray-900 rounded-2xl p-6 flex flex-col items-center justify-center">
              <img src={logo} alt="Logo ONSights" className="w-32 h-32 rounded-full border-2 border-[#FFA500] shadow-lg object-cover" />
            </div>
          </div>
        </div>

        {/* Challenge Description */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-[#FFA500]" />
            <h2 className="text-lg font-semibold text-[#F5F5F5]">Desafio Datathons 2025</h2>
          </div>
          <p className="text-sm text-gray-400 leading-relaxed">
            Análise inteligente de dados do setor elétrico brasileiro, fornecendo insights em tempo real sobre geração, demanda e operações do Sistema Interligado Nacional.
          </p>
        </div>

        {/* Team Section */}
        <div className="mb-8">
          <h3 className="text-lg font-semibold text-[#F5F5F5] mb-3">Equipe 12 - Integrantes</h3>
          <div className="space-y-2">
            {teamMembers.map((member, index) => (
              <div key={index} className="flex items-center gap-2 text-sm text-gray-400 hover:text-[#FFA500] transition-colors">
                <div className="w-2 h-2 bg-gradient-to-r from-[#FFA500] to-[#FFC107] rounded-full"></div>
                {member}
              </div>
            ))}
          </div>
        </div>

        {/* Suggested Questions */}
        <div>
          <h3 className="text-lg font-semibold text-[#F5F5F5] mb-4">Perguntas Sugeridas</h3>
          <div className="space-y-2">
            {suggestedQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleQuestionClick(question.text)}
                className="w-full text-left p-3 bg-gray-800/30 hover:bg-gradient-to-r hover:from-[#FFA500]/10 hover:to-[#FFB300]/10 border border-gray-700 hover:border-[#FFA500]/30 rounded-xl transition-all duration-300 group"
                style={{ borderRadius: '12px' }}
              >
                <div className="flex items-start gap-3">
                  <div className="text-[#FFA500] group-hover:text-[#FFC107] transition-colors mt-0.5">
                    {question.icon}
                  </div>
                  <p className="text-sm text-gray-400 group-hover:text-[#F5F5F5] transition-colors">
                    {question.text}
                  </p>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-6 border-t border-gray-800">
          <p className="text-xs text-gray-500 text-center">
            © 2025 ONSights • v1.0.0
          </p>
        </div>
      </div>

      {/* Mobile Sidebar Toggle - Optional */}
      <button className="lg:hidden fixed bottom-20 right-4 p-3 bg-gradient-to-r from-[#FFA500] to-[#FFC107] text-white rounded-full shadow-lg z-50">
        <Sparkles className="w-6 h-6" />
      </button>
    </div>
  );
};

export default ChatInterface;