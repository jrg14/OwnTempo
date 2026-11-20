import { mutate, request } from './client';

export type Space = {
  id: number;
  name: string;
  kind: 'personal' | 'shared';
  role: 'owner' | 'member';
};

export async function fetchSpaces() {
  return (await request('/api/v1/spaces/')) as Space[];
}

export async function fetchPersonalSpace() {
  return (await request('/api/v1/spaces/personal/')) as Space;
}

export async function updatePersonalSpace(name: string) {
  return (await mutate('/api/v1/spaces/personal/', 'PATCH', { name })) as Space;
}
