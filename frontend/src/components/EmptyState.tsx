import { Box, Typography } from "@mui/material";
import type { ReactNode } from "react";

/** Props for {@link EmptyState}. */
export interface EmptyStateProps {
  /** The main message describing what's missing. */
  message: string;
  /** Optional secondary line with more detail or next-step guidance. */
  hint?: string;
  /** Optional action, e.g. a button to resolve the empty state. */
  action?: ReactNode;
}

/** A centered placeholder for an empty list/table, replacing a bare line of text. */
export function EmptyState({ message, hint, action }: EmptyStateProps) {
  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        textAlign: "center",
        py: 6,
        px: 2,
        gap: 1,
      }}
    >
      <Typography variant="subtitle1">{message}</Typography>
      {hint && (
        <Typography variant="body2" color="text.secondary">
          {hint}
        </Typography>
      )}
      {action && <Box sx={{ mt: 1 }}>{action}</Box>}
    </Box>
  );
}
