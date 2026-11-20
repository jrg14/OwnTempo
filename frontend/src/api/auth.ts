import { API_BASE_URL } from './config';

export type UserAccount = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
};

type LoginResponse = {
  user: UserAccount;
};

type CsrfResponse = {
  csrf_token: string;
};

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

function getErrorDetail(body: unknown) {
  if (!body || typeof body !== 'object') {
    return null;
  }

  const data = body as Record<string, unknown>;

  if (typeof data.detail === 'string') {
    return data.detail;
  }

  for (const value of Object.values(data)) {
    if (Array.isArray(value) && typeof value[0] === 'string') {
      return value[0];
    }
  }

  return null;
}

async function readBody(response: Response): Promise<unknown> {
  if (response.status === 204) {
    return null;
  }

  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function request(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...init?.headers,
    },
  });
  const body = await readBody(response);

  if (!response.ok) {
    throw new ApiError(
      getErrorDetail(body) ?? 'No se pudo completar la operación.',
      response.status,
    );
  }

  return body;
}

async function getCsrfToken() {
  const body = (await request('/api/v1/auth/csrf/')) as CsrfResponse;

  if (typeof body?.csrf_token !== 'string') {
    throw new ApiError('No se pudo preparar la sesión segura.', 500);
  }

  return body.csrf_token;
}

async function mutate(path: string, method: 'POST' | 'PATCH', body?: unknown) {
  const csrfToken = await getCsrfToken();

  return request(path, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken,
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}

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
