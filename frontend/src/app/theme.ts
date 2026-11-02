import { createTheme } from "@mui/material/styles";

/** The app's MUI theme: palette, typography, shape, and shared component defaults. */
export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#4f46e5", dark: "#3730a3", light: "#818cf8" },
    secondary: { main: "#0891b2" },
    success: { main: "#059669" },
    warning: { main: "#d97706" },
    background: { default: "#f6f7fb", paper: "#ffffff" },
    text: { primary: "#172033", secondary: "#64748b" },
    divider: "#e7eaf1",
  },
  shape: {
    borderRadius: 14,
  },
  typography: {
    fontFamily: 'Inter, "Segoe UI", system-ui, -apple-system, sans-serif',
    h4: { fontWeight: 750, letterSpacing: "-0.035em" },
    h5: { fontWeight: 700, letterSpacing: "-0.025em" },
    h6: { fontWeight: 700, letterSpacing: "-0.015em" },
    subtitle1: { fontWeight: 600 },
    subtitle2: { fontWeight: 600 },
    button: { fontWeight: 650 },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: { backgroundColor: "#f6f7fb" },
        "*::selection": { backgroundColor: "#c7d2fe" },
      },
    },
    MuiAppBar: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          backgroundColor: "rgba(255, 255, 255, 0.92)",
          color: "#172033",
          borderBottom: "1px solid #e7eaf1",
          backdropFilter: "blur(14px)",
        },
      },
    },
    MuiPaper: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: { backgroundImage: "none" },
        elevation0: { border: "1px solid", borderColor: "#e7eaf1" },
      },
    },
    MuiCard: {
      defaultProps: { elevation: 0 },
      styleOverrides: {
        root: {
          border: "1px solid #e7eaf1",
          boxShadow: "0 10px 30px rgba(23, 32, 51, 0.06)",
        },
      },
    },
    MuiButton: {
      defaultProps: { disableElevation: true },
      styleOverrides: {
        root: { textTransform: "none", borderRadius: 10, minHeight: 40, paddingInline: 18 },
        contained: { boxShadow: "0 8px 18px rgba(79, 70, 229, 0.2)" },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600 },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: { fontWeight: 700, color: "#475569", backgroundColor: "#f8fafc" },
        root: { borderColor: "#eef0f5" },
      },
    },
    MuiTextField: { defaultProps: { size: "small" } },
    MuiAlert: { styleOverrides: { root: { borderRadius: 12 } } },
  },
});
