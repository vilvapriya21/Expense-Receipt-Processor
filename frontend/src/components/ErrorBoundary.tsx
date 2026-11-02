import { Alert, Box, Button, Typography } from "@mui/material";
import { Component, type ErrorInfo, type ReactNode } from "react";

/** Props for {@link ErrorBoundary}. */
export interface ErrorBoundaryProps {
  /** The subtree to guard against rendering errors. */
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

/** Catches rendering errors in its subtree and shows a fallback instead of a blank page. */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  public override state: ErrorBoundaryState = { error: null };

  public static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  public override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("Unhandled UI error", error, info);
  }

  private handleReload = (): void => {
    window.location.reload();
  };

  public override render(): ReactNode {
    if (this.state.error) {
      return (
        <Box
          sx={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: 2,
          }}
        >
          <Alert severity="error" variant="outlined" sx={{ maxWidth: 480 }}>
            <Typography gutterBottom>
              Something went wrong. You can try reloading the page.
            </Typography>
            <Button onClick={this.handleReload} variant="outlined" size="small" color="error">
              Reload
            </Button>
          </Alert>
        </Box>
      );
    }
    return this.props.children;
  }
}
