import CloseIcon from "@mui/icons-material/Close";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  Drawer,
  IconButton,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useState } from "react";

import { useReceiptFilePreview } from "@/features/receipts/hooks/useReceiptFilePreview";
import { formatCurrency, formatDate } from "@/utils/formatters";

import type { Receipt } from "../types";
import { StatusChip } from "./StatusChip";

/** Props for {@link ReceiptDetailDrawer}. */
export interface ReceiptDetailDrawerProps {
  /** The receipt to show, or null when the drawer is closed. */
  receipt: Receipt | null;
  /** Called when the drawer should close. */
  onClose: () => void;
  /** Called to approve the open receipt. */
  onApprove: (receiptId: number) => void;
  /** Called to reject the open receipt, with a required comment. */
  onReject: (receiptId: number, comment: string) => void;
  /** Whether an approve request is in flight. */
  isApproving?: boolean;
  /** Whether a reject request is in flight. */
  isRejecting?: boolean;
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <Box sx={{ display: "flex", justifyContent: "space-between", py: 0.5 }}>
      <Typography variant="body2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="body2">{value}</Typography>
    </Box>
  );
}

/** A right-hand drawer showing a receipt's file preview, values, and admin actions. */
export function ReceiptDetailDrawer({
  receipt,
  onClose,
  onApprove,
  onReject,
  isApproving = false,
  isRejecting = false,
}: ReceiptDetailDrawerProps) {
  const [rejectComment, setRejectComment] = useState("");
  const [isRejectMode, setIsRejectMode] = useState(false);

  const { url: previewUrl, isLoading: isPreviewLoading } = useReceiptFilePreview(receipt?.id);

  const handleClose = (): void => {
    setRejectComment("");
    setIsRejectMode(false);
    onClose();
  };

  const canReview = receipt?.status === "SUBMITTED";

  return (
    <Drawer anchor="right" open={receipt !== null} onClose={handleClose}>
      <Box sx={{ width: { xs: "100vw", sm: 480 }, p: 3 }} role="presentation">
        {receipt && (
          <Stack spacing={2}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <Typography variant="h6" component="h2">
                Receipt #{receipt.id}
              </Typography>
              <IconButton onClick={handleClose} aria-label="Close">
                <CloseIcon />
              </IconButton>
            </Box>

            {isPreviewLoading && <CircularProgress size={24} />}
            {previewUrl && receipt.mimeType === "application/pdf" && (
              <Box
                component="iframe"
                src={previewUrl}
                title="Receipt preview"
                sx={{ width: "100%", height: 300, border: "1px solid", borderColor: "divider" }}
              />
            )}
            {previewUrl && receipt.mimeType !== "application/pdf" && (
              <Box
                component="img"
                src={previewUrl}
                alt={`Receipt file: ${receipt.originalFilename}`}
                sx={{ maxWidth: "100%", maxHeight: 300 }}
              />
            )}

            <StatusChip status={receipt.status} />

            <Divider />

            <DetailRow label="Employee" value={receipt.ownerName} />
            <DetailRow label="Merchant" value={receipt.merchantName ?? "—"} />
            <DetailRow label="Date" value={formatDate(receipt.receiptDate)} />
            <DetailRow
              label="Subtotal"
              value={formatCurrency(receipt.subtotal, receipt.currency)}
            />
            <DetailRow label="Tax" value={formatCurrency(receipt.taxAmount, receipt.currency)} />
            <DetailRow
              label="Total"
              value={formatCurrency(receipt.totalAmount, receipt.currency)}
            />
            <DetailRow label="Currency" value={receipt.currency ?? "—"} />

            {receipt.needsReview && (
              <Alert severity="warning">
                Flagged for review during extraction (low confidence on one or more fields).
              </Alert>
            )}

            {receipt.lineItems.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Line items
                </Typography>
                {receipt.lineItems.map((item) => (
                  <DetailRow
                    key={item.id}
                    label={`${item.description} ×${item.quantity}`}
                    value={formatCurrency(item.amount, receipt.currency)}
                  />
                ))}
              </Box>
            )}

            {receipt.status === "REJECTED" && receipt.reviewComment && (
              <Alert severity="error">Rejected: {receipt.reviewComment}</Alert>
            )}

            {canReview && (
              <Stack spacing={1}>
                <Divider />
                <Typography variant="subtitle2">Admin review</Typography>
                {isRejectMode ? (
                  <Stack spacing={1}>
                    <TextField
                      label="Rejection comment"
                      id="reject-comment"
                      required
                      multiline
                      minRows={2}
                      value={rejectComment}
                      onChange={(event) => setRejectComment(event.target.value)}
                    />
                    <Stack direction="row" spacing={1}>
                      <Button
                        variant="contained"
                        color="error"
                        disabled={rejectComment.trim().length === 0 || isRejecting}
                        onClick={() => onReject(receipt.id, rejectComment.trim())}
                      >
                        {isRejecting ? "Rejecting..." : "Confirm reject"}
                      </Button>
                      <Button variant="text" onClick={() => setIsRejectMode(false)}>
                        Cancel
                      </Button>
                    </Stack>
                  </Stack>
                ) : (
                  <Stack direction="row" spacing={2}>
                    <Button
                      variant="contained"
                      color="success"
                      disabled={isApproving}
                      onClick={() => onApprove(receipt.id)}
                    >
                      {isApproving ? "Approving..." : "Approve"}
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      onClick={() => setIsRejectMode(true)}
                    >
                      Reject
                    </Button>
                  </Stack>
                )}
              </Stack>
            )}
          </Stack>
        )}
      </Box>
    </Drawer>
  );
}
