import DeleteIcon from "@mui/icons-material/Delete";
import EditIcon from "@mui/icons-material/Edit";
import {
  Alert,
  Button,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from "@mui/material";
import { useState } from "react";

import { EmptyState } from "@/components/EmptyState";
import { LoadingState } from "@/components/LoadingState";
import { PageHeader } from "@/components/PageHeader";
import { CategoryForm } from "@/features/categories/components/CategoryForm";
import {
  useAdminCategories,
  useCreateCategory,
  useDeleteCategory,
  useUpdateCategory,
} from "@/features/categories/hooks/useCategories";
import type { Category, CategoryCreateInput } from "@/features/categories/types";

/** The admin's categories page: create, edit keywords, and activate/deactivate. */
export default function AdminCategoriesPage() {
  const { data: categories = [], isLoading, isError } = useAdminCategories();
  const createMutation = useCreateCategory();
  const updateMutation = useUpdateCategory();
  const deleteMutation = useDeleteCategory();

  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [isCreating, setIsCreating] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const isFormOpen = isCreating || editingCategory !== null;

  const closeForm = (): void => {
    setIsCreating(false);
    setEditingCategory(null);
  };

  const handleSubmit = (input: CategoryCreateInput): void => {
    if (editingCategory) {
      updateMutation.mutate(
        { categoryId: editingCategory.id, input },
        { onSuccess: closeForm },
      );
    } else {
      createMutation.mutate(input, { onSuccess: closeForm });
    }
  };

  const handleToggleActive = (category: Category): void => {
    updateMutation.mutate({
      categoryId: category.id,
      input: { isActive: !category.isActive },
    });
  };

  const handleDelete = (category: Category): void => {
    setDeleteError(null);
    deleteMutation.mutate(category.id, {
      onError: (error) => {
        const message = (error as { message?: string }).message ?? "Could not delete category.";
        setDeleteError(message);
      },
    });
  };

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Categories"
        description="Create and manage the expense categories employees can choose from."
        actions={
          <Button variant="contained" onClick={() => setIsCreating(true)}>
            New category
          </Button>
        }
      />

      {deleteError && (
        <Alert severity="error" onClose={() => setDeleteError(null)}>
          {deleteError}
        </Alert>
      )}
      {isLoading && <LoadingState label="Loading categories…" />}
      {isError && <Alert severity="error">Could not load categories.</Alert>}

      {!isLoading && !isError && categories.length === 0 && (
        <EmptyState
          message="No categories yet"
          hint="Create one to let employees start categorizing their receipts."
        />
      )}

      {categories.length > 0 && (
        <TableContainer component={Paper}>
          <Table aria-label="Categories">
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Keywords</TableCell>
                <TableCell>Active</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {categories.map((category) => (
                <TableRow key={category.id} hover>
                  <TableCell>{category.name}</TableCell>
                  <TableCell>
                    {category.keywords.map((keyword) => (
                      <Chip key={keyword} label={keyword} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                    ))}
                  </TableCell>
                  <TableCell>
                    <Switch
                      checked={category.isActive}
                      onChange={() => handleToggleActive(category)}
                      inputProps={{ "aria-label": `Toggle ${category.name} active` }}
                    />
                  </TableCell>
                  <TableCell>
                    <IconButton
                      aria-label={`Edit ${category.name}`}
                      onClick={() => setEditingCategory(category)}
                      size="small"
                    >
                      <EditIcon fontSize="small" />
                    </IconButton>
                    <IconButton
                      aria-label={`Delete ${category.name}`}
                      onClick={() => handleDelete(category)}
                      size="small"
                      color="error"
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Dialog open={isFormOpen} onClose={closeForm} fullWidth maxWidth="xs">
        <DialogTitle>{editingCategory ? "Edit category" : "New category"}</DialogTitle>
        <DialogContent>
          <CategoryForm
            category={editingCategory}
            onSubmit={handleSubmit}
            onCancel={closeForm}
            isSaving={createMutation.isPending || updateMutation.isPending}
          />
        </DialogContent>
      </Dialog>
    </Stack>
  );
}
