import {
  Alert,
  Box,
  Card,
  CardContent,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { useAdminSummary } from "@/features/summaries/hooks/useAdminSummary";
import type { SummaryDateRange } from "@/features/summaries/types";
import { formatCurrency } from "@/utils/formatters";

function TotalCard({ label, value }: { label: string; value: string }) {
  return (
    <Card sx={{ minWidth: 180, flex: "1 1 180px" }}>
      <CardContent>
        <Typography variant="body2" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="h5">{value}</Typography>
      </CardContent>
    </Card>
  );
}

/** The admin's finance summaries page: date-range filter, totals, and breakdown tables. */
export default function AdminSummariesPage() {
  const [range, setRange] = useState<SummaryDateRange>({});
  const { data: summary, isLoading, isError } = useAdminSummary(range);

  const totalApproved = summary
    ? Object.entries(summary.countsByStatus).reduce((sum, [, count]) => sum + count, 0)
    : 0;
  const totalSpend = summary
    ? summary.byCategory.reduce((sum, item) => sum + item.totalAmount, 0)
    : 0;

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Summaries"
        description="Spend and status breakdowns across all receipts."
      />
      <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
        <TextField
          label="From"
          id="summary-date-from"
          type="date"
          slotProps={{ inputLabel: { shrink: true } }}
          value={range.dateFrom ?? ""}
          onChange={(event) =>
            setRange((prev) => ({ ...prev, dateFrom: event.target.value || undefined }))
          }
        />
        <TextField
          label="To"
          id="summary-date-to"
          type="date"
          slotProps={{ inputLabel: { shrink: true } }}
          value={range.dateTo ?? ""}
          onChange={(event) =>
            setRange((prev) => ({ ...prev, dateTo: event.target.value || undefined }))
          }
        />
      </Stack>

      {isLoading && <LoadingState label="Loading summaries…" />}
      {isError && <Alert severity="error">Could not load summaries.</Alert>}

      {summary && (
        <>
          <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
            <TotalCard label="Total approved spend" value={formatCurrency(totalSpend)} />
            <TotalCard label="Total tax" value={formatCurrency(summary.taxTotal)} />
            <TotalCard label="Receipts (all statuses)" value={String(totalApproved)} />
          </Stack>

          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Counts by status
            </Typography>
            <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap>
              {Object.entries(summary.countsByStatus).map(([status, count]) => (
                <TotalCard key={status} label={status} value={String(count)} />
              ))}
            </Stack>
          </Box>

          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Spend by category
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table aria-label="Spend by category" size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Category</TableCell>
                    <TableCell>Total</TableCell>
                    <TableCell>Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {summary.byCategory.map((item) => (
                    <TableRow key={item.categoryId ?? "uncategorized"} hover>
                      <TableCell>{item.categoryName ?? "Uncategorized"}</TableCell>
                      <TableCell>{formatCurrency(item.totalAmount)}</TableCell>
                      <TableCell>{item.count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Spend by month
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table aria-label="Spend by month" size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Month</TableCell>
                    <TableCell>Total</TableCell>
                    <TableCell>Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {summary.byMonth.map((item) => (
                    <TableRow key={item.month} hover>
                      <TableCell>{item.month}</TableCell>
                      <TableCell>{formatCurrency(item.totalAmount)}</TableCell>
                      <TableCell>{item.count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>

          <Box>
            <Typography variant="subtitle1" gutterBottom>
              Spend by employee
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table aria-label="Spend by employee" size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Employee</TableCell>
                    <TableCell>Total</TableCell>
                    <TableCell>Count</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {summary.byEmployee.map((item) => (
                    <TableRow key={item.employeeId} hover>
                      <TableCell>{item.employeeName}</TableCell>
                      <TableCell>{formatCurrency(item.totalAmount)}</TableCell>
                      <TableCell>{item.count}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Box>
        </>
      )}
    </Stack>
  );
}
