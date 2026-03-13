import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import Index from "./pages/Index.tsx";
import EventFeed from "./pages/EventFeed.tsx";
import Companies from "./pages/Companies.tsx";
import EventStudies from "./pages/EventStudies.tsx";
import ResearchJournal from "./pages/ResearchJournal.tsx";
import PaperTrades from "./pages/PaperTrades.tsx";
import SettingsPage from "./pages/Settings.tsx";
import NotFound from "./pages/NotFound.tsx";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
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
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
