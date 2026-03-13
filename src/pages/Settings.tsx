import { AppLayout } from "@/components/AppLayout";
import { useState } from "react";
import { Save, Plus, X } from "lucide-react";

interface Relationship {
  company: string;
  related: string;
  type: string;
}

export default function SettingsPage() {
  const [relationships, setRelationships] = useState<Relationship[]>([
    { company: "NVDA", related: "TSM", type: "Supplier" },
    { company: "NVDA", related: "AMD", type: "Competitor" },
    { company: "NVDA", related: "MSFT", type: "Customer" },
    { company: "AAPL", related: "QCOM", type: "Supplier" },
    { company: "TSLA", related: "RIVN", type: "Competitor" },
  ]);

  const [notifications, setNotifications] = useState({
    eventAlerts: true,
    dailyDigest: true,
    tradeSignals: false,
    weeklyReport: true,
  });

  const addRelationship = () => {
    setRelationships([...relationships, { company: "", related: "", type: "Supplier" }]);
  };

  const removeRelationship = (index: number) => {
    setRelationships(relationships.filter((_, i) => i !== index));
  };

  const updateRelationship = (index: number, field: keyof Relationship, value: string) => {
    const updated = [...relationships];
    updated[index] = { ...updated[index], [field]: value };
    setRelationships(updated);
  };

  return (
    <AppLayout>
      <div className="space-y-6 max-w-3xl">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Configure data sources, classifications, and preferences</p>
        </div>

        {/* Data Sources */}
        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Data Sources</h3>
          <div className="space-y-3">
            {[
              { name: "Financial News API", status: "Connected", enabled: true },
              { name: "SEC Filings (EDGAR)", status: "Connected", enabled: true },
              { name: "Social Sentiment Feed", status: "Not configured", enabled: false },
              { name: "Alternative Data Provider", status: "Not configured", enabled: false },
            ].map((source) => (
              <div key={source.name} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <div>
                  <p className="text-sm text-foreground">{source.name}</p>
                  <p className="text-xs text-muted-foreground">{source.status}</p>
                </div>
                <div
                  className={`w-10 h-5 rounded-full flex items-center cursor-pointer transition-colors ${
                    source.enabled ? "bg-primary justify-end" : "bg-muted justify-start"
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-foreground mx-0.5" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Event Classification */}
        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Event Classification</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {[
              "Product Launch", "Regulatory Approval", "Supply Disruption",
              "Capital Expenditure", "Legal/Regulatory", "Earnings",
              "M&A", "Management Change", "Partnership", "Macro Event",
            ].map((cat) => (
              <label key={cat} className="flex items-center gap-2 p-2 rounded-lg bg-muted/30 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded border-border accent-primary" />
                <span className="text-xs text-foreground">{cat}</span>
              </label>
            ))}
          </div>
        </div>

        {/* Relationship Mapping */}
        <div className="terminal-card p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">Relationship Mapping</h3>
            <button
              onClick={addRelationship}
              className="flex items-center gap-1 text-xs bg-primary/10 text-primary px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-colors"
            >
              <Plus className="h-3 w-3" /> Add
            </button>
          </div>
          <div className="space-y-2">
            {relationships.map((rel, i) => (
              <div key={i} className="flex items-center gap-2">
                <input
                  value={rel.company}
                  onChange={(e) => updateRelationship(i, "company", e.target.value.toUpperCase())}
                  placeholder="Company"
                  className="flex-1 bg-muted border border-border rounded-md px-2 py-1.5 text-xs text-foreground font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <span className="text-xs text-muted-foreground">→</span>
                <input
                  value={rel.related}
                  onChange={(e) => updateRelationship(i, "related", e.target.value.toUpperCase())}
                  placeholder="Related"
                  className="flex-1 bg-muted border border-border rounded-md px-2 py-1.5 text-xs text-foreground font-mono placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                />
                <select
                  value={rel.type}
                  onChange={(e) => updateRelationship(i, "type", e.target.value)}
                  className="bg-muted border border-border rounded-md px-2 py-1.5 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
                >
                  <option>Supplier</option>
                  <option>Competitor</option>
                  <option>Customer</option>
                  <option>Sector Peer</option>
                </select>
                <button
                  onClick={() => removeRelationship(i)}
                  className="text-muted-foreground hover:text-danger transition-colors p-1"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Notifications */}
        <div className="terminal-card p-5">
          <h3 className="text-sm font-semibold text-foreground mb-4">Notification Preferences</h3>
          <div className="space-y-3">
            {Object.entries(notifications).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                <span className="text-sm text-foreground capitalize">
                  {key.replace(/([A-Z])/g, " $1").trim()}
                </span>
                <div
                  onClick={() => setNotifications({ ...notifications, [key]: !value })}
                  className={`w-10 h-5 rounded-full flex items-center cursor-pointer transition-colors ${
                    value ? "bg-primary justify-end" : "bg-muted justify-start"
                  }`}
                >
                  <div className="w-4 h-4 rounded-full bg-foreground mx-0.5" />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Save */}
        <button className="flex items-center gap-2 bg-primary text-primary-foreground px-6 py-2.5 rounded-lg text-sm font-medium hover:bg-primary/90 transition-colors">
          <Save className="h-4 w-4" /> Save Settings
        </button>
      </div>
    </AppLayout>
  );
}
