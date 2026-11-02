import { Alert, Stack } from "@mui/material";
import { useNavigate } from "react-router-dom";

import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { FilePicker } from "@/features/receipts/components/FilePicker";
import { useUploadReceipt } from "@/features/receipts/hooks/useReceipts";

/** The receipt upload page: pick a file, then jump straight to its review page. */
export default function UploadReceiptPage() {
  const navigate = useNavigate();
  const uploadMutation = useUploadReceipt();

  const handleFileSelected = (file: File): void => {
    uploadMutation.mutate(file, {
      onSuccess: (receipt) => {
        navigate(`/employee/receipts/${receipt.id}/review`);
      },
    });
  };

  return (
    <Stack spacing={3} sx={{ maxWidth: 480 }}>
      <PageHeader
        title="Upload a receipt"
        description="We'll extract the merchant, date, and amounts automatically."
      />
      {uploadMutation.isError && (
        <Alert severity="error">Could not process this receipt. Please try again.</Alert>
      )}
      <FilePicker onFileSelected={handleFileSelected} isUploading={uploadMutation.isPending} />
      {uploadMutation.isPending && (
        <LoadingState label="Extracting fields and suggesting a category…" />
      )}
    </Stack>
  );
}
