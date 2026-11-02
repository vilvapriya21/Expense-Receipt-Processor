import MenuIcon from "@mui/icons-material/Menu";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Container,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useState } from "react";
import { Link as RouterLink, Outlet, useLocation } from "react-router-dom";

import { useAuthStore } from "@/features/auth/authStore";

interface NavLink {
  to: string;
  label: string;
}

const EMPLOYEE_LINKS: NavLink[] = [
  { to: "/employee", label: "Dashboard" },
  { to: "/employee/upload", label: "Upload" },
  { to: "/employee/receipts", label: "My Receipts" },
];

const ADMIN_LINKS: NavLink[] = [
  { to: "/admin", label: "Admin" },
  { to: "/admin/receipts", label: "Receipts" },
  { to: "/admin/categories", label: "Categories" },
  { to: "/admin/summaries", label: "Summaries" },
];

/** Shared page chrome: a top app bar with role-based navigation, and the routed content. */
export function Layout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [isNavOpen, setIsNavOpen] = useState(false);

  const user = useAuthStore((state) => state.user);
  const logout = useAuthStore((state) => state.logout);
  const location = useLocation();

  const links =
    user?.role === "ADMIN" ? ADMIN_LINKS : user?.role === "EMPLOYEE" ? EMPLOYEE_LINKS : [];

  const closeNav = (): void => setIsNavOpen(false);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="sticky">
        <Toolbar sx={{ gap: 1.5, minHeight: { xs: 64, md: 72 } }}>
          {isMobile && links.length > 0 && (
            <IconButton
              color="primary"
              edge="start"
              aria-label="Open navigation menu"
              onClick={() => setIsNavOpen(true)}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Box
            sx={{
              width: 38,
              height: 38,
              display: { xs: "none", sm: "grid" },
              placeItems: "center",
              borderRadius: 2.5,
              color: "common.white",
              background: "linear-gradient(135deg, #4f46e5, #0891b2)",
              boxShadow: "0 8px 18px rgba(79, 70, 229, 0.25)",
            }}
          >
            <ReceiptLongIcon fontSize="small" />
          </Box>
          <Box sx={{ flexGrow: 1 }}>
            <Typography variant="subtitle1" component="div" sx={{ lineHeight: 1.15 }}>
              ExpenseFlow
            </Typography>
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{ display: { xs: "none", sm: "block" } }}
            >
              Receipt management
            </Typography>
          </Box>
          {!isMobile &&
            links.map((link) => (
              <Button
                key={link.to}
                color={location.pathname === link.to ? "primary" : "inherit"}
                component={RouterLink}
                to={link.to}
                sx={{
                  borderRadius: 2.5,
                  bgcolor: location.pathname === link.to ? "primary.main" : "transparent",
                  color: location.pathname === link.to ? "common.white" : "text.secondary",
                  "&:hover": {
                    bgcolor: location.pathname === link.to ? "primary.dark" : "action.hover",
                  },
                }}
              >
                {link.label}
              </Button>
            ))}
          {user && (
            <>
              <Tooltip title={user.fullName ?? user.email}>
                <Avatar sx={{ width: 34, height: 34, bgcolor: "primary.main", fontSize: 14 }}>
                  {(user.fullName ?? user.email).slice(0, 1).toUpperCase()}
                </Avatar>
              </Tooltip>
              <Button color="inherit" onClick={logout} sx={{ color: "text.secondary", px: 1.5 }}>
                Log out
              </Button>
            </>
          )}
        </Toolbar>
      </AppBar>
      <Drawer anchor="left" open={isNavOpen} onClose={closeNav}>
        <Box sx={{ width: 280, p: 2 }} role="presentation" onClick={closeNav}>
          <Typography variant="h6" sx={{ px: 2, py: 2 }}>
            ExpenseFlow
          </Typography>
          <List sx={{ display: "grid", gap: 0.5 }}>
            {links.map((link) => (
              <ListItemButton
                key={link.to}
                component={RouterLink}
                to={link.to}
                selected={location.pathname === link.to}
              >
                <ListItemText primary={link.label} />
              </ListItemButton>
            ))}
          </List>
        </Box>
      </Drawer>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          bgcolor: "background.default",
          backgroundImage:
            "radial-gradient(circle at 90% 0%, rgba(129, 140, 248, 0.09), transparent 28%)",
        }}
      >
        <Container maxWidth="lg" sx={{ py: { xs: 3, md: 5 } }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
}
