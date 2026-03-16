import { mockHandler } from "@/api/mockServer";
import { getSupabaseConfigurationIssue, isSupabaseConfigured, supabase } from "@/integrations/supabase/client";
import { shouldUseSupabaseLiveData } from "./settingsService";

type SupabaseErrorLike = {
  code?: string;
  details?: string;
  hint?: string;
  message?: string;
};

type SupabaseQueryResult<Row> = {
  data: Row[] | null;
  error: SupabaseErrorLike | null;
};

type FallbackAwareQueryOptions<Row, Result> = {
  resource: string;
  table: string;
  mockEndpoint: string;
  execute: () => Promise<SupabaseQueryResult<Row>>;
  transform?: (rows: Row[]) => Result | Promise<Result>;
};

export type DataSourceStatus = "connected" | "partial" | "fallback" | "error";

export interface DataSourceProbe {
  table: string;
  status: DataSourceStatus;
  detail: string;
}

const missingTableCodes = new Set(["42P01", "PGRST116", "PGRST205"]);
const missingTablePatterns = [
  /does not exist/i,
  /could not find the table/i,
  /relation .* does not exist/i,
];

function logDev(resource: string, message: string, context?: unknown) {
  if (!import.meta.env.DEV) {
    return;
  }

  if (context === undefined) {
    console.debug(`[${resource}] ${message}`);
    return;
  }

  console.debug(`[${resource}] ${message}`, context);
}

function normalizeErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === "string") {
    return error;
  }

  if (error && typeof error === "object" && "message" in error) {
    return String(error.message);
  }

  return "Unknown error";
}

export function isMissingTableError(error: SupabaseErrorLike | null | undefined) {
  if (!error) {
    return false;
  }

  if (error.code && missingTableCodes.has(error.code)) {
    return true;
  }

  const combinedMessage = [error.message, error.details, error.hint].filter(Boolean).join(" ");
  return missingTablePatterns.some((pattern) => pattern.test(combinedMessage));
}

export async function getMockFallback<T>(endpoint: string) {
  return mockHandler<T>(endpoint, { method: "GET" });
}

export async function fetchSupabaseWithFallback<Row, Result = Row[]>(
  options: FallbackAwareQueryOptions<Row, Result>
): Promise<Result> {
  const { resource, table, mockEndpoint, execute, transform } = options;

  if (!shouldUseSupabaseLiveData()) {
    logDev(resource, 'Using mock fallback because "Supabase Event Store" is disabled in settings.');
    return getMockFallback<Result>(mockEndpoint);
  }

  if (!isSupabaseConfigured || !supabase) {
    logDev(resource, `Using mock fallback because Supabase is not configured. ${getSupabaseConfigurationIssue() ?? ""}`.trim());
    return getMockFallback<Result>(mockEndpoint);
  }

  try {
    const { data, error } = await execute();

    if (error) {
      if (isMissingTableError(error)) {
        logDev(resource, `Using mock fallback because table "${table}" is missing.`, error);
      } else {
        console.error(`[${resource}] Supabase fetch failed; using mock fallback.`, error);
      }

      return getMockFallback<Result>(mockEndpoint);
    }

    if (!data || data.length === 0) {
      logDev(resource, `Using mock fallback because table "${table}" returned no rows.`);
      return getMockFallback<Result>(mockEndpoint);
    }

    logDev(resource, `Loaded ${data.length} row(s) from "${table}".`);
    return transform ? await transform(data) : (data as Result);
  } catch (error) {
    console.error(`[${resource}] Supabase request crashed; using mock fallback.`, error);
    return getMockFallback<Result>(mockEndpoint);
  }
}

export async function fetchOptionalSupabaseRows<Row>(options: {
  resource: string;
  table: string;
  execute: () => Promise<SupabaseQueryResult<Row>>;
}) {
  const { resource, table, execute } = options;

  if (!shouldUseSupabaseLiveData()) {
    logDev(resource, `Optional Supabase fetch for "${table}" skipped because live reads are disabled in settings.`);
    return [] as Row[];
  }

  if (!isSupabaseConfigured || !supabase) {
    return [] as Row[];
  }

  try {
    const { data, error } = await execute();

    if (error) {
      if (!isMissingTableError(error)) {
        console.error(`[${resource}] Optional Supabase fetch failed; continuing without "${table}".`, error);
      } else {
        logDev(resource, `Optional table "${table}" is missing; continuing without it.`);
      }

      return [] as Row[];
    }

    return data ?? [];
  } catch (error) {
    console.error(`[${resource}] Optional Supabase fetch crashed; continuing without "${table}".`, error);
    return [] as Row[];
  }
}

export async function probeSupabaseTable(table: string) {
  if (!shouldUseSupabaseLiveData()) {
    return {
      table,
      status: "fallback",
      detail: 'Live Supabase reads are disabled in Settings.',
    } satisfies DataSourceProbe;
  }

  if (!isSupabaseConfigured || !supabase) {
    return {
      table,
      status: "fallback",
      detail: getSupabaseConfigurationIssue() ?? "Supabase is not configured.",
    } satisfies DataSourceProbe;
  }

  try {
    const { count, error } = await supabase
      .from(table)
      .select("id", { count: "exact", head: true });

    if (error) {
      if (isMissingTableError(error)) {
        return {
          table,
          status: "fallback",
          detail: `Table "${table}" is missing.`,
        } satisfies DataSourceProbe;
      }

      return {
        table,
        status: "error",
        detail: `Table "${table}" failed: ${normalizeErrorMessage(error)}`,
      } satisfies DataSourceProbe;
    }

    if (!count) {
      return {
        table,
        status: "fallback",
        detail: `Table "${table}" is empty.`,
      } satisfies DataSourceProbe;
    }

    return {
      table,
      status: "connected",
      detail: `Table "${table}" is reachable with ${count} row(s).`,
    } satisfies DataSourceProbe;
  } catch (error) {
    return {
      table,
      status: "error",
      detail: `Table "${table}" failed: ${normalizeErrorMessage(error)}`,
    } satisfies DataSourceProbe;
  }
}
