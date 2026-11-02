import CategoryIcon from "@mui/icons-material/Category";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import InsightsIcon from "@mui/icons-material/Insights";
import { Stack } from "@mui/material";

import { DashboardActionCard } from "@/components/DashboardActionCard";
import { PageHeader } from "@/components/PageHeader";

/** The admin's landing page: quick links into the receipts, categories, and summaries pages. */
export default function AdminDashboardPage() {
  return (
    <Stack spacing={3}>
      <PageHeader
        title="Admin"
        description="Review submitted receipts, manage categories, and track spend."
      />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2} flexWrap="wrap" useFlexGap>
        <DashboardActionCard
          title="Review receipts"
          description="Open submitted expenses and make approval decisions."
          to="/admin/receipts"
          icon={<FactCheckIcon />}
        />
        <DashboardActionCard
          title="Manage categories"
          description="Keep expense categories and smart-match keywords organized."
          to="/admin/categories"
          icon={<CategoryIcon />}
          accent="secondary.main"
        />
        <DashboardActionCard
          title="View summaries"
          description="Explore spend, tax, status, and employee-level trends."
          to="/admin/summaries"
          icon={<InsightsIcon />}
          accent="success.main"
        />
      </Stack>
    </Stack>
  );
}
