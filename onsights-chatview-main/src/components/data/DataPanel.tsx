import { Download, FileText, BarChart3, Database, TrendingUp, Eye, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";

const datasets = [
  {
    id: 1,
    name: "Geração por Usina",
    description: "Dados históricos de geração",
    size: "2.4 MB",
    records: "125k registros",
    lastUpdate: "Hoje",
    type: "CSV",
    category: "Geração",
    trend: "+12%",
    color: "bg-blue-500/10 text-blue-600 border-blue-200"
  },
  {
    id: 2,
    name: "Capacidade Instalada",
    description: "Capacidade por fonte",
    size: "1.8 MB", 
    records: "89k registros",
    lastUpdate: "Ontem",
    type: "CSV",
    category: "Capacidade",
    trend: "+8%",
    color: "bg-green-500/10 text-green-600 border-green-200"
  },
  {
    id: 3,
    name: "Restrições Operacionais",
    description: "Constrained-off e restrições",
    size: "950 KB",
    records: "45k registros", 
    lastUpdate: "2 dias",
    type: "CSV",
    category: "Operação",
    trend: "-3%",
    color: "bg-amber-500/10 text-amber-600 border-amber-200"
  }
];

const recentCharts = [
  {
    id: 1,
    title: "Geração Eólica - Agosto",
    type: "line",
    createdAt: "Há 2 horas",
    thumbnail: "📈"
  },
  {
    id: 2, 
    title: "Ranking Usinas",
    type: "bar",
    createdAt: "Há 1 dia",
    thumbnail: "📊"
  },
  {
    id: 3,
    title: "Capacidade por Região",
    type: "pie", 
    createdAt: "Há 2 dias",
    thumbnail: "🥧"
  }
];

const DataPanel = () => {
  return (
    <div className="h-full border-l bg-card/30 p-4 overflow-y-auto">
      <div className="space-y-6">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Buscar datasets..."
            className="pl-10 h-9 bg-background/50"
          />
        </div>

        {/* Datasets Section */}
        <div>
          <div className="mb-4 flex items-center gap-2">
            <Database className="h-4 w-4 text-primary" />
            <h2 className="text-sm font-semibold">Datasets Disponíveis</h2>
            <Badge variant="outline" className="ml-auto text-xs">
              {datasets.length}
            </Badge>
          </div>
          
          <div className="space-y-3">
            {datasets.map((dataset) => (
              <Card key={dataset.id} className="group p-4 hover:bg-card-hover hover:shadow-md transition-all cursor-pointer border-l-4 border-l-transparent hover:border-l-primary">
                <div className="space-y-3">
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium group-hover:text-primary transition-colors">
                        {dataset.name}
                      </h3>
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {dataset.description}
                      </p>
                    </div>
                    <div className="flex flex-col items-end gap-1">
                      <Badge className={dataset.color}>
                        {dataset.type}
                      </Badge>
                      <div className="flex items-center gap-1 text-xs">
                        <TrendingUp className="h-3 w-3 text-green-500" />
                        <span className="text-green-500 font-medium">{dataset.trend}</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span className="font-medium">{dataset.size}</span>
                    <span>{dataset.records}</span>
                    <span>{dataset.lastUpdate}</span>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="h-7 px-3 text-xs hover:bg-primary/5">
                      <Eye className="h-3 w-3 mr-1" />
                      Prévia
                    </Button>
                    <Button variant="outline" size="sm" className="h-7 px-3 text-xs hover:bg-secondary/5">
                      <Download className="h-3 w-3 mr-1" />
                      Baixar
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </div>

        <Separator />

        {/* Recent Charts Section */}
        <div>
          <div className="mb-4 flex items-center gap-2">
            <BarChart3 className="h-4 w-4 text-secondary" />
            <h2 className="text-sm font-semibold">Gráficos Recentes</h2>
            <Badge variant="outline" className="ml-auto text-xs">
              {recentCharts.length}
            </Badge>
          </div>
          
          <div className="space-y-3">
            {recentCharts.map((chart) => (
              <Card key={chart.id} className="group p-4 hover:bg-card-hover hover:shadow-md transition-all cursor-pointer">
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-secondary/20 to-secondary/10 text-lg">
                    {chart.thumbnail}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium group-hover:text-secondary transition-colors">
                      {chart.title}
                    </h3>
                    <div className="flex items-center gap-2 text-xs text-muted-foreground">
                      <Badge variant="secondary" className="text-xs px-2 py-0">
                        {chart.type}
                      </Badge>
                      <span>•</span>
                      <span>{chart.createdAt}</span>
                    </div>
                  </div>
                  
                  <Button variant="ghost" size="sm" className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <Eye className="h-3 w-3" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
          
          <Button 
            variant="outline" 
            size="sm" 
            className="w-full mt-3 text-xs hover:bg-secondary/5"
          >
            Ver todos os gráficos
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DataPanel;