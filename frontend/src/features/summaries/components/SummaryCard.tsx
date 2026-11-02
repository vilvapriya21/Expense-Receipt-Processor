import { Box, Card, CardContent, Skeleton, Typography } from "@mui/material";

import { useReceiptSummary } from "@/features/receipts/hooks/useReceipts";
import { formatCurrency } from "@/utils/formatters";

/** A dashboard card showing the employee's own receipt totals. */
export function SummaryCard() {
  const { data: summary, isLoading, isError } = useReceiptSummary();

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Skeleton variant="text" width={160} />
          <Skeleton variant="rectangular" height={80} sx={{ mt: 1 }} />
        </CardContent>
      </Card>
    );
  }

  if (isError || !summary) {
    return (
      <Card>
        <CardContent>
          <Typography color="error">Could not load your summary.</Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" component="h2" gutterBottom>
          Your expense summary
        </Typography>
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          <Box>
            <Typography variant="body2" color="text.secondary">
              Approved total
            </Typography>
            <Typography variant="h5">{formatCurrency(summary.approvedTotalAmount)}</Typography>
          </Box>
          <Box>
            <Typography variant="body2" color="text.secondary">
              By status
            </Typography>
            {Object.entries(summary.countsByStatus).map(([status, count]) => (
              <Typography key={status} variant="body2">
                {status}: {count}
              </Typography>
            ))}
          </Box>
        </Box>
        {summary.approvedByCategory.length > 0 && (
          <Box sx={{ mt: 2 }}>
            <Typography variant="body2" color="text.secondary">
              By category
            </Typography>
            {summary.approvedByCategory.map((item) => (
              <Typography key={item.categoryId ?? "uncategorized"} variant="body2">
                {item.categoryName ?? "Uncategorized"}: {formatCurrency(item.totalAmount)} (
                {item.count})
              </Typography>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
