import { ApiError, mutate, request } from './client';

export type UserAccount = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};

type LoginResponse = {
  user: UserAccount;
};

export async function fetchCurrentAccount(): Promise<UserAccount | null> {
  try {
    return (await request('/api/v1/account/me/')) as UserAccount;
  } catch (error) {
    if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
      return null;
    }

    throw error;
  }
}

export async function login(username: string, password: string) {
  const body = (await mutate('/api/v1/auth/login/', 'POST', {
    username,
    password,
  })) as LoginResponse;

  return body.user;
}

export async function logout() {
  await mutate('/api/v1/auth/logout/', 'POST');
}

export async function updateCurrentAccount(
  changes: Pick<UserAccount, 'username' | 'first_name' | 'last_name'>,
) {
  return (await mutate('/api/v1/account/me/', 'PATCH', changes)) as UserAccount;
}
