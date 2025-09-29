import { Wind, Sun, Zap, BarChart3, Battery, TrendingUp, MapPin, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface QuickActionsProps {
  onQuickAction: (question: string) => void;
}

interface QuickQuestion {
  icon: any;
  text: string;
  question: string;
  category: string;
  color: string;
}

const quickQuestions: QuickQuestion[] = [
  // Geração
  {
    icon: Wind,
    text: "Geração eólica agosto 2025",
    question: "Qual foi a geração eólica total no mês de agosto de 2025?",
    category: "Geração",
    color: "bg-blue-500/10 text-blue-600 border-blue-200"
  },
  {
    icon: Sun,
    text: "Fator capacidade solar",
    question: "Qual o fator de capacidade médio das usinas solares no último trimestre?",
    category: "Geração",
    color: "bg-blue-500/10 text-blue-600 border-blue-200"
  },
  
  // Capacidade
  {
    icon: Battery,
    text: "Capacidade instalada",
    question: "Qual a capacidade instalada total de energia renovável no Brasil?",
    category: "Capacidade",
    color: "bg-green-500/10 text-green-600 border-green-200"
  },
  {
    icon: TrendingUp,
    text: "Crescimento capacidade",
    question: "Qual foi o crescimento da capacidade renovável nos últimos 12 meses?",
    category: "Capacidade",
    color: "bg-green-500/10 text-green-600 border-green-200"
  },
  
  // Restrições
  {
    icon: Zap,
    text: "Restrições operacionais",
    question: "Quantos dias as usinas eólicas foram restringidas por constrained-off em setembro?",
    category: "Restrições",
    color: "bg-amber-500/10 text-amber-600 border-amber-200"
  },
  {
    icon: Clock,
    text: "Histórico restrições",
    question: "Qual usina teve mais restrições operacionais no último ano?",
    category: "Restrições",
    color: "bg-amber-500/10 text-amber-600 border-amber-200"
  },
  
  // Rankings
  {
    icon: BarChart3,
    text: "Ranking usinas",
    question: "Quais são as 10 usinas com maior geração de energia renovável?",
    category: "Rankings",
    color: "bg-purple-500/10 text-purple-600 border-purple-200"
  },
  {
    icon: MapPin,
    text: "Ranking por região",
    question: "Qual região do Brasil tem maior geração de energia eólica?",
    category: "Rankings",
    color: "bg-purple-500/10 text-purple-600 border-purple-200"
  }
];

// Agrupar perguntas por categoria
const groupedQuestions = quickQuestions.reduce((acc, question) => {
  if (!acc[question.category]) {
    acc[question.category] = [];
  }
  acc[question.category].push(question);
  return acc;
}, {} as Record<string, QuickQuestion[]>);

const QuickActions = ({ onQuickAction }: QuickActionsProps) => {
  return (
    <div className="border-t bg-muted/30 px-6 py-4">
      <div className="mx-auto max-w-4xl">
        <h3 className="mb-4 text-sm font-medium text-muted-foreground">
          Perguntas Sugeridas por Categoria
        </h3>
        
        <div className="space-y-4">
          {Object.entries(groupedQuestions).map(([category, questions]) => (
            <div key={category} className="space-y-2">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-xs">
                  {category}
                </Badge>
              </div>
              
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {questions.map((item, index) => (
                  <Card
                    key={`${category}-${index}`}
                    className="group cursor-pointer transition-all duration-fast hover:shadow-md hover:bg-card-hover hover:border-primary/20"
                    onClick={() => onQuickAction(item.question)}
                  >
                    <div className="p-3">
                      <div className="flex items-start gap-3">
                        <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${item.color} group-hover:scale-105 transition-transform`}>
                          <item.icon className="h-4 w-4" />
                        </div>
                        
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium leading-tight group-hover:text-primary transition-colors">
                            {item.text}
                          </p>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-4 text-center">
          <Button variant="ghost" size="sm" className="text-xs text-muted-foreground">
            Ver mais perguntas sugeridas
          </Button>
        </div>
      </div>
    </div>
  );
};

export default QuickActions;