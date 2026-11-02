import { Alert, Box, Paper } from "@mui/material";
import { useParams } from "react-router-dom";

import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { ReceiptReviewForm } from "@/features/receipts/components/ReceiptReviewForm";
import { useReceiptFilePreview } from "@/features/receipts/hooks/useReceiptFilePreview";
import {
  useReceipt,
  useSubmitReceipt,
  useUpdateReceipt,
} from "@/features/receipts/hooks/useReceipts";
import type { ReceiptUpdateInput } from "@/features/receipts/types";

/** The review page: file preview beside a form prefilled from extraction, Save and Submit. */
export default function ReviewReceiptPage() {
  const params = useParams<{ receiptId: string }>();
  const receiptId = params.receiptId ? Number(params.receiptId) : undefined;

  const { data: receipt, isLoading, isError } = useReceipt(receiptId);
  const { url: previewUrl, isLoading: isPreviewLoading } = useReceiptFilePreview(receiptId);
  const updateMutation = useUpdateReceipt(receiptId ?? 0);
  const submitMutation = useSubmitReceipt();

  if (isLoading) {
    return <LoadingState label="Loading receipt…" />;
  }

  if (isError || !receipt) {
    return <Alert severity="error">Could not load this receipt.</Alert>;
  }

  const handleSave = (input: ReceiptUpdateInput): void => {
    updateMutation.mutate(input);
  };

  const handleSubmit = (): void => {
    submitMutation.mutate(receipt.id);
  };

  return (
    <Box>
      <PageHeader
        title="Review receipt"
        description="Confirm or correct the extracted fields, then submit for approval."
      />
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 4, mt: 3 }}>
        <Paper
          variant="outlined"
          sx={{ flex: "1 1 400px", p: 2, display: "flex", justifyContent: "center" }}
        >
          {isPreviewLoading && <LoadingState label="Loading preview…" />}
          {previewUrl && receipt.mimeType === "application/pdf" && (
            <Box
              component="iframe"
              src={previewUrl}
              title="Receipt preview"
              sx={{ width: "100%", height: 500, border: "none" }}
            />
          )}
          {previewUrl && receipt.mimeType !== "application/pdf" && (
            <Box
              component="img"
              src={previewUrl}
              alt={`Receipt file: ${receipt.originalFilename}`}
              sx={{ maxWidth: "100%", maxHeight: 500 }}
            />
          )}
        </Paper>
        <Paper variant="outlined" sx={{ flex: "1 1 400px", p: 3 }}>
          <ReceiptReviewForm
            receipt={receipt}
            onSave={handleSave}
            onSubmit={handleSubmit}
            isSaving={updateMutation.isPending}
            isSubmitting={submitMutation.isPending}
          />
          {updateMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Saved.
            </Alert>
          )}
          {submitMutation.isSuccess && (
            <Alert severity="success" sx={{ mt: 2 }}>
              Submitted for review.
            </Alert>
          )}
        </Paper>
      </Box>
    </Box>
  );
}
