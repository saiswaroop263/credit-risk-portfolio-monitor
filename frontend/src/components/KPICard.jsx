import { cn } from "../lib/utils";

export function KPICard({ title, value, subtitle, icon: Icon, trend, className }) {
  return (
    <div className={cn("kpi-card animate-in", className)} data-testid={`kpi-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-muted-foreground uppercase tracking-widest">
            {title}
          </p>
          <p className="text-2xl font-bold tabular-nums">{value}</p>
          {subtitle && (
            <p className="text-sm text-muted-foreground">{subtitle}</p>
          )}
        </div>
        {Icon && (
          <div className="p-2 rounded-md bg-muted">
            <Icon className="w-5 h-5 text-muted-foreground" />
          </div>
        )}
      </div>
      {trend && (
        <div className={cn(
          "mt-4 text-xs font-medium",
          trend > 0 ? "text-green-600" : trend < 0 ? "text-red-600" : "text-muted-foreground"
        )}>
          {trend > 0 ? "↑" : trend < 0 ? "↓" : "→"} {Math.abs(trend)}% from last run
        </div>
      )}
    </div>
  );
}
