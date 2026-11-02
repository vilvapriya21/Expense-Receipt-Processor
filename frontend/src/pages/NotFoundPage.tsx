import { Button } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";

import { EmptyState } from "@/components/EmptyState";

/** Shown for any route that doesn't match. */
export default function NotFoundPage() {
  return (
    <EmptyState
      message="Page not found"
      hint="The page you're looking for doesn't exist or has moved."
      action={
        <Button variant="contained" component={RouterLink} to="/">
          Go home
        </Button>
      }
    />
  );
}
