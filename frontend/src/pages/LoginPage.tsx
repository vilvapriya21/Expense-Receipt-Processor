import { zodResolver } from "@hookform/resolvers/zod";
import ReceiptLongIcon from "@mui/icons-material/ReceiptLong";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import { Alert, Avatar, Box, Button, Paper, Stack, TextField, Typography } from "@mui/material";
import { useEffect } from "react";
import { Controller, useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";

import { useAuthStore } from "@/features/auth/authStore";
import { useLogin } from "@/features/auth/hooks/useAuth";

const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

/** The sign-in page: an email/password form backed by the real login endpoint. */
export default function LoginPage() {
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const loginMutation = useLogin();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  useEffect(() => {
    if (user) {
      navigate(user.role === "ADMIN" ? "/admin" : "/employee", { replace: true });
    }
  }, [user, navigate]);

  const onSubmit = handleSubmit((values) => {
    loginMutation.mutate(values);
  });

  return (
    <Box
      sx={{
        minHeight: "100vh",
        display: "grid",
        gridTemplateColumns: { xs: "1fr", md: "minmax(420px, 1.05fr) minmax(420px, 0.95fr)" },
        alignItems: "center",
        background: "linear-gradient(145deg, #eef2ff 0%, #f8fafc 48%, #ecfeff 100%)",
        p: { xs: 2, md: 3 },
      }}
    >
      <Box
        sx={{
          display: { xs: "none", md: "flex" },
          minHeight: "calc(100vh - 48px)",
          flexDirection: "column",
          justifyContent: "space-between",
          p: 7,
          borderRadius: 5,
          color: "common.white",
          background: "linear-gradient(145deg, #312e81 0%, #4f46e5 55%, #0891b2 120%)",
          position: "relative",
          overflow: "hidden",
          "&::after": {
            content: '""',
            position: "absolute",
            width: 360,
            height: 360,
            borderRadius: "50%",
            right: -120,
            bottom: -140,
            background: "rgba(255,255,255,0.1)",
          },
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1.5}>
          <Avatar sx={{ bgcolor: "rgba(255,255,255,0.16)" }}>
            <ReceiptLongIcon />
          </Avatar>
          <Typography variant="h6">ExpenseFlow</Typography>
        </Stack>
        <Box sx={{ maxWidth: 560, zIndex: 1 }}>
          <Typography variant="h3" sx={{ fontWeight: 750, letterSpacing: "-0.04em", mb: 2 }}>
            Expenses, captured and cleared faster.
          </Typography>
          <Typography sx={{ color: "rgba(255,255,255,0.78)", fontSize: 18, mb: 4 }}>
            Turn receipts into organized, review-ready expenses with one streamlined workspace.
          </Typography>
          <Stack spacing={1.5}>
            {[
              "Smart receipt extraction",
              "Simple approval workflows",
              "Clear spend visibility",
            ].map((item) => (
              <Stack key={item} direction="row" spacing={1.25} alignItems="center">
                <CheckCircleOutlineIcon fontSize="small" />
                <Typography>{item}</Typography>
              </Stack>
            ))}
          </Stack>
        </Box>
        <Typography variant="caption" sx={{ color: "rgba(255,255,255,0.65)" }}>
          Secure expense management for modern teams
        </Typography>
      </Box>
      <Paper
        sx={{
          p: { xs: 3, sm: 5 },
          maxWidth: 460,
          width: "100%",
          justifySelf: "center",
          borderRadius: 4,
          boxShadow: "0 24px 70px rgba(23, 32, 51, 0.12)",
        }}
        component="form"
        onSubmit={onSubmit}
      >
        <Box sx={{ mb: 3 }}>
          <Avatar sx={{ bgcolor: "primary.main", mb: 2, display: { md: "none" } }}>
            <ReceiptLongIcon />
          </Avatar>
          <Typography variant="h4" component="h1">
            Welcome back
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1 }}>
            Sign in to manage your expense receipts.
          </Typography>
        </Box>
        {loginMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Incorrect email or password.
          </Alert>
        )}
        <Controller
          name="email"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Email"
              type="email"
              fullWidth
              margin="normal"
              autoComplete="username"
              error={!!errors.email}
              helperText={errors.email?.message}
            />
          )}
        />
        <Controller
          name="password"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Password"
              type="password"
              fullWidth
              margin="normal"
              autoComplete="current-password"
              error={!!errors.password}
              helperText={errors.password?.message}
            />
          )}
        />
        <Button
          type="submit"
          variant="contained"
          fullWidth
          sx={{ mt: 2.5, minHeight: 48 }}
          disabled={loginMutation.isPending}
        >
          {loginMutation.isPending ? "Signing in..." : "Sign in"}
        </Button>
      </Paper>
    </Box>
  );
}
