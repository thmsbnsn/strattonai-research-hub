import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppLayout } from "@/components/AppLayout";
import { EventCard } from "@/components/EventCard";
import { ListSkeleton } from "@/components/LoadingSkeletons";
import { ErrorState, EmptyState } from "@/components/StateDisplays";
import { getEvents } from "@/services/eventService";

export default function EventFeed() {
  const [filter, setFilter] = useState("All");
  const { data: events, isLoading, isError, refetch } = useQuery({ queryKey: ["events"], queryFn: getEvents });

  const categories = ["All", ...new Set(events?.map((e) => e.category) ?? [])];
  const filtered = filter === "All" ? events : events?.filter((e) => e.category === filter);

  return (
    <AppLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Event Feed</h1>
          <p className="text-sm text-muted-foreground mt-1">Real-time detected market events</p>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat)}
              className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
                filter === cat
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Event List */}
        {isLoading ? (
          <ListSkeleton count={4} />
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : !filtered?.length ? (
          <EmptyState title="No events" description="No events match the current filter." />
        ) : (
          <div className="space-y-3">
            {filtered.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
