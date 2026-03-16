import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { AppLayout } from "@/components/AppLayout";
import { ChartCard } from "@/components/ChartCard";
import { CardSkeleton, ChartSkeleton, ListSkeleton } from "@/components/LoadingSkeletons";
import { ErrorState } from "@/components/StateDisplays";
import { getCompanyProfile, getCompanyRelationships, getPriceHistory, getEventMarkers } from "@/services/companyService";
import { getEvents } from "@/services/eventService";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

export default function Companies() {
  const [search, setSearch] = useState("NVDA");

  const profile = useQuery({ queryKey: ["company", "profile", search], queryFn: () => getCompanyProfile(search) });
  const relationships = useQuery({ queryKey: ["company", "relationships"], queryFn: getCompanyRelationships });
  const prices = useQuery({ queryKey: ["company", "prices", search], queryFn: () => getPriceHistory(search) });
  const markers = useQuery({ queryKey: ["company", "markers", search], queryFn: () => getEventMarkers(search) });
  const events = useQuery({ queryKey: ["events"], queryFn: getEvents });

  const chartData = prices.data?.map((d) => ({ ...d, price: Math.round(d.price * 100) / 100 }));
  const companyEvents = events.data?.filter(
    (e) => e.ticker === profile.data?.ticker || e.relatedCompanies.some((r) => r.ticker === profile.data?.ticker)
  );
  const companyRelationships = relationships.data?.filter(
    (e) => e.source === profile.data?.ticker || e.target === profile.data?.ticker
  );

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Company Research</h1>
          <p className="text-sm text-muted-foreground mt-1">Deep-dive into company events and relationships</p>
        </div>

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
        {profile.isLoading ? (
          <CardSkeleton />
        ) : profile.isError ? (
          <ErrorState onRetry={() => profile.refetch()} />
        ) : profile.data ? (
          <div className="terminal-card p-5">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4 justify-between">
              <div>
                <div className="flex items-center gap-3">
                  <span className="font-mono text-lg font-bold text-primary">{profile.data.ticker}</span>
                  <h2 className="text-lg font-semibold text-foreground">{profile.data.name}</h2>
                </div>
                <p className="text-sm text-muted-foreground mt-1">{profile.data.sector} · {profile.data.industry}</p>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
                {[
                  { label: "Market Cap", value: profile.data.marketCap },
                  { label: "P/E", value: profile.data.pe.toString() },
                  { label: "Revenue", value: profile.data.revenue },
                  { label: "Employees", value: profile.data.employees },
                ].map((s) => (
                  <div key={s.label}>
                    <p className="text-xs text-muted-foreground">{s.label}</p>
                    <p className="font-mono text-sm font-semibold text-foreground">{s.value}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}

        {/* Price Chart */}
        {prices.isLoading ? (
          <ChartSkeleton />
        ) : chartData ? (
          <ChartCard title="Price Chart (90 Days)">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <XAxis dataKey="date" tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} tickFormatter={(v) => v.slice(5)} interval={14} axisLine={{ stroke: "hsl(222 30% 16%)" }} />
                <YAxis domain={["auto", "auto"]} tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} width={60} />
                <Tooltip contentStyle={{ backgroundColor: "hsl(222 44% 8%)", border: "1px solid hsl(222 30% 16%)", borderRadius: "8px", fontSize: "12px", color: "hsl(210 40% 92%)" }} />
                <Line type="monotone" dataKey="price" stroke="hsl(210 100% 56%)" strokeWidth={2} dot={false} />
                {markers.data?.map((m, i) => (
                  <ReferenceLine key={i} x={m.date} stroke={m.type === "positive" ? "hsl(152 69% 45%)" : "hsl(0 72% 55%)"} strokeDasharray="3 3"
                    label={{ value: m.label, position: "top", fill: "hsl(215 20% 55%)", fontSize: 9 }} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        ) : null}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Related Companies */}
          <div className="terminal-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Related Companies</h3>
            {relationships.isLoading ? (
              <ListSkeleton count={3} />
            ) : (
              <div className="space-y-2">
                {companyRelationships?.map((edge, i) => {
                  const related = edge.source === profile.data?.ticker ? edge.target : edge.source;
                  return (
                    <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-bold text-primary">{related}</span>
                        <span className="text-xs text-muted-foreground">{edge.relationship}</span>
                      </div>
                      <div className="w-20 h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full rounded-full bg-primary" style={{ width: `${edge.strength * 100}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Recent Events */}
          <div className="terminal-card p-5">
            <h3 className="text-sm font-semibold text-foreground mb-4">Recent Events</h3>
            {events.isLoading ? (
              <ListSkeleton count={3} />
            ) : (
              <div className="space-y-2">
                {companyEvents?.map((evt) => (
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
            )}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
