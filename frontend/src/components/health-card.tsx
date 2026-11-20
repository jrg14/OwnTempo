import { API_DISPLAY_URL } from '../api/config';
import type { HealthResponse } from '../api/health';

type HealthCardProps = {
  status: 'checking' | 'online' | 'offline';
  data: HealthResponse | null;
  error: string | null;
  checkedAt: Date | null;
  onRetry: () => void;
};

const statusContent = {
  checking: {
    label: 'Comprobando servicios',
    detail: 'Conectando con el backend de OwnTempo…',
    className: 'is-checking',
  },
  online: {
    label: 'Todos los sistemas operativos',
    detail: 'OwnTempo está conectado y listo para usar.',
    className: 'is-online',
  },
  offline: {
    label: 'No se puede conectar',
    detail: 'Revisa que el backend esté iniciado y que la URL sea accesible.',
    className: 'is-offline',
  },
} as const;

export function HealthCard({
  status,
  data,
  error,
  checkedAt,
  onRetry,
}: HealthCardProps) {
  const content = statusContent[status];
  const checkedAtLabel = checkedAt?.toLocaleTimeString('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  });

  return (
    <article className="health-card">
      <div className="health-card__heading">
        <div>
          <h2>Estado de OwnTempo</h2>
        </div>
        <span
          aria-label={content.label}
          className={`status-indicator ${content.className}`}
          role="status"
        >
          <span className={status === 'checking' ? 'spinner' : 'status-dot'} />
        </span>
      </div>

      <p className={`status-label ${content.className}`}>{content.label}</p>
      <p className="health-card__detail">{error ?? content.detail}</p>

      {data ? (
        <details className="technical-details">
          <summary>Ver detalles técnicos</summary>
          <div className="health-card__checks">
            <span>Django · {data.checks.django}</span>
            <span>PostgreSQL · {data.checks.database}</span>
          </div>
        </details>
      ) : null}

      <footer className="health-card__footer">
        <div className="connection-info">
          <span className="api-url">{API_DISPLAY_URL}</span>
          {checkedAtLabel ? (
            <span>Última revisión: {checkedAtLabel}</span>
          ) : null}
        </div>
        <button
          disabled={status === 'checking'}
          onClick={onRetry}
          type="button"
        >
          Comprobar
        </button>
      </footer>
    </article>
  );
}

