import UploadFileIcon from "@mui/icons-material/UploadFile";
import ViewListIcon from "@mui/icons-material/ViewList";
import { Stack } from "@mui/material";

import { DashboardActionCard } from "@/components/DashboardActionCard";
import { PageHeader } from "@/components/PageHeader";
import { SummaryCard } from "@/features/summaries/components/SummaryCard";

/** The employee's landing page: their own summary, and quick links. */
export default function EmployeeDashboardPage() {
  return (
    <Stack spacing={3}>
      <PageHeader title="Dashboard" description="Your expense receipts, at a glance." />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <DashboardActionCard
          title="Upload a receipt"
          description="Add a JPG, PNG, or PDF and extract the expense details."
          to="/employee/upload"
          icon={<UploadFileIcon />}
        />
        <DashboardActionCard
          title="My receipts"
          description="Track submitted expenses and review their current status."
          to="/employee/receipts"
          icon={<ViewListIcon />}
          accent="secondary.main"
        />
      </Stack>
      <SummaryCard />
    </Stack>
  );
}
