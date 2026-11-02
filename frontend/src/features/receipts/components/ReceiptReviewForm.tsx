import { zodResolver } from "@hookform/resolvers/zod";
import { Alert, Box, Button, Stack, TextField } from "@mui/material";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { CategorySelect } from "@/features/categories/components/CategorySelect";
import { LOW_CONFIDENCE_THRESHOLD } from "@/constants/upload";

import type { Receipt, ReceiptUpdateInput } from "../types";

const reviewSchema = z.object({
  merchantName: z.string().min(1, "Merchant name is required"),
  receiptDate: z.string().min(1, "Date is required"),
  subtotal: z.coerce.number().min(0, "Must be 0 or more"),
  taxAmount: z.coerce.number().min(0, "Must be 0 or more"),
  totalAmount: z.coerce.number().min(0, "Must be 0 or more"),
  currency: z.string().length(3, "Use a 3-letter currency code"),
  categoryId: z.number().nullable(),
});

type ReviewFormValues = z.infer<typeof reviewSchema>;

/** Props for {@link ReceiptReviewForm}. */
export interface ReceiptReviewFormProps {
  /** The receipt being reviewed, prefilling the form. */
  receipt: Receipt;
  /** Called with the corrected fields when the employee clicks Save. */
  onSave: (input: ReceiptUpdateInput) => void;
  /** Called after a successful save, when the employee clicks Submit. */
  onSubmit: () => void;
  /** Whether a save request is in flight. */
  isSaving?: boolean;
  /** Whether a submit request is in flight. */
  isSubmitting?: boolean;
}

function isLowConfidence(score: number | undefined): boolean {
  return score !== undefined && score < LOW_CONFIDENCE_THRESHOLD;
}

/** A form prefilled from extraction results, with low-confidence fields highlighted. */
export function ReceiptReviewForm({
  receipt,
  onSave,
  onSubmit,
  isSaving = false,
  isSubmitting = false,
}: ReceiptReviewFormProps) {
  const confidence = receipt.extractionConfidence;

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<ReviewFormValues>({
    resolver: zodResolver(reviewSchema),
    defaultValues: {
      merchantName: receipt.merchantName ?? "",
      receiptDate: receipt.receiptDate ?? "",
      subtotal: receipt.subtotal ?? 0,
      taxAmount: receipt.taxAmount ?? 0,
      totalAmount: receipt.totalAmount ?? 0,
      currency: receipt.currency ?? "USD",
      categoryId: receipt.categoryId,
    },
  });

  const onFormSubmit = handleSubmit((values) => {
    onSave(values);
  });

  return (
    <Box component="form" onSubmit={onFormSubmit}>
      {receipt.needsReview && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Some fields had low extraction confidence — please double-check them below.
        </Alert>
      )}
      {receipt.status === "REJECTED" && receipt.reviewComment && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Rejected by admin: {receipt.reviewComment}
        </Alert>
      )}
      <Stack spacing={1}>
        <Controller
          name="merchantName"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Merchant"
              fullWidth
              error={!!errors.merchantName || isLowConfidence(confidence?.merchantName)}
              helperText={
                errors.merchantName?.message ??
                (isLowConfidence(confidence?.merchantName) ? "Low confidence — please verify" : "")
              }
            />
          )}
        />
        <Controller
          name="receiptDate"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Date"
              type="date"
              fullWidth
              slotProps={{ inputLabel: { shrink: true } }}
              error={!!errors.receiptDate || isLowConfidence(confidence?.receiptDate)}
              helperText={
                errors.receiptDate?.message ??
                (isLowConfidence(confidence?.receiptDate) ? "Low confidence — please verify" : "")
              }
            />
          )}
        />
        <Controller
          name="subtotal"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Subtotal"
              type="number"
              fullWidth
              error={!!errors.subtotal || isLowConfidence(confidence?.subtotal)}
              helperText={
                errors.subtotal?.message ??
                (isLowConfidence(confidence?.subtotal) ? "Low confidence — please verify" : "")
              }
            />
          )}
        />
        <Controller
          name="taxAmount"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Tax"
              type="number"
              fullWidth
              error={!!errors.taxAmount || isLowConfidence(confidence?.taxAmount)}
              helperText={
                errors.taxAmount?.message ??
                (isLowConfidence(confidence?.taxAmount) ? "Low confidence — please verify" : "")
              }
            />
          )}
        />
        <Controller
          name="totalAmount"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Total"
              type="number"
              fullWidth
              error={!!errors.totalAmount || isLowConfidence(confidence?.totalAmount)}
              helperText={
                errors.totalAmount?.message ??
                (isLowConfidence(confidence?.totalAmount) ? "Low confidence — please verify" : "")
              }
            />
          )}
        />
        <Controller
          name="currency"
          control={control}
          render={({ field }) => (
            <TextField
              {...field}
              label="Currency"
              fullWidth
              error={!!errors.currency || isLowConfidence(confidence?.currency)}
              helperText={
                errors.currency?.message ??
                (isLowConfidence(confidence?.currency) ? "Low confidence — please verify" : "")
              }
            />
          )}
        />
        <Controller
          name="categoryId"
          control={control}
          render={({ field }) => (
            <CategorySelect
              value={field.value}
              onChange={field.onChange}
              suggestedCategoryId={receipt.suggestedCategoryId}
              suggestionConfidence={receipt.categoryConfidence}
            />
          )}
        />
      </Stack>
      <Stack direction="row" spacing={2} sx={{ mt: 3 }}>
        <Button type="submit" variant="outlined" disabled={isSaving}>
          {isSaving ? "Saving..." : "Save"}
        </Button>
        <Button
          type="button"
          variant="contained"
          onClick={onSubmit}
          disabled={isSubmitting || receipt.status === "SUBMITTED" || receipt.status === "APPROVED"}
        >
          {isSubmitting ? "Submitting..." : "Submit"}
        </Button>
      </Stack>
    </Box>
  );
}
