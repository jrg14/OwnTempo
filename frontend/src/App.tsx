import { AccountCard } from './components/account-card';
import { HealthCard } from './components/health-card';
import { LoginScreen } from './components/login-screen';
import { ModuleCard } from './components/module-card';
import { SpacesWorkspace } from './components/spaces-workspace';
import { useAuth } from './hooks/use-auth';
import { useHealthCheck } from './hooks/use-health-check';

const modules = [
  { icon: '✓', title: 'Tareas', description: 'Organiza lo que tienes pendiente.' },
  { icon: '+', title: 'Compras', description: 'Comparte listas sin complicaciones.' },
  { icon: '♡', title: 'Deseos', description: 'Guarda ideas para más adelante.' },
  { icon: '○', title: 'Calendario', description: 'Ten tus planes siempre a mano.' },
  { icon: '€', title: 'Gastos', description: 'Separa lo personal de lo común.' },
];

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

  if (auth.status === 'checking') {
    return <LoadingScreen />;
  }

  if (auth.status === 'anonymous' || !auth.user) {
    return <LoginScreen busy={auth.busy} error={auth.error} onLogin={auth.login} />;
  }

  const displayName = auth.user.first_name || auth.user.username;

  return (
    <main>
      <div className="page-shell">
        <header className="brand-row">
          <span aria-hidden="true" className="logo-mark">
            <span />
          </span>
          <span className="brand">OwnTempo</span>
          <div className="session-actions">
            <span>Hola, {displayName}</span>
            <button
              className="text-button"
              disabled={auth.busy}
              onClick={() => void auth.logout()}
              type="button"
            >
              Salir
            </button>
          </div>
        </header>

        <section className="hero">
          <span aria-hidden="true" className="hero-circle hero-circle--large" />
          <span aria-hidden="true" className="hero-circle hero-circle--small" />
          <div className="hero__copy">
            <p className="hero__eyebrow">TU VIDA, A TU RITMO</p>
            <h1>Todo lo importante, en un solo lugar.</h1>
            <p>
              Organiza tu día a día y comparte solo lo que quieras con tu pareja,
              familia o compañeros de piso.
            </p>
          </div>
        </section>

        <section className="section" aria-labelledby="modules-title">
          <h2 id="modules-title">Una aplicación que se adapta a ti</h2>
          <p className="section__description">
            Activa los módulos que necesites y úsalos de forma personal o compartida.
          </p>
          <div className="module-grid">
            {modules.map((module) => (
              <ModuleCard key={module.title} {...module} />
            ))}
          </div>
        </section>

        <section className="section" aria-label="Espacios">
          <SpacesWorkspace />
        </section>

        <section className="section" aria-label="Cuenta personal">
          <AccountCard
            busy={auth.busy}
            error={auth.error}
            key={auth.user.id}
            onSave={auth.updateAccount}
            user={auth.user}
          />
        </section>

        <section className="section" aria-label="Estado técnico">
          <HealthCard
            checkedAt={health.checkedAt}
            data={health.data}
            error={health.error}
            onRetry={() => void health.refresh()}
            status={health.status}
          />
        </section>

        <footer className="page-footer">OwnTempo · Construyendo con calma</footer>
      </div>
    </main>
  );
}
