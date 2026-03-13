export interface CompanyProfile {
  ticker: string;
  name: string;
  sector: string;
  industry: string;
  marketCap: string;
  pe: number;
  revenue: string;
  employees: string;
}

export interface CompanyRelationship {
  source: string;
  target: string;
  relationship: string;
  strength: number;
}
