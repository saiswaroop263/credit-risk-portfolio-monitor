import { useState, useEffect, useCallback } from "react";
import { 
  DollarSign, 
  TrendingUp, 
  AlertTriangle, 
  BarChart3,
  Play,
  RefreshCw
} from "lucide-react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { formatCurrency, formatNumber, formatPercent } from "../lib/utils";
import { KPICard } from "../components/KPICard";
import { LoadingState, EmptyState } from "../components/StateComponents";
import { Button } from "../components/ui/button";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from "recharts";

const RISK_COLORS = {
  low: "#16A34A",
  medium: "#F59E0B", 
  high: "#DC2626"
};

export default function Dashboard() {
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [demoLoading, setDemoLoading] = useState(false);
  const [hasData, setHasData] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await api.getKpis();
      if (response.data && !response.data.message) {
        setKpis(response.data);
        setHasData(true);
      } else {
        setHasData(false);
      }
    } catch (error) {
      console.error("Failed to fetch KPIs:", error);
      setHasData(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRunDemo = async () => {
    try {
      setDemoLoading(true);
      toast.info("Generating demo data and running pipeline...");
      const response = await api.demo();
      toast.success(response.data.message);
      await fetchData();
    } catch (error) {
      console.error("Demo error:", error);
      toast.error(error.response?.data?.detail || "Failed to run demo");
    } finally {
      setDemoLoading(false);
    }
  };

  if (loading) {
    return <LoadingState message="Loading dashboard..." />;
  }

  if (!hasData) {
    return (
      <EmptyState
        icon={BarChart3}
        title="No Data Available"
        description="Run the demo pipeline or upload your own CSV data to get started with credit risk analysis."
        action={
          <Button
            onClick={handleRunDemo}
            disabled={demoLoading}
            data-testid="run-demo-btn"
            className="gap-2"
          >
            {demoLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {demoLoading ? "Running Demo..." : "Run Demo Pipeline"}
          </Button>
        }
      />
    );
  }

  const riskData = [
    { name: "Low Risk", value: kpis.low_risk_count, color: RISK_COLORS.low },
    { name: "Medium Risk", value: kpis.medium_risk_count, color: RISK_COLORS.medium },
    { name: "High Risk", value: kpis.high_risk_count, color: RISK_COLORS.high },
  ];

  const exposureData = [
    { name: "Low", value: kpis.low_risk_exposure, fill: RISK_COLORS.low },
    { name: "Medium", value: kpis.medium_risk_exposure, fill: RISK_COLORS.medium },
    { name: "High", value: kpis.high_risk_exposure, fill: RISK_COLORS.high },
  ];

  return (
    <div className="space-y-8" data-testid="dashboard">
      {/* Header with Demo Button */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold">Portfolio Overview</h2>
          <p className="text-muted-foreground">Credit risk metrics at a glance</p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={fetchData}
            data-testid="refresh-btn"
            className="gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button
            onClick={handleRunDemo}
            disabled={demoLoading}
            data-testid="run-demo-btn"
            className="gap-2"
          >
            {demoLoading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {demoLoading ? "Running..." : "Run Demo"}
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Loans"
          value={formatNumber(kpis.total_loans)}
          subtitle="Active portfolio"
          icon={BarChart3}
          className="stagger-1"
        />
        <KPICard
          title="Portfolio Value"
          value={formatCurrency(kpis.total_portfolio_value)}
          subtitle={`Avg: ${formatCurrency(kpis.avg_loan_amount)}`}
          icon={DollarSign}
          className="stagger-2"
        />
        <KPICard
          title="Avg Risk Score"
          value={formatPercent(kpis.avg_risk_score)}
          subtitle={`Default Rate: ${formatPercent(kpis.default_rate)}`}
          icon={TrendingUp}
          className="stagger-3"
        />
        <KPICard
          title="High Risk Loans"
          value={formatNumber(kpis.high_risk_count)}
          subtitle={formatCurrency(kpis.high_risk_exposure)}
          icon={AlertTriangle}
          className="stagger-4"
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Distribution Pie Chart */}
        <div className="bg-white border border-border rounded-md p-6 card-hover">
          <h3 className="text-lg font-semibold mb-6">Risk Distribution</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => formatNumber(value)}
                  contentStyle={{ 
                    borderRadius: '6px', 
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex justify-center gap-6 mt-4">
            {riskData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm text-muted-foreground">{item.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Exposure Bar Chart */}
        <div className="bg-white border border-border rounded-md p-6 card-hover">
          <h3 className="text-lg font-semibold mb-6">Risk Exposure</h3>
          <div className="h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={exposureData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                <XAxis 
                  type="number" 
                  tickFormatter={(v) => `$${(v/1000000).toFixed(1)}M`}
                  tick={{ fontSize: 12, fill: '#64748B' }}
                />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  tick={{ fontSize: 12, fill: '#64748B' }}
                  width={60}
                />
                <Tooltip 
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={{ 
                    borderRadius: '6px', 
                    border: '1px solid #E2E8F0',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                  }}
                />
                <Bar dataKey="value" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="bg-white border border-border rounded-md p-6">
        <h3 className="text-lg font-semibold mb-4">Portfolio Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Avg Interest Rate</p>
            <p className="text-xl font-semibold tabular-nums">{kpis.avg_interest_rate?.toFixed(2)}%</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Predicted Default</p>
            <p className="text-xl font-semibold tabular-nums">{formatPercent(kpis.predicted_default_rate)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Medium Risk Loans</p>
            <p className="text-xl font-semibold tabular-nums">{formatNumber(kpis.medium_risk_count)}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Low Risk Loans</p>
            <p className="text-xl font-semibold tabular-nums">{formatNumber(kpis.low_risk_count)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
