import { Chip } from "@mui/material";

import type { ReceiptStatus } from "../types";

/** Props for {@link StatusChip}. */
export interface StatusChipProps {
  /** The receipt status to render. */
  status: ReceiptStatus;
}

const COLOR_BY_STATUS: Record<
  ReceiptStatus,
  "default" | "info" | "warning" | "success" | "error"
> = {
  UPLOADED: "default",
  EXTRACTED: "info",
  SUBMITTED: "warning",
  APPROVED: "success",
  REJECTED: "error",
};

/** A small colored chip showing a receipt's lifecycle status. */
export function StatusChip({ status }: StatusChipProps) {
  return <Chip label={status} color={COLOR_BY_STATUS[status]} size="small" />;
}
