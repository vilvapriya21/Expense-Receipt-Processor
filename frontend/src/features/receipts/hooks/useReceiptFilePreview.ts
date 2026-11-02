import { useEffect, useState } from "react";

import { receiptService } from "../services/receiptService";

/**
 * Fetches a receipt's original file as an object URL suitable for an <img>/<iframe> preview.
 *
 * @param receiptId - The receipt whose file should be previewed.
 * @returns The object URL (or null while loading/on error) and the loading/error state.
 */
export function useReceiptFilePreview(receiptId: number | undefined): {
  url: string | null;
  isLoading: boolean;
  isError: boolean;
} {
  const [url, setUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isError, setIsError] = useState(false);

  useEffect(() => {
    if (receiptId === undefined) {
      return;
    }

    let objectUrl: string | null = null;
    setIsLoading(true);
    setIsError(false);

    receiptService
      .getFileBlob(receiptId)
      .then((blob) => {
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => {
        setIsError(true);
      })
      .finally(() => {
        setIsLoading(false);
      });

    return () => {
      if (objectUrl) {
        URL.revokeObjectURL(objectUrl);
      }
    };
  }, [receiptId]);

  return { url, isLoading, isError };
}
