import { useEffect, useMemo, useState, type FormEvent } from 'react';

import {
  deleteMonthlyExpenseReport,
  fetchMonthlyExpenseReports,
  queueMonthlyExpenseReport,
  type ExpenseCategory,
  type ExpenseReportMetrics,
  type ExpenseReportResult,
  type MonthlyExpenseReport,
} from '../api/expenses';
import { spaceErrorMessage } from '../hooks/use-spaces';

type ExpenseReportsPanelProps = {
  categories: ExpenseCategory[];
  spaceId: number;
  spaceKind: 'personal' | 'shared';
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

const money = (value: number | null) => value == null
  ? 'Sin datos'
  : new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(value);

const signedMoney = (value: number | null) => value == null
  ? 'Sin referencia'
  : `${value > 0 ? '+' : ''}${money(value)}`;

const statusCopy: Record<MonthlyExpenseReport['status'], string> = {
  pending: 'En cola',
  processing: 'Analizando',
  completed: 'Listo',
  failed: 'No generado',
};

const scoreOrder: Array<keyof ExpenseReportResult['scores']> = [
  'spending_control',
  'trend',
  'savings_outlook',
];

const scoreLabels: Record<keyof ExpenseReportResult['scores'], string> = {
  spending_control: 'Control',
  trend: 'Evolución',
  savings_outlook: 'Ahorro previsto',
};

function isCompleted(report: MonthlyExpenseReport | undefined): report is MonthlyExpenseReport & {
  input_payload: ExpenseReportMetrics;
  result_payload: ExpenseReportResult;
} {
  return report?.status === 'completed'
    && 'current_month' in report.input_payload
    && 'title' in report.result_payload;
}

export function ExpenseReportsPanel({ categories, spaceId, spaceKind }: ExpenseReportsPanelProps) {
  const [reports, setReports] = useState<MonthlyExpenseReport[]>([]);
  const [month, setMonth] = useState(currentMonth());
  const [goal, setGoal] = useState('');
  const [budget, setBudget] = useState('');
  const [avoidableIds, setAvoidableIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const report = useMemo(
    () => reports.find((candidate) => candidate.month === month),
    [month, reports],
  );
  const completed = isCompleted(report) ? report : null;
  const metrics = completed?.input_payload ?? null;
  const result = completed?.result_payload ?? null;
  const active = reports.some((candidate) => (
    candidate.status === 'pending' || candidate.status === 'processing'
  ));

  const refresh = async () => {
    const next = await fetchMonthlyExpenseReports(spaceId);
    setReports(next);
    return next;
  };

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const next = await fetchMonthlyExpenseReports(spaceId);
        if (!mounted) return;
        setReports(next);
        const current = next.find((item) => item.month === currentMonth());
        if (current) {
          setGoal(current.goal);
          setBudget(current.monthly_budget ?? '');
          setAvoidableIds(current.avoidable_category_ids);
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
  // refresh intentionally follows the active report queue.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, spaceId]);

  const selectMonth = (nextMonth: string) => {
    const existing = reports.find((item) => item.month === nextMonth);
    setMonth(nextMonth);
    setGoal(existing?.goal ?? '');
    setBudget(existing?.monthly_budget ?? '');
    setAvoidableIds(existing?.avoidable_category_ids ?? []);
  };

  const toggleAvoidable = (categoryId: number) => {
    setAvoidableIds((current) => (
      current.includes(categoryId)
        ? current.filter((item) => item !== categoryId)
        : [...current, categoryId]
    ));
  };

  const generate = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await queueMonthlyExpenseReport(spaceId, {
        month,
        goal,
        monthly_budget: budget ? budget : null,
        avoidable_category_ids: avoidableIds,
      });
      await refresh();
    } catch (failure) {
      setError(spaceErrorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    if (!report || !window.confirm(`¿Eliminar el informe de ${formatMonth(month)}?`)) return;
    setBusy(true);
    setError(null);
    try {
      await deleteMonthlyExpenseReport(spaceId, report.id);
      await refresh();
    } catch (failure) {
      setError(spaceErrorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="expense-report-loading" role="status"><span className="spinner" />Preparando informes…</div>;
  }

  const scopeName = spaceKind === 'personal' ? 'tus gastos personales' : 'los gastos comunes';

  return (
    <div className="expense-reports" id="expense-reports-panel" role="tabpanel">
      <header className="expense-reports-heading">
        <div>
          <h2>Entender el gasto, decidir el siguiente paso</h2>
          <p>Compara {scopeName}, detecta excesos y proyecta el cierre del año con cálculos locales.</p>
        </div>
        <span>{spaceKind === 'personal' ? 'Solo tú' : 'Espacio compartido'} · IA local</span>
      </header>

      {error ? <p className="form-error" role="alert">{error}</p> : null}

      <form className="expense-report-form" onSubmit={(event) => void generate(event)}>
        <div className="expense-report-form__row">
          <label>Mes<input max={currentMonth()} onChange={(event) => selectMonth(event.target.value)} required type="month" value={month} /></label>
          <label>Presupuesto mensual, opcional<input min="0" onChange={(event) => setBudget(event.target.value)} placeholder="1500,00" step="0.01" type="number" value={budget} /></label>
        </div>
        <label>Objetivo del periodo<textarea maxLength={1000} onChange={(event) => setGoal(event.target.value)} placeholder="Por ejemplo: reducir ocio y ahorrar 400 € al mes." rows={2} value={goal} /></label>
        <fieldset>
          <legend>¿Qué categorías consideras evitables?</legend>
          <p>Las simulaciones del 10 % y 20 % se aplicarán únicamente a tu selección.</p>
          <div className="expense-report-categories">
            {categories.map((category) => (
              <label key={category.id}>
                <input checked={avoidableIds.includes(category.id)} onChange={() => toggleAvoidable(category.id)} type="checkbox" />
                {category.name}
              </label>
            ))}
          </div>
        </fieldset>
        <button className="expense-add-button" disabled={busy || report?.status === 'processing'} type="submit">
          {report ? 'Regenerar análisis' : 'Generar análisis'}
        </button>
      </form>

      {!report ? (
        <section className="expense-report-empty">
          <strong>{formatMonth(month)}</strong>
          <h3>Todavía no hay análisis</h3>
          <p>Genera el informe para comparar el mes con tu histórico y estimar el cierre anual.</p>
        </section>
      ) : null}

      {report && (report.status === 'pending' || report.status === 'processing') ? (
        <section className="expense-report-progress" aria-live="polite">
          <span className="spinner" />
          <div><strong>{report.status === 'pending' ? 'Análisis en cola' : 'Calculando tendencias'}</strong><p>Puedes seguir usando OwnTempo; esta vista se actualizará sola.</p></div>
        </section>
      ) : null}

      {report?.status === 'failed' ? (
        <section className="expense-report-failed" role="alert">
          <div><strong>No se pudo generar el análisis</strong><p>{report.error_message || 'Comprueba Ollama y el worker de informes.'}</p></div>
          <button className="secondary-button" disabled={busy} onClick={() => void remove()} type="button">Eliminar</button>
        </section>
      ) : null}

      {metrics && result ? (
        <article className="expense-report-result">
          <header>
            <div>
              <span className={`expense-report-status expense-report-status--${result.overall_status}`}>
                {result.overall_status === 'on_track' ? 'Buen control' : result.overall_status === 'needs_attention' ? 'Conviene revisar' : 'Faltan datos'}
              </span>
              <h3>{result.title}</h3>
              <p>{result.summary}</p>
            </div>
            <button disabled={busy} onClick={() => void remove()} type="button">Eliminar</button>
          </header>

          <dl className="expense-report-key-metrics">
            <div><dt>Gasto del mes</dt><dd>{money(metrics.current_month.total)}</dd><small>{metrics.current_month.movement_count} movimientos</small></div>
            <div><dt>Frente al mes anterior</dt><dd>{signedMoney(metrics.evolution.previous_month_change)}</dd><small>{metrics.evolution.trend === 'increasing' ? 'Tendencia al alza' : metrics.evolution.trend === 'decreasing' ? 'Tendencia a la baja' : 'Tendencia estable'}</small></div>
            <div><dt>Proyección anual</dt><dd>{money(metrics.annual_forecast.projected_expenses)}</dd><small>Estimación, no garantía</small></div>
            <div><dt>{spaceKind === 'personal' ? 'Ahorro previsto' : 'Disponible previsto'}</dt><dd>{money(metrics.annual_forecast.projected_savings)}</dd><small>Según ingresos registrados</small></div>
          </dl>

          <section className="expense-report-scenarios">
            <header><h4>Escenarios de reducción</h4><p>Impacto previsto sobre las categorías evitables durante el resto del año.</p></header>
            <div>
              {([
                ['baseline', 'Sin cambios'],
                ['reduce_avoidable_10', 'Reducir 10 %'],
                ['reduce_avoidable_20', 'Reducir 20 %'],
              ] as const).map(([key, label]) => {
                const scenario = metrics.annual_forecast.scenarios[key];
                return <article key={key}><span>{label}</span><strong>{money(scenario.projected_expenses)}</strong><small>{scenario.future_avoidable_reduction ? `${money(scenario.future_avoidable_reduction)} menos` : 'Referencia actual'}</small></article>;
              })}
            </div>
          </section>

          <section className="expense-report-categories-table">
            <header><h4>Gasto por categoría</h4><span>{money(metrics.avoidable_spending.current_total)} evitable</span></header>
            <div role="table" aria-label="Comparación de categorías">
              <div role="row"><span role="columnheader">Categoría</span><span role="columnheader">Mes</span><span role="columnheader">Media</span><span role="columnheader">Exceso</span></div>
              {metrics.current_month.categories.map((category) => (
                <div role="row" key={category.id}>
                  <span role="cell">{category.name}{category.avoidable ? <small>Evitable</small> : null}</span>
                  <span role="cell">{money(category.total)}</span>
                  <span role="cell">{money(category.historical_average)}</span>
                  <span className={category.excess && category.excess > 0 ? 'is-over' : ''} role="cell">{category.excess == null ? '—' : money(category.excess)}</span>
                </div>
              ))}
            </div>
          </section>

          <dl className="expense-report-scores">
            {scoreOrder.map((key) => <div key={key}><dt>{scoreLabels[key]}</dt><dd>{result.scores[key]}<span>/10</span></dd></div>)}
          </dl>

          <div className="expense-report-findings">
            <section><h4>Gasto evitable</h4><ul>{result.avoidable_findings.map((item) => <li key={item}>{item}</li>)}</ul></section>
            <section><h4>Evolución</h4><ul>{result.trend_findings.map((item) => <li key={item}>{item}</li>)}</ul></section>
            <section><h4>Previsión anual</h4><ul>{result.forecast_findings.map((item) => <li key={item}>{item}</li>)}</ul></section>
            <section className="expense-report-actions"><h4>Acciones recomendadas</h4><ol>{result.recommended_actions.map((item) => <li key={item}>{item}</li>)}</ol></section>
          </div>

          {[...metrics.data_quality.warnings, ...result.cautions].length ? (
            <aside><strong>Cómo leer este análisis</strong><ul>{[...metrics.data_quality.warnings, ...result.cautions].map((item) => <li key={item}>{item}</li>)}</ul></aside>
          ) : null}

          <footer><span>{formatMonth(completed!.month)} · {statusCopy[completed!.status]}</span><span>{completed!.model_name} · prompt {completed!.prompt_version}</span></footer>
        </article>
      ) : null}

      <p className="expense-report-disclaimer">Estimación orientativa basada en los datos registrados; no es asesoramiento financiero.</p>

      {reports.length > 1 ? (
        <nav className="expense-report-history" aria-label="Análisis anteriores">
          <span>Otros meses</span>
          {reports.filter((item) => item.month !== month).slice(0, 6).map((item) => (
            <button key={item.id} onClick={() => selectMonth(item.month)} type="button">{formatMonth(item.month)}<small>{statusCopy[item.status]}</small></button>
          ))}
        </nav>
      ) : null}
    </div>
  );
}

