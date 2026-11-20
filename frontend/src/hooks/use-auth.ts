import { useCallback, useEffect, useState } from 'react';

import {
  fetchCurrentAccount,
  login as loginRequest,
  logout as logoutRequest,
  updateCurrentAccount,
  type UserAccount,
} from '../api/auth';

type AuthState = {
  status: 'checking' | 'anonymous' | 'authenticated';
  user: UserAccount | null;
  error: string | null;
  busy: boolean;
};

const initialState: AuthState = {
  status: 'checking',
  user: null,
  error: null,
  busy: false,
};

function errorMessage(error: unknown) {
  if (error instanceof TypeError) {
    return 'No se pudo conectar con OwnTempo.';
  }

  return error instanceof Error ? error.message : 'No se pudo completar la operación.';
}

export function useAuth() {
  const [state, setState] = useState<AuthState>(initialState);

  useEffect(() => {
    let active = true;

    fetchCurrentAccount()
      .then((user) => {
        if (!active) return;

        setState({
          status: user ? 'authenticated' : 'anonymous',
          user,
          error: null,
          busy: false,
        });
      })
      .catch((error: unknown) => {
        if (!active) return;

        setState({
          status: 'anonymous',
          user: null,
          error: errorMessage(error),
          busy: false,
        });
      });

    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    setState((current) => ({ ...current, busy: true, error: null }));

    try {
      const user = await loginRequest(username, password);
      setState({
        status: 'authenticated',
        user,
        error: null,
        busy: false,
      });
    } catch (error) {
      setState({
        status: 'anonymous',
        user: null,
        error: errorMessage(error),
        busy: false,
      });
    }
  }, []);

  const logout = useCallback(async () => {
    setState((current) => ({ ...current, busy: true, error: null }));

    try {
      await logoutRequest();
      setState({
        status: 'anonymous',
        user: null,
        error: null,
        busy: false,
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        error: errorMessage(error),
        busy: false,
      }));
    }
  }, []);

  const updateAccount = useCallback(
    async (changes: Pick<UserAccount, 'username' | 'first_name' | 'last_name'>) => {
      setState((current) => ({ ...current, busy: true, error: null }));

      try {
        const user = await updateCurrentAccount(changes);
        setState({
          status: 'authenticated',
          user,
          error: null,
          busy: false,
        });
        return true;
      } catch (error) {
        setState((current) => ({
          ...current,
          error: errorMessage(error),
          busy: false,
        }));
        return false;
      }
    },
    [],
  );

  return { ...state, login, logout, updateAccount };
}
