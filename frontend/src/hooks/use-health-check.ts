import { useCallback, useEffect, useRef, useState } from 'react';

import { fetchHealthStatus, type HealthResponse } from '../api/health';

type HealthState = {
  status: 'checking' | 'online' | 'offline';
  data: HealthResponse | null;
  error: string | null;
  checkedAt: Date | null;
};

const initialState: HealthState = {
  status: 'checking',
  data: null,
  error: null,
  checkedAt: null,
};

function getErrorMessage(error: unknown) {
  return error instanceof Error && error.name !== 'AbortError'
    ? error.message
    : 'La comprobación ha tardado demasiado.';
}

export function useHealthCheck() {
  const [state, setState] = useState<HealthState>(initialState);
  const requestRef = useRef<AbortController | null>(null);

  const performCheck = useCallback(async (controller: AbortController) => {
    const timeout = setTimeout(() => controller.abort(), 5000);

    try {
      const data = await fetchHealthStatus(controller.signal);

      if (requestRef.current === controller) {
        setState({
          status: 'online',
          data,
          error: null,
          checkedAt: new Date(),
        });
      }
    } catch (error) {
      if (requestRef.current !== controller) {
        return;
      }

      setState({
        status: 'offline',
        data: null,
        error: getErrorMessage(error),
        checkedAt: new Date(),
      });
    } finally {
      clearTimeout(timeout);

      if (requestRef.current === controller) {
        requestRef.current = null;
      }
    }
  }, []);

  const refresh = useCallback(async () => {
    requestRef.current?.abort();

    const controller = new AbortController();
    requestRef.current = controller;
    setState((current) => ({ ...current, status: 'checking', error: null }));

    await performCheck(controller);
  }, [performCheck]);

  useEffect(() => {
    const controller = new AbortController();
    requestRef.current = controller;
    const timeout = setTimeout(() => controller.abort(), 5000);

    fetchHealthStatus(controller.signal)
      .then((data) => {
        if (requestRef.current === controller) {
          setState({
            status: 'online',
            data,
            error: null,
            checkedAt: new Date(),
          });
        }
      })
      .catch((error: unknown) => {
        if (requestRef.current === controller) {
          setState({
            status: 'offline',
            data: null,
            error: getErrorMessage(error),
            checkedAt: new Date(),
          });
        }
      })
      .finally(() => {
        clearTimeout(timeout);

        if (requestRef.current === controller) {
          requestRef.current = null;
        }
      });

    return () => {
      clearTimeout(timeout);
      const activeRequest = requestRef.current;
      requestRef.current = null;
      activeRequest?.abort();
    };
  }, [performCheck]);

  return { ...state, refresh };
}

