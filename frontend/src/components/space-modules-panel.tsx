import { useEffect, useState } from 'react';

import {
  fetchSpaceModules,
  updateSpaceModule,
  type SpaceModuleConfiguration,
} from '../api/modules';
import type { Space } from '../api/spaces';
import { spaceErrorMessage } from '../hooks/use-spaces';

const moduleIcons: Record<SpaceModuleConfiguration['icon'], string> = {
  check: '✓',
  cart: '+',
  heart: '♡',
  calendar: '○',
  wallet: '€',
};

type SpaceModulesPanelProps = {
  space: Space;
};

export function SpaceModulesPanel({ space }: SpaceModulesPanelProps) {
  const [modules, setModules] = useState<SpaceModuleConfiguration[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyKey, setBusyKey] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isOwner = space.role === 'owner';

  useEffect(() => {
    let active = true;

    fetchSpaceModules(space.id)
      .then((configurations) => {
        if (active) setModules(configurations);
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
  }, [space.id]);

  const toggle = async (configuration: SpaceModuleConfiguration) => {
    setBusyKey(configuration.key);
    setError(null);
    try {
      const updated = await updateSpaceModule(
        space.id,
        configuration.key,
        !configuration.enabled,
      );
      setModules((current) =>
        current.map((item) => (item.key === updated.key ? updated : item)),
      );
    } catch (updateError) {
      setError(spaceErrorMessage(updateError));
    } finally {
      setBusyKey(null);
    }
  };

  const navigableModules = modules.filter(
    (configuration) => configuration.enabled && configuration.available,
  );

  return (
    <section className="space-modules-panel" aria-labelledby="space-modules-title">
      <div className="module-panel-heading">
        <div>
          <p className="eyebrow">FUNCIONALIDADES</p>
          <h3 id="space-modules-title">Módulos de {space.name}</h3>
        </div>
        {isOwner ? <span className="role-badge">Configurable</span> : null}
      </div>

      {error ? <p className="form-error" role="alert">{error}</p> : null}

      {loading ? (
        <p className="muted-status" role="status">Cargando módulos…</p>
      ) : (
        <>
          {navigableModules.length > 0 ? (
            <nav className="module-navigation" aria-label="Módulos activos">
              {navigableModules.map((configuration) => (
                <a href={configuration.route} key={configuration.key}>
                  {configuration.name}
                </a>
              ))}
            </nav>
          ) : (
            <p className="module-empty-state">
              Todavía no hay módulos disponibles para abrir. Puedes dejar preparada
              su activación mientras construimos cada funcionalidad.
            </p>
          )}

          <ul className="module-config-list">
            {modules.map((configuration) => (
              <li key={configuration.key}>
                <span aria-hidden="true" className="module-config-icon">
                  {moduleIcons[configuration.icon]}
                </span>
                <div className="module-config-copy">
                  <div>
                    <strong>{configuration.name}</strong>
                    {!configuration.available ? (
                      <span className="coming-soon-badge">Próximamente</span>
                    ) : null}
                  </div>
                  <p>{configuration.description}</p>
                </div>
                {isOwner ? (
                  <label className="module-toggle">
                    <input
                      checked={configuration.enabled}
                      disabled={busyKey === configuration.key}
                      onChange={() => void toggle(configuration)}
                      type="checkbox"
                    />
                    <span>{configuration.enabled ? 'Activo' : 'Inactivo'}</span>
                  </label>
                ) : configuration.enabled ? (
                  <span className="enabled-label">Activo</span>
                ) : null}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
