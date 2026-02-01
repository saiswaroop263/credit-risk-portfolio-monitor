import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { formatPercent } from "../lib/utils";
import { LoadingState, EmptyState } from "../components/StateComponents";
import { Badge } from "../components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../components/ui/tabs";
import { ShieldCheck, AlertTriangle, CheckCircle, XCircle, TrendingUp } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { cn } from "../lib/utils";

export default function DQDrift() {
  const [dqReport, setDqReport] = useState(null);
  const [driftReport, setDriftReport] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dqRes, driftRes] = await Promise.all([
          api.getDq(),
          api.getDrift()
        ]);
        
        if (dqRes.data && !dqRes.data.message) {
          setDqReport(dqRes.data);
        }
        if (driftRes.data && !driftRes.data.message) {
          setDriftReport(driftRes.data);
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
    return <LoadingState message="Loading reports..." />;
  }

  if (!dqReport && !driftReport) {
    return (
      <EmptyState
        icon={ShieldCheck}
        title="No Reports Available"
        description="Run the pipeline first to see data quality and drift reports."
      />
    );
  }

  return (
    <div className="space-y-8" data-testid="dq-drift">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Data Quality & Drift</h2>
        <p className="text-muted-foreground">Monitor data quality and feature drift</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white border border-border rounded-md p-6 card-hover">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground uppercase tracking-widest">DQ Rules</span>
            <ShieldCheck className="w-5 h-5 text-muted-foreground" />
          </div>
          <p className="text-3xl font-bold">{dqReport?.total_rules || 0}</p>
          <p className="text-sm text-muted-foreground">Total rules checked</p>
        </div>
        
        <div className="bg-white border border-border rounded-md p-6 card-hover">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground uppercase tracking-widest">Passed</span>
            <CheckCircle className="w-5 h-5 text-green-500" />
          </div>
          <p className="text-3xl font-bold text-green-600">{dqReport?.passed_rules || 0}</p>
          <p className="text-sm text-muted-foreground">{formatPercent((dqReport?.passed_rules || 0) / (dqReport?.total_rules || 1))} pass rate</p>
        </div>
        
        <div className="bg-white border border-border rounded-md p-6 card-hover">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground uppercase tracking-widest">Failed</span>
            <XCircle className="w-5 h-5 text-red-500" />
          </div>
          <p className="text-3xl font-bold text-red-600">{dqReport?.failed_rules || 0}</p>
          <p className="text-sm text-muted-foreground">Rules with issues</p>
        </div>
        
        <div className="bg-white border border-border rounded-md p-6 card-hover">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs text-muted-foreground uppercase tracking-widest">Drift Status</span>
            <TrendingUp className={cn("w-5 h-5", driftReport?.overall_drift_detected ? "text-amber-500" : "text-green-500")} />
          </div>
          <p className={cn("text-3xl font-bold", driftReport?.overall_drift_detected ? "text-amber-600" : "text-green-600")}>
            {driftReport?.overall_drift_detected ? "Detected" : "Stable"}
          </p>
          <p className="text-sm text-muted-foreground">{driftReport?.drifted_features || 0} features drifted</p>
        </div>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="dq">
        <TabsList className="mb-6">
          <TabsTrigger value="dq" className="gap-2">
            <ShieldCheck className="w-4 h-4" />
            Data Quality
          </TabsTrigger>
          <TabsTrigger value="drift" className="gap-2">
            <TrendingUp className="w-4 h-4" />
            Drift Report
          </TabsTrigger>
        </TabsList>

        {/* DQ Tab */}
        <TabsContent value="dq">
          <div className="bg-white border border-border rounded-md">
            <div className="p-6 border-b border-border">
              <h3 className="text-lg font-semibold">Data Quality Rules</h3>
              <p className="text-sm text-muted-foreground">10 validation rules checked against the dataset</p>
            </div>
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Rule ID</th>
                    <th>Rule Name</th>
                    <th>Description</th>
                    <th>Status</th>
                    <th>Pass Rate</th>
                    <th>Failed Records</th>
                  </tr>
                </thead>
                <tbody>
                  {dqReport?.rules?.map((rule) => (
                    <tr key={rule.rule_id}>
                      <td className="font-mono text-sm">{rule.rule_id}</td>
                      <td className="font-medium">{rule.rule_name}</td>
                      <td className="text-muted-foreground text-sm max-w-xs truncate">{rule.rule_description}</td>
                      <td>
                        <Badge className={rule.passed ? "bg-green-50 text-green-700 border-green-200" : "bg-red-50 text-red-700 border-red-200"}>
                          {rule.passed ? (
                            <><CheckCircle className="w-3 h-3 mr-1" /> Pass</>
                          ) : (
                            <><XCircle className="w-3 h-3 mr-1" /> Fail</>
                          )}
                        </Badge>
                      </td>
                      <td className="tabular-nums">{rule.pass_rate}%</td>
                      <td className="tabular-nums">{rule.failed_records}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Failed Examples */}
          {dqReport?.rules?.some(r => r.failed_examples?.length > 0) && (
            <div className="mt-6 bg-white border border-border rounded-md p-6">
              <h3 className="text-lg font-semibold mb-4">Failed Record Examples</h3>
              <div className="space-y-4">
                {dqReport.rules.filter(r => r.failed_examples?.length > 0).slice(0, 3).map((rule) => (
                  <div key={rule.rule_id} className="p-4 bg-red-50 border border-red-200 rounded-md">
                    <p className="font-medium text-red-700 mb-2">{rule.rule_name}</p>
                    <div className="text-sm font-mono text-red-600">
                      {JSON.stringify(rule.failed_examples[0], null, 2)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </TabsContent>

        {/* Drift Tab */}
        <TabsContent value="drift">
          {driftReport && (
            <>
              {/* PSI Chart */}
              <div className="bg-white border border-border rounded-md p-6 mb-6">
                <h3 className="text-lg font-semibold mb-6">PSI Scores by Feature</h3>
                <div className="h-[400px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart 
                      data={driftReport.features?.map(f => ({
                        name: f.feature_name?.replace(/_/g, ' ') || 'Unknown',
                        psi: f.psi_score || 0,
                        status: f.drift_detected ? 'drift' : (f.psi_score >= 0.1 ? 'warning' : 'stable')
                      })) || []}
                      layout="vertical"
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
                      <XAxis type="number" tick={{ fontSize: 12, fill: '#64748B' }} />
                      <YAxis type="category" dataKey="name" tick={{ fontSize: 11, fill: '#64748B' }} width={150} />
                      <Tooltip 
                        formatter={(value) => value.toFixed(4)}
                        contentStyle={{ borderRadius: '6px', border: '1px solid #E2E8F0' }}
                      />
                      <Bar dataKey="psi" radius={[0, 4, 4, 0]}>
                        {(driftReport.features || []).map((entry, index) => (
                          <Cell 
                            key={`cell-${index}`} 
                            fill={entry.drift_detected ? '#DC2626' : (entry.psi_score >= 0.1 ? '#F59E0B' : '#16A34A')} 
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                
                {/* PSI Legend */}
                <div className="flex justify-center gap-6 mt-4 pt-4 border-t border-border">
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-green-500" />
                    <span className="text-sm text-muted-foreground">Stable (PSI &lt; 0.1)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-amber-500" />
                    <span className="text-sm text-muted-foreground">Warning (0.1 ≤ PSI &lt; 0.25)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-3 h-3 rounded-full bg-red-500" />
                    <span className="text-sm text-muted-foreground">Drift (PSI ≥ 0.25)</span>
                  </div>
                </div>
              </div>

              {/* Feature Table */}
              <div className="bg-white border border-border rounded-md">
                <div className="p-6 border-b border-border">
                  <h3 className="text-lg font-semibold">Feature Drift Details</h3>
                </div>
                <div className="overflow-x-auto">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Feature</th>
                        <th>PSI Score</th>
                        <th>Status</th>
                        <th>Action Required</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(driftReport.features || []).map((feature) => (
                        <tr key={feature.feature_name}>
                          <td className="font-medium">{feature.feature_name.replace(/_/g, ' ')}</td>
                          <td className="tabular-nums font-mono">{feature.psi_score.toFixed(4)}</td>
                          <td>
                            <Badge className={
                              feature.drift_detected 
                                ? "bg-red-50 text-red-700 border-red-200" 
                                : feature.psi_score >= 0.1 
                                  ? "bg-amber-50 text-amber-700 border-amber-200"
                                  : "bg-green-50 text-green-700 border-green-200"
                            }>
                              {feature.drift_detected ? "Drift" : feature.psi_score >= 0.1 ? "Warning" : "Stable"}
                            </Badge>
                          </td>
                          <td className="text-sm text-muted-foreground">
                            {feature.drift_detected 
                              ? "Review and retrain model" 
                              : feature.psi_score >= 0.1 
                                ? "Monitor closely"
                                : "No action needed"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
