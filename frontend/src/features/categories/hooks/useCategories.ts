import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { categoryService } from "../services/categoryService";
import type { CategoryCreateInput, CategoryUpdateInput } from "../types";

const CATEGORIES_KEY = "categories" as const;
const ADMIN_CATEGORIES_KEY = "admin-categories" as const;

/**
 * Fetches the list of active categories, for category pickers.
 *
 * @returns The TanStack Query result wrapping the list of active categories.
 */
export function useCategories() {
  return useQuery({
    queryKey: [CATEGORIES_KEY],
    queryFn: categoryService.list,
  });
}

/**
 * Fetches every category, active or not, for admin management.
 *
 * @returns The TanStack Query result wrapping the full list of categories.
 */
export function useAdminCategories() {
  return useQuery({
    queryKey: [ADMIN_CATEGORIES_KEY],
    queryFn: categoryService.listAll,
  });
}

function invalidateCategoryQueries(queryClient: ReturnType<typeof useQueryClient>): void {
  void queryClient.invalidateQueries({ queryKey: [ADMIN_CATEGORIES_KEY] });
  void queryClient.invalidateQueries({ queryKey: [CATEGORIES_KEY] });
}

/**
 * Creates a new category.
 *
 * @returns The TanStack Query mutation for triggering and observing the create.
 */
export function useCreateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CategoryCreateInput) => categoryService.create(input),
    onSuccess: () => invalidateCategoryQueries(queryClient),
  });
}

/**
 * Updates a category, including toggling is_active to activate/deactivate it.
 *
 * @returns The TanStack Query mutation for triggering and observing the update.
 */
export function useUpdateCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ categoryId, input }: { categoryId: number; input: CategoryUpdateInput }) =>
      categoryService.update(categoryId, input),
    onSuccess: () => invalidateCategoryQueries(queryClient),
  });
}

/**
 * Deletes a category, which the backend blocks if any receipt still uses it.
 *
 * @returns The TanStack Query mutation for triggering and observing the delete.
 */
export function useDeleteCategory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (categoryId: number) => categoryService.remove(categoryId),
    onSuccess: () => invalidateCategoryQueries(queryClient),
  });
}
