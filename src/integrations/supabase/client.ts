import { createClient } from "@supabase/supabase-js";

const supabaseUrl = __SUPABASE_URL__.trim();
const supabasePublishableKey = __SUPABASE_PUBLISHABLE_KEY__.trim();

export const isSupabaseConfigured = Boolean(supabaseUrl && supabasePublishableKey);

export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl, supabasePublishableKey, {
      auth: {
        autoRefreshToken: false,
        persistSession: false,
      },
    })
  : null;

export function getSupabaseConfigurationIssue() {
  if (!supabaseUrl) {
    return "Missing Supabase project URL.";
  }

  if (!supabasePublishableKey) {
    return "Missing Supabase publishable key.";
  }

  return null;
}
