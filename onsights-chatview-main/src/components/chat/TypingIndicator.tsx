import { Zap } from "lucide-react";

const TypingIndicator = () => {
  return (
    <div className="flex gap-3 justify-start message-enter">
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-primary">
        <Zap className="h-4 w-4 text-primary-foreground" />
      </div>
      
      <div className="max-w-2xl">
        <div className="bg-chat-assistant text-chat-assistant-foreground rounded-2xl px-4 py-3 shadow-sm">
          <div className="flex items-center gap-1">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-muted-foreground rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
            <span className="text-xs text-muted-foreground ml-2">Analisando sua pergunta...</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;