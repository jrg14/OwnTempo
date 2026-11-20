import { mutate, request } from './client';

export type Space = {
  id: number;
  name: string;
  kind: 'personal' | 'shared';
  role: 'owner' | 'member';
};

export type SpaceMember = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  role: 'owner' | 'member';
};

export type UserSummary = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};

export type SpaceInvitation = {
  id: number;
  space: Pick<Space, 'id' | 'name' | 'kind'>;
  invited_user: UserSummary;
  invited_by: UserSummary;
  status: 'pending' | 'accepted' | 'rejected' | 'cancelled';
  created_at: string;
  responded_at: string | null;
};

export async function fetchSpaces() {
  return (await request('/api/v1/spaces/')) as Space[];
}

export async function fetchPersonalSpace() {
  return (await request('/api/v1/spaces/personal/')) as Space;
}

export async function createSharedSpace(name: string) {
  return (await mutate('/api/v1/spaces/', 'POST', { name })) as Space;
}

export async function updateSpace(space: Space, name: string) {
  const path =
    space.kind === 'personal'
      ? '/api/v1/spaces/personal/'
      : `/api/v1/spaces/${space.id}/`;
  return (await mutate(path, 'PATCH', { name })) as Space;
}

export async function fetchMembers(spaceId: number) {
  return (await request(`/api/v1/spaces/${spaceId}/members/`)) as SpaceMember[];
}

export async function removeMember(spaceId: number, userId: number) {
  await mutate(`/api/v1/spaces/${spaceId}/members/${userId}/`, 'DELETE');
}

export async function leaveSpace(spaceId: number) {
  await mutate(`/api/v1/spaces/${spaceId}/leave/`, 'POST');
}

export async function fetchReceivedInvitations() {
  return (await request('/api/v1/invitations/')) as SpaceInvitation[];
}

export async function fetchSpaceInvitations(spaceId: number) {
  return (await request(
    `/api/v1/spaces/${spaceId}/invitations/`,
  )) as SpaceInvitation[];
}

export async function inviteMember(spaceId: number, username: string) {
  return (await mutate(`/api/v1/spaces/${spaceId}/invitations/`, 'POST', {
    username,
  })) as SpaceInvitation;
}

export async function cancelInvitation(spaceId: number, invitationId: number) {
  await mutate(
    `/api/v1/spaces/${spaceId}/invitations/${invitationId}/`,
    'DELETE',
  );
}

export async function acceptInvitation(invitationId: number) {
  await mutate(`/api/v1/invitations/${invitationId}/accept/`, 'POST');
}

export async function rejectInvitation(invitationId: number) {
  await mutate(`/api/v1/invitations/${invitationId}/reject/`, 'POST');
}
