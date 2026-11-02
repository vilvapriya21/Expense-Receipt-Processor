/** MIME types the backend accepts for a receipt upload. */
export const ALLOWED_UPLOAD_MIME_TYPES = ["image/jpeg", "image/png", "application/pdf"] as const;

/** Maximum receipt file size, in bytes (10 MB), matching the backend's limit. */
export const MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024;

/** Confidence (0.0-1.0) below which an extracted field is flagged for review. */
export const LOW_CONFIDENCE_THRESHOLD = 0.6;
