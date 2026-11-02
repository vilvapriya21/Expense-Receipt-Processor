import { zodResolver } from "@hookform/resolvers/zod";
import { Button, Stack, TextField } from "@mui/material";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import type { Category, CategoryCreateInput } from "../types";

const categorySchema = z.object({
  name: z.string().min(1, "Name is required"),
  description: z.string(),
  keywords: z.string(),
});

type CategoryFormValues = z.infer<typeof categorySchema>;

/** Props for {@link CategoryForm}. */
export interface CategoryFormProps {
  /** The category being edited, or null when creating a new one. */
  category: Category | null;
  /** Called with the submitted fields on save. */
  onSubmit: (input: CategoryCreateInput) => void;
  /** Called when the form is cancelled. */
  onCancel: () => void;
  /** Whether a save request is in flight. */
  isSaving?: boolean;
}

/** A create/edit form for a category, including its comma-separated keyword list. */
export function CategoryForm({
  category,
  onSubmit,
  onCancel,
  isSaving = false,
}: CategoryFormProps) {
  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: category?.name ?? "",
      description: category?.description ?? "",
      keywords: category?.keywords.join(", ") ?? "",
    },
  });

  const onFormSubmit = handleSubmit((values) => {
    onSubmit({
      name: values.name,
      description: values.description.trim() === "" ? null : values.description,
      keywords: values.keywords
        .split(",")
        .map((keyword) => keyword.trim())
        .filter((keyword) => keyword.length > 0),
    });
  });

  return (
    <Stack component="form" spacing={2} onSubmit={onFormSubmit} sx={{ mt: 1, minWidth: 320 }}>
      <Controller
        name="name"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            label="Name"
            fullWidth
            autoFocus
            error={!!errors.name}
            helperText={errors.name?.message}
          />
        )}
      />
      <Controller
        name="description"
        control={control}
        render={({ field }) => <TextField {...field} label="Description" fullWidth />}
      />
      <Controller
        name="keywords"
        control={control}
        render={({ field }) => (
          <TextField
            {...field}
            label="Keywords (comma-separated)"
            fullWidth
            helperText="Used to auto-suggest this category from a receipt's merchant name."
          />
        )}
      />
      <Stack direction="row" spacing={2}>
        <Button type="submit" variant="contained" disabled={isSaving}>
          {isSaving ? "Saving..." : "Save"}
        </Button>
        <Button type="button" variant="text" onClick={onCancel}>
          Cancel
        </Button>
      </Stack>
    </Stack>
  );
}
