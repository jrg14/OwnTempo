import { useCallback, useEffect, useRef, useState } from 'react';

import { fetchSpaces, type Space } from './api/spaces';
import { fetchSpaceModules, type SpaceModuleConfiguration } from './api/modules';
import { AccountCard } from './components/account-card';
import { CalendarWorkspace } from './components/calendar-workspace';
import { ExpensesWorkspace } from './components/expenses-workspace';
import { HealthCard } from './components/health-card';
import { Icon } from './components/icon';
import { LoginScreen } from './components/login-screen';
import { SpacesWorkspace } from './components/spaces-workspace';
import { ShoppingWorkspace } from './components/shopping-workspace';
import { TasksWorkspace } from './components/tasks-workspace';
import { WishlistWorkspace } from './components/wishlist-workspace';
import { useAuth } from './hooks/use-auth';
import { useHealthCheck } from './hooks/use-health-check';

type AppView = 'home' | 'modules' | 'spaces' | 'account' | 'diagnostics' | 'tasks' | 'shopping' | 'wishlist' | 'calendar' | 'expenses';

function taskSpaceIdFromLocation() {
  const match = window.location.pathname.match(/^\/spaces\/(\d+)\/tasks\/?$/);
  return match ? Number(match[1]) : null;
}

function shoppingSpaceIdFromLocation() {
  const match = window.location.pathname.match(/^\/spaces\/(\d+)\/shopping\/?$/);
  return match ? Number(match[1]) : null;
}

function wishlistSpaceIdFromLocation() {
  const match = window.location.pathname.match(/^\/spaces\/(\d+)\/wishlist\/?$/);
  return match ? Number(match[1]) : null;
}

function calendarSpaceIdFromLocation() {
  const match = window.location.pathname.match(/^\/spaces\/(\d+)\/calendar\/?$/);
  return match ? Number(match[1]) : null;
}

function expensesSpaceIdFromLocation() {
  const match = window.location.pathname.match(/^\/spaces\/(\d+)\/expenses\/?$/);
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
  const initialShoppingSpaceId = shoppingSpaceIdFromLocation();
  const initialWishlistSpaceId = wishlistSpaceIdFromLocation();
  const initialCalendarSpaceId = calendarSpaceIdFromLocation();
  const initialExpensesSpaceId = expensesSpaceIdFromLocation();
  const [activeView, setActiveView] = useState<AppView>(
    initialTaskSpaceId
      ? 'tasks'
      : initialShoppingSpaceId
        ? 'shopping'
        : initialWishlistSpaceId
          ? 'wishlist'
          : initialCalendarSpaceId
            ? 'calendar'
            : initialExpensesSpaceId
              ? 'expenses'
            : 'home',
  );
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [taskSpace, setTaskSpace] = useState<Space | null>(null);
  const [taskSpaceId, setTaskSpaceId] = useState<number | null>(initialTaskSpaceId);
  const [shoppingSpace, setShoppingSpace] = useState<Space | null>(null);
  const [shoppingSpaceId, setShoppingSpaceId] = useState<number | null>(initialShoppingSpaceId);
  const [wishlistSpace, setWishlistSpace] = useState<Space | null>(null);
  const [wishlistSpaceId, setWishlistSpaceId] = useState<number | null>(initialWishlistSpaceId);
  const [calendarSpace, setCalendarSpace] = useState<Space | null>(null);
  const [calendarSpaceId, setCalendarSpaceId] = useState<number | null>(initialCalendarSpaceId);
  const [expensesSpace, setExpensesSpace] = useState<Space | null>(null);
  const [expensesSpaceId, setExpensesSpaceId] = useState<number | null>(initialExpensesSpaceId);
  const [homeNotice, setHomeNotice] = useState<string | null>(null);
  const [menuSpaces, setMenuSpaces] = useState<Space[]>([]);
  const [menuModules, setMenuModules] = useState<Record<number, SpaceModuleConfiguration[]>>({});
  const profileButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!profileMenuOpen || !auth.user) return;
    let active = true;
    fetchSpaces()
      .then(async (spaces) => {
        const entries = await Promise.all(
          spaces.map(async (space) => [space.id, await fetchSpaceModules(space.id)] as const),
        );
        if (!active) return;
        setMenuSpaces(spaces);
        setMenuModules(Object.fromEntries(entries));
      })
      .catch(() => {
        if (active) {
          setMenuSpaces([]);
          setMenuModules({});
        }
      });
    return () => { active = false; };
  }, [auth.user, profileMenuOpen]);

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
      const routeShoppingSpaceId = shoppingSpaceIdFromLocation();
      const routeWishlistSpaceId = wishlistSpaceIdFromLocation();
      const routeCalendarSpaceId = calendarSpaceIdFromLocation();
      const routeExpensesSpaceId = expensesSpaceIdFromLocation();
      setTaskSpaceId(routeSpaceId);
      setTaskSpace(null);
      setShoppingSpaceId(routeShoppingSpaceId);
      setShoppingSpace(null);
      setWishlistSpaceId(routeWishlistSpaceId);
      setWishlistSpace(null);
      setCalendarSpaceId(routeCalendarSpaceId);
      setCalendarSpace(null);
      setExpensesSpaceId(routeExpensesSpaceId);
      setExpensesSpace(null);
      setActiveView(
        routeSpaceId ? 'tasks' : routeShoppingSpaceId ? 'shopping' : routeWishlistSpaceId ? 'wishlist' : routeCalendarSpaceId ? 'calendar' : routeExpensesSpaceId ? 'expenses' : 'home',
      );
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

  useEffect(() => {
    if (!auth.user || !shoppingSpaceId || shoppingSpace?.id === shoppingSpaceId) return;
    let active = true;
    fetchSpaces()
      .then((spaces) => {
        if (!active) return;
        const space = spaces.find((candidate) => candidate.id === shoppingSpaceId);
        if (space) {
          setShoppingSpace(space);
        } else {
          setHomeNotice('Ese espacio ya no está disponible.');
          window.history.replaceState({}, '', '/');
          setShoppingSpaceId(null);
          setActiveView('home');
        }
      })
      .catch(() => {
        if (active) setHomeNotice('No pudimos abrir el espacio solicitado.');
      });
    return () => { active = false; };
  }, [auth.user, shoppingSpace, shoppingSpaceId]);

  useEffect(() => {
    if (!auth.user || !wishlistSpaceId || wishlistSpace?.id === wishlistSpaceId) return;
    let active = true;
    fetchSpaces()
      .then((spaces) => {
        if (!active) return;
        const space = spaces.find((candidate) => candidate.id === wishlistSpaceId);
        if (space) setWishlistSpace(space);
        else {
          setHomeNotice('Ese espacio ya no está disponible.');
          window.history.replaceState({}, '', '/');
          setWishlistSpaceId(null);
          setActiveView('home');
        }
      })
      .catch(() => { if (active) setHomeNotice('No pudimos abrir el espacio solicitado.'); });
    return () => { active = false; };
  }, [auth.user, wishlistSpace, wishlistSpaceId]);

  useEffect(() => {
    if (!auth.user || !calendarSpaceId || calendarSpace?.id === calendarSpaceId) return;
    let active = true;
    fetchSpaces()
      .then((spaces) => {
        if (!active) return;
        const space = spaces.find((candidate) => candidate.id === calendarSpaceId);
        if (space) setCalendarSpace(space);
        else {
          setHomeNotice('Ese espacio ya no está disponible.');
          window.history.replaceState({}, '', '/');
          setCalendarSpaceId(null);
          setActiveView('home');
        }
      })
      .catch(() => { if (active) setHomeNotice('No pudimos abrir el espacio solicitado.'); });
    return () => { active = false; };
  }, [auth.user, calendarSpace, calendarSpaceId]);

  useEffect(() => {
    if (!auth.user || !expensesSpaceId || expensesSpace?.id === expensesSpaceId) return;
    let active = true;
    fetchSpaces()
      .then((spaces) => {
        if (!active) return;
        const space = spaces.find((candidate) => candidate.id === expensesSpaceId);
        if (space) setExpensesSpace(space);
        else {
          setHomeNotice('Ese espacio ya no está disponible.');
          window.history.replaceState({}, '', '/');
          setExpensesSpaceId(null);
          setActiveView('home');
        }
      })
      .catch(() => { if (active) setHomeNotice('No pudimos abrir el espacio solicitado.'); });
    return () => { active = false; };
  }, [auth.user, expensesSpace, expensesSpaceId]);

  const goHome = useCallback(() => {
    if (window.location.pathname !== '/') window.history.pushState({}, '', '/');
    setActiveView('home');
    setTaskSpaceId(null);
    setTaskSpace(null);
    setShoppingSpaceId(null);
    setShoppingSpace(null);
    setWishlistSpaceId(null);
    setWishlistSpace(null);
    setCalendarSpaceId(null);
    setCalendarSpace(null);
    setExpensesSpaceId(null);
    setExpensesSpace(null);
    window.scrollTo({ top: 0 });
  }, []);

  const handleTasksUnavailable = useCallback(() => {
    setHomeNotice('El módulo de tareas se ha desactivado en este espacio.');
    goHome();
  }, [goHome]);

  const handleShoppingUnavailable = useCallback(() => {
    setHomeNotice('El módulo de listas de la compra se ha desactivado en este espacio.');
    goHome();
  }, [goHome]);

  const handleWishlistUnavailable = useCallback(() => {
    setHomeNotice('El módulo de lista de deseos se ha desactivado en este espacio.');
    goHome();
  }, [goHome]);

  const handleCalendarUnavailable = useCallback(() => {
    setHomeNotice('El módulo de calendario se ha desactivado en este espacio.');
    goHome();
  }, [goHome]);

  const handleExpensesUnavailable = useCallback(() => {
    setHomeNotice('El módulo de gastos se ha desactivado en este espacio.');
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

  const openShopping = (space: Space) => {
    window.history.pushState({}, '', `/spaces/${space.id}/shopping/`);
    setHomeNotice(null);
    setShoppingSpace(space);
    setShoppingSpaceId(space.id);
    setActiveView('shopping');
    window.scrollTo({ top: 0 });
  };

  const openWishlist = (space: Space) => {
    window.history.pushState({}, '', `/spaces/${space.id}/wishlist/`);
    setHomeNotice(null);
    setWishlistSpace(space);
    setWishlistSpaceId(space.id);
    setActiveView('wishlist');
    window.scrollTo({ top: 0 });
  };

  const openCalendar = (space: Space) => {
    window.history.pushState({}, '', `/spaces/${space.id}/calendar/`);
    setHomeNotice(null);
    setCalendarSpace(space);
    setCalendarSpaceId(space.id);
    setActiveView('calendar');
    window.scrollTo({ top: 0 });
  };

  const openExpenses = (space: Space) => {
    window.history.pushState({}, '', `/spaces/${space.id}/expenses/`);
    setHomeNotice(null);
    setExpensesSpace(space);
    setExpensesSpaceId(space.id);
    setActiveView('expenses');
    window.scrollTo({ top: 0 });
  };

  const openMenuModule = (space: Space, moduleKey: SpaceModuleConfiguration['key']) => {
    const module = menuModules[space.id]?.find((item) => item.key === moduleKey);
    if (!module?.enabled || !module.available) return;
    if (moduleKey === 'tasks') openTasks(space);
    if (moduleKey === 'shopping') openShopping(space);
    if (moduleKey === 'wishlist') openWishlist(space);
    if (moduleKey === 'calendar') openCalendar(space);
    if (moduleKey === 'expenses') openExpenses(space);
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
          <section className="empty-home" id="home" aria-label="Inicio" />
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

        {activeView === 'spaces' ? (
          <section className="app-subpage" aria-labelledby="spaces-page-title">
            <button className="back-button" onClick={goHome} type="button">
              <Icon name="arrow-left" />
              Volver al inicio
            </button>
            <header className="subpage-heading">
              <h1 id="spaces-page-title">Gestionar espacios</h1>
              <p>Administra tus espacios, miembros e invitaciones.</p>
            </header>
            <SpacesWorkspace
              mode="manage"
              notice={homeNotice}
              onOpenCalendar={openCalendar}
              onOpenExpenses={openExpenses}
              onOpenShopping={openShopping}
              onOpenTasks={openTasks}
              onOpenWishlist={openWishlist}
            />
          </section>
        ) : null}

        {activeView === 'modules' ? (
          <section className="app-subpage" aria-labelledby="modules-page-title">
            <button className="back-button" onClick={goHome} type="button">
              <Icon name="arrow-left" />
              Volver al inicio
            </button>
            <header className="subpage-heading">
              <h1 id="modules-page-title">Configurar módulos</h1>
              <p>Elige qué módulos quieres utilizar en cada espacio.</p>
            </header>
            <SpacesWorkspace
              mode="home"
              onOpenCalendar={openCalendar}
              onOpenExpenses={openExpenses}
              onOpenShopping={openShopping}
              onOpenTasks={openTasks}
              onOpenWishlist={openWishlist}
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

        {activeView === 'shopping' && shoppingSpace ? (
          <ShoppingWorkspace
            onBack={goHome}
            onModuleUnavailable={handleShoppingUnavailable}
            space={shoppingSpace}
          />
        ) : activeView === 'shopping' ? (
          <div className="app-subpage" role="status">Preparando el espacio…</div>
        ) : null}

        {activeView === 'wishlist' && wishlistSpace ? (
          <WishlistWorkspace
            onBack={goHome}
            onModuleUnavailable={handleWishlistUnavailable}
            space={wishlistSpace}
          />
        ) : activeView === 'wishlist' ? (
          <div className="app-subpage" role="status">Preparando el espacio…</div>
        ) : null}

        {activeView === 'calendar' && calendarSpace ? (
          <CalendarWorkspace
            onBack={goHome}
            onModuleUnavailable={handleCalendarUnavailable}
            space={calendarSpace}
          />
        ) : activeView === 'calendar' ? (
          <div className="app-subpage" role="status">Preparando el espacio…</div>
        ) : null}

        {activeView === 'expenses' && expensesSpace ? (
          <ExpensesWorkspace
            currentUserId={auth.user.id}
            onBack={goHome}
            onModuleUnavailable={handleExpensesUnavailable}
            space={expensesSpace}
          />
        ) : activeView === 'expenses' ? (
          <div className="app-subpage" role="status">Preparando el espacio…</div>
        ) : null}
      </div>

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
              <div className="profile-menu__spaces">
                <span className="profile-menu__section-label">Mis espacios</span>
                {menuSpaces.map((space) => (
                  <div className="profile-menu__space" key={space.id}>
                    <strong><Icon name={space.kind === 'personal' ? 'home' : 'users'} />{space.name}</strong>
                    <div className="profile-menu__modules">
                      {menuModules[space.id]?.filter((module) => module.enabled && module.available).map((module) => (
                        <button key={module.key} onClick={() => openMenuModule(space, module.key)} type="button">
                          <Icon name={module.icon} />{module.name}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={() => openView('modules')} type="button">
                <span className="profile-menu__item-icon"><Icon name="settings" /></span>
                <span><strong>Configurar módulos</strong><small>Activar módulos por espacio</small></span>
                <Icon name="arrow-right" />
              </button>
              <button onClick={() => openView('spaces')} type="button">
                <span className="profile-menu__item-icon"><Icon name="users" /></span>
                <span><strong>Gestionar espacios</strong><small>Crear, editar y administrar miembros</small></span>
                <Icon name="arrow-right" />
              </button>
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
