import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { formatCurrency, formatNumber, formatPercent, getRiskColor } from "../lib/utils";
import { LoadingState, EmptyState } from "../components/StateComponents";
import { Badge } from "../components/ui/badge";
import { PieChart as PieChartIcon } from "lucide-react";
import { 
  PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend,
  BarChart, Bar, XAxis, YAxis, CartesianGrid
} from "recharts";

const RISK_COLORS = {
  low: "#16A34A",
  medium: "#F59E0B",
  high: "#DC2626"
};

export default function RiskSegments() {
  const [kpis, setKpis] = useState(null);
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [kpisRes, scoresRes] = await Promise.all([
          api.getKpis(),
          api.getScores(null, null, 50)
        ]);
        
        if (kpisRes.data && !kpisRes.data.message) {
          setKpis(kpisRes.data);
        }
        if (scoresRes.data?.scores) {
          setScores(scoresRes.data.scores);
        }
      } catch (error) {
        console.error("Failed to fetch data:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return <LoadingState message="Loading risk segments..." />;
  }

  if (!kpis) {
    return (
      <EmptyState
        icon={PieChartIcon}
        title="No Risk Data Available"
        description="Run the pipeline first to see risk segments."
      />
    );
  }

  const riskDistribution = [
    { name: "Low Risk", value: kpis.low_risk_count, exposure: kpis.low_risk_exposure, color: RISK_COLORS.low },
    { name: "Medium Risk", value: kpis.medium_risk_count, exposure: kpis.medium_risk_exposure, color: RISK_COLORS.medium },
    { name: "High Risk", value: kpis.high_risk_count, exposure: kpis.high_risk_exposure, color: RISK_COLORS.high },
  ];

  const totalLoans = kpis.total_loans;

  return (
    <div className="space-y-8" data-testid="risk-segments">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Risk Segments</h2>
        <p className="text-muted-foreground">Portfolio breakdown by risk level</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {riskDistribution.map((segment) => (
          <div 
            key={segment.name}
            className="bg-white border border-border rounded-md p-6 card-hover"
          >
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium text-muted-foreground">{segment.name}</span>
              <div 
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: segment.color }}
              />
            </div>
            <div className="space-y-2">
              <p className="text-3xl font-bold tabular-nums">{formatNumber(segment.value)}</p>
              <p className="text-sm text-muted-foreground">
                {((segment.value / totalLoans) * 100).toFixed(1)}% of portfolio
              </p>
              <p className="text-lg font-semibold text-muted-foreground">
                {formatCurrency(segment.exposure)}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribution Pie */}
        <div className="bg-white border border-border rounded-md p-6">
          <h3 className="text-lg font-semibold mb-6">Loan Count Distribution</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value) => formatNumber(value)}
                  contentStyle={{ borderRadius: '6px', border: '1px solid #E2E8F0' }}
                />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Exposure Bar */}
        <div className="bg-white border border-border rounded-md p-6">
          <h3 className="text-lg font-semibold mb-6">Exposure by Risk Level</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#64748B' }} />
                <YAxis 
                  tickFormatter={(v) => `$${(v/1000000).toFixed(1)}M`}
                  tick={{ fontSize: 12, fill: '#64748B' }}
                />
                <Tooltip 
                  formatter={(value) => formatCurrency(value)}
                  contentStyle={{ borderRadius: '6px', border: '1px solid #E2E8F0' }}
                />
                <Bar dataKey="exposure" radius={[4, 4, 0, 0]}>
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Scores Table */}
      <div className="bg-white border border-border rounded-md">
        <div className="p-6 border-b border-border">
          <h3 className="text-lg font-semibold">Recent Loan Scores</h3>
          <p className="text-sm text-muted-foreground">Latest scored loans with risk levels</p>
        </div>
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Loan ID</th>
                <th>Customer ID</th>
                <th>Logistic Score</th>
                <th>Boosted Score</th>
                <th>Ensemble Score</th>
                <th>Risk Level</th>
              </tr>
            </thead>
            <tbody>
              {scores.slice(0, 10).map((score) => (
                <tr key={score.loan_id}>
                  <td className="font-mono text-sm">{score.loan_id}</td>
                  <td className="font-mono text-sm">{score.customer_id}</td>
                  <td className="tabular-nums">{formatPercent(score.logistic_score)}</td>
                  <td className="tabular-nums">{formatPercent(score.boosted_score)}</td>
                  <td className="tabular-nums font-medium">{formatPercent(score.ensemble_score)}</td>
                  <td>
                    <Badge className={getRiskColor(score.risk_level)}>
                      {score.risk_level}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
