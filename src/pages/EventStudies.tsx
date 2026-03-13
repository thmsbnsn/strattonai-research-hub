import { useState } from "react";
import { AppLayout } from "@/components/AppLayout";
import { eventStudyResults, returnDistribution, forwardCurveData, eventCategories, timeHorizons } from "@/lib/mockData";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart,
  CartesianGrid, Cell, ReferenceLine,
} from "recharts";

export default function EventStudies() {
  const [eventType, setEventType] = useState("Product Launch");
  const [horizon, setHorizon] = useState("5D");

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Event Study Explorer</h1>
          <p className="text-sm text-muted-foreground mt-1">Research historical event outcomes and forward returns</p>
        </div>

        {/* Filters */}
        <div className="terminal-card p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Event Type</label>
              <select
                value={eventType}
                onChange={(e) => setEventType(e.target.value)}
                className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {eventCategories.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Primary Company</label>
              <input
                placeholder="Any"
                className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Related Company</label>
              <input
                placeholder="Any"
                className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
              />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Time Horizon</label>
              <div className="flex gap-1">
                {timeHorizons.map((h) => (
                  <button
                    key={h}
                    onClick={() => setHorizon(h)}
                    className={`flex-1 text-xs py-2 rounded-md transition-colors font-mono ${
                      horizon === h ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"
                    }`}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Results Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Avg Forward Return", value: "+1.78%", color: "text-success" },
            { label: "Win Rate", value: "65%", color: "text-primary" },
            { label: "Sample Size", value: "42", color: "text-foreground" },
            { label: "Sharpe Ratio", value: "1.24", color: "text-foreground" },
          ].map((stat) => (
            <div key={stat.label} className="terminal-card p-4 text-center">
              <p className="text-xs text-muted-foreground mb-1">{stat.label}</p>
              <p className={`font-mono text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            </div>
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Forward Performance Curve */}
          <div className="terminal-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Forward Performance Curve</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forwardCurveData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 30% 16%)" />
                  <XAxis
                    dataKey="day"
                    tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }}
                    axisLine={{ stroke: "hsl(222 30% 16%)" }}
                    label={{ value: "Days", position: "bottom", fill: "hsl(215 20% 55%)", fontSize: 10 }}
                  />
                  <YAxis
                    tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }}
                    axisLine={{ stroke: "hsl(222 30% 16%)" }}
                    tickFormatter={(v) => `${v.toFixed(1)}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(222 44% 8%)",
                      border: "1px solid hsl(222 30% 16%)",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "hsl(210 40% 92%)",
                    }}
                    formatter={(v: number) => [`${v.toFixed(2)}%`]}
                  />
                  <Area type="monotone" dataKey="upperBound" stroke="none" fill="hsl(210 100% 56% / 0.08)" />
                  <Area type="monotone" dataKey="lowerBound" stroke="none" fill="hsl(210 100% 56% / 0.08)" />
                  <Line type="monotone" dataKey="avgReturn" stroke="hsl(210 100% 56%)" strokeWidth={2} dot={false} />
                  <ReferenceLine y={0} stroke="hsl(222 30% 20%)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Return Distribution */}
          <div className="terminal-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Return Distribution</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={returnDistribution.sort((a, b) => a.return - b.return)}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 30% 16%)" />
                  <XAxis
                    dataKey="return"
                    tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }}
                    axisLine={{ stroke: "hsl(222 30% 16%)" }}
                    tickFormatter={(v) => `${v.toFixed(0)}%`}
                  />
                  <YAxis hide />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(222 44% 8%)",
                      border: "1px solid hsl(222 30% 16%)",
                      borderRadius: "8px",
                      fontSize: "12px",
                      color: "hsl(210 40% 92%)",
                    }}
                    formatter={(v: number) => [`${v.toFixed(2)}%`, "Return"]}
                  />
                  <Bar dataKey="return" radius={[2, 2, 0, 0]}>
                    {returnDistribution.sort((a, b) => a.return - b.return).map((entry, i) => (
                      <Cell key={i} fill={entry.return >= 0 ? "hsl(152 69% 45%)" : "hsl(0 72% 55%)"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Results Table */}
        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Results by Time Horizon</h3>
          <div className="overflow-x-auto">
            <table className="w-full data-grid">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2 px-3 text-xs text-muted-foreground font-medium">Horizon</th>
                  <th className="text-right py-2 px-3 text-xs text-muted-foreground font-medium">Avg Return</th>
                  <th className="text-right py-2 px-3 text-xs text-muted-foreground font-medium">Win Rate</th>
                  <th className="text-right py-2 px-3 text-xs text-muted-foreground font-medium">Sample Size</th>
                </tr>
              </thead>
              <tbody>
                {eventStudyResults.map((r) => (
                  <tr key={r.horizon} className="border-b border-border/50 hover:bg-muted/20">
                    <td className="py-2.5 px-3 text-foreground font-semibold">{r.horizon}</td>
                    <td className={`py-2.5 px-3 text-right ${r.avgReturn >= 0 ? "text-success" : "text-danger"}`}>
                      {r.avgReturn >= 0 ? "+" : ""}{r.avgReturn.toFixed(2)}%
                    </td>
                    <td className="py-2.5 px-3 text-right text-foreground">{r.winRate}%</td>
                    <td className="py-2.5 px-3 text-right text-muted-foreground">{r.sampleSize}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
