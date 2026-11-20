import { useCallback, useEffect, useState, type FormEvent } from 'react';

import {
  cancelInvitation,
  fetchMembers,
  fetchSpaceInvitations,
  inviteMember,
  removeMember,
  type Space,
  type SpaceInvitation,
  type SpaceMember,
} from '../api/spaces';
import { spaceErrorMessage } from '../hooks/use-spaces';

type SharedSpaceCardProps = {
  busy: boolean;
  space: Space;
  onLeave: (spaceId: number) => Promise<boolean>;
  onRename: (space: Space, name: string) => Promise<boolean>;
};

function memberName(member: SpaceMember) {
  return [member.first_name, member.last_name].filter(Boolean).join(' ') || member.username;
}

export function SharedSpaceCard({
  busy: globalBusy,
  space,
  onLeave,
  onRename,
}: SharedSpaceCardProps) {
  const [name, setName] = useState(space.name);
  const [username, setUsername] = useState('');
  const [members, setMembers] = useState<SpaceMember[]>([]);
  const [invitations, setInvitations] = useState<SpaceInvitation[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const isOwner = space.role === 'owner';

  const loadDetails = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loadedMembers, loadedInvitations] = await Promise.all([
        fetchMembers(space.id),
        isOwner ? fetchSpaceInvitations(space.id) : Promise.resolve([]),
      ]);
      setMembers(loadedMembers);
      setInvitations(loadedInvitations);
    } catch (loadError) {
      setError(spaceErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }, [isOwner, space.id]);

  useEffect(() => {
    let active = true;

    Promise.all([
      fetchMembers(space.id),
      isOwner ? fetchSpaceInvitations(space.id) : Promise.resolve([]),
    ])
      .then(([loadedMembers, loadedInvitations]) => {
        if (!active) return;
        setMembers(loadedMembers);
        setInvitations(loadedInvitations);
      })
      .catch((loadError: unknown) => {
        if (active) setError(spaceErrorMessage(loadError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [isOwner, space.id]);

  const rename = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaved(false);
    const normalizedName = name.trim();
    if (await onRename(space, normalizedName)) {
      setName(normalizedName);
      setSaved(true);
    }
  };

  const invite = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await inviteMember(space.id, username.trim());
      setUsername('');
      await loadDetails();
    } catch (inviteError) {
      setError(spaceErrorMessage(inviteError));
    } finally {
      setBusy(false);
    }
  };

  const remove = async (member: SpaceMember) => {
    if (!window.confirm(`¿Retirar a ${memberName(member)} de ${space.name}?`)) return;
    setBusy(true);
    setError(null);
    try {
      await removeMember(space.id, member.id);
      await loadDetails();
    } catch (removeError) {
      setError(spaceErrorMessage(removeError));
    } finally {
      setBusy(false);
    }
  };

  const cancel = async (invitation: SpaceInvitation) => {
    setBusy(true);
    setError(null);
    try {
      await cancelInvitation(space.id, invitation.id);
      await loadDetails();
    } catch (cancelError) {
      setError(spaceErrorMessage(cancelError));
    } finally {
      setBusy(false);
    }
  };

  const leave = async () => {
    if (!window.confirm(`¿Abandonar el espacio ${space.name}?`)) return;
    await onLeave(space.id);
  };

  const pendingInvitations = invitations.filter(
    (invitation) => invitation.status === 'pending',
  );
  const isBusy = busy || globalBusy;

  return (
    <section className="shared-space-card" aria-labelledby="shared-space-title">
      <div className="space-card__heading">
        <div>
          <h2 id="shared-space-title">{space.name}</h2>
        </div>
        <span className="role-badge">
          {isOwner ? 'Propietario' : 'Miembro'}
        </span>
      </div>

      {isOwner ? (
        <form className="space-form compact-form" onSubmit={(event) => void rename(event)}>
          <label htmlFor={`shared-space-name-${space.id}`}>Nombre del espacio</label>
          <div className="inline-form">
            <input
              id={`shared-space-name-${space.id}`}
              maxLength={120}
              onChange={(event) => setName(event.target.value)}
              required
              value={name}
            />
            <button className="secondary-button" disabled={isBusy} type="submit">
              Guardar
            </button>
          </div>
          {saved ? <p className="form-success" role="status">Nombre guardado.</p> : null}
        </form>
      ) : null}

      {error ? <p className="form-error" role="alert">{error}</p> : null}

      <div className="space-subsection">
        <div className="subsection-heading">
          <h3>Miembros</h3>
          <span>{members.length}</span>
        </div>
        {loading ? (
          <p className="muted-status" role="status">Cargando miembros…</p>
        ) : (
          <ul className="member-list">
            {members.map((member) => (
              <li key={member.id}>
                <div>
                  <strong>{memberName(member)}</strong>
                  <span>@{member.username} · {member.role === 'owner' ? 'Propietario' : 'Miembro'}</span>
                </div>
                {isOwner && member.role !== 'owner' ? (
                  <button
                    className="danger-text-button"
                    disabled={isBusy}
                    onClick={() => void remove(member)}
                    type="button"
                  >
                    Retirar
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </div>

      {isOwner ? (
        <div className="space-subsection">
          <h3>Invitar a otra persona</h3>
          <form className="inline-form invite-form" onSubmit={(event) => void invite(event)}>
            <div>
              <label htmlFor={`invite-username-${space.id}`}>Nombre de usuario</label>
              <input
                autoCapitalize="none"
                id={`invite-username-${space.id}`}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="por ejemplo, luis"
                required
                value={username}
              />
            </div>
            <button className="primary-button" disabled={isBusy} type="submit">
              Invitar
            </button>
          </form>

          {pendingInvitations.length > 0 ? (
            <ul className="pending-list" aria-label="Invitaciones pendientes">
              {pendingInvitations.map((invitation) => (
                <li key={invitation.id}>
                  <span>Invitación pendiente para @{invitation.invited_user.username}</span>
                  <button
                    className="text-button"
                    disabled={isBusy}
                    onClick={() => void cancel(invitation)}
                    type="button"
                  >
                    Cancelar
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : (
        <button
          className="danger-button"
          disabled={isBusy}
          onClick={() => void leave()}
          type="button"
        >
          Abandonar espacio
        </button>
      )}
    </section>
  );
}
