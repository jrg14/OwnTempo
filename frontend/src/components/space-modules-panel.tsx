import { useEffect, useState } from 'react';

import {
  fetchSpaceModules,
  updateSpaceModule,
  type SpaceModuleConfiguration,
} from '../api/modules';
import type { Space } from '../api/spaces';
import { spaceErrorMessage } from '../hooks/use-spaces';
import { Icon } from './icon';

type SpaceModulesPanelProps = {
  onOpenModule: (moduleKey: SpaceModuleConfiguration['key']) => void;
  space: Space;
  showNavigation?: boolean;
  showHeading?: boolean;
};

export function SpaceModulesPanel({
  onOpenModule,
  showHeading = true,
  showNavigation = true,
  space,
}: SpaceModulesPanelProps) {
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
    <section
      className="space-modules-panel"
      id="space-modules"
      aria-labelledby="space-modules-title"
    >
      {showHeading ? (
        <div className="module-panel-heading">
          <h2 id="space-modules-title">¿Qué quieres organizar hoy?</h2>
        </div>
      ) : null}

      {error ? <p className="form-error" role="alert">{error}</p> : null}

      {loading ? (
        <p className="muted-status" role="status">Cargando módulos…</p>
      ) : (
        <>
          {showNavigation && navigableModules.length > 0 ? (
            <nav className="module-navigation" aria-label="Módulos activos">
              {navigableModules.map((configuration) => (
                <button key={configuration.key} onClick={() => onOpenModule(configuration.key)} type="button">
                  <span className="module-navigation__icon">
                    <Icon name={configuration.icon} />
                  </span>
                  <span className="module-navigation__copy">
                    <strong>{configuration.name}</strong>
                    <small>{configuration.description}</small>
                  </span>
                  <span className="module-navigation__action">Abrir</span>
                </button>
              ))}
            </nav>
          ) : showNavigation ? (
            <p className="module-empty-state">
              Todavía no hay módulos disponibles para abrir. Puedes dejar preparada
              su activación mientras construimos cada funcionalidad.
            </p>
          ) : null}

          {isOwner ? (
            <details className="module-settings">
              <summary>
                <span><Icon name="settings" />Configurar módulos</span>
                <Icon name="chevron" />
              </summary>
              <ul className="module-config-list">
                {modules.map((configuration) => (
                  <li key={configuration.key}>
                    <span aria-hidden="true" className="module-config-icon">
                      <Icon name={configuration.icon} />
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
                    <label className="module-toggle">
                      <input
                        checked={configuration.enabled}
                        disabled={busyKey === configuration.key}
                        onChange={() => void toggle(configuration)}
                        type="checkbox"
                      />
                      <span>{configuration.enabled ? 'Activo' : 'Inactivo'}</span>
                    </label>
                  </li>
                ))}
              </ul>
            </details>
          ) : null}
        </>
      )}
    </section>
  );
}
