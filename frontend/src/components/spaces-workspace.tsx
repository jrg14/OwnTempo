import { useState, type FormEvent } from 'react';

import { useSpaces } from '../hooks/use-spaces';
import { PersonalSpaceCard } from './personal-space-card';
import { SharedSpaceCard } from './shared-space-card';
import { SpaceModulesPanel } from './space-modules-panel';

export function SpacesWorkspace() {
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
    <div className="spaces-workspace">
      <div className="workspace-heading">
        <div>
          <p className="eyebrow">TUS CONTEXTOS</p>
          <h2>Espacios</h2>
          <p className="workspace-description">
            Separa lo privado y comparte solo lo que pertenezca a un espacio común.
          </p>
        </div>
        {spaces.invitations.length > 0 ? (
          <span className="invitation-count">
            {spaces.invitations.length} pendiente{spaces.invitations.length === 1 ? '' : 's'}
          </span>
        ) : null}
      </div>

      {spaces.error ? <p className="form-error" role="alert">{spaces.error}</p> : null}

      {spaces.invitations.length > 0 ? (
        <section className="invitation-inbox" aria-labelledby="invitation-title">
          <h3 id="invitation-title">Invitaciones</h3>
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

      <div className="space-toolbar">
        <div>
          <label htmlFor="active-space">Espacio activo</label>
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

        <form className="create-space-form" onSubmit={(event) => void create(event)}>
          <label htmlFor="new-space-name">Nuevo espacio compartido</label>
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

      <div className="active-space-panel">
        {spaces.activeSpace?.kind === 'personal' ? (
          <PersonalSpaceCard
            busy={spaces.busy}
            error={null}
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

        {spaces.activeSpace ? (
          <SpaceModulesPanel key={`modules-${spaces.activeSpace.id}`} space={spaces.activeSpace} />
        ) : null}
      </div>
    </div>
  );
}
