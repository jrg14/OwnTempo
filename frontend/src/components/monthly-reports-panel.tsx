import { useEffect, useMemo, useState, type FormEvent } from 'react';

import {
  deleteMonthlyReport,
  fetchMonthlyReports,
  queueMonthlyReport,
  type MonthlyReportResult,
  type MonthlyTrainingReport,
} from '../api/training';
import { spaceErrorMessage } from '../hooks/use-spaces';

type MonthlyReportsPanelProps = {
  spaceId: number;
};

const currentMonth = () => {
  const value = new Date();
  return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}`;
};

const formatMonth = (month: string) => new Intl.DateTimeFormat('es-ES', {
  month: 'long',
  year: 'numeric',
  timeZone: 'UTC',
}).format(new Date(`${month}-01T00:00:00Z`));

const statusCopy: Record<MonthlyTrainingReport['status'], string> = {
  pending: 'En cola',
  processing: 'Analizando',
  completed: 'Listo',
  failed: 'No generado',
};

const scoreLabels: Record<keyof MonthlyReportResult['scores'], string> = {
  training: 'Entrenamiento',
  activity: 'Actividad',
  health_tracking: 'Seguimiento',
  consistency: 'Constancia',
};
const scoreOrder: Array<keyof MonthlyReportResult['scores']> = [
  'training',
  'activity',
  'health_tracking',
  'consistency',
];

function isCompletedResult(
  report: MonthlyTrainingReport | undefined,
): report is MonthlyTrainingReport & { result_payload: MonthlyReportResult } {
  return report?.status === 'completed' && 'title' in report.result_payload;
}

export function MonthlyReportsPanel({ spaceId }: MonthlyReportsPanelProps) {
  const [reports, setReports] = useState<MonthlyTrainingReport[]>([]);
  const [month, setMonth] = useState(currentMonth());
  const [goal, setGoal] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const report = useMemo(
    () => reports.find((candidate) => candidate.month === month),
    [month, reports],
  );
  const completedReport = isCompletedResult(report) ? report : null;
  const result = completedReport?.result_payload ?? null;
  const active = reports.some((candidate) => (
    candidate.status === 'pending' || candidate.status === 'processing'
  ));

  const refresh = async () => {
    const nextReports = await fetchMonthlyReports(spaceId);
    setReports(nextReports);
    return nextReports;
  };

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const nextReports = await fetchMonthlyReports(spaceId);
        if (mounted) {
          setReports(nextReports);
          setGoal(nextReports.find((item) => item.month === currentMonth())?.goal ?? '');
        }
      } catch (failure) {
        if (mounted) setError(spaceErrorMessage(failure));
      } finally {
        if (mounted) setLoading(false);
      }
    };
    void load();
    return () => { mounted = false; };
  }, [spaceId]);

  useEffect(() => {
    if (!active) return undefined;
    const interval = window.setInterval(() => {
      void refresh().catch((failure) => setError(spaceErrorMessage(failure)));
    }, 3000);
    return () => window.clearInterval(interval);
  // refresh only depends on the active space and is intentionally polled.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, spaceId]);

  const generate = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await queueMonthlyReport(spaceId, month, goal);
      await refresh();
    } catch (failure) {
      setError(spaceErrorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  const selectMonth = (nextMonth: string) => {
    setMonth(nextMonth);
    setGoal(reports.find((item) => item.month === nextMonth)?.goal ?? '');
  };

  const remove = async () => {
    if (!report || !window.confirm(`¿Eliminar el informe de ${formatMonth(month)}?`)) return;
    setBusy(true);
    setError(null);
    try {
      await deleteMonthlyReport(spaceId, report.id);
      await refresh();
    } catch (failure) {
      setError(spaceErrorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="training-report-loading" role="status"><span className="spinner" />Cargando informes…</div>;
  }

  return (
    <div className="training-reports" role="tabpanel">
      <header className="training-reports-heading">
        <div>
          <h2>Tu mes, con perspectiva</h2>
          <p>La IA local interpreta tus registros. Las cifras siempre se calculan en OwnTempo.</p>
        </div>
        <span>Privado · análisis local</span>
      </header>

      {error ? <p className="form-error" role="alert">{error}</p> : null}

      <form className="training-report-controls" onSubmit={(event) => void generate(event)}>
        <label>
          Mes
          <input
            max={currentMonth()}
            onChange={(event) => selectMonth(event.target.value)}
            required
            type="month"
            value={month}
          />
        </label>
        <label className="training-report-goal">
          Tu objetivo para este periodo
          <textarea
            maxLength={1000}
            onChange={(event) => setGoal(event.target.value)}
            placeholder="Por ejemplo: entrenar fuerza tres veces por semana y mejorar mi constancia."
            rows={2}
            value={goal}
          />
        </label>
        <button className="training-add-workout" disabled={busy || report?.status === 'processing'} type="submit">
          {report ? 'Regenerar informe' : 'Generar informe'}
        </button>
      </form>

      {!report ? (
        <section className="training-report-empty">
          <div aria-hidden="true">30</div>
          <h3>Aún no hay informe para {formatMonth(month)}</h3>
          <p>Cuando lo generes, compararemos entrenamientos, pasos y mediciones con el mes anterior.</p>
        </section>
      ) : null}

      {report && (report.status === 'pending' || report.status === 'processing') ? (
        <section className="training-report-progress" aria-live="polite">
          <span className="spinner" />
          <div>
            <strong>{report.status === 'pending' ? 'Informe en cola' : 'Analizando tus registros'}</strong>
            <p>Puedes seguir usando OwnTempo. Esta vista se actualizará automáticamente.</p>
          </div>
        </section>
      ) : null}

      {report?.status === 'failed' ? (
        <section className="training-report-failed" role="alert">
          <div>
            <strong>No se pudo generar el informe</strong>
            <p>{report.error_message || 'Comprueba que Ollama y el worker estén disponibles.'}</p>
          </div>
          <button className="secondary-button" disabled={busy} onClick={() => void remove()} type="button">Eliminar</button>
        </section>
      ) : null}

      {result ? (
        <article className="training-report-result">
          <header>
            <div>
              <span className={`training-report-status training-report-status--${result.overall_status}`}>
                {result.overall_status === 'on_track'
                  ? 'Buen rumbo'
                  : result.overall_status === 'needs_attention'
                    ? 'Conviene ajustar'
                    : 'Faltan datos'}
              </span>
              <h3>{result.title}</h3>
              <p>{result.summary}</p>
            </div>
            <button aria-label="Eliminar informe" disabled={busy} onClick={() => void remove()} type="button">Eliminar</button>
          </header>

          <dl className="training-report-scores">
            {scoreOrder.map((key) => (
              <div key={key}>
                <dt>{scoreLabels[key]}</dt>
                <dd>{result.scores[key]}<span>/10</span></dd>
              </div>
            ))}
          </dl>

          <div className="training-report-sections">
            <section>
              <h4>Lo que ha funcionado</h4>
              <ul>{result.highlights.map((item) => <li key={item}>{item}</li>)}</ul>
            </section>
            <section>
              <h4>Próximos ajustes</h4>
              <ul>{result.improvements.map((item) => <li key={item}>{item}</li>)}</ul>
            </section>
            <section className="training-report-actions">
              <h4>Acciones para el próximo mes</h4>
              <ol>{result.next_month_actions.map((item) => <li key={item}>{item}</li>)}</ol>
            </section>
          </div>

          {result.cautions.length ? (
            <aside>
              <strong>Cómo leer este análisis</strong>
              <ul>{result.cautions.map((item) => <li key={item}>{item}</li>)}</ul>
            </aside>
          ) : null}

          <footer>
            <span>{formatMonth(completedReport!.month)} · {statusCopy[completedReport!.status]}</span>
            <span>{completedReport!.model_name} · prompt {completedReport!.prompt_version}</span>
          </footer>
        </article>
      ) : null}

      <p className="training-report-disclaimer">
        Análisis orientativo basado en tus registros; no es un diagnóstico médico.
      </p>

      {reports.length > 1 ? (
        <nav className="training-report-history" aria-label="Informes anteriores">
          <span>Otros meses</span>
          {reports.filter((item) => item.month !== month).slice(0, 6).map((item) => (
            <button key={item.id} onClick={() => selectMonth(item.month)} type="button">
              {formatMonth(item.month)}<small>{statusCopy[item.status]}</small>
            </button>
          ))}
        </nav>
      ) : null}
    </div>
  );
}

