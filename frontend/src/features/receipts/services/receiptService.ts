import { httpClient } from "@/services/httpClient";

import type {
  AdminReceiptFilters,
  CategoryTotal,
  ExtractionConfidence,
  LineItem,
  PaginatedReceipts,
  Receipt,
  ReceiptStatus,
  ReceiptSummary,
  ReceiptUpdateInput,
} from "../types";

interface LineItemResponse {
  id: number;
  description: string;
  quantity: string;
  unit_price: string;
  amount: string;
}

interface ExtractionConfidenceResponse {
  merchant_name: number;
  receipt_date: number;
  subtotal: number;
  tax_amount: number;
  total_amount: number;
  currency: number;
}

interface ReceiptResponse {
  id: number;
  owner_id: number;
  owner_name: string;
  original_filename: string;
  mime_type: string;
  status: ReceiptStatus;
  needs_review: boolean;
  merchant_name: string | null;
  receipt_date: string | null;
  subtotal: string | null;
  tax_amount: string | null;
  total_amount: string | null;
  currency: string | null;
  category_id: number | null;
  suggested_category_id: number | null;
  category_confidence: number | null;
  extraction_confidence: ExtractionConfidenceResponse | null;
  reviewer_id: number | null;
  review_comment: string | null;
  line_items: LineItemResponse[];
  created_at: string;
  updated_at: string;
}

interface PaginatedReceiptsResponse {
  items: ReceiptResponse[];
  total: number;
  page: number;
  size: number;
}

interface CategoryTotalResponse {
  category_id: number | null;
  category_name: string | null;
  total_amount: string;
  count: number;
}

interface ReceiptSummaryResponse {
  counts_by_status: Record<string, number>;
  approved_total_amount: string;
  approved_by_category: CategoryTotalResponse[];
}

function toNumberOrNull(value: string | null): number | null {
  return value === null ? null : Number(value);
}

function mapLineItem(data: LineItemResponse): LineItem {
  return {
    id: data.id,
    description: data.description,
    quantity: Number(data.quantity),
    unitPrice: Number(data.unit_price),
    amount: Number(data.amount),
  };
}

function mapConfidence(
  data: ExtractionConfidenceResponse | null,
): ExtractionConfidence | null {
  if (data === null) {
    return null;
  }
  return {
    merchantName: data.merchant_name,
    receiptDate: data.receipt_date,
    subtotal: data.subtotal,
    taxAmount: data.tax_amount,
    totalAmount: data.total_amount,
    currency: data.currency,
  };
}

function mapReceipt(data: ReceiptResponse): Receipt {
  return {
    id: data.id,
    ownerId: data.owner_id,
    ownerName: data.owner_name,
    originalFilename: data.original_filename,
    mimeType: data.mime_type,
    status: data.status,
    needsReview: data.needs_review,
    merchantName: data.merchant_name,
    receiptDate: data.receipt_date,
    subtotal: toNumberOrNull(data.subtotal),
    taxAmount: toNumberOrNull(data.tax_amount),
    totalAmount: toNumberOrNull(data.total_amount),
    currency: data.currency,
    categoryId: data.category_id,
    suggestedCategoryId: data.suggested_category_id,
    categoryConfidence: data.category_confidence,
    extractionConfidence: mapConfidence(data.extraction_confidence),
    reviewerId: data.reviewer_id,
    reviewComment: data.review_comment,
    lineItems: data.line_items.map(mapLineItem),
    createdAt: data.created_at,
    updatedAt: data.updated_at,
  };
}

function mapCategoryTotal(data: CategoryTotalResponse): CategoryTotal {
  return {
    categoryId: data.category_id,
    categoryName: data.category_name,
    totalAmount: Number(data.total_amount),
    count: data.count,
  };
}

function toUpdatePayload(input: ReceiptUpdateInput): Record<string, unknown> {
  return {
    merchant_name: input.merchantName,
    receipt_date: input.receiptDate,
    subtotal: input.subtotal,
    tax_amount: input.taxAmount,
    total_amount: input.totalAmount,
    currency: input.currency,
    category_id: input.categoryId,
  };
}

export interface ListReceiptsParams {
  page: number;
  size: number;
  status?: ReceiptStatus;
}

export const receiptService = {
  /** POST /receipts/upload — upload a file; runs extraction + categorization. */
  async upload(file: File): Promise<Receipt> {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await httpClient.post<ReceiptResponse>("/receipts/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return mapReceipt(data);
  },

  /** GET /receipts — the current user's own receipts, paginated and status-filtered. */
  async list(params: ListReceiptsParams): Promise<PaginatedReceipts> {
    const { data } = await httpClient.get<PaginatedReceiptsResponse>("/receipts", {
      params: { page: params.page, size: params.size, status: params.status },
    });
    return {
      items: data.items.map(mapReceipt),
      total: data.total,
      page: data.page,
      size: data.size,
    };
  },

  /** GET /receipts/{id} — a single receipt owned by the current user. */
  async get(receiptId: number): Promise<Receipt> {
    const { data } = await httpClient.get<ReceiptResponse>(`/receipts/${receiptId}`);
    return mapReceipt(data);
  },

  /** PUT /receipts/{id} — apply employee corrections to an editable receipt. */
  async update(receiptId: number, input: ReceiptUpdateInput): Promise<Receipt> {
    const { data } = await httpClient.put<ReceiptResponse>(
      `/receipts/${receiptId}`,
      toUpdatePayload(input),
    );
    return mapReceipt(data);
  },

  /** POST /receipts/{id}/submit — submit a receipt for admin review. */
  async submit(receiptId: number): Promise<Receipt> {
    const { data } = await httpClient.post<ReceiptResponse>(`/receipts/${receiptId}/submit`);
    return mapReceipt(data);
  },

  /** DELETE /receipts/{id} — delete a receipt that has not yet been submitted. */
  async remove(receiptId: number): Promise<void> {
    await httpClient.delete(`/receipts/${receiptId}`);
  },

  /** GET /receipts/{id}/file — the original uploaded file, as a Blob for preview. */
  async getFileBlob(receiptId: number): Promise<Blob> {
    const { data } = await httpClient.get<Blob>(`/receipts/${receiptId}/file`, {
      responseType: "blob",
    });
    return data;
  },

  /** GET /receipts/summary — the current user's own receipt totals. */
  async summary(): Promise<ReceiptSummary> {
    const { data } = await httpClient.get<ReceiptSummaryResponse>("/receipts/summary");
    return {
      countsByStatus: data.counts_by_status,
      approvedTotalAmount: Number(data.approved_total_amount),
      approvedByCategory: data.approved_by_category.map(mapCategoryTotal),
    };
  },

  /** GET /admin/receipts — all receipts, filtered by status/employee/category/date. */
  async listAdmin(filters: AdminReceiptFilters): Promise<PaginatedReceipts> {
    const { data } = await httpClient.get<PaginatedReceiptsResponse>("/admin/receipts", {
      params: {
        page: filters.page,
        size: filters.size,
        status: filters.status,
        employee_id: filters.employeeId,
        category_id: filters.categoryId,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
      },
    });
    return {
      items: data.items.map(mapReceipt),
      total: data.total,
      page: data.page,
      size: data.size,
    };
  },

  /** POST /admin/receipts/{id}/approve — approve a submitted receipt. */
  async approve(receiptId: number): Promise<Receipt> {
    const { data } = await httpClient.post<ReceiptResponse>(
      `/admin/receipts/${receiptId}/approve`,
    );
    return mapReceipt(data);
  },

  /** POST /admin/receipts/{id}/reject — reject a submitted receipt; comment required. */
  async reject(receiptId: number, comment: string): Promise<Receipt> {
    const { data } = await httpClient.post<ReceiptResponse>(
      `/admin/receipts/${receiptId}/reject`,
      { comment },
    );
    return mapReceipt(data);
  },
};
