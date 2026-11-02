import { format, parseISO } from "date-fns";

/** Format a number as currency, e.g. 12.5 -> "$12.50" (defaults to USD). */
export function formatCurrency(amount: number | null, currency: string | null = "USD"): string {
  if (amount === null) {
    return "—";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: currency ?? "USD",
  }).format(amount);
}

/** Format an ISO date string as "MMM d, yyyy", or a placeholder when absent. */
export function formatDate(isoDate: string | null): string {
  if (!isoDate) {
    return "—";
  }
  return format(parseISO(isoDate), "MMM d, yyyy");
}
