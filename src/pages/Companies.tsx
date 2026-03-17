import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { AppLayout } from "@/components/AppLayout";
import { ChartCard } from "@/components/ChartCard";
import { CardSkeleton, ChartSkeleton, ListSkeleton } from "@/components/LoadingSkeletons";
import { ErrorState } from "@/components/StateDisplays";
import { RelationshipStudyTable } from "@/components/research/RelationshipStudyTable";
import { CompanySearch } from "@/components/trader/CompanySearch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { getCompanyProfile, getCompanyRelationships, getPriceHistory, getEventMarkers } from "@/services/companyService";
import { getEvents } from "@/services/eventService";
import { getCategorySummaryStudies } from "@/services/eventStudyStatisticsService";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

export default function Companies() {
  const [searchParams] = useSearchParams();
  const [search, setSearch] = useState((searchParams.get("search") || "NVDA").trim().toUpperCase());

  useEffect(() => {
    const nextSearch = (searchParams.get("search") || "NVDA").trim().toUpperCase();
    if (nextSearch && nextSearch !== search) {
      setSearch(nextSearch);
    }
  }, [search, searchParams]);

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
  const mostCommonCategory = useMemo(() => {
    const counts = new Map<string, number>();
    (companyEvents ?? []).forEach((event) => counts.set(event.category, (counts.get(event.category) ?? 0) + 1));
    return Array.from(counts.entries()).sort((left, right) => right[1] - left[1])[0]?.[0] ?? null;
  }, [companyEvents]);
  const studySummaryQuery = useQuery({
    queryKey: ["studies", "category-summary", mostCommonCategory ?? "none", profile.data?.ticker ?? search],
    queryFn: () => getCategorySummaryStudies(mostCommonCategory || ""),
    enabled: Boolean(mostCommonCategory),
  });
  const compactSummary = ["1D", "3D", "5D", "10D", "20D"].map((horizon) => studySummaryQuery.data?.find((row) => row.horizon === horizon));

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Company Research</h1>
          <p className="text-sm text-muted-foreground mt-1">Deep-dive into company events and relationships</p>
        </div>

        <div className="max-w-2xl">
          <CompanySearch onSearch={setSearch} initialQuery={search} />
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

        <Tabs defaultValue="overview" className="space-y-4">
          <TabsList className="grid w-full max-w-sm grid-cols-2">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="studies">Studies</TabsTrigger>
          </TabsList>
          <TabsContent value="overview">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
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
          </TabsContent>
          <TabsContent value="studies">
            <div className="space-y-4">
              <div className="terminal-card p-4">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold text-foreground">Study Summary</h3>
                    <p className="text-xs text-muted-foreground">
                      {mostCommonCategory ? `Most common category: ${mostCommonCategory}` : "No category summary available yet."}
                    </p>
                  </div>
                  <button
                    onClick={() => studySummaryQuery.refetch()}
                    className="rounded-md border border-border bg-muted/30 px-3 py-2 text-xs text-foreground hover:bg-muted/50"
                  >
                    Refresh Studies
                  </button>
                </div>
                <div className="grid grid-cols-5 gap-2">
                  {compactSummary.map((row, index) => (
                    <div key={["1D", "3D", "5D", "10D", "20D"][index]} className="rounded-md bg-muted/30 p-3 text-center">
                      <div className="text-[10px] text-muted-foreground">{["1D", "3D", "5D", "10D", "20D"][index]}</div>
                      <div className={`font-mono text-sm font-semibold ${!row || row.avgReturn >= 0 ? "text-success" : "text-danger"}`}>
                        {row ? `${row.avgReturn >= 0 ? "+" : ""}${row.avgReturn.toFixed(2)}%` : "—"}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <RelationshipStudyTable ticker={profile.data?.ticker || search} />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </AppLayout>
  );
}
