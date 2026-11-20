import { useCallback, useEffect, useMemo, useState } from 'react';

import {
  acceptInvitation,
  createSharedSpace,
  fetchReceivedInvitations,
  fetchSpaces,
  leaveSpace,
  rejectInvitation,
  updateSpace,
  type Space,
  type SpaceInvitation,
} from '../api/spaces';

type SpacesState = {
  status: 'loading' | 'ready' | 'error';
  spaces: Space[];
  invitations: SpaceInvitation[];
  activeSpaceId: number | null;
  error: string | null;
  busy: boolean;
};

const initialState: SpacesState = {
  status: 'loading',
  spaces: [],
  invitations: [],
  activeSpaceId: null,
  error: null,
  busy: false,
};

export function spaceErrorMessage(error: unknown) {
  if (error instanceof TypeError) {
    return 'No se pudo conectar con OwnTempo.';
  }

  return error instanceof Error ? error.message : 'No se pudo completar la operación.';
}

export function useSpaces() {
  const [state, setState] = useState<SpacesState>(initialState);

  const load = useCallback(async () => {
    setState((current) => ({ ...current, status: 'loading', error: null }));

    try {
      const [spaces, invitations] = await Promise.all([
        fetchSpaces(),
        fetchReceivedInvitations(),
      ]);
      setState((current) => {
        const activeStillExists = spaces.some(
          (space) => space.id === current.activeSpaceId,
        );
        const defaultSpace = spaces.find((space) => space.kind === 'personal') ?? spaces[0];

        return {
          status: 'ready',
          spaces,
          invitations,
          activeSpaceId: activeStillExists
            ? current.activeSpaceId
            : (defaultSpace?.id ?? null),
          error: null,
          busy: false,
        };
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        status: 'error',
        error: spaceErrorMessage(error),
        busy: false,
      }));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const activeSpace = useMemo(
    () => state.spaces.find((space) => space.id === state.activeSpaceId) ?? null,
    [state.activeSpaceId, state.spaces],
  );

  const createSpace = useCallback(async (name: string) => {
    setState((current) => ({ ...current, busy: true, error: null }));
    try {
      const space = await createSharedSpace(name);
      setState((current) => ({
        ...current,
        spaces: [...current.spaces, space],
        activeSpaceId: space.id,
        busy: false,
      }));
      return true;
    } catch (error) {
      setState((current) => ({
        ...current,
        error: spaceErrorMessage(error),
        busy: false,
      }));
      return false;
    }
  }, []);

  const renameSpace = useCallback(async (space: Space, name: string) => {
    setState((current) => ({ ...current, busy: true, error: null }));
    try {
      const updated = await updateSpace(space, name);
      setState((current) => ({
        ...current,
        spaces: current.spaces.map((item) =>
          item.id === updated.id ? updated : item,
        ),
        busy: false,
      }));
      return true;
    } catch (error) {
      setState((current) => ({
        ...current,
        error: spaceErrorMessage(error),
        busy: false,
      }));
      return false;
    }
  }, []);

  const respond = useCallback(async (invitationId: number, accepted: boolean) => {
    setState((current) => ({ ...current, busy: true, error: null }));
    try {
      if (accepted) await acceptInvitation(invitationId);
      else await rejectInvitation(invitationId);
      await load();
      return true;
    } catch (error) {
      setState((current) => ({
        ...current,
        error: spaceErrorMessage(error),
        busy: false,
      }));
      return false;
    }
  }, [load]);

  const leave = useCallback(async (spaceId: number) => {
    setState((current) => ({ ...current, busy: true, error: null }));
    try {
      await leaveSpace(spaceId);
      await load();
      return true;
    } catch (error) {
      setState((current) => ({
        ...current,
        error: spaceErrorMessage(error),
        busy: false,
      }));
      return false;
    }
  }, [load]);

  return {
    ...state,
    activeSpace,
    createSpace,
    leave,
    reload: load,
    renameSpace,
    respond,
    selectSpace: (spaceId: number) =>
      setState((current) => ({ ...current, activeSpaceId: spaceId, error: null })),
  };
}
