import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { AppLayout } from "@/components/AppLayout";
import { StatCard } from "@/components/StatCard";
import { ChartCard } from "@/components/ChartCard";
import { CardSkeleton, ChartSkeleton, TableSkeleton } from "@/components/LoadingSkeletons";
import { ErrorState } from "@/components/StateDisplays";
import { EvidenceSliceDrawer } from "@/components/research/EvidenceSliceDrawer";
import { getEventStudies, getReturnDistribution, getForwardCurve, getEventCategories, getTimeHorizons } from "@/services/eventService";
import { getEvents } from "@/services/eventService";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart,
  CartesianGrid, Cell, ReferenceLine,
} from "recharts";

export default function EventStudies() {
  const [searchParams] = useSearchParams();
  const initialCategory = searchParams.get("category") || "Product Launch";
  const initialTicker = (searchParams.get("ticker") || "").trim().toUpperCase();
  const [eventType, setEventType] = useState(initialCategory);
  const [horizon, setHorizon] = useState("5D");
  const [primaryTicker, setPrimaryTicker] = useState(initialTicker);
  const [relatedTicker, setRelatedTicker] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [drawerTicker, setDrawerTicker] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const studies = useQuery({ queryKey: ["events", "studies", eventType], queryFn: () => getEventStudies(eventType) });
  const distribution = useQuery({ queryKey: ["events", "distribution", eventType], queryFn: () => getReturnDistribution(eventType) });
  const forwardCurve = useQuery({ queryKey: ["events", "forward-curve", eventType], queryFn: () => getForwardCurve(eventType) });
  const categories = useQuery({ queryKey: ["events", "categories"], queryFn: getEventCategories });
  const horizons = useQuery({ queryKey: ["events", "horizons", eventType], queryFn: () => getTimeHorizons(eventType) });
  const events = useQuery({ queryKey: ["events"], queryFn: getEvents });

  const sortedDistribution = distribution.data?.slice().sort((a, b) => a.return - b.return);
  const selectedStudy = studies.data?.find((study) => study.horizon === horizon) || studies.data?.[0];
  const categoryTicker = events.data?.find((event) => event.category === eventType)?.ticker || null;

  useEffect(() => {
    if (categories.data?.length && !categories.data.includes(eventType)) {
      setEventType(categories.data[0]);
    }
  }, [categories.data, eventType]);

  useEffect(() => {
    if (categories.data?.includes(initialCategory)) {
      setEventType(initialCategory);
    }
    setPrimaryTicker(initialTicker);
  }, [categories.data, initialCategory, initialTicker]);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Event Study Explorer</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Research historical event outcomes and forward returns
            {initialTicker ? ` · focused on ${initialTicker}` : ""}
          </p>
        </div>

        {/* Filters */}
        <div className="terminal-card p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Event Type</label>
              <select value={eventType} onChange={(e) => setEventType(e.target.value)}
                className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-primary">
                {categories.data?.map((c) => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Primary Company</label>
              <input value={primaryTicker} onChange={(e) => setPrimaryTicker(e.target.value.toUpperCase())} placeholder="Any" className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Related Company</label>
              <input value={relatedTicker} onChange={(e) => setRelatedTicker(e.target.value.toUpperCase())} placeholder="Any" className="w-full bg-muted border border-border rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary font-mono" />
            </div>
            <div>
              <label className="text-xs text-muted-foreground block mb-1.5">Time Horizon</label>
              <div className="flex gap-1">
                {(horizons.data ?? ["1D", "3D", "5D", "10D", "20D"]).map((h) => (
                  <button key={h} onClick={() => setHorizon(h)}
                    className={`flex-1 text-xs py-2 rounded-md transition-colors font-mono ${horizon === h ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground hover:bg-accent"}`}>
                    {h}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Results Summary */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {studies.isLoading ? (
            <><CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton /></>
          ) : studies.isError ? (
            <div className="col-span-4"><ErrorState onRetry={() => studies.refetch()} /></div>
          ) : (
            <>
              <StatCard label="Avg Forward Return" value={`${selectedStudy && selectedStudy.avgReturn >= 0 ? "+" : ""}${(selectedStudy?.avgReturn ?? 0).toFixed(2)}%`} color={(selectedStudy?.avgReturn ?? 0) >= 0 ? "text-success" : "text-danger"} />
              <StatCard label="Win Rate" value={`${(selectedStudy?.winRate ?? 0).toFixed(0)}%`} color="text-primary" />
              <StatCard label="Sample Size" value={`${selectedStudy?.sampleSize ?? 0}`} />
              <StatCard label="Median Return" value={`${selectedStudy && (selectedStudy.medianReturn ?? 0) >= 0 ? "+" : ""}${(selectedStudy?.medianReturn ?? 0).toFixed(2)}%`} color={(selectedStudy?.medianReturn ?? 0) >= 0 ? "text-success" : "text-danger"} />
            </>
          )}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {forwardCurve.isLoading ? (
            <ChartSkeleton />
          ) : (
            <ChartCard title="Forward Performance Curve">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={forwardCurve.data}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 30% 16%)" />
                  <XAxis dataKey="horizon" tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} />
                  <YAxis tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} tickFormatter={(v) => `${v.toFixed(1)}%`} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(222 44% 8%)", border: "1px solid hsl(222 30% 16%)", borderRadius: "8px", fontSize: "12px", color: "hsl(210 40% 92%)" }} formatter={(v: number) => [`${v.toFixed(2)}%`]} labelFormatter={(value) => `Horizon ${value}`} />
                  <Area type="monotone" dataKey="upperBound" stroke="none" fill="hsl(210 100% 56% / 0.08)" />
                  <Area type="monotone" dataKey="lowerBound" stroke="none" fill="hsl(210 100% 56% / 0.08)" />
                  <Line type="monotone" dataKey="avgReturn" stroke="hsl(210 100% 56%)" strokeWidth={2} dot={false} />
                  <ReferenceLine y={0} stroke="hsl(222 30% 20%)" />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          )}

          {distribution.isLoading ? (
            <ChartSkeleton />
          ) : (
            <ChartCard title="Return Distribution">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={sortedDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(222 30% 16%)" />
                  <XAxis dataKey="return" tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} tickFormatter={(v) => `${v.toFixed(1)}%`} />
                  <YAxis tick={{ fill: "hsl(215 20% 55%)", fontSize: 10 }} axisLine={{ stroke: "hsl(222 30% 16%)" }} allowDecimals={false} />
                  <Tooltip contentStyle={{ backgroundColor: "hsl(222 44% 8%)", border: "1px solid hsl(222 30% 16%)", borderRadius: "8px", fontSize: "12px", color: "hsl(210 40% 92%)" }} formatter={(v: number) => [`${v}`, "Study count"]} labelFormatter={(value) => `Bucket ${Number(value).toFixed(1)}%`} />
                  <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                    {sortedDistribution?.map((entry, i) => (
                      <Cell key={i} fill={entry.return >= 0 ? "hsl(152 69% 45%)" : "hsl(0 72% 55%)"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          )}
        </div>

        {/* Results Table */}
        {studies.isLoading ? (
          <TableSkeleton />
        ) : (
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
                  {studies.data?.map((r) => (
                    <tr
                      key={r.horizon}
                      className="border-b border-border/50 hover:bg-muted/20 cursor-pointer"
                      onClick={() => {
                        const targetTicker = primaryTicker || relatedTicker || categoryTicker || null;
                        setSelectedCategory(eventType);
                        setDrawerTicker(targetTicker);
                        setDrawerOpen(true);
                      }}
                    >
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
        )}

        {selectedCategory ? (
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <button
              className="rounded-md border border-border bg-muted/30 px-2 py-1 text-foreground hover:bg-muted/50"
              onClick={() => {
                setSelectedCategory(null);
                setDrawerTicker(null);
                setDrawerOpen(false);
              }}
            >
              Back
            </button>
            <span>Event Studies &gt; {selectedCategory}</span>
          </div>
        ) : null}

        <EvidenceSliceDrawer ticker={drawerTicker} category={selectedCategory} open={drawerOpen} onOpenChange={setDrawerOpen} />
      </div>
    </AppLayout>
  );
}
