export type HealthResponse = {
  status: 'ok' | 'degraded';
  service: string;
  checks: {
    django: 'ok' | 'unavailable';
    database: 'ok' | 'unavailable';
  };
  timestamp: string;
};

const developmentApiUrl = import.meta.env.DEV ? 'http://localhost:8000' : '';

export const API_BASE_URL = (
  import.meta.env.VITE_API_URL ?? developmentApiUrl
).replace(/\/+$/, '');

export const API_DISPLAY_URL = API_BASE_URL || window.location.origin;

function isHealthResponse(value: unknown): value is HealthResponse {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const response = value as Partial<HealthResponse>;

  return (
    (response.status === 'ok' || response.status === 'degraded') &&
    typeof response.service === 'string' &&
    typeof response.timestamp === 'string' &&
    !!response.checks &&
    typeof response.checks === 'object' &&
    typeof response.checks.django === 'string' &&
    typeof response.checks.database === 'string'
  );
}

export async function fetchHealthStatus(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health/`, {
    headers: { Accept: 'application/json' },
    signal,
  });

  const body: unknown = await response.json();

  if (!isHealthResponse(body)) {
    throw new Error('La API devolvió una respuesta inesperada.');
  }

  if (!response.ok || body.status !== 'ok') {
    throw new Error('El backend está disponible, pero alguno de sus servicios ha fallado.');
  }

  return body;
}

