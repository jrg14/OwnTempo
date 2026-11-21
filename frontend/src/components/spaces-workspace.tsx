import { useState, type FormEvent } from 'react';

import type { Space } from '../api/spaces';
import { useSpaces } from '../hooks/use-spaces';
import { Icon } from './icon';
import { PersonalSpaceCard } from './personal-space-card';
import { SharedSpaceCard } from './shared-space-card';
import { SpaceModulesPanel } from './space-modules-panel';

type SpacesWorkspaceProps = {
  notice?: string | null;
  onOpenTasks: (space: Space) => void;
};

export function SpacesWorkspace({ notice, onOpenTasks }: SpacesWorkspaceProps) {
  const spaces = useSpaces();
  const [newSpaceName, setNewSpaceName] = useState('');

  const create = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (await spaces.createSpace(newSpaceName.trim())) setNewSpaceName('');
  };

  if (spaces.status === 'loading' && spaces.spaces.length === 0) {
    return (
      <div className="spaces-workspace spaces-workspace--loading" role="status">
        <span aria-hidden="true" className="spinner" />
        <p>Preparando tus espacios…</p>
      </div>
    );
  }

  if (spaces.status === 'error' && spaces.spaces.length === 0) {
    return (
      <div className="spaces-workspace" role="alert">
        <h2>No pudimos cargar tus espacios</h2>
        <p className="workspace-description">{spaces.error}</p>
        <button className="primary-button" onClick={() => void spaces.reload()} type="button">
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="spaces-workspace workspace-home">
      <div className="active-space-header">
        <div className="active-space-copy">
          <h1>{spaces.activeSpace?.name ?? 'Tus espacios'}</h1>
          {spaces.activeSpace ? (
            <span className="space-kind-label">
              <Icon name={spaces.activeSpace.kind === 'personal' ? 'home' : 'users'} />
              {spaces.activeSpace.kind === 'personal'
                ? 'Tu espacio privado'
                : 'Espacio compartido'}
            </span>
          ) : null}
        </div>
        <div className="active-space-select">
          <label htmlFor="active-space">Cambiar espacio</label>
          <select
            id="active-space"
            onChange={(event) => spaces.selectSpace(Number(event.target.value))}
            value={spaces.activeSpaceId ?? ''}
          >
            {spaces.spaces.map((space) => (
              <option key={space.id} value={space.id}>
                {space.name} {space.kind === 'personal' ? '(personal)' : ''}
              </option>
            ))}
          </select>
        </div>
      </div>

      {spaces.error ? <p className="form-error" role="alert">{spaces.error}</p> : null}
      {notice ? <p className="form-success" role="status">{notice}</p> : null}

      {spaces.invitations.length > 0 ? (
        <section className="invitation-inbox" aria-labelledby="invitation-title">
          <div className="invitation-title-row">
            <h2 id="invitation-title">Tienes una invitación</h2>
            <span className="invitation-count" aria-label={`${spaces.invitations.length} invitaciones pendientes`}>
              {spaces.invitations.length}
            </span>
          </div>
          <ul>
            {spaces.invitations.map((invitation) => (
              <li key={invitation.id}>
                <div>
                  <strong>{invitation.space.name}</strong>
                  <span>Te invita @{invitation.invited_by.username}</span>
                </div>
                <div className="invitation-actions">
                  <button
                    className="primary-button"
                    disabled={spaces.busy}
                    onClick={() => void spaces.respond(invitation.id, true)}
                    type="button"
                  >
                    Aceptar
                  </button>
                  <button
                    className="secondary-button"
                    disabled={spaces.busy}
                    onClick={() => void spaces.respond(invitation.id, false)}
                    type="button"
                  >
                    Rechazar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      <div className="active-space-panel">
        {spaces.activeSpace ? (
          <SpaceModulesPanel
            key={`modules-${spaces.activeSpace.id}`}
            onOpenModule={(moduleKey) => {
              if (moduleKey === 'tasks') onOpenTasks(spaces.activeSpace!);
            }}
            space={spaces.activeSpace}
          />
        ) : null}

        <details className="space-management" id="space-management">
          <summary>
            <span><Icon name="users" />Gestionar espacios</span>
            <Icon name="chevron" />
          </summary>
          <div className="space-management__content">
            {spaces.activeSpace?.kind === 'personal' ? (
              <PersonalSpaceCard
                busy={spaces.busy}
                error={spaces.error}
                key={spaces.activeSpace.id}
                onSave={(name) => spaces.renameSpace(spaces.activeSpace!, name)}
                space={spaces.activeSpace}
              />
            ) : spaces.activeSpace ? (
              <SharedSpaceCard
                busy={spaces.busy}
                key={spaces.activeSpace.id}
                onLeave={spaces.leave}
                onRename={spaces.renameSpace}
                space={spaces.activeSpace}
              />
            ) : null}

            <form className="create-space-form" onSubmit={(event) => void create(event)}>
              <label htmlFor="new-space-name">Crear un espacio compartido</label>
              <p>Para una casa, familia, viaje o cualquier plan en común.</p>
              <div className="inline-form">
                <input
                  id="new-space-name"
                  maxLength={120}
                  onChange={(event) => setNewSpaceName(event.target.value)}
                  placeholder="Casa, familia, viaje…"
                  required
                  value={newSpaceName}
                />
                <button className="secondary-button" disabled={spaces.busy} type="submit">
                  Crear
                </button>
              </div>
            </form>
          </div>
        </details>
      </div>
    </div>
  );
}
