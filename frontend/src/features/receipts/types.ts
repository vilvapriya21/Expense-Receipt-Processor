/** A receipt's position in its review lifecycle. */
export type ReceiptStatus = "UPLOADED" | "EXTRACTED" | "SUBMITTED" | "APPROVED" | "REJECTED";

/** A single line item belonging to a receipt. */
export interface LineItem {
  id: number;
  description: string;
  quantity: number;
  unitPrice: number;
  amount: number;
}

/** Per-field extraction confidence (0.0-1.0). */
export interface ExtractionConfidence {
  merchantName: number;
  receiptDate: number;
  subtotal: number;
  taxAmount: number;
  totalAmount: number;
  currency: number;
}

/** A receipt as returned by the API, in the app's idiomatic camelCase shape. */
export interface Receipt {
  id: number;
  ownerId: number;
  ownerName: string;
  originalFilename: string;
  mimeType: string;
  status: ReceiptStatus;
  needsReview: boolean;
  merchantName: string | null;
  receiptDate: string | null;
  subtotal: number | null;
  taxAmount: number | null;
  totalAmount: number | null;
  currency: string | null;
  categoryId: number | null;
  suggestedCategoryId: number | null;
  categoryConfidence: number | null;
  extractionConfidence: ExtractionConfidence | null;
  reviewerId: number | null;
  reviewComment: string | null;
  lineItems: LineItem[];
  createdAt: string;
  updatedAt: string;
}

/** Employee-submitted corrections to an extracted receipt. */
export interface ReceiptUpdateInput {
  merchantName?: string | null;
  receiptDate?: string | null;
  subtotal?: number | null;
  taxAmount?: number | null;
  totalAmount?: number | null;
  currency?: string | null;
  categoryId?: number | null;
}

/** A page of receipts plus pagination metadata. */
export interface PaginatedReceipts {
  items: Receipt[];
  total: number;
  page: number;
  size: number;
}

/** Total approved amount and count for a single category. */
export interface CategoryTotal {
  categoryId: number | null;
  categoryName: string | null;
  totalAmount: number;
  count: number;
}

/** An employee's own receipt totals. */
export interface ReceiptSummary {
  countsByStatus: Record<string, number>;
  approvedTotalAmount: number;
  approvedByCategory: CategoryTotal[];
}

/** Filters for the admin receipts list. */
export interface AdminReceiptFilters {
  page: number;
  size: number;
  status?: ReceiptStatus;
  employeeId?: number;
  categoryId?: number;
  dateFrom?: string;
  dateTo?: string;
}
