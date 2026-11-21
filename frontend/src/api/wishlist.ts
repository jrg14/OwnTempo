import { mutate, request } from './client';

export type WishKind = 'product' | 'experience' | 'idea';
export type WishStatus = 'pending' | 'obtained' | 'dismissed';
export type WishPriority = 'low' | 'normal' | 'high';

export type WishUser = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};

export type WishItem = {
  id: number;
  space_id: number;
  title: string;
  description: string;
  kind: WishKind;
  status: WishStatus;
  priority: WishPriority;
  url: string;
  image_url: string;
  price: string | null;
  currency: string;
  created_by: WishUser;
  obtained_at: string | null;
  created_at: string;
  updated_at: string;
};

export type WishInput = {
  title: string;
  description?: string;
  kind?: WishKind;
  status?: WishStatus;
  priority?: WishPriority;
  url?: string;
  image_url?: string;
  price?: string | null;
  currency?: string;
};

export type WishCounts = Record<WishStatus, number> & { total: number };

type WishListResponse = {
  results: WishItem[];
  counts: WishCounts;
};

export async function fetchWishes(spaceId: number) {
  return (await request(`/api/v1/spaces/${spaceId}/wishlist/`)) as WishListResponse;
}

export async function createWish(spaceId: number, input: WishInput) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/wishlist/`,
    'POST',
    input,
  )) as WishItem;
}

export async function updateWish(spaceId: number, wishId: number, input: Partial<WishInput>) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/wishlist/${wishId}/`,
    'PATCH',
    input,
  )) as WishItem;
}

export async function deleteWish(spaceId: number, wishId: number) {
  await mutate(`/api/v1/spaces/${spaceId}/wishlist/${wishId}/`, 'DELETE');
}
