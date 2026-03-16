export type { CompanyProfile } from "@/models";

export interface CompanyRelationship {
  source: string;
  target: string;
  relationship: string;
  strength: number;
}
