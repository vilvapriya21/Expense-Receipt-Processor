import { Box, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";

/** Props for {@link PageHeader}. */
export interface PageHeaderProps {
  /** The page's main heading. */
  title: string;
  /** Optional supporting text shown under the title. */
  description?: string;
  /** Optional trailing content, e.g. a primary action button. */
  actions?: ReactNode;
}

/** A consistent page-level heading row: title, optional description, optional actions. */
export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <Stack
      direction={{ xs: "column", sm: "row" }}
      spacing={2}
      sx={{ alignItems: { xs: "flex-start", sm: "center" }, justifyContent: "space-between" }}
    >
      <Box>
        <Typography variant="h4" component="h1" sx={{ color: "text.primary" }}>
          {title}
        </Typography>
        {description && (
          <Typography variant="body1" color="text.secondary" sx={{ mt: 0.75 }}>
            {description}
          </Typography>
        )}
      </Box>
      {actions && <Box>{actions}</Box>}
    </Stack>
  );
}
