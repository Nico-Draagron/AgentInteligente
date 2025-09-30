import React from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie,
  ScatterChart, Scatter, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, LabelList
} from 'recharts';
import { Card } from '@/components/ui/card';

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

interface VisualizationProps {
  data: VisualizationData;
}

const COLORS = [
  '#FFA500', // laranja principal
  '#FFB300', // laranja claro
  '#FFC107', // amarelo
  '#FFD54F', // amarelo claro extra
  '#FF9800', // laranja escuro
  '#FFECB3', // amarelo pastel
  '#FFF8E1', // amarelo muito claro
  '#FFB74D', // laranja pastel
];

const Visualization: React.FC<VisualizationProps> = ({ data }) => {
  if (!data) return null;

  // Prepara dados para Recharts (formato: [{name: label, value: value}])
  const prepareChartData = () => {
    if (!data.labels || !data.values) return [];
    
    // Se values for um array de arrays (múltiplas séries)
    if (Array.isArray(data.values[0])) {
      return data.labels.map((label, index) => {
        const dataPoint: any = { name: label };
        (data.values as number[][]).forEach((series, seriesIndex) => {
          const seriesName = data.extra?.legendas?.[seriesIndex] || `Série ${seriesIndex + 1}`;
          dataPoint[seriesName] = series[index];
        });
        return dataPoint;
      });
    }
    
    // Dados simples (uma série)
    return data.labels.map((label, index) => ({
      name: label,
      value: (data.values as number[])[index],
      // Para scatter plots
      x: typeof label === 'number' ? label : index,
      y: (data.values as number[])[index]
    }));
  };

  const chartData = prepareChartData();
  const customColors = data.extra?.colors || COLORS;

  const renderChart = () => {
    switch (data.type) {
      case 'bar':
        return (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="name" 
              tick={{ fontSize: 12 }}
              label={data.extra?.xLabel ? { value: data.extra.xLabel, position: 'insideBottom', offset: -5 } : undefined}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              label={data.extra?.yLabel ? { value: data.extra.yLabel, angle: -90, position: 'insideLeft' } : undefined}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            {Array.isArray(data.values[0]) ? (
              // Múltiplas barras
              (data.values as number[][]).map((_, index) => {
                const seriesName = data.extra?.legendas?.[index] || `Série ${index + 1}`;
                return (
                  <Bar 
                    key={seriesName}
                    dataKey={seriesName} 
                    fill={customColors[index % customColors.length]}
                    radius={[4, 4, 0, 0]}
                  />
                );
              })
            ) : (
              <Bar dataKey="value" fill={customColors[0]} radius={[4, 4, 0, 0]}>
                <LabelList dataKey="value" position="top" style={{ fontSize: 11 }} />
              </Bar>
            )}
            {data.extra?.legendas && <Legend />}
          </BarChart>
        );

      case 'line':
      case 'timeseries':
        return (
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="name"
              tick={{ fontSize: 12 }}
              label={data.extra?.xLabel ? { value: data.extra.xLabel, position: 'insideBottom', offset: -5 } : undefined}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              label={data.extra?.yLabel ? { value: data.extra.yLabel, angle: -90, position: 'insideLeft' } : undefined}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            {Array.isArray(data.values[0]) ? (
              // Múltiplas linhas
              (data.values as number[][]).map((_, index) => {
                const seriesName = data.extra?.legendas?.[index] || `Série ${index + 1}`;
                return (
                  <Line 
                    key={seriesName}
                    type="monotone"
                    dataKey={seriesName}
                    stroke={customColors[index % customColors.length]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                );
              })
            ) : (
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke={customColors[0]}
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            )}
            {data.extra?.legendas && <Legend />}
          </LineChart>
        );

      case 'pie':
        const pieData = chartData.map((item, index) => ({
          ...item,
          fill: customColors[index % customColors.length]
        }));
        return (
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(entry) => `${entry.name}: ${entry.value}`}
              outerRadius={120}
              fill="#8884d8"
              dataKey="value"
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
          </PieChart>
        );

      case 'scatter':
        return (
          <ScatterChart>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              type="number" 
              dataKey="x" 
              tick={{ fontSize: 12 }}
              label={data.extra?.xLabel ? { value: data.extra.xLabel, position: 'insideBottom', offset: -5 } : undefined}
            />
            <YAxis 
              type="number" 
              dataKey="y" 
              tick={{ fontSize: 12 }}
              label={data.extra?.yLabel ? { value: data.extra.yLabel, angle: -90, position: 'insideLeft' } : undefined}
            />
            <Tooltip 
              cursor={{ strokeDasharray: '3 3' }}
              contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            <Scatter name="Dados" data={chartData} fill={customColors[0]} />
          </ScatterChart>
        );

      case 'histogram':
        // Histogram é similar ao bar chart mas com barras contíguas
        return (
          <BarChart data={chartData} barCategoryGap={0}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis 
              dataKey="name"
              tick={{ fontSize: 12 }}
              label={data.extra?.xLabel ? { value: data.extra.xLabel, position: 'insideBottom', offset: -5 } : undefined}
            />
            <YAxis 
              tick={{ fontSize: 12 }}
              label={data.extra?.yLabel ? { value: data.extra.yLabel || 'Frequência', angle: -90, position: 'insideLeft' } : undefined}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            <Bar dataKey="value" fill={customColors[0]} />
          </BarChart>
        );

      case 'boxplot':
        // Boxplot simplificado - mostra como área com min/max
        // Você pode implementar um boxplot mais complexo se necessário
        const boxData = data.extra?.quartis || chartData;
        return (
          <AreaChart data={boxData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis dataKey="name" tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip 
              contentStyle={{ backgroundColor: 'rgba(255, 255, 255, 0.95)', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            <Area 
              type="monotone" 
              dataKey="value" 
              stroke={customColors[0]} 
              fill={customColors[0]} 
              fillOpacity={0.3}
            />
            {data.extra?.ranges && (
              <Area 
                type="monotone" 
                dataKey="max" 
                stroke={customColors[1]} 
                fill={customColors[1]} 
                fillOpacity={0.2}
              />
            )}
          </AreaChart>
        );

      default:
        return (
          <div className="text-center text-muted-foreground p-4">
            Tipo de gráfico não suportado: {data.type}
          </div>
        );
    }
  };

  return (
    <Card className="p-4 mt-4 bg-gradient-to-br from-blue-50 to-white border-blue-200">
      {data.extra?.title && (
        <h3 className="text-lg font-semibold text-gray-800 mb-4 text-center">
          {data.extra.title}
        </h3>
      )}
      <div className="w-full h-[400px]">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </Card>
  );
};

export default Visualization;