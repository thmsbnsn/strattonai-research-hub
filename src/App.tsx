import { lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";

const Index = lazy(() => import("./pages/Index"));
const EventFeed = lazy(() => import("./pages/EventFeed"));
const Companies = lazy(() => import("./pages/Companies"));
const EventStudies = lazy(() => import("./pages/EventStudies"));
const ResearchJournal = lazy(() => import("./pages/ResearchJournal"));
const PaperTrades = lazy(() => import("./pages/PaperTrades"));
const SettingsPage = lazy(() => import("./pages/Settings"));
const NotFound = lazy(() => import("./pages/NotFound"));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 2,
    },
  },
});

function PageLoader() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="animate-pulse text-muted-foreground text-sm">Loading…</div>
    </div>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/events" element={<EventFeed />} />
            <Route path="/companies" element={<Companies />} />
            <Route path="/studies" element={<EventStudies />} />
            <Route path="/journal" element={<ResearchJournal />} />
            <Route path="/trades" element={<PaperTrades />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
