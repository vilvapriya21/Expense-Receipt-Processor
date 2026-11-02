import UploadFileIcon from "@mui/icons-material/UploadFile";
import { Alert, Box, Button, Paper, Typography } from "@mui/material";
import { useId, useRef, useState } from "react";

import { ALLOWED_UPLOAD_MIME_TYPES, MAX_UPLOAD_SIZE_BYTES } from "@/constants/upload";

/** Props for {@link FilePicker}. */
export interface FilePickerProps {
  /** Called with the chosen file once it passes type/size validation. */
  onFileSelected: (file: File) => void;
  /** Whether a selection/upload is currently in progress. */
  isUploading?: boolean;
}

type AllowedMimeType = (typeof ALLOWED_UPLOAD_MIME_TYPES)[number];

function validateFile(file: File): string | null {
  if (!ALLOWED_UPLOAD_MIME_TYPES.includes(file.type as AllowedMimeType)) {
    return "Only JPG, PNG, or PDF files are allowed.";
  }
  if (file.size > MAX_UPLOAD_SIZE_BYTES) {
    return "File is too large (10 MB maximum).";
  }
  return null;
}

/** A labeled file input that validates type and size before handing the file off. */
export function FilePicker({ onFileSelected, isUploading = false }: FilePickerProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      setFileName(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
      return;
    }
    setError(null);
    setFileName(file.name);
    onFileSelected(file);
  };

  return (
    <Box>
      <Paper
        variant="outlined"
        sx={{
          p: { xs: 4, sm: 6 },
          textAlign: "center",
          borderStyle: "dashed",
          borderWidth: 2,
          borderColor: error ? "error.main" : "primary.light",
          bgcolor: error ? "error.50" : "rgba(238, 242, 255, 0.55)",
          transition: "border-color 160ms ease, background-color 160ms ease",
          "&:hover": {
            borderColor: error ? "error.main" : "primary.main",
            bgcolor: "rgba(238, 242, 255, 0.9)",
          },
        }}
      >
        <Box
          sx={{
            width: 62,
            height: 62,
            display: "grid",
            placeItems: "center",
            mx: "auto",
            mb: 2,
            borderRadius: 3,
            bgcolor: "primary.main",
            color: "common.white",
            boxShadow: "0 10px 24px rgba(79, 70, 229, 0.22)",
          }}
        >
          <UploadFileIcon sx={{ fontSize: 30 }} />
        </Box>
        <label htmlFor={inputId}>
          <Typography component="span" sx={{ display: "block", mb: 2 }}>
            <strong>Choose a receipt</strong> to start processing
          </Typography>
          <Typography
            component="span"
            variant="body2"
            color="text.secondary"
            sx={{ display: "block", mb: 2 }}
          >
            JPG, PNG, or PDF · up to 10 MB
          </Typography>
        </label>
        <input
          id={inputId}
          ref={inputRef}
          type="file"
          accept={ALLOWED_UPLOAD_MIME_TYPES.join(",")}
          onChange={handleChange}
          disabled={isUploading}
          style={{ display: "none" }}
        />
        <Button variant="outlined" component="label" htmlFor={inputId} disabled={isUploading}>
          Choose file
        </Button>
        {fileName && !error && (
          <Typography variant="body2" sx={{ mt: 2 }}>
            Selected: {fileName}
          </Typography>
        )}
      </Paper>
      {error && (
        <Alert severity="error" sx={{ mt: 1 }}>
          {error}
        </Alert>
      )}
    </Box>
  );
}
