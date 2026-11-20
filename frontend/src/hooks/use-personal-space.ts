import { useCallback, useEffect, useState } from 'react';

import {
  fetchPersonalSpace,
  updatePersonalSpace,
  type Space,
} from '../api/spaces';

type PersonalSpaceState = {
  status: 'idle' | 'loading' | 'ready' | 'error';
  space: Space | null;
  error: string | null;
  busy: boolean;
};

const initialState: PersonalSpaceState = {
  status: 'idle',
  space: null,
  error: null,
  busy: false,
};

function errorMessage(error: unknown) {
  if (error instanceof TypeError) {
    return 'No se pudo conectar con OwnTempo.';
  }

  return error instanceof Error ? error.message : 'No se pudo completar la operación.';
}

export function usePersonalSpace(enabled: boolean) {
  const [state, setState] = useState<PersonalSpaceState>(initialState);

  const load = useCallback(async () => {
    setState((current) => ({
      ...current,
      status: 'loading',
      error: null,
    }));

    try {
      const space = await fetchPersonalSpace();
      setState({ status: 'ready', space, error: null, busy: false });
    } catch (error) {
      setState((current) => ({
        ...current,
        status: 'error',
        error: errorMessage(error),
        busy: false,
      }));
    }
  }, []);

  useEffect(() => {
    if (!enabled) {
      setState(initialState);
      return;
    }

    void load();
  }, [enabled, load]);

  const updateName = useCallback(async (name: string) => {
    setState((current) => ({ ...current, busy: true, error: null }));

    try {
      const space = await updatePersonalSpace(name);
      setState({ status: 'ready', space, error: null, busy: false });
      return true;
    } catch (error) {
      setState((current) => ({
        ...current,
        error: errorMessage(error),
        busy: false,
      }));
      return false;
    }
  }, []);

  return { ...state, reload: load, updateName };
}
