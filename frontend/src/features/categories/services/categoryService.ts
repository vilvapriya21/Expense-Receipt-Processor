import { httpClient } from "@/services/httpClient";

import type { Category, CategoryCreateInput, CategoryUpdateInput } from "../types";

interface CategoryResponse {
  id: number;
  name: string;
  description: string | null;
  keywords: string[];
  is_active: boolean;
}

function mapCategory(data: CategoryResponse): Category {
  return {
    id: data.id,
    name: data.name,
    description: data.description,
    keywords: data.keywords,
    isActive: data.is_active,
  };
}

export const categoryService = {
  /** GET /categories — every active category, available to any authenticated user. */
  async list(): Promise<Category[]> {
    const { data } = await httpClient.get<CategoryResponse[]>("/categories");
    return data.map(mapCategory);
  },

  /** GET /admin/categories — every category, active or not (admin-only). */
  async listAll(): Promise<Category[]> {
    const { data } = await httpClient.get<CategoryResponse[]>("/admin/categories");
    return data.map(mapCategory);
  },

  /** POST /admin/categories — create a new category (admin-only). */
  async create(input: CategoryCreateInput): Promise<Category> {
    const { data } = await httpClient.post<CategoryResponse>("/admin/categories", {
      name: input.name,
      description: input.description,
      keywords: input.keywords,
    });
    return mapCategory(data);
  },

  /** PUT /admin/categories/{id} — update a category, or soft-deactivate it (admin-only). */
  async update(categoryId: number, input: CategoryUpdateInput): Promise<Category> {
    const { data } = await httpClient.put<CategoryResponse>(`/admin/categories/${categoryId}`, {
      name: input.name,
      description: input.description,
      keywords: input.keywords,
      is_active: input.isActive,
    });
    return mapCategory(data);
  },

  /** DELETE /admin/categories/{id} — delete a category, blocked if it is in use (admin-only). */
  async remove(categoryId: number): Promise<void> {
    await httpClient.delete(`/admin/categories/${categoryId}`);
  },
};
