import { API_BASE_URL } from './config';

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

export async function request(path: string, init?: RequestInit) {
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

export async function mutate(
  path: string,
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  body?: unknown,
) {
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
