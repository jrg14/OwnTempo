import { HealthCard } from './components/health-card';
import { ModuleCard } from './components/module-card';
import { useHealthCheck } from './hooks/use-health-check';

const modules = [
  { icon: '✓', title: 'Tareas', description: 'Organiza lo que tienes pendiente.' },
  { icon: '○', title: 'Calendario', description: 'Ten tus planes siempre a mano.' },
  { icon: '+', title: 'Compra', description: 'Comparte listas sin complicaciones.' },
  { icon: '€', title: 'Gastos', description: 'Separa lo personal de lo común.' },
];

export function App() {
  const health = useHealthCheck();

  return (
    <main>
      <div className="page-shell">
        <header className="brand-row">
          <span aria-hidden="true" className="logo-mark">
            <span />
          </span>
          <span className="brand">OwnTempo</span>
          <span className="preview-badge">PWA · PRIMERA VERSIÓN</span>
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

        <section className="spaces-card">
          <div aria-hidden="true" className="spaces-illustration">
            <span className="avatar avatar--back" />
            <span className="avatar avatar--middle" />
            <span className="avatar avatar--front" />
          </div>
          <div>
            <h2>Un espacio para cada parte de tu vida</h2>
            <p>
              Mantén tus cosas personales separadas y crea espacios comunes para
              organizarte con otras personas.
            </p>
          </div>
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
