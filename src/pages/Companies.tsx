import { useState } from "react";
import { Search, ExternalLink } from "lucide-react";
import { companyProfile, priceData, eventMarkers, relatedCompaniesGraph, marketEvents } from "@/lib/mockData";
import { AppLayout } from "@/components/AppLayout";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

export default function Companies() {
  const [search, setSearch] = useState("NVDA");
  const profile = companyProfile;

  const chartData = priceData.map((d) => ({
    ...d,
    price: Math.round(d.price * 100) / 100,
  }));

  const uniqueNodes = new Set<string>();
  relatedCompaniesGraph.forEach((e) => {
    uniqueNodes.add(e.source);
    uniqueNodes.add(e.target);
  });

  const companyEvents = marketEvents.filter(
    (e) => e.ticker === profile.ticker || e.relatedCompanies.some((r) => r.ticker === profile.ticker)
  );

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Company Research</h1>
          <p className="text-sm text-muted-foreground mt-1">Deep-dive into company events and relationships</p>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value.toUpperCase())}
            placeholder="Search ticker..."
            className="w-full pl-10 pr-4 py-2.5 bg-muted border border-border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono"
          />
        </div>

        {/* Company Overview */}
        <div className="terminal-card p-5">
          <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
            <div>
              <div className="flex items-center gap-3">
                <span className="font-mono text-lg font-bold text-primary">{profile.ticker}</span>
                <h2 className="text-lg font-semibold text-foreground">{profile.name}</h2>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{profile.sector} · {profile.industry}</p>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
              {[
                { label: "Market Cap", value: profile.marketCap },
                { label: "P/E", value: profile.pe.toString() },
                { label: "Revenue", value: profile.revenue },
                { label: "Employees", value: profile.employees },
              ].map((s) => (
                <div key={s.label}>
                  <p className="text-xs text-muted-foreground">{s.label}</p>
                  <p className="font-mono text-sm font-semibold text-foreground">{s.value}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Price Chart */}
        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Price Chart (90 Days)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis
                  dataKey="date"
                  tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }}
                  tickFormatter={(v) => v.slice(5)}
                  interval={14}
                  axisLine={{ stroke: "hsl(222 30% 16%)" }}
                />
                <YAxis
                  domain={["auto", "auto"]}
                  tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }}
                  axisLine={{ stroke: "hsl(222 30% 16%)" }}
                  width={60}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "hsl(222 44% 8%)",
                    border: "1px solid hsl(222 30% 16%)",
                    borderRadius: "8px",
                    fontSize: "12px",
                    color: "hsl(210 40% 92%)",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="price"
                  stroke="hsl(210 100% 56%)"
                  strokeWidth={2}
                  dot={false}
                />
                {eventMarkers.map((m, i) => (
                  <ReferenceLine
                    key={i}
                    x={m.date}
                    stroke={m.type === "positive" ? "hsl(152 69% 45%)" : "hsl(0 72% 55%)"}
                    strokeDasharray="3 3"
                    label={{
                      value: m.label,
                      position: "top",
                      fill: "hsl(215 20% 55%)",
                      fontSize: 9,
                    }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Related Companies */}
          <div className="terminal-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Related Companies</h3>
            <div className="space-y-2">
              {relatedCompaniesGraph
                .filter((e) => e.source === profile.ticker || e.target === profile.ticker)
                .map((edge, i) => {
                  const related = edge.source === profile.ticker ? edge.target : edge.source;
                  return (
                    <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-primary">{related}</span>
                        <span className="text-xs text-muted-foreground">{edge.relationship}</span>
                      </div>
                      <div className="w-20 h-1.5 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-primary"
                          style={{ width: `${edge.strength * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
            </div>
          </div>

          {/* Recent Events */}
          <div className="terminal-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Recent Events</h3>
            <div className="space-y-2">
              {companyEvents.map((evt) => (
                <div key={evt.id} className="p-3 rounded-lg bg-muted/30">
                  <p className="text-sm text-foreground leading-snug line-clamp-2">{evt.headline}</p>
                  <div className="flex items-center gap-2 mt-1.5">
                    <span className="text-xs bg-muted px-2 py-0.5 rounded text-muted-foreground">{evt.category}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      evt.sentiment === "positive" ? "bg-success/10 text-success" :
                      evt.sentiment === "negative" ? "bg-danger/10 text-danger" :
                      "bg-muted text-muted-foreground"
                    }`}>
                      {evt.sentiment}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
