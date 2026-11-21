import { useEffect, useMemo, useState, type FormEvent } from 'react';

import { ApiError } from '../api/client';
import { fetchSpaceModules } from '../api/modules';
import type { Space } from '../api/spaces';
import {
  createDailySteps,
  createHealthMeasurement,
  createWorkout,
  deleteWorkout,
  fetchDailySteps,
  fetchTrainingProfile,
  fetchTrainingSummary,
  fetchHealthMeasurements,
  fetchWorkouts,
  saveTrainingProfile,
  updateDailySteps,
  updateHealthMeasurement,
  type HealthMeasurement,
  type DailySteps,
  type StrengthWorkout,
  type TrainingProfile,
  type TrainingSummary,
} from '../api/training';
import { spaceErrorMessage } from '../hooks/use-spaces';
import { Icon } from './icon';

type TrainingWorkspaceProps = {
  onBack: () => void;
  onModuleUnavailable: () => void;
  space: Space;
};

type Tab = 'summary' | 'strength' | 'evolution';
type HealthMetricKey = Exclude<keyof HealthMeasurement, 'id' | 'date' | 'notes'>;
type DraftSet = { weight: string; repetitions: string };
type DraftExercise = { name: string; sets: DraftSet[] };
type HealthDraft = Record<HealthMetricKey, string>;

const healthMetrics: Array<{ key: HealthMetricKey; label: string; unit: string }> = [
  { key: 'weight_kg', label: 'Peso', unit: 'kg' },
  { key: 'bmi', label: 'IMC', unit: '' },
  { key: 'body_fat_percentage', label: 'Grasa corporal', unit: '%' },
  { key: 'subcutaneous_fat_percentage', label: 'Grasa subcutánea', unit: '%' },
  { key: 'visceral_fat_level', label: 'Grasa visceral', unit: 'nivel' },
  { key: 'body_water_percentage', label: 'Agua corporal', unit: '%' },
  { key: 'muscle_mass_kg', label: 'Masa muscular', unit: 'kg' },
  { key: 'bone_mass_kg', label: 'Masa ósea', unit: 'kg' },
  { key: 'basal_metabolic_rate_kcal', label: 'Tasa metabólica basal', unit: 'kcal' },
  { key: 'metabolic_age', label: 'Edad metabólica', unit: 'años' },
];

const emptyHealthDraft = (): HealthDraft => Object.fromEntries(
  healthMetrics.map((metric) => [metric.key, '']),
) as HealthDraft;

const today = () => {
  const value = new Date();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${value.getFullYear()}-${month}-${day}`;
};

const formatDate = (value: string) => new Intl.DateTimeFormat('es-ES', {
  day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC',
}).format(new Date(`${value}T00:00:00Z`));

const number = (value: string | number | null | undefined) => Number(value ?? 0);
const newExercise = (): DraftExercise => ({ name: '', sets: [{ weight: '', repetitions: '' }] });

export function TrainingWorkspace({ onBack, onModuleUnavailable, space }: TrainingWorkspaceProps) {
  const [tab, setTab] = useState<Tab>('summary');
  const [profile, setProfile] = useState<TrainingProfile | null>(null);
  const [summary, setSummary] = useState<TrainingSummary | null>(null);
  const [workouts, setWorkouts] = useState<StrengthWorkout[]>([]);
  const [steps, setSteps] = useState<DailySteps[]>([]);
  const [healthMeasurements, setHealthMeasurements] = useState<HealthMeasurement[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const [profileHeight, setProfileHeight] = useState('');
  const [profileBirthDate, setProfileBirthDate] = useState('');
  const [stepsValue, setStepsValue] = useState('');
  const [stepsGoal, setStepsGoal] = useState('10000');
  const [healthDraft, setHealthDraft] = useState<HealthDraft>(emptyHealthDraft);
  const [healthMetric, setHealthMetric] = useState<HealthMetricKey>('weight_kg');
  const [quickForm, setQuickForm] = useState<'steps' | 'health' | null>(null);
  const [workoutFormOpen, setWorkoutFormOpen] = useState(false);
  const [workoutDate, setWorkoutDate] = useState(today());
  const [workoutDuration, setWorkoutDuration] = useState('');
  const [workoutNotes, setWorkoutNotes] = useState('');
  const [exercises, setExercises] = useState<DraftExercise[]>([newExercise()]);

  const load = async () => {
    const modules = await fetchSpaceModules(space.id);
    const module = modules.find((candidate) => candidate.key === 'training');
    if (!module?.enabled || !module.available || space.kind !== 'personal') {
      onModuleUnavailable();
      return;
    }
    const profilePromise = fetchTrainingProfile(space.id).catch((failure: unknown) => {
      if (failure instanceof ApiError && failure.status === 404) return null;
      throw failure;
    });
    const [nextProfile, nextSummary, nextWorkouts, nextSteps, nextHealthMeasurements] = await Promise.all([
      profilePromise,
      fetchTrainingSummary(space.id),
      fetchWorkouts(space.id),
      fetchDailySteps(space.id),
      fetchHealthMeasurements(space.id),
    ]);
    setProfile(nextProfile);
    setSummary(nextSummary);
    setWorkouts(nextWorkouts);
    setSteps(nextSteps);
    setHealthMeasurements(nextHealthMeasurements);
    if (nextProfile) {
      setProfileHeight(String(nextProfile.height_cm));
      setProfileBirthDate(nextProfile.date_of_birth);
    }
    const todaySteps = nextSteps.find((entry) => entry.date === today());
    const todayHealth = nextHealthMeasurements.find((entry) => entry.date === today());
    setStepsValue(todaySteps ? String(todaySteps.steps) : '');
    setStepsGoal(String(todaySteps?.goal ?? 10000));
    setHealthDraft(Object.fromEntries(
      healthMetrics.map((metric) => [metric.key, todayHealth?.[metric.key] == null ? '' : String(todayHealth[metric.key])]),
    ) as HealthDraft);
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
  // load follows the active personal space.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [space.id]);

  const run = async (action: () => Promise<void>, message: string) => {
    setBusy(true);
    setError(null);
    try {
      await action();
      await load();
      setAnnouncement(message);
    } catch (failure) {
      setError(spaceErrorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  const saveProfile = async (event: FormEvent) => {
    event.preventDefault();
    await run(async () => {
      await saveTrainingProfile(space.id, {
        height_cm: Number(profileHeight),
        date_of_birth: profileBirthDate,
      });
    }, profile ? 'Perfil actualizado.' : 'Perfil preparado. Ya puedes registrar tu actividad.');
  };

  const saveSteps = async (event: FormEvent) => {
    event.preventDefault();
    await run(async () => {
      const existing = steps.find((entry) => entry.date === today());
      const input = { date: today(), steps: Number(stepsValue), goal: Number(stepsGoal) || null };
      if (existing) await updateDailySteps(space.id, existing.id, input);
      else await createDailySteps(space.id, input);
      setQuickForm(null);
    }, 'Pasos de hoy actualizados.');
  };

  const saveHealthEntry = async (event: FormEvent) => {
    event.preventDefault();
    await run(async () => {
      const existing = healthMeasurements.find((entry) => entry.date === today());
      const input = {
        date: today(),
        weight_kg: healthDraft.weight_kg,
        bmi: healthDraft.bmi,
        body_fat_percentage: healthDraft.body_fat_percentage,
        subcutaneous_fat_percentage: healthDraft.subcutaneous_fat_percentage,
        visceral_fat_level: healthDraft.visceral_fat_level,
        body_water_percentage: healthDraft.body_water_percentage,
        muscle_mass_kg: healthDraft.muscle_mass_kg,
        bone_mass_kg: healthDraft.bone_mass_kg,
        basal_metabolic_rate_kcal: Number(healthDraft.basal_metabolic_rate_kcal),
        metabolic_age: Number(healthDraft.metabolic_age),
      };
      if (existing) await updateHealthMeasurement(space.id, existing.id, input);
      else await createHealthMeasurement(space.id, input);
      setQuickForm(null);
    }, 'Medición de salud actualizada.');
  };

  const updateExercise = (index: number, update: Partial<DraftExercise>) => {
    setExercises((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, ...update } : item));
  };

  const updateSet = (exerciseIndex: number, setIndex: number, update: Partial<DraftSet>) => {
    const nextSets = exercises[exerciseIndex].sets.map((item, itemIndex) => itemIndex === setIndex ? { ...item, ...update } : item);
    updateExercise(exerciseIndex, { sets: nextSets });
  };

  const saveWorkout = async (event: FormEvent) => {
    event.preventDefault();
    await run(async () => {
      await createWorkout(space.id, {
        workout_date: workoutDate,
        duration_minutes: workoutDuration ? Number(workoutDuration) : null,
        notes: workoutNotes,
        exercises: exercises.map((exercise, exerciseIndex) => ({
          name: exercise.name,
          order: exerciseIndex + 1,
          sets: exercise.sets.map((set, setIndex) => ({
            set_number: setIndex + 1,
            weight_kg: set.weight,
            repetitions: Number(set.repetitions),
          })),
        })),
      });
      setWorkoutFormOpen(false);
      setWorkoutDuration('');
      setWorkoutNotes('');
      setExercises([newExercise()]);
      setTab('strength');
    }, 'Entrenamiento guardado.');
  };

  const latestWorkout = workouts[0];
  const todaySteps = summary?.today.steps ?? 0;
  const todayGoal = summary?.today.steps_goal ?? 10000;
  const stepsProgress = Math.min(100, todayGoal ? (todaySteps / todayGoal) * 100 : 0);
  const recentSteps = useMemo(() => [...(summary?.steps_history ?? [])].slice(-7), [summary]);
  const maxSteps = Math.max(...recentSteps.map((entry) => entry.steps), 1);
  const selectedMetric = healthMetrics.find((metric) => metric.key === healthMetric)!;
  const healthSeries = useMemo(() => (summary?.health_history ?? [])
    .flatMap((entry) => entry[healthMetric] == null
      ? []
      : [{ date: entry.date, value: number(entry[healthMetric]) }]), [healthMetric, summary]);
  const healthValues = healthSeries.map((entry) => entry.value);
  const healthMin = healthValues.length ? Math.min(...healthValues) : 0;
  const healthMax = healthValues.length ? Math.max(...healthValues) : 1;
  const healthRange = Math.max(healthMax - healthMin, 1);
  const healthPoints = healthSeries.map((entry, index) => {
    const x = healthSeries.length === 1 ? 50 : (index / (healthSeries.length - 1)) * 100;
    const y = healthSeries.length === 1 ? 52 : 88 - ((entry.value - healthMin) / healthRange) * 72;
    return `${x},${y}`;
  }).join(' ');

  if (loading) {
    return <div className="training-loading" role="status"><span className="spinner" />Preparando tu entrenamiento…</div>;
  }

  return (
    <section className="training-workspace" aria-labelledby="training-title">
      <header className="training-header">
        <button aria-label="Volver al inicio" className="training-back" onClick={onBack} type="button"><Icon name="arrow-left" /></button>
        <div><h1 id="training-title">Entrenamiento</h1><p>{space.name} · espacio personal</p></div>
        <button className="training-profile-button" onClick={() => setTab('evolution')} type="button">{profile ? `${profile.height_cm} cm · ${profile.age} años` : 'Completar perfil'}</button>
      </header>

      {error ? <p className="form-error" role="alert">{error}</p> : null}
      <span className="sr-only" aria-live="polite">{announcement}</span>

      {!profile ? (
        <form className="training-profile-setup" onSubmit={(event) => void saveProfile(event)}>
          <div><h2>Prepara tu perfil</h2><p>La estatura y la fecha de nacimiento ayudan a contextualizar tu evolución. Solo tú puedes ver estos datos.</p></div>
          <label>Estatura en cm<input max="250" min="80" onChange={(event) => setProfileHeight(event.target.value)} required type="number" value={profileHeight} /></label>
          <label>Fecha de nacimiento<input max={today()} onChange={(event) => setProfileBirthDate(event.target.value)} required type="date" value={profileBirthDate} /></label>
          <button className="primary-button" disabled={busy} type="submit">Guardar perfil</button>
        </form>
      ) : null}

      <div className="training-tabs" role="tablist" aria-label="Secciones de entrenamiento">
        {(['summary', 'strength', 'evolution'] as Tab[]).map((item) => (
          <button aria-selected={tab === item} key={item} onClick={() => setTab(item)} role="tab" type="button">
            {item === 'summary' ? 'Resumen' : item === 'strength' ? 'Fuerza' : 'Salud'}
          </button>
        ))}
      </div>

      {tab === 'summary' ? (
        <div role="tabpanel">
          <section className="training-today">
            <div><h2>Tu día, en marcha</h2><p>{summary?.today.workout_count ? `Has completado ${summary.today.workout_count} sesión de fuerza hoy.` : 'Aún no has registrado una sesión de fuerza hoy.'}</p><dl><div><dt>Entrenamientos</dt><dd>{summary?.today.workout_count ?? 0}</dd></div><div><dt>Última medición</dt><dd>{summary?.health.latest ? `${number(summary.health.latest.weight_kg).toFixed(1)} kg` : '—'}</dd></div><div><dt>Esta semana</dt><dd>{summary?.week.workout_count ?? 0} sesiones</dd></div></dl></div>
            <div className="training-steps-progress"><span>Pasos de hoy</span><strong>{todaySteps.toLocaleString('es-ES')}</strong><div aria-label={`${Math.round(stepsProgress)}% del objetivo`}><span style={{ width: `${stepsProgress}%` }} /></div><small>{Math.max(todayGoal - todaySteps, 0).toLocaleString('es-ES')} pasos para tu objetivo</small></div>
          </section>

          <div className="training-section-heading"><h2>Registro rápido</h2><span>{formatDate(today())}</span></div>
          <div className="training-quick-actions"><button onClick={() => { setWorkoutFormOpen(true); setTab('strength'); }} type="button"><Icon name="plus" />Añadir entrenamiento</button><button onClick={() => setQuickForm(quickForm === 'steps' ? null : 'steps')} type="button"><Icon name="activity" />Registrar pasos</button><button onClick={() => setQuickForm(quickForm === 'health' ? null : 'health')} type="button"><Icon name="heart" />Añadir medición de salud</button></div>
          {quickForm === 'steps' ? <form className="training-inline-form" onSubmit={(event) => void saveSteps(event)}><label>Pasos<input min="0" onChange={(event) => setStepsValue(event.target.value)} required type="number" value={stepsValue} /></label><label>Objetivo diario<input min="1" onChange={(event) => setStepsGoal(event.target.value)} type="number" value={stepsGoal} /></label><button className="primary-button" disabled={busy} type="submit">Guardar pasos</button></form> : null}
          {quickForm === 'health' ? <form className="training-health-form" onSubmit={(event) => void saveHealthEntry(event)}><header><div><h3>Medición de la báscula</h3><p>Introduce los valores que pertenecen a la misma medición de hoy.</p></div><button aria-label="Cerrar medición" onClick={() => setQuickForm(null)} type="button"><Icon name="close" /></button></header><div>{healthMetrics.map((metric) => <label key={metric.key}>{metric.label}{metric.unit ? ` (${metric.unit})` : ''}<input min={metric.key === 'weight_kg' ? 20 : metric.key === 'bmi' ? 5 : metric.key === 'basal_metabolic_rate_kcal' ? 500 : metric.key === 'metabolic_age' ? 1 : 0} max={metric.key === 'weight_kg' ? 500 : metric.key === 'bmi' || metric.key.includes('percentage') || metric.key === 'visceral_fat_level' ? 100 : metric.key === 'muscle_mass_kg' ? 300 : metric.key === 'bone_mass_kg' ? 30 : metric.key === 'basal_metabolic_rate_kcal' ? 10000 : 150} onChange={(event) => setHealthDraft((current) => ({ ...current, [metric.key]: event.target.value }))} required step={metric.key === 'basal_metabolic_rate_kcal' || metric.key === 'metabolic_age' ? 1 : 0.1} type="number" value={healthDraft[metric.key]} /></label>)}</div><div className="training-form-actions"><button className="primary-button" disabled={busy} type="submit">Guardar medición</button><button className="secondary-button" onClick={() => setQuickForm(null)} type="button">Cancelar</button></div></form> : null}

          <div className="training-section-heading"><h2>Esta semana</h2><button onClick={() => setTab('evolution')} type="button">Ver salud</button></div>
          <div className="training-overview-grid">
            <section className="training-chart-panel"><header><div><h3>Pasos diarios</h3><p>Media: {(summary?.week.average_steps ?? 0).toLocaleString('es-ES')}</p></div><strong>{(summary?.week.total_steps ?? 0).toLocaleString('es-ES')}</strong></header><div className="training-bars">{recentSteps.length ? recentSteps.map((entry) => <div key={entry.date}><span style={{ height: `${Math.max(8, (entry.steps / maxSteps) * 100)}%` }} /><small>{new Intl.DateTimeFormat('es-ES', { weekday: 'short', timeZone: 'UTC' }).format(new Date(`${entry.date}T00:00:00Z`)).slice(0, 1).toUpperCase()}</small></div>) : <p>Registra pasos para ver tu semana.</p>}</div></section>
            <section className="training-latest"><header><div><h3>Última sesión</h3><p>{latestWorkout ? formatDate(latestWorkout.workout_date) : 'Sin sesiones'}</p></div>{latestWorkout ? <button onClick={() => setTab('strength')} type="button">Abrir</button> : null}</header>{latestWorkout ? <ul>{latestWorkout.exercises.slice(0, 3).map((exercise) => <li key={exercise.id}><span /><div><strong>{exercise.name}</strong><small>{exercise.sets.length} series</small></div><b>{exercise.sets.reduce((total, set) => total + number(set.weight_kg) * set.repetitions, 0).toLocaleString('es-ES')} kg</b></li>)}</ul> : <p className="training-empty-copy">Añade tu primera sesión de fuerza para verla aquí.</p>}</section>
          </div>
        </div>
      ) : null}

      {tab === 'strength' ? (
        <div role="tabpanel">
          <div className="training-section-heading"><div><h2>Sesiones de fuerza</h2><p>Pesos, repeticiones y volumen por ejercicio.</p></div><button className="training-add-workout" onClick={() => setWorkoutFormOpen((open) => !open)} type="button"><Icon name="plus" />Nueva sesión</button></div>
          {workoutFormOpen ? <form className="training-workout-form" onSubmit={(event) => void saveWorkout(event)}><header><h3>Nueva sesión</h3><button aria-label="Cerrar formulario" onClick={() => setWorkoutFormOpen(false)} type="button"><Icon name="close" /></button></header><div className="training-form-row"><label>Fecha<input onChange={(event) => setWorkoutDate(event.target.value)} required type="date" value={workoutDate} /></label><label>Duración en minutos<input min="1" onChange={(event) => setWorkoutDuration(event.target.value)} type="number" value={workoutDuration} /></label></div>{exercises.map((exercise, exerciseIndex) => <fieldset className="training-exercise" key={exerciseIndex}><legend>Ejercicio {exerciseIndex + 1}</legend><div className="training-exercise-head"><input aria-label={`Nombre del ejercicio ${exerciseIndex + 1}`} maxLength={120} onChange={(event) => updateExercise(exerciseIndex, { name: event.target.value })} placeholder="Press banca, sentadilla…" required value={exercise.name} />{exercises.length > 1 ? <button aria-label={`Eliminar ejercicio ${exerciseIndex + 1}`} onClick={() => setExercises((current) => current.filter((_, index) => index !== exerciseIndex))} type="button"><Icon name="trash" /></button> : null}</div><div className="training-set-labels"><span>Serie</span><span>Peso (kg)</span><span>Repeticiones</span><span /></div>{exercise.sets.map((set, setIndex) => <div className="training-set-row" key={setIndex}><strong>{setIndex + 1}</strong><input aria-label={`Peso de la serie ${setIndex + 1}`} min="0" onChange={(event) => updateSet(exerciseIndex, setIndex, { weight: event.target.value })} required step="0.25" type="number" value={set.weight} /><input aria-label={`Repeticiones de la serie ${setIndex + 1}`} min="1" onChange={(event) => updateSet(exerciseIndex, setIndex, { repetitions: event.target.value })} required type="number" value={set.repetitions} />{exercise.sets.length > 1 ? <button aria-label={`Eliminar serie ${setIndex + 1}`} onClick={() => updateExercise(exerciseIndex, { sets: exercise.sets.filter((_, index) => index !== setIndex) })} type="button"><Icon name="close" /></button> : <span />}</div>)}<button className="training-add-set" onClick={() => updateExercise(exerciseIndex, { sets: [...exercise.sets, { weight: '', repetitions: '' }] })} type="button">+ Añadir serie</button></fieldset>)}<button className="training-add-exercise" onClick={() => setExercises((current) => [...current, newExercise()])} type="button">+ Añadir ejercicio</button><label className="training-notes">Notas<textarea onChange={(event) => setWorkoutNotes(event.target.value)} placeholder="Sensaciones, ajustes o recordatorios…" value={workoutNotes} /></label><div className="training-form-actions"><button className="primary-button" disabled={busy} type="submit">Guardar entrenamiento</button><button className="secondary-button" onClick={() => setWorkoutFormOpen(false)} type="button">Cancelar</button></div></form> : null}
          {workouts.length ? <div className="training-workout-list">{workouts.map((workout) => <article key={workout.id}><header><div><h3>{formatDate(workout.workout_date)}</h3><p>{workout.duration_minutes ? `${workout.duration_minutes} min · ` : ''}{workout.exercises.length} ejercicios · {workout.exercises.reduce((total, exercise) => total + exercise.sets.length, 0)} series</p></div><div><strong>{number(workout.total_volume_kg).toLocaleString('es-ES')} kg</strong><button aria-label={`Eliminar entrenamiento del ${formatDate(workout.workout_date)}`} disabled={busy} onClick={() => { if (window.confirm('¿Eliminar este entrenamiento?')) void run(() => deleteWorkout(space.id, workout.id), 'Entrenamiento eliminado.'); }} type="button"><Icon name="trash" /></button></div></header><ul>{workout.exercises.map((exercise) => <li key={exercise.id}><div><strong>{exercise.name}</strong><span>{exercise.sets.map((set) => `${number(set.weight_kg)} kg × ${set.repetitions}`).join(' · ')}</span></div><b>{exercise.sets.reduce((total, set) => total + number(set.weight_kg) * set.repetitions, 0).toLocaleString('es-ES')} kg</b></li>)}</ul>{workout.notes ? <p className="training-workout-notes">{workout.notes}</p> : null}</article>)}</div> : <div className="training-empty"><Icon name="activity" size={34} /><h3>Aún no hay entrenamientos</h3><p>Añade tu primera sesión con los ejercicios, pesos y repeticiones que has realizado.</p><button className="primary-button" onClick={() => setWorkoutFormOpen(true)} type="button">Crear primera sesión</button></div>}
        </div>
      ) : null}

      {tab === 'evolution' ? (
        <div role="tabpanel">
          <div className="training-section-heading"><div><h2>Salud</h2><p>Evolución de las mediciones de tu báscula inteligente.</p></div><button className="training-add-workout" onClick={() => { setQuickForm('health'); setTab('summary'); }} type="button"><Icon name="plus" />Nueva medición</button></div>
          {summary?.health.latest ? <div className="training-health-metrics">{healthMetrics.map((metric) => <button aria-pressed={healthMetric === metric.key} key={metric.key} onClick={() => setHealthMetric(metric.key)} type="button"><span>{metric.label}</span><strong>{summary.health.latest?.[metric.key] == null ? '—' : `${number(summary.health.latest[metric.key]).toLocaleString('es-ES', { maximumFractionDigits: 2 })}${metric.unit ? ` ${metric.unit}` : ''}`}</strong></button>)}</div> : null}
          <section className="training-health-chart"><header><div><h3>Evolución de {selectedMetric.label.toLocaleLowerCase('es-ES')}</h3><p>Últimos 30 días · {selectedMetric.unit || 'índice'}</p></div><label>Parámetro<select onChange={(event) => setHealthMetric(event.target.value as HealthMetricKey)} value={healthMetric}>{healthMetrics.map((metric) => <option key={metric.key} value={metric.key}>{metric.label}</option>)}</select></label></header>{healthSeries.length ? <><svg aria-label={`Gráfica de ${selectedMetric.label}`} role="img" viewBox="0 0 100 100" preserveAspectRatio="none"><path d="M0 16H100M0 52H100M0 88H100" /><polyline points={healthPoints} />{healthSeries.map((entry, index) => { const [x, y] = healthPoints.split(' ')[index].split(','); return <circle cx={x} cy={y} key={entry.date} r="1.7" />; })}</svg><div className="training-chart-scale"><span>{healthSeries[0] ? formatDate(healthSeries[0].date) : ''}</span><strong>{healthSeries.at(-1)?.value.toLocaleString('es-ES', { maximumFractionDigits: 2 })} {selectedMetric.unit}</strong><span>{healthSeries.at(-1) ? formatDate(healthSeries.at(-1)!.date) : ''}</span></div></> : <div className="training-empty-copy">Añade una medición para empezar a ver la evolución de {selectedMetric.label.toLocaleLowerCase('es-ES')}.</div>}</section>
          <div className="training-overview-grid"><section className="training-health-history"><header><h3>Mediciones recientes</h3><span>{healthMeasurements.length} registros</span></header>{healthMeasurements.length ? <ol>{healthMeasurements.slice(0, 5).map((entry) => <li key={entry.id}><time>{formatDate(entry.date)}</time><span>{number(entry.weight_kg).toFixed(1)} kg</span><span>{entry.body_fat_percentage == null ? '—' : `${number(entry.body_fat_percentage).toFixed(1)}% grasa`}</span><span>{entry.muscle_mass_kg == null ? '—' : `${number(entry.muscle_mass_kg).toFixed(1)} kg músculo`}</span></li>)}</ol> : <p className="training-empty-copy">Todavía no hay mediciones de salud.</p>}</section><section className="training-profile-card"><header><h3>Datos personales</h3><Icon name="settings" /></header><form onSubmit={(event) => void saveProfile(event)}><label>Estatura en cm<input max="250" min="80" onChange={(event) => setProfileHeight(event.target.value)} required type="number" value={profileHeight} /></label><label>Fecha de nacimiento<input max={today()} onChange={(event) => setProfileBirthDate(event.target.value)} required type="date" value={profileBirthDate} /></label><button className="secondary-button" disabled={busy} type="submit">Actualizar perfil</button></form></section></div>
        </div>
      ) : null}
    </section>
  );
}
