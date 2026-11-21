import { useEffect, useMemo, useState, type FormEvent } from 'react';

import {
  createCommonExpense,
  createExpenseCategory,
  createExpensePeriod,
  createPersonalExpense,
  deleteCommonExpense,
  deletePersonalExpense,
  fetchCommonExpenses,
  fetchExpenseCategories,
  fetchExpensePeriods,
  fetchExpenseSummary,
  fetchPersonalExpenses,
  updateCommonExpense,
  updateExpenseCategory,
  updateExpensePeriod,
  updatePersonalExpense,
  type ExpenseCategory,
  type ExpenseEntry,
  type ExpenseEntryInput,
  type ExpenseParticipant,
  type ExpensePeriod,
  type ExpenseSplitMode,
  type ExpenseSummary,
  type ParticipantInput,
} from '../api/expenses';
import { fetchSpaceModules } from '../api/modules';
import { fetchMembers, type Space, type SpaceMember } from '../api/spaces';
import { spaceErrorMessage } from '../hooks/use-spaces';
import { Icon } from './icon';

type ExpensesWorkspaceProps = {
  currentUserId: number;
  onBack: () => void;
  onModuleUnavailable: () => void;
  space: Space;
};

const pad = (value: number) => String(value).padStart(2, '0');
const monthKey = (year: number, month: number) => `${year}-${pad(month)}`;
const today = new Date();
const initialMonth = monthKey(today.getFullYear(), today.getMonth() + 1);
const money = (value: string | number) => new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' }).format(Number(value));
const displayName = (user: { username: string; first_name: string }) => user.first_name || user.username;

function EntryForm({ categories, editing, kind, participants, period, busy, onCancel, onSave }: {
  categories: ExpenseCategory[];
  editing: ExpenseEntry | null;
  kind: 'common' | 'personal';
  participants: ExpenseParticipant[];
  period: ExpensePeriod;
  busy: boolean;
  onCancel: () => void;
  onSave: (input: ExpenseEntryInput) => Promise<void>;
}) {
  const [description, setDescription] = useState(editing?.description ?? '');
  const [amount, setAmount] = useState(editing?.amount ?? '');
  const [spentOn, setSpentOn] = useState(editing?.spent_on ?? `${monthKey(period.year, period.month)}-01`);
  const [categoryId, setCategoryId] = useState(editing?.category.id ?? categories.find((item) => item.is_active)?.id ?? 0);
  const [paidById, setPaidById] = useState(editing?.paid_by?.id ?? participants[0]?.id ?? 0);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSave({
      description: description.trim(),
      amount,
      spent_on: spentOn,
      category_id: categoryId,
      ...(kind === 'common' ? { paid_by_id: paidById } : {}),
    });
  };

  return (
    <form className="expense-entry-form" onSubmit={(event) => void submit(event)}>
      <h3>{editing ? 'Editar' : 'Añadir'} gasto {kind === 'common' ? 'común' : 'personal'}</h3>
      <div className="expense-form-grid">
        <label><span>Concepto</span><input maxLength={200} onChange={(event) => setDescription(event.target.value)} required value={description} /></label>
        <label><span>Importe</span><input min="0.01" onChange={(event) => setAmount(event.target.value)} required step="0.01" type="number" value={amount} /></label>
        <label><span>Fecha</span><input max={`${monthKey(period.year, period.month)}-31`} min={`${monthKey(period.year, period.month)}-01`} onChange={(event) => setSpentOn(event.target.value)} required type="date" value={spentOn} /></label>
        <label><span>Categoría</span><select onChange={(event) => setCategoryId(Number(event.target.value))} required value={categoryId}>{categories.filter((item) => item.is_active || item.id === editing?.category.id).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
        {kind === 'common' ? <label><span>Pagado por</span><select onChange={(event) => setPaidById(Number(event.target.value))} value={paidById}>{participants.map((item) => <option key={item.id} value={item.id}>{displayName(item.user)}</option>)}</select></label> : null}
      </div>
      <div className="expense-form-actions">
        <button className="primary-button" disabled={busy || !description.trim() || !amount || !categoryId} type="submit">{busy ? 'Guardando…' : 'Guardar'}</button>
        {editing ? <button className="secondary-button" disabled={busy} onClick={onCancel} type="button">Cancelar</button> : null}
      </div>
    </form>
  );
}

function PeriodSetup({ currentUserId, members, month, busy, onCreate }: {
  currentUserId: number;
  members: SpaceMember[];
  month: string;
  busy: boolean;
  onCreate: (mode: ExpenseSplitMode, participants: ParticipantInput[]) => Promise<void>;
}) {
  const current = members.find((member) => member.id === currentUserId) ?? members[0];
  const other = members.find((member) => member.id !== current?.id);
  const [firstId, setFirstId] = useState(current?.id ?? 0);
  const [secondId, setSecondId] = useState(other?.id ?? 0);
  const [firstIncome, setFirstIncome] = useState('0.00');
  const [secondIncome, setSecondIncome] = useState('0.00');
  const [mode, setMode] = useState<ExpenseSplitMode>('income');
  const [firstPercentage, setFirstPercentage] = useState('50.00');
  const secondPercentage = String(Math.max(0, 100 - Number(firstPercentage || 0)).toFixed(2));

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onCreate(mode, [
      { user_id: firstId, income: firstIncome, custom_percentage: firstPercentage },
      { user_id: secondId, income: secondIncome, custom_percentage: secondPercentage },
    ]);
  };

  if (members.length < 2) return <div className="expense-empty"><Icon name="users" /><h2>Falta otra persona</h2><p>Invita a tu pareja al espacio antes de crear el periodo.</p></div>;

  return (
    <form className="expense-setup" onSubmit={(event) => void submit(event)}>
      <header><h2>Configurar {new Date(`${month}-01T12:00:00`).toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}</h2><p>Elige las dos personas, sus ingresos y cómo se reparten los gastos comunes.</p></header>
      <div className="expense-participant-grid">
        <label><span>Primera persona</span><select onChange={(event) => setFirstId(Number(event.target.value))} value={firstId}>{members.map((member) => <option disabled={member.id === secondId} key={member.id} value={member.id}>{displayName(member)}</option>)}</select></label>
        <label><span>Ingreso</span><input min="0" onChange={(event) => setFirstIncome(event.target.value)} required step="0.01" type="number" value={firstIncome} /></label>
        <label><span>Segunda persona</span><select onChange={(event) => setSecondId(Number(event.target.value))} value={secondId}>{members.map((member) => <option disabled={member.id === firstId} key={member.id} value={member.id}>{displayName(member)}</option>)}</select></label>
        <label><span>Ingreso</span><input min="0" onChange={(event) => setSecondIncome(event.target.value)} required step="0.01" type="number" value={secondIncome} /></label>
      </div>
      <fieldset className="expense-split-options"><legend>Regla de reparto</legend>{([['equal', '50/50'], ['income', 'Proporcional a ingresos'], ['custom', 'Porcentaje personalizado']] as const).map(([value, label]) => <label key={value}><input checked={mode === value} name="split-mode" onChange={() => setMode(value)} type="radio" />{label}</label>)}</fieldset>
      {mode === 'custom' ? <div className="expense-percentage"><label><span>Porcentaje primera persona</span><input max="100" min="0" onChange={(event) => setFirstPercentage(event.target.value)} step="0.01" type="number" value={firstPercentage} /></label><strong>{secondPercentage}% para la segunda</strong></div> : null}
      <button className="primary-button" disabled={busy || firstId === secondId || (mode === 'income' && Number(firstIncome) + Number(secondIncome) <= 0)} type="submit">{busy ? 'Creando…' : 'Crear periodo'}</button>
    </form>
  );
}

function PersonalPeriodSetup({ currentUserId, month, busy, onCreate }: {
  currentUserId: number;
  month: string;
  busy: boolean;
  onCreate: (participants: ParticipantInput[]) => Promise<void>;
}) {
  const [startingSavings, setStartingSavings] = useState('0.00');
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onCreate([{
      user_id: currentUserId,
      income: '0.00',
      personal_starting_savings: startingSavings,
      custom_percentage: '100.00',
    }]);
  };
  return <form className="expense-setup expense-setup--personal" onSubmit={(event) => void submit(event)}><header><h2>Configurar {new Date(`${month}-01T12:00:00`).toLocaleDateString('es-ES', { month: 'long', year: 'numeric' })}</h2><p>Indica con cuánto dinero quieres empezar a controlar tus gastos personales este mes.</p></header><label><span>Saldo personal inicial</span><input min="0" onChange={(event) => setStartingSavings(event.target.value)} required step="0.01" type="number" value={startingSavings} /></label><button className="primary-button" disabled={busy} type="submit">{busy ? 'Creando…' : 'Crear periodo personal'}</button></form>;
}

function PeriodConfiguration({ period, busy, onSave }: { period: ExpensePeriod; busy: boolean; onSave: (mode: ExpenseSplitMode, participants: ParticipantInput[]) => Promise<void> }) {
  const [mode, setMode] = useState(period.split_mode);
  const [incomes, setIncomes] = useState(period.participants.map((item) => item.income));
  const [percentages, setPercentages] = useState(period.participants.map((item) => item.custom_percentage));
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSave(mode, period.participants.map((item, index) => ({ user_id: item.user.id, income: incomes[index], personal_starting_savings: item.personal_starting_savings, custom_percentage: percentages[index] })));
  };
  return <form className="expense-config" onSubmit={(event) => void submit(event)}><div className="expense-config__heading"><div><h2>Reparto común</h2><p>Los cambios recalculan aportes, ajuste y ahorros.</p></div><select aria-label="Regla de reparto" onChange={(event) => setMode(event.target.value as ExpenseSplitMode)} value={mode}><option value="equal">50/50</option><option value="income">Proporcional a ingresos</option><option value="custom">Porcentaje personalizado</option></select></div><div className="expense-config__people">{period.participants.map((item, index) => <div key={item.id}><strong>{displayName(item.user)}</strong><label><span>Ingreso</span><input disabled={period.status === 'closed'} min="0" onChange={(event) => setIncomes((current) => current.map((value, position) => position === index ? event.target.value : value))} step="0.01" type="number" value={incomes[index]} /></label>{mode === 'custom' ? <label><span>Porcentaje</span><input disabled={period.status === 'closed'} max="100" min="0" onChange={(event) => setPercentages((current) => current.map((value, position) => position === index ? event.target.value : value))} step="0.01" type="number" value={percentages[index]} /></label> : null}</div>)}</div>{period.status === 'open' ? <button className="secondary-button" disabled={busy} type="submit">Guardar reparto</button> : null}</form>;
}

function PersonalBalanceForm({ busy, participant, period, onSave }: {
  busy: boolean;
  participant: ExpenseParticipant;
  period: ExpensePeriod;
  onSave: (participants: ParticipantInput[]) => Promise<void>;
}) {
  const [value, setValue] = useState(participant.personal_starting_savings);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSave(period.participants.map((item) => ({
      user_id: item.user.id,
      income: item.income,
      personal_starting_savings: item.id === participant.id ? value : item.personal_starting_savings,
      custom_percentage: item.custom_percentage,
    })));
  };
  return <form className="expense-personal-balance" onSubmit={(event) => void submit(event)}><label><span>Saldo inicial para gastos personales</span><input disabled={busy || period.status === 'closed'} min="0" onChange={(event) => setValue(event.target.value)} required step="0.01" type="number" value={value} /></label><p>Introduce manualmente cuánto dinero quieres usar. No depende del resultado de los gastos comunes.</p>{period.status === 'open' ? <button className="secondary-button" disabled={busy} type="submit">Guardar saldo</button> : null}</form>;
}

export function ExpensesWorkspace({ currentUserId, onBack, onModuleUnavailable, space }: ExpensesWorkspaceProps) {
  const [month, setMonth] = useState(initialMonth);
  const [periods, setPeriods] = useState<ExpensePeriod[]>([]);
  const [members, setMembers] = useState<SpaceMember[]>([]);
  const [categories, setCategories] = useState<ExpenseCategory[]>([]);
  const [summary, setSummary] = useState<ExpenseSummary | null>(null);
  const [commonExpenses, setCommonExpenses] = useState<ExpenseEntry[]>([]);
  const [personalExpenses, setPersonalExpenses] = useState<ExpenseEntry[]>([]);
  const [editingCommon, setEditingCommon] = useState<ExpenseEntry | null>(null);
  const [editingPersonal, setEditingPersonal] = useState<ExpenseEntry | null>(null);
  const [commonFormOpen, setCommonFormOpen] = useState(false);
  const [personalFormOpen, setPersonalFormOpen] = useState(false);
  const [newCategory, setNewCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');

  const [year, monthNumber] = month.split('-').map(Number);
  const period = useMemo(() => periods.find((item) => item.year === year && item.month === monthNumber) ?? null, [monthNumber, periods, year]);
  const currentSummary = summary?.participants.find((item) => item.user.id === currentUserId);
  const currentParticipant = period?.participants.find((item) => item.user.id === currentUserId);

  const loadPeriodData = async (target: ExpensePeriod | null) => {
    if (!target) { setSummary(null); setCommonExpenses([]); setPersonalExpenses([]); return; }
    const [nextSummary, common, personal] = await Promise.all([
      fetchExpenseSummary(space.id, target.id),
      fetchCommonExpenses(space.id, target.id),
      fetchPersonalExpenses(space.id, target.id),
    ]);
    setSummary(nextSummary); setCommonExpenses(common); setPersonalExpenses(personal);
  };

  const load = async () => {
    const modules = await fetchSpaceModules(space.id);
    const module = modules.find((candidate) => candidate.key === 'expenses');
    if (!module?.enabled || !module.available) { onModuleUnavailable(); return; }
    const [nextPeriods, nextMembers, nextCategories] = await Promise.all([fetchExpensePeriods(space.id), fetchMembers(space.id), fetchExpenseCategories(space.id)]);
    setPeriods(nextPeriods); setMembers(nextMembers); setCategories(nextCategories);
    const target = nextPeriods.find((item) => item.year === year && item.month === monthNumber) ?? null;
    await loadPeriodData(target);
  };

  useEffect(() => {
    let active = true;
    const initialLoad = async () => {
      try {
        await load();
      } catch (failure) {
        if (active) setError(spaceErrorMessage(failure));
      } finally {
        if (active) setLoading(false);
      }
    };
    void initialLoad();
    return () => { active = false; };
  // load follows the active space and month.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [space.id, month]);

  const run = async (action: () => Promise<void>, message: string) => { setBusy(true); setError(null); try { await action(); await load(); setAnnouncement(message); } catch (failure) { setError(spaceErrorMessage(failure)); } finally { setBusy(false); } };
  const saveCommon = async (input: ExpenseEntryInput) => run(async () => { if (!period) return; if (editingCommon) await updateCommonExpense(space.id, period.id, editingCommon.id, input); else await createCommonExpense(space.id, period.id, input); setEditingCommon(null); setCommonFormOpen(false); }, editingCommon ? 'Gasto común actualizado.' : 'Gasto común añadido.');
  const savePersonal = async (input: ExpenseEntryInput) => run(async () => { if (!period) return; if (editingPersonal) await updatePersonalExpense(space.id, period.id, editingPersonal.id, input); else await createPersonalExpense(space.id, period.id, input); setEditingPersonal(null); setPersonalFormOpen(false); }, editingPersonal ? 'Gasto personal actualizado.' : 'Gasto personal añadido.');

  const categoryManager = (
    <section className="expense-category-manager">
      <header><h2>Categorías</h2><p>Organiza los conceptos disponibles para tus gastos.</p></header>
      <div className="expense-category-chips">
        {categories.map((category) => <span className={category.is_active ? '' : 'is-inactive'} key={category.id}>{category.name}<button aria-label={`Renombrar ${category.name}`} disabled={busy} onClick={() => { const name = window.prompt('Nuevo nombre', category.name)?.trim(); if (name && name !== category.name) void run(() => updateExpenseCategory(space.id, category.id, { name }).then(() => undefined), 'Categoría actualizada.'); }} type="button"><Icon name="edit" /></button><button disabled={busy} onClick={() => void run(() => updateExpenseCategory(space.id, category.id, { is_active: !category.is_active }).then(() => undefined), category.is_active ? 'Categoría desactivada.' : 'Categoría activada.')} type="button">{category.is_active ? 'Desactivar' : 'Activar'}</button></span>)}
      </div>
      <form className="expense-category-form" onSubmit={(event) => { event.preventDefault(); if (newCategory.trim()) void run(async () => { await createExpenseCategory(space.id, newCategory.trim()); setNewCategory(''); }, 'Categoría creada.'); }}>
        <label><span>Nueva categoría</span><input maxLength={80} onChange={(event) => setNewCategory(event.target.value)} placeholder="Mascotas, salud…" value={newCategory} /></label>
        <button className="secondary-button" disabled={busy || !newCategory.trim()} type="submit">Añadir</button>
      </form>
    </section>
  );

  return (
    <section className={`expenses-workspace expenses-workspace--${space.kind}`} aria-labelledby="expenses-title">
      <header className="expenses-header">
        <button aria-label="Volver al inicio" className="expenses-back-button" onClick={onBack} type="button"><Icon name="arrow-left" /></button>
        <div className="expenses-header__copy"><h1 id="expenses-title">Gastos</h1><p>{space.name}</p></div>
        <label className="expenses-period"><span>Periodo</span><input aria-label="Periodo" onChange={(event) => setMonth(event.target.value)} type="month" value={month} /></label>
      </header>
      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <span className="sr-only" aria-live="polite">{announcement}</span>

      {loading ? <div className="expense-loading" role="status"><span className="spinner" />Calculando el periodo…</div> : !period ? space.kind === 'personal' ? <PersonalPeriodSetup busy={busy} currentUserId={currentUserId} month={month} onCreate={(participantInputs) => run(async () => { await createExpensePeriod(space.id, { year, month: monthNumber, split_mode: 'equal', participant_inputs: participantInputs }); }, 'Periodo personal creado.')} /> : <PeriodSetup busy={busy} currentUserId={currentUserId} members={members} month={month} onCreate={(mode, participantInputs) => run(async () => { await createExpensePeriod(space.id, { year, month: monthNumber, split_mode: mode, participant_inputs: participantInputs }); }, 'Periodo creado.')} /> : space.kind === 'shared' ? (
        <>
          {summary ? (
            <section className="expense-common-overview" aria-labelledby="common-total-label">
              <div className="expense-common-overview__heading">
                <div><span id="common-total-label">Total común</span><strong>{money(summary.total_common)}</strong></div>
                <span className={`expense-status expense-status--${period.status}`}>{period.status === 'open' ? 'Abierto' : 'Cerrado'}</span>
              </div>
              <dl>
                <div><dt>Tu aporte</dt><dd>{money(currentSummary?.expected_contribution ?? 0)}</dd></div>
                <div><dt>Has pagado</dt><dd>{money(currentSummary?.paid ?? 0)}</dd></div>
              </dl>
            </section>
          ) : null}

          {period.status === 'open' ? (
            <button className="expense-add-button" onClick={() => { setEditingCommon(null); setCommonFormOpen((open) => !open); }} type="button">
              <Icon name={commonFormOpen ? 'close' : 'plus'} />{commonFormOpen ? 'Cerrar formulario' : 'Añadir gasto'}
            </button>
          ) : null}

          {commonFormOpen && period.status === 'open' ? (
            <section className="expense-compose" aria-label={editingCommon ? 'Editar gasto común' : 'Añadir gasto común'}>
              <EntryForm busy={busy} categories={categories} editing={editingCommon} key={`common-${editingCommon?.id ?? 'new'}-${commonExpenses.length}-${categories.filter((item) => item.is_active).map((item) => item.id).join('-')}`} kind="common" onCancel={() => { setEditingCommon(null); setCommonFormOpen(false); }} onSave={saveCommon} participants={period.participants} period={period} />
            </section>
          ) : null}

          <section className="expense-movements" aria-labelledby="expense-movements-title">
            <header><div><h2 id="expense-movements-title">Movimientos</h2><p>{commonExpenses.length} {commonExpenses.length === 1 ? 'gasto' : 'gastos'} este mes</p></div></header>
            <ul className="expense-list expense-list--compact">
              {commonExpenses.map((item) => <li key={item.id}><span className={`expense-category-icon expense-category-icon--${item.category.color}`}><Icon name="wallet" /></span><div className="expense-row-copy"><strong>{item.description}</strong><span>{item.category.name}{item.paid_by ? ` · ${displayName(item.paid_by.user)}` : ''} · {new Date(`${item.spent_on}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}</span></div><b>{money(item.amount)}</b>{period.status === 'open' ? <details className="expense-row-menu"><summary aria-label={`Opciones de ${item.description}`}><Icon name="more" /></summary><div><button onClick={() => { setEditingCommon(item); setCommonFormOpen(true); window.scrollTo({ top: 0, behavior: 'smooth' }); }} type="button"><Icon name="edit" />Editar</button><button className="is-danger" onClick={() => { if (window.confirm(`¿Eliminar “${item.description}”?`)) void run(() => deleteCommonExpense(space.id, period.id, item.id), 'Gasto eliminado.'); }} type="button"><Icon name="trash" />Eliminar</button></div></details> : null}</li>)}
            </ul>
            {commonExpenses.length === 0 ? <div className="expense-list-empty"><Icon name="wallet" /><strong>Aún no hay movimientos</strong><span>Añade el primer gasto común de este periodo.</span></div> : null}
          </section>

          <details className="expense-management">
            <summary><span><Icon name="settings" />Gestionar periodo</span><Icon name="chevron" /></summary>
            <div className="expense-management__content">
              <section className="expense-settlement"><h2>Ajuste común</h2>{summary?.transfers[0] ? <p><strong>{displayName(summary.transfers[0].from)}</strong> debe transferir <strong>{money(summary.transfers[0].amount)}</strong> a <strong>{displayName(summary.transfers[0].to)}</strong>.</p> : <p>No hay nada que ajustar.</p>}</section>
              <PeriodConfiguration busy={busy} key={period.updated_at} onSave={(mode, participantInputs) => run(async () => { await updateExpensePeriod(space.id, period.id, { split_mode: mode, participant_inputs: participantInputs }); }, 'Reparto actualizado.')} period={period} />
              {categoryManager}
              {period.status === 'open' || space.role === 'owner' ? <button className="secondary-button expense-period-toggle" disabled={busy} onClick={() => void run(async () => { await updateExpensePeriod(space.id, period.id, { status: period.status === 'open' ? 'closed' : 'open' }); }, period.status === 'open' ? 'Periodo cerrado.' : 'Periodo reabierto.')} type="button">{period.status === 'open' ? 'Cerrar periodo' : 'Reabrir periodo'}</button> : null}
            </div>
          </details>
        </>
      ) : (
        <>
          {currentSummary ? (
            <section className="expense-common-overview expense-personal-overview" aria-labelledby="personal-balance-label">
              <div className="expense-common-overview__heading">
                <div><span id="personal-balance-label">Disponible</span><strong>{money(currentSummary.final_savings)}</strong></div>
                <span className={`expense-status expense-status--${period.status}`}>{period.status === 'open' ? 'Abierto' : 'Cerrado'}</span>
              </div>
              <dl>
                <div><dt>Saldo inicial</dt><dd>{money(currentSummary.personal_starting_savings)}</dd></div>
                <div><dt>Gastado</dt><dd>{money(currentSummary.personal_spent)}</dd></div>
              </dl>
            </section>
          ) : null}

          {period.status === 'open' && currentSummary ? (
            <button className="expense-add-button" onClick={() => { setEditingPersonal(null); setPersonalFormOpen((open) => !open); }} type="button">
              <Icon name={personalFormOpen ? 'close' : 'plus'} />{personalFormOpen ? 'Cerrar formulario' : 'Añadir gasto'}
            </button>
          ) : null}

          {personalFormOpen && period.status === 'open' && currentSummary ? (
            <section className="expense-compose" aria-label={editingPersonal ? 'Editar gasto personal' : 'Añadir gasto personal'}>
              <EntryForm busy={busy} categories={categories} editing={editingPersonal} key={`personal-${editingPersonal?.id ?? 'new'}-${personalExpenses.length}-${categories.filter((item) => item.is_active).map((item) => item.id).join('-')}`} kind="personal" onCancel={() => { setEditingPersonal(null); setPersonalFormOpen(false); }} onSave={savePersonal} participants={period.participants} period={period} />
            </section>
          ) : null}

          <section className="expense-movements" aria-labelledby="personal-movements-title">
            <header><div><h2 id="personal-movements-title">Movimientos</h2><p>{personalExpenses.length} {personalExpenses.length === 1 ? 'gasto' : 'gastos'} este mes</p></div></header>
            <ul className="expense-list expense-list--compact">
              {personalExpenses.map((item) => <li key={item.id}><span className={`expense-category-icon expense-category-icon--${item.category.color}`}><Icon name="wallet" /></span><div className="expense-row-copy"><strong>{item.description}</strong><span>{item.category.name} · {new Date(`${item.spent_on}T12:00:00`).toLocaleDateString('es-ES', { day: 'numeric', month: 'short' })}</span></div><b>{money(item.amount)}</b>{period.status === 'open' ? <details className="expense-row-menu"><summary aria-label={`Opciones de ${item.description}`}><Icon name="more" /></summary><div><button onClick={() => { setEditingPersonal(item); setPersonalFormOpen(true); window.scrollTo({ top: 0, behavior: 'smooth' }); }} type="button"><Icon name="edit" />Editar</button><button className="is-danger" onClick={() => { if (window.confirm(`¿Eliminar “${item.description}”?`)) void run(() => deletePersonalExpense(space.id, period.id, item.id), 'Gasto personal eliminado.'); }} type="button"><Icon name="trash" />Eliminar</button></div></details> : null}</li>)}
            </ul>
            {personalExpenses.length === 0 ? <div className="expense-list-empty"><Icon name="wallet" /><strong>Aún no hay movimientos</strong><span>Añade el primer gasto personal de este periodo.</span></div> : null}
          </section>

          <details className="expense-management">
            <summary><span><Icon name="settings" />Gestionar gastos personales</span><Icon name="chevron" /></summary>
            <div className="expense-management__content">
              {currentParticipant ? <PersonalBalanceForm busy={busy} key={`${currentParticipant.id}-${currentParticipant.personal_starting_savings}`} onSave={(participantInputs) => run(async () => { await updateExpensePeriod(space.id, period.id, { participant_inputs: participantInputs }); }, 'Saldo personal actualizado.')} participant={currentParticipant} period={period} /> : null}
              {categoryManager}
              {period.status === 'open' || space.role === 'owner' ? <button className="secondary-button expense-period-toggle" disabled={busy} onClick={() => void run(async () => { await updateExpensePeriod(space.id, period.id, { status: period.status === 'open' ? 'closed' : 'open' }); }, period.status === 'open' ? 'Periodo cerrado.' : 'Periodo reabierto.')} type="button">{period.status === 'open' ? 'Cerrar periodo' : 'Reabrir periodo'}</button> : null}
            </div>
          </details>
        </>
      )}
    </section>
  );
}
