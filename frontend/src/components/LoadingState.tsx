import { Box, CircularProgress, Typography } from "@mui/material";

/** Props for {@link LoadingState}. */
export interface LoadingStateProps {
  /** Text shown beneath the spinner. */
  label?: string;
}

/** A centered spinner with an optional label, for a page or section that is loading. */
export function LoadingState({ label = "Loading…" }: LoadingStateProps) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", py: 6, gap: 1.5 }}>
      <CircularProgress size={32} />
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
    </Box>
  );
}
