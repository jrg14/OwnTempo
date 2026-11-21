import { useCallback, useEffect, useRef, useState } from 'react';

import { fetchSpaces, type Space } from './api/spaces';
import { AccountCard } from './components/account-card';
import { HealthCard } from './components/health-card';
import { Icon } from './components/icon';
import { LoginScreen } from './components/login-screen';
import { SpacesWorkspace } from './components/spaces-workspace';
import { TasksWorkspace } from './components/tasks-workspace';
import { useAuth } from './hooks/use-auth';
import { useHealthCheck } from './hooks/use-health-check';

type AppView = 'home' | 'account' | 'diagnostics' | 'tasks';

function taskSpaceIdFromLocation() {
  const match = window.location.pathname.match(/^\/spaces\/(\d+)\/tasks\/?$/);
  return match ? Number(match[1]) : null;
}

function LoadingScreen() {
  return (
    <main className="auth-page">
      <div className="loading-card" role="status">
        <span aria-hidden="true" className="spinner" />
        <p>Preparando OwnTempo…</p>
      </div>
    </main>
  );
}

export function App() {
  const auth = useAuth();
  const health = useHealthCheck();
  const initialTaskSpaceId = taskSpaceIdFromLocation();
  const [activeView, setActiveView] = useState<AppView>(
    initialTaskSpaceId ? 'tasks' : 'home',
  );
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [taskSpace, setTaskSpace] = useState<Space | null>(null);
  const [taskSpaceId, setTaskSpaceId] = useState<number | null>(initialTaskSpaceId);
  const [homeNotice, setHomeNotice] = useState<string | null>(null);
  const profileButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!profileMenuOpen) return;

    const previousOverflow = document.body.style.overflow;
    const profileButton = profileButtonRef.current;
    const handleMenuKeyboard = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setProfileMenuOpen(false);
        return;
      }

      if (event.key !== 'Tab') return;

      const menu = document.getElementById('profile-menu');
      const focusable = Array.from(
        menu?.querySelectorAll<HTMLElement>('button:not(:disabled), a[href]') ?? [],
      );
      const first = focusable[0];
      const last = focusable.at(-1);

      if (!first || !last) return;

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleMenuKeyboard);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleMenuKeyboard);
      profileButton?.focus();
    };
  }, [profileMenuOpen]);

  useEffect(() => {
    const handleNavigation = () => {
      const routeSpaceId = taskSpaceIdFromLocation();
      setTaskSpaceId(routeSpaceId);
      setTaskSpace(null);
      setActiveView(routeSpaceId ? 'tasks' : 'home');
    };
    window.addEventListener('popstate', handleNavigation);
    return () => window.removeEventListener('popstate', handleNavigation);
  }, []);

  useEffect(() => {
    if (!auth.user || !taskSpaceId || taskSpace?.id === taskSpaceId) return;
    let active = true;
    fetchSpaces()
      .then((spaces) => {
        if (!active) return;
        const space = spaces.find((candidate) => candidate.id === taskSpaceId);
        if (space) {
          setTaskSpace(space);
        } else {
          setHomeNotice('Ese espacio ya no está disponible.');
          window.history.replaceState({}, '', '/');
          setTaskSpaceId(null);
          setActiveView('home');
        }
      })
      .catch(() => {
        if (active) setHomeNotice('No pudimos abrir el espacio solicitado.');
      });
    return () => {
      active = false;
    };
  }, [auth.user, taskSpace, taskSpaceId]);

  const goHome = useCallback(() => {
    if (window.location.pathname !== '/') window.history.pushState({}, '', '/');
    setActiveView('home');
    setTaskSpaceId(null);
    setTaskSpace(null);
    window.scrollTo({ top: 0 });
  }, []);

  const handleTasksUnavailable = useCallback(() => {
    setHomeNotice('El módulo de tareas se ha desactivado en este espacio.');
    goHome();
  }, [goHome]);

  if (auth.status === 'checking') {
    return <LoadingScreen />;
  }

  if (auth.status === 'anonymous' || !auth.user) {
    return <LoginScreen busy={auth.busy} error={auth.error} onLogin={auth.login} />;
  }

  const displayName = auth.user.first_name || auth.user.username;

  const openView = (view: Exclude<AppView, 'home'>) => {
    setActiveView(view);
    setProfileMenuOpen(false);
    window.scrollTo({ top: 0 });
  };

  const openTasks = (space: Space) => {
    window.history.pushState({}, '', `/spaces/${space.id}/tasks/`);
    setHomeNotice(null);
    setTaskSpace(space);
    setTaskSpaceId(space.id);
    setActiveView('tasks');
    window.scrollTo({ top: 0 });
  };

  return (
    <main className="app-page">
      <div className="app-shell">
        <header className="brand-row app-header">
          <span aria-hidden="true" className="logo-mark">
            <span />
          </span>
          <span className="brand">OwnTempo</span>
          <div className="session-actions">
            <span className="welcome-copy">Hola, {displayName}</span>
            <button
              aria-controls="profile-menu"
              aria-expanded={profileMenuOpen}
              aria-label={`Abrir menú de ${displayName}`}
              className="header-avatar"
              onClick={() => setProfileMenuOpen(true)}
              ref={profileButtonRef}
              type="button"
            >
              {displayName.slice(0, 1).toUpperCase()}
            </button>
          </div>
        </header>

        {activeView === 'home' ? (
          <>
            <section id="home" aria-label="Inicio">
              <SpacesWorkspace
                notice={homeNotice}
                onOpenTasks={openTasks}
              />
            </section>
            <footer className="page-footer">OwnTempo · A tu ritmo</footer>
          </>
        ) : null}

        {activeView === 'account' ? (
          <section className="app-subpage" aria-labelledby="account-page-title">
            <button className="back-button" onClick={goHome} type="button">
              <Icon name="arrow-left" />
              Volver al inicio
            </button>
            <header className="subpage-heading">
              <h1 id="account-page-title">Cuenta y ajustes</h1>
              <p>Actualiza la información que utilizas en OwnTempo.</p>
            </header>
            <AccountCard
              busy={auth.busy}
              error={auth.error}
              key={auth.user.id}
              onSave={auth.updateAccount}
              user={auth.user}
            />
          </section>
        ) : null}

        {activeView === 'diagnostics' ? (
          <section className="app-subpage" aria-labelledby="diagnostics-page-title">
            <button className="back-button" onClick={goHome} type="button">
              <Icon name="arrow-left" />
              Volver al inicio
            </button>
            <header className="subpage-heading">
              <h1 id="diagnostics-page-title">Ayuda y diagnóstico</h1>
              <p>
                Comprueba el estado de OwnTempo y vuelve a intentarlo si hay algún
                problema.
              </p>
            </header>
            <HealthCard
              checkedAt={health.checkedAt}
              data={health.data}
              error={health.error}
              onRetry={() => void health.refresh()}
              status={health.status}
            />
          </section>
        ) : null}

        {activeView === 'tasks' && taskSpace ? (
          <TasksWorkspace
            onBack={goHome}
            onModuleUnavailable={handleTasksUnavailable}
            space={taskSpace}
          />
        ) : activeView === 'tasks' ? (
          <div className="app-subpage" role="status">Preparando el espacio…</div>
        ) : null}
      </div>

      {activeView === 'home' ? (
        <nav className="bottom-navigation" aria-label="Navegación principal">
          <a href="#home"><Icon name="home" /><span>Inicio</span></a>
          <a href="#space-modules"><Icon name="activity" /><span>Módulos</span></a>
          <a href="#space-management"><Icon name="users" /><span>Gestionar</span></a>
        </nav>
      ) : null}

      {profileMenuOpen ? (
        <div className="profile-menu-layer">
          <button
            aria-label="Cerrar menú"
            className="profile-menu-backdrop"
            onClick={() => setProfileMenuOpen(false)}
            type="button"
          />
          <aside
            aria-label={`Menú de ${displayName}`}
            aria-modal="true"
            className="profile-menu"
            id="profile-menu"
            role="dialog"
          >
            <header className="profile-menu__header">
              <span className="profile-menu__avatar">
                {displayName.slice(0, 1).toUpperCase()}
              </span>
              <div>
                <strong>{displayName}</strong>
                <span>@{auth.user.username}</span>
              </div>
              <button
                aria-label="Cerrar menú"
                autoFocus
                className="profile-menu__close"
                onClick={() => setProfileMenuOpen(false)}
                type="button"
              >
                <Icon name="close" />
              </button>
            </header>

            <nav className="profile-menu__navigation" aria-label="Opciones personales">
              <button onClick={() => openView('account')} type="button">
                <span className="profile-menu__item-icon"><Icon name="settings" /></span>
                <span>
                  <strong>Cuenta y ajustes</strong>
                  <small>Datos personales y preferencias</small>
                </span>
                <Icon name="arrow-right" />
              </button>
              <button onClick={() => openView('diagnostics')} type="button">
                <span className="profile-menu__item-icon"><Icon name="activity" /></span>
                <span>
                  <strong>Ayuda y diagnóstico</strong>
                  <small>Estado y conexión de OwnTempo</small>
                </span>
                <Icon name="arrow-right" />
              </button>
            </nav>

            <footer className="profile-menu__footer">
              <button disabled={auth.busy} onClick={() => void auth.logout()} type="button">
                <Icon name="logout" />
                {auth.busy ? 'Cerrando sesión…' : 'Cerrar sesión'}
              </button>
            </footer>
          </aside>
        </div>
      ) : null}
    </main>
  );
}
