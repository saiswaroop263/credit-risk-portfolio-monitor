import { useState, useEffect } from "react";
import { api } from "../lib/api";
import { formatDate, getStatusColor } from "../lib/utils";
import { LoadingState, EmptyState } from "../components/StateComponents";
import { Badge } from "../components/ui/badge";
import { History, CheckCircle, XCircle, Clock, PlayCircle } from "lucide-react";
import { cn } from "../lib/utils";

export default function RunHistory() {
  const [runs, setRuns] = useState([]);
  const [selectedRun, setSelectedRun] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await api.getRuns();
        if (response.data?.runs) {
          setRuns(response.data.runs);
        }
      } catch (error) {
        console.error("Failed to fetch runs:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const fetchRunDetails = async (runId) => {
    try {
      const response = await api.getRun(runId);
      setSelectedRun(response.data);
    } catch (error) {
      console.error("Failed to fetch run details:", error);
    }
  };

  if (loading) {
    return <LoadingState message="Loading run history..." />;
  }

  if (!runs.length) {
    return (
      <EmptyState
        icon={History}
        title="No Pipeline Runs"
        description="No pipeline runs yet. Upload data or run the demo to get started."
      />
    );
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "running":
        return <PlayCircle className="w-4 h-4 text-amber-500 animate-pulse" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="space-y-8" data-testid="run-history">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Run History</h2>
        <p className="text-muted-foreground">Pipeline execution history and status</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Run List */}
        <div className="lg:col-span-2 bg-white border border-border rounded-md">
          <div className="p-6 border-b border-border">
            <h3 className="text-lg font-semibold">Recent Runs</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Run ID</th>
                  <th>Status</th>
                  <th>Records</th>
                  <th>DQ Status</th>
                  <th>Drift</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((run) => (
                  <tr 
                    key={run.run_id}
                    onClick={() => fetchRunDetails(run.run_id)}
                    className={cn(
                      "cursor-pointer",
                      selectedRun?.run_id === run.run_id && "bg-muted/50"
                    )}
                  >
                    <td className="font-mono text-sm">{run.run_id.slice(0, 8)}...</td>
                    <td>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(run.status)}
                        <Badge className={getStatusColor(run.status)}>
                          {run.status}
                        </Badge>
                      </div>
                    </td>
                    <td className="tabular-nums">{run.raw_records || 0}</td>
                    <td>
                      {run.status === "completed" && (
                        <Badge className={run.dq_passed ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-700"}>
                          {run.dq_passed ? "Passed" : "Issues"}
                        </Badge>
                      )}
                    </td>
                    <td>
                      {run.status === "completed" && (
                        <Badge className={run.drift_detected ? "bg-amber-50 text-amber-700" : "bg-green-50 text-green-700"}>
                          {run.drift_detected ? "Detected" : "Stable"}
                        </Badge>
                      )}
                    </td>
                    <td className="text-sm text-muted-foreground">{formatDate(run.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Run Details */}
        <div className="bg-white border border-border rounded-md">
          <div className="p-6 border-b border-border">
            <h3 className="text-lg font-semibold">Run Details</h3>
          </div>
          {selectedRun ? (
            <div className="p-6 space-y-6">
              {/* Run Info */}
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-widest mb-2">Run ID</p>
                <p className="font-mono text-sm break-all">{selectedRun.run_id}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Status</p>
                  <Badge className={getStatusColor(selectedRun.status)}>
                    {selectedRun.status}
                  </Badge>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-widest mb-1">Records</p>
                  <p className="font-semibold">{selectedRun.processed_records || selectedRun.raw_records}</p>
                </div>
              </div>

              {/* Timestamps */}
              <div className="pt-4 border-t border-border">
                <p className="text-xs text-muted-foreground uppercase tracking-widest mb-3">Timeline</p>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Created</span>
                    <span>{formatDate(selectedRun.created_at)}</span>
                  </div>
                  {selectedRun.started_at && (
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Started</span>
                      <span>{formatDate(selectedRun.started_at)}</span>
                    </div>
                  )}
                  {selectedRun.completed_at && (
                    <div className="flex justify-between text-sm">
                      <span className="text-muted-foreground">Completed</span>
                      <span>{formatDate(selectedRun.completed_at)}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Pipeline Steps */}
              {selectedRun.steps?.length > 0 && (
                <div className="pt-4 border-t border-border">
                  <p className="text-xs text-muted-foreground uppercase tracking-widest mb-3">Pipeline Steps</p>
                  <div className="space-y-2">
                    {selectedRun.steps.map((step, index) => (
                      <div key={index} className="flex items-center gap-2 text-sm">
                        {getStatusIcon(step.status)}
                        <span className="capitalize">{step.step_name.replace(/_/g, ' ')}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 text-center text-muted-foreground">
              <p>Select a run to view details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
