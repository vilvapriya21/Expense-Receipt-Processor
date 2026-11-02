import { useQuery } from "@tanstack/react-query";

import { summaryService } from "../services/summaryService";
import type { SummaryDateRange } from "../types";

/**
 * Fetches finance-wide receipt totals for an optional date range (admin-only).
 *
 * @param range - The optional date-from/date-to filter.
 * @returns The TanStack Query result wrapping the admin summary.
 */
export function useAdminSummary(range: SummaryDateRange) {
  return useQuery({
    queryKey: ["admin-summary", range],
    queryFn: () => summaryService.getAdminSummary(range),
  });
}
