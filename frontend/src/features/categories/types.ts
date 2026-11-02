/** An expense category, as shown in the category picker. */
export interface Category {
  id: number;
  name: string;
  description: string | null;
  keywords: string[];
  isActive: boolean;
}

/** Fields required to create a new category. */
export interface CategoryCreateInput {
  name: string;
  description: string | null;
  keywords: string[];
}

/** Admin-submitted changes to an existing category; also used to soft-deactivate. */
export interface CategoryUpdateInput {
  name?: string;
  description?: string | null;
  keywords?: string[];
  isActive?: boolean;
}
