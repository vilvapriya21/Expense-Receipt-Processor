import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { receiptService, type ListReceiptsParams } from "../services/receiptService";
import type { AdminReceiptFilters, ReceiptUpdateInput } from "../types";

const RECEIPTS_KEY = "receipts" as const;
const ADMIN_RECEIPTS_KEY = "admin-receipts" as const;
const SUMMARY_KEY = "receipt-summary" as const;

/**
 * Fetches a paginated, optionally status-filtered page of the current user's receipts.
 *
 * @param params - Page, size, and optional status filter.
 * @returns The TanStack Query result wrapping the paginated receipts.
 */
export function useReceiptsList(params: ListReceiptsParams) {
  return useQuery({
    queryKey: [RECEIPTS_KEY, params],
    queryFn: () => receiptService.list(params),
  });
}

/**
 * Fetches a single receipt by id.
 *
 * @param receiptId - The receipt to fetch, or undefined to skip the request.
 * @returns The TanStack Query result wrapping the receipt.
 */
export function useReceipt(receiptId: number | undefined) {
  return useQuery({
    queryKey: [RECEIPTS_KEY, receiptId],
    queryFn: () => receiptService.get(receiptId as number),
    enabled: receiptId !== undefined,
  });
}

/**
 * Fetches the current user's own receipt totals.
 *
 * @returns The TanStack Query result wrapping the receipt summary.
 */
export function useReceiptSummary() {
  return useQuery({
    queryKey: [SUMMARY_KEY],
    queryFn: receiptService.summary,
  });
}

/**
 * Uploads a new receipt file.
 *
 * @returns The TanStack Query mutation for triggering and observing the upload.
 */
export function useUploadReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => receiptService.upload(file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [RECEIPTS_KEY] });
    },
  });
}

/**
 * Applies employee corrections to a receipt.
 *
 * @param receiptId - The receipt being corrected.
 * @returns The TanStack Query mutation for triggering and observing the update.
 */
export function useUpdateReceipt(receiptId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: ReceiptUpdateInput) => receiptService.update(receiptId, input),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [RECEIPTS_KEY] });
    },
  });
}

/**
 * Submits a receipt for admin review.
 *
 * @returns The TanStack Query mutation for triggering and observing the submit.
 */
export function useSubmitReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (receiptId: number) => receiptService.submit(receiptId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [RECEIPTS_KEY] });
      void queryClient.invalidateQueries({ queryKey: [SUMMARY_KEY] });
    },
  });
}

/**
 * Deletes a receipt that has not yet been submitted.
 *
 * @returns The TanStack Query mutation for triggering and observing the delete.
 */
export function useDeleteReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (receiptId: number) => receiptService.remove(receiptId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [RECEIPTS_KEY] });
    },
  });
}

/**
 * Fetches a paginated, filtered page of all receipts (admin-only on the backend).
 *
 * @param filters - Page, size, and optional status/employee/category/date filters.
 * @returns The TanStack Query result wrapping the paginated receipts.
 */
export function useAdminReceiptsList(filters: AdminReceiptFilters) {
  return useQuery({
    queryKey: [ADMIN_RECEIPTS_KEY, filters],
    queryFn: () => receiptService.listAdmin(filters),
  });
}

/**
 * Approves a submitted receipt (admin-only on the backend).
 *
 * @returns The TanStack Query mutation for triggering and observing the approval.
 */
export function useApproveReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (receiptId: number) => receiptService.approve(receiptId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [ADMIN_RECEIPTS_KEY] });
    },
  });
}

/**
 * Rejects a submitted receipt with a required comment (admin-only on the backend).
 *
 * @returns The TanStack Query mutation for triggering and observing the rejection.
 */
export function useRejectReceipt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ receiptId, comment }: { receiptId: number; comment: string }) =>
      receiptService.reject(receiptId, comment),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [ADMIN_RECEIPTS_KEY] });
    },
  });
}
