import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
import { Box, Card, CardActionArea, Stack, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { Link as RouterLink } from "react-router-dom";

export interface DashboardActionCardProps {
  title: string;
  description: string;
  to: string;
  icon: ReactNode;
  accent?: string;
}

/** A prominent, reusable dashboard shortcut for a primary workflow. */
export function DashboardActionCard({
  title,
  description,
  to,
  icon,
  accent = "primary.main",
}: DashboardActionCardProps) {
  return (
    <Card sx={{ flex: "1 1 240px", overflow: "hidden" }}>
      <CardActionArea component={RouterLink} to={to} sx={{ height: "100%", p: 2.5 }}>
        <Stack direction="row" spacing={2} alignItems="flex-start">
          <Box
            sx={{
              display: "grid",
              placeItems: "center",
              width: 46,
              height: 46,
              borderRadius: 3,
              bgcolor: accent,
              color: "common.white",
              flexShrink: 0,
            }}
          >
            {icon}
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="subtitle1">{title}</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
              {description}
            </Typography>
          </Box>
          <ArrowForwardIcon sx={{ color: "text.disabled", mt: 0.5 }} />
        </Stack>
      </CardActionArea>
    </Card>
  );
}
