import { MenuItem, TextField } from "@mui/material";

import { useCategories } from "../hooks/useCategories";

/** Props for {@link CategorySelect}. */
export interface CategorySelectProps {
  /** The currently selected category id, or null for none chosen. */
  value: number | null;
  /** Called with the newly selected category id, or null when cleared. */
  onChange: (categoryId: number | null) => void;
  /** Optional suggested category id, shown as a hint in the helper text. */
  suggestedCategoryId?: number | null;
  /** Optional suggestion confidence (0-1), shown alongside the suggestion. */
  suggestionConfidence?: number | null;
  /** Error message to show beneath the field, if validation failed. */
  error?: string;
}

/** A dropdown of active categories, optionally showing the system's suggested category. */
export function CategorySelect({
  value,
  onChange,
  suggestedCategoryId,
  suggestionConfidence,
  error,
}: CategorySelectProps) {
  const { data: categories = [], isLoading } = useCategories();
  const suggested = categories.find((c) => c.id === suggestedCategoryId);

  const confidencePercent = Math.round((suggestionConfidence ?? 0) * 100);
  const suggestionText = suggested
    ? `Suggested: ${suggested.name} (${confidencePercent}% confidence)`
    : undefined;
  const helperText = error ?? suggestionText;

  return (
    <TextField
      select
      label="Category"
      id="receipt-category"
      value={value ?? ""}
      onChange={(event) => {
        const next = event.target.value;
        onChange(next === "" ? null : Number(next));
      }}
      disabled={isLoading}
      error={!!error}
      helperText={helperText}
      fullWidth
      margin="normal"
    >
      <MenuItem value="">
        <em>None</em>
      </MenuItem>
      {categories.map((category) => (
        <MenuItem key={category.id} value={category.id}>
          {category.name}
          {category.id === suggestedCategoryId ? " (suggested)" : ""}
        </MenuItem>
      ))}
    </TextField>
  );
}
