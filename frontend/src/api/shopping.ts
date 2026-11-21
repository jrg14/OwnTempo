import { mutate, request } from './client';

export type ShoppingItemStatus = 'pending' | 'purchased';

export type ShoppingUser = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};

export type ShoppingItem = {
  id: number;
  name: string;
  quantity: string;
  unit: string;
  note: string;
  status: ShoppingItemStatus;
  position: number;
  created_by: ShoppingUser;
  purchased_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ShoppingList = {
  id: number;
  space_id: number;
  name: string;
  pending_count: number;
  purchased_count: number;
  item_count: number;
  items: ShoppingItem[];
  created_by: ShoppingUser;
  created_at: string;
  updated_at: string;
};

export type ShoppingItemInput = {
  name: string;
  quantity?: string;
  unit?: string;
  note?: string;
  status?: ShoppingItemStatus;
};

export async function fetchShoppingLists(spaceId: number) {
  return (await request(`/api/v1/spaces/${spaceId}/shopping/lists/`)) as ShoppingList[];
}

export async function fetchShoppingList(spaceId: number, listId: number) {
  return (await request(
    `/api/v1/spaces/${spaceId}/shopping/lists/${listId}/`,
  )) as ShoppingList;
}

export async function createShoppingList(spaceId: number, name: string) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/shopping/lists/`,
    'POST',
    { name },
  )) as ShoppingList;
}

export async function updateShoppingList(spaceId: number, listId: number, name: string) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/shopping/lists/${listId}/`,
    'PATCH',
    { name },
  )) as ShoppingList;
}

export async function deleteShoppingList(spaceId: number, listId: number) {
  await mutate(`/api/v1/spaces/${spaceId}/shopping/lists/${listId}/`, 'DELETE');
}

export async function createShoppingItem(
  spaceId: number,
  listId: number,
  input: ShoppingItemInput,
) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/shopping/lists/${listId}/items/`,
    'POST',
    input,
  )) as ShoppingItem;
}

export async function updateShoppingItem(
  spaceId: number,
  listId: number,
  itemId: number,
  input: Partial<ShoppingItemInput>,
) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/shopping/lists/${listId}/items/${itemId}/`,
    'PATCH',
    input,
  )) as ShoppingItem;
}

export async function deleteShoppingItem(spaceId: number, listId: number, itemId: number) {
  await mutate(
    `/api/v1/spaces/${spaceId}/shopping/lists/${listId}/items/${itemId}/`,
    'DELETE',
  );
}

export async function reorderShoppingItems(spaceId: number, listId: number, itemIds: number[]) {
  return (await mutate(
    `/api/v1/spaces/${spaceId}/shopping/lists/${listId}/items/reorder/`,
    'POST',
    { item_ids: itemIds },
  )) as ShoppingItem[];
}
