import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { formatPercent } from "../lib/utils";
import { LoadingState, EmptyState } from "../components/StateComponents";
import { Brain } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend
} from "recharts";

export default function ModelPerformance() {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getModels();
        if (response.data?.models) {
          setModels(response.data.models);
        }
      } catch (error) {
        console.error("Failed to fetch models:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <LoadingState message="Loading model performance..." />;
  }

  if (!models.length) {
    return (
      <EmptyState
        icon={Brain}
        title="No Model Data Available"
        description="Run the pipeline first to see model performance metrics."
      />
    );
  }

  const logisticModel = models.find(m => m.model_type === "logistic");
  const boostedModel = models.find(m => m.model_type === "boosted");

  const metricsComparison = [
    { metric: "AUC-ROC", logistic: logisticModel?.auc_roc || 0, boosted: boostedModel?.auc_roc || 0 },
    { metric: "Precision", logistic: logisticModel?.precision || 0, boosted: boostedModel?.precision || 0 },
    { metric: "Recall", logistic: logisticModel?.recall || 0, boosted: boostedModel?.recall || 0 },
    { metric: "F1 Score", logistic: logisticModel?.f1_score || 0, boosted: boostedModel?.f1_score || 0 },
    { metric: "Accuracy", logistic: logisticModel?.accuracy || 0, boosted: boostedModel?.accuracy || 0 },
  ];

  const radarData = metricsComparison.map(m => ({
    metric: m.metric,
    Logistic: m.logistic,
    Boosted: m.boosted,
  }));

  const getFeatureImportance = (model) => {
    if (!model?.feature_importance) return [];
    return Object.entries(model.feature_importance)
      .map(([name, value]) => ({ name: name.replace(/_/g, ' '), value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 10);
  };

  return (
    <div className="space-y-8" data-testid="model-performance">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Model Performance</h2>
        <p className="text-muted-foreground">ML model metrics and feature importance</p>
      </div>

      {/* Model Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {[logisticModel, boostedModel].filter(Boolean).map((model) => (
          <div 
            key={model.model_type}
            className="bg-white border border-border rounded-md p-6 card-hover"
          >
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-lg font-semibold capitalize">{model.model_type} Regression</h3>
                <p className="text-sm text-muted-foreground">Version {model.model_version}</p>
              </div>
              <div className="p-2 rounded-md bg-muted">
                <Brain className="w-5 h-5 text-muted-foreground" />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-muted/50 rounded-md">
                <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">AUC-ROC</p>
                <p className="text-2xl font-bold tabular-nums">{formatPercent(model.auc_roc)}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-md">
                <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Accuracy</p>
                <p className="text-2xl font-bold tabular-nums">{formatPercent(model.accuracy)}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-md">
                <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Precision</p>
                <p className="text-2xl font-bold tabular-nums">{formatPercent(model.precision)}</p>
              </div>
              <div className="p-4 bg-muted/50 rounded-md">
                <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Recall</p>
                <p className="text-2xl font-bold tabular-nums">{formatPercent(model.recall)}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Comparison Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart Comparison */}
        <div className="bg-white border border-border rounded-md p-6">
          <h3 className="text-lg font-semibold mb-6">Metrics Comparison</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metricsComparison} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                <XAxis type="number" domain={[0, 1]} tick={{ fontSize: 12, fill: '#64748B' }} />
                <YAxis type="category" dataKey="metric" tick={{ fontSize: 12, fill: '#64748B' }} width={80} />
                <Tooltip 
                  formatter={(value) => formatPercent(value)}
                  contentStyle={{ borderRadius: '6px', border: '1px solid #E2E8F0' }}
                />
                <Legend />
                <Bar dataKey="logistic" name="Logistic" fill="#2563EB" radius={[0, 4, 4, 0]} />
                <Bar dataKey="boosted" name="Boosted" fill="#16A34A" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Radar Chart */}
        <div className="bg-white border border-border rounded-md p-6">
          <h3 className="text-lg font-semibold mb-6">Performance Radar</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={radarData}>
                <PolarGrid stroke="#E2E8F0" />
                <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: '#64748B' }} />
                <PolarRadiusAxis angle={30} domain={[0, 1]} tick={{ fontSize: 10, fill: '#64748B' }} />
                <Radar name="Logistic" dataKey="Logistic" stroke="#2563EB" fill="#2563EB" fillOpacity={0.3} />
                <Radar name="Boosted" dataKey="Boosted" stroke="#16A34A" fill="#16A34A" fillOpacity={0.3} />
                <Legend />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Feature Importance */}
      <div className="bg-white border border-border rounded-md p-6">
        <h3 className="text-lg font-semibold mb-6">Feature Importance</h3>
        <Tabs defaultValue="logistic">
          <TabsList className="mb-6">
            <TabsTrigger value="logistic">Logistic Regression</TabsTrigger>
            <TabsTrigger value="boosted">Boosted Model</TabsTrigger>
          </TabsList>
          
          <TabsContent value="logistic">
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getFeatureImportance(logisticModel)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 12, fill: '#64748B' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} width={150} />
                  <Tooltip 
                    formatter={(value) => formatPercent(value)}
                    contentStyle={{ borderRadius: '6px', border: '1px solid #E2E8F0' }}
                  />
                  <Bar dataKey="value" fill="#2563EB" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>
          
          <TabsContent value="boosted">
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={getFeatureImportance(boostedModel)} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 12, fill: '#64748B' }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} width={150} />
                  <Tooltip 
                    formatter={(value) => formatPercent(value)}
                    contentStyle={{ borderRadius: '6px', border: '1px solid #E2E8F0' }}
                  />
                  <Bar dataKey="value" fill="#16A34A" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
