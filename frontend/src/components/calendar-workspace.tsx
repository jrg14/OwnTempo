import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';

import {
  createCalendarEvent,
  deleteCalendarEvent,
  fetchCalendarEvents,
  updateCalendarEvent,
  type CalendarColor,
  type CalendarEvent,
  type CalendarEventInput,
} from '../api/calendar';
import { fetchSpaceModules } from '../api/modules';
import type { Space } from '../api/spaces';
import { spaceErrorMessage } from '../hooks/use-spaces';
import { Icon } from './icon';

type CalendarWorkspaceProps = {
  onBack: () => void;
  onModuleUnavailable: () => void;
  space: Space;
};

const pad = (value: number) => String(value).padStart(2, '0');

function dateKey(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function localDateTimeValue(value: string | null, fallback: Date) {
  const date = value ? new Date(value) : fallback;
  return `${dateKey(date)}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function monthBounds(month: Date) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const last = new Date(month.getFullYear(), month.getMonth() + 1, 0);
  return { from: dateKey(first), to: dateKey(last) };
}

function monthDays(month: Date) {
  const first = new Date(month.getFullYear(), month.getMonth(), 1);
  const mondayOffset = (first.getDay() + 6) % 7;
  const start = new Date(first);
  start.setDate(first.getDate() - mondayOffset);
  return Array.from({ length: 42 }, (_, index) => {
    const day = new Date(start);
    day.setDate(start.getDate() + index);
    return day;
  });
}

function eventOccursOn(event: CalendarEvent, key: string) {
  if (event.all_day) return event.date === key;
  const start = new Date(`${key}T00:00:00`);
  const end = new Date(start);
  end.setDate(end.getDate() + 1);
  return Boolean(event.start_at && event.end_at)
    && new Date(event.start_at!) < end
    && new Date(event.end_at!) > start;
}

function formatTime(value: string) {
  return new Intl.DateTimeFormat('es-ES', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value));
}

function isHttpUrl(value: string) {
  return /^https?:\/\//i.test(value);
}

function EventForm({
  busy,
  event,
  initialDate,
  onCancel,
  onSave,
}: {
  busy: boolean;
  event: CalendarEvent | null;
  initialDate: string;
  onCancel: () => void;
  onSave: (input: CalendarEventInput) => Promise<void>;
}) {
  const fallbackStart = new Date(`${initialDate}T09:00:00`);
  const fallbackEnd = new Date(`${initialDate}T10:00:00`);
  const [title, setTitle] = useState(event?.title ?? '');
  const [description, setDescription] = useState(event?.description ?? '');
  const [allDay, setAllDay] = useState(event?.all_day ?? false);
  const [eventDate, setEventDate] = useState(event?.date ?? initialDate);
  const [startAt, setStartAt] = useState(localDateTimeValue(event?.start_at ?? null, fallbackStart));
  const [endAt, setEndAt] = useState(localDateTimeValue(event?.end_at ?? null, fallbackEnd));
  const [location, setLocation] = useState(event?.location ?? '');
  const [color, setColor] = useState<CalendarColor>(event?.color ?? 'teal');
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => titleRef.current?.focus(), []);

  const submit = async (formEvent: FormEvent<HTMLFormElement>) => {
    formEvent.preventDefault();
    await onSave({
      title: title.trim(),
      description: description.trim(),
      all_day: allDay,
      date: allDay ? eventDate : null,
      start_at: allDay ? null : new Date(startAt).toISOString(),
      end_at: allDay ? null : new Date(endAt).toISOString(),
      location: location.trim(),
      color,
    });
  };

  return (
    <form className="calendar-form" onSubmit={(formEvent) => void submit(formEvent)}>
      <div className="calendar-form__heading">
        <div><h2>{event ? 'Editar evento' : 'Nuevo evento'}</h2><p>Reserva un momento en la agenda del espacio.</p></div>
        <button aria-label="Cerrar formulario" className="icon-button" onClick={onCancel} type="button"><Icon name="close" /></button>
      </div>
      <div className="calendar-form__grid">
        <label className="calendar-form__wide"><span>Título</span><input maxLength={200} onChange={(inputEvent) => setTitle(inputEvent.target.value)} placeholder="¿Qué va a ocurrir?" ref={titleRef} required value={title} /></label>
        <label className="calendar-all-day"><input checked={allDay} onChange={(inputEvent) => setAllDay(inputEvent.target.checked)} type="checkbox" /><span>Todo el día</span></label>
        {allDay ? <label><span>Fecha</span><input onChange={(inputEvent) => setEventDate(inputEvent.target.value)} required type="date" value={eventDate} /></label> : <><label><span>Inicio</span><input onChange={(inputEvent) => setStartAt(inputEvent.target.value)} required type="datetime-local" value={startAt} /></label><label><span>Final</span><input min={startAt} onChange={(inputEvent) => setEndAt(inputEvent.target.value)} required type="datetime-local" value={endAt} /></label></>}
        <label><span>Color</span><select onChange={(inputEvent) => setColor(inputEvent.target.value as CalendarColor)} value={color}><option value="teal">Verde</option><option value="amber">Ámbar</option><option value="rose">Rosa</option><option value="blue">Azul</option><option value="violet">Violeta</option><option value="slate">Gris</option></select></label>
        <label className="calendar-form__wide"><span>Ubicación o enlace <small>opcional</small></span><input maxLength={300} onChange={(inputEvent) => setLocation(inputEvent.target.value)} placeholder="Dirección o https://…" value={location} /></label>
        <label className="calendar-form__wide"><span>Descripción <small>opcional</small></span><textarea maxLength={4000} onChange={(inputEvent) => setDescription(inputEvent.target.value)} placeholder="Añade detalles" rows={3} value={description} /></label>
      </div>
      <div className="calendar-form__actions"><button className="primary-button" disabled={busy || !title.trim()} type="submit">{busy ? 'Guardando…' : event ? 'Guardar cambios' : 'Crear evento'}</button><button className="secondary-button" disabled={busy} onClick={onCancel} type="button">Cancelar</button></div>
    </form>
  );
}

export function CalendarWorkspace({ onBack, onModuleUnavailable, space }: CalendarWorkspaceProps) {
  const today = new Date();
  const [month, setMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedDate, setSelectedDate] = useState(dateKey(today));
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyEventId, setBusyEventId] = useState<number | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [editingEvent, setEditingEvent] = useState<CalendarEvent | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');

  const load = async (targetMonth: Date) => {
    const modules = await fetchSpaceModules(space.id);
    const module = modules.find((candidate) => candidate.key === 'calendar');
    if (!module?.enabled || !module.available) {
      onModuleUnavailable();
      return;
    }
    const { from, to } = monthBounds(targetMonth);
    setEvents(await fetchCalendarEvents(space.id, from, to));
  };

  useEffect(() => {
    let active = true;
    const initialLoad = async () => {
      try {
        await load(month);
      } catch (loadFailure) {
        if (active) setLoadError(spaceErrorMessage(loadFailure));
      } finally {
        if (active) setLoading(false);
      }
    };
    void initialLoad();
    return () => { active = false; };
  // load is intentionally scoped to the current month and space.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [month, space.id]);

  useEffect(() => {
    const verifyModule = () => fetchSpaceModules(space.id).then((modules) => {
      const module = modules.find((candidate) => candidate.key === 'calendar');
      if (!module?.enabled || !module.available) onModuleUnavailable();
    }).catch(() => undefined);
    window.addEventListener('focus', verifyModule);
    return () => window.removeEventListener('focus', verifyModule);
  }, [onModuleUnavailable, space.id]);

  const days = useMemo(() => monthDays(month), [month]);
  const selectedEvents = useMemo(
    () => events.filter((event) => eventOccursOn(event, selectedDate)).sort((left, right) => {
      if (left.all_day !== right.all_day) return left.all_day ? -1 : 1;
      return (left.start_at ?? '').localeCompare(right.start_at ?? '');
    }),
    [events, selectedDate],
  );

  const refresh = () => load(month);
  const closeForm = () => { setFormOpen(false); setEditingEvent(null); };

  const save = async (input: CalendarEventInput) => {
    setBusy(true);
    setError(null);
    try {
      if (editingEvent) await updateCalendarEvent(space.id, editingEvent.id, input);
      else await createCalendarEvent(space.id, input);
      await refresh();
      setAnnouncement(editingEvent ? 'Evento actualizado.' : 'Evento creado.');
      closeForm();
    } catch (saveError) {
      setError(spaceErrorMessage(saveError));
    } finally { setBusy(false); }
  };

  const remove = async (event: CalendarEvent) => {
    if (!window.confirm(`¿Eliminar “${event.title}”?`)) return;
    setBusyEventId(event.id);
    setError(null);
    try {
      await deleteCalendarEvent(space.id, event.id);
      setEvents((current) => current.filter((item) => item.id !== event.id));
      setAnnouncement('Evento eliminado.');
    } catch (deleteError) {
      setError(spaceErrorMessage(deleteError));
    } finally { setBusyEventId(null); }
  };

  const changeMonth = (offset: number) => {
    const next = new Date(month.getFullYear(), month.getMonth() + offset, 1);
    setLoading(true);
    setLoadError(null);
    setMonth(next);
    setSelectedDate(dateKey(next));
  };

  const goToday = () => {
    const current = new Date();
    setLoading(true);
    setLoadError(null);
    setMonth(new Date(current.getFullYear(), current.getMonth(), 1));
    setSelectedDate(dateKey(current));
  };

  const selectDay = (day: Date) => {
    if (day.getMonth() !== month.getMonth() || day.getFullYear() !== month.getFullYear()) {
      setLoading(true);
      setLoadError(null);
      setMonth(new Date(day.getFullYear(), day.getMonth(), 1));
    }
    setSelectedDate(dateKey(day));
  };

  const monthLabel = new Intl.DateTimeFormat('es-ES', { month: 'long', year: 'numeric' }).format(month);
  const selectedLabel = new Intl.DateTimeFormat('es-ES', { weekday: 'long', day: 'numeric', month: 'long' }).format(new Date(`${selectedDate}T12:00:00`));

  const retry = async () => {
    setLoading(true);
    setLoadError(null);
    try { await load(month); } catch (retryError) { setLoadError(spaceErrorMessage(retryError)); }
    finally { setLoading(false); }
  };

  return (
    <section className="calendar-workspace" aria-labelledby="calendar-title">
      <header className="calendar-header"><button className="back-button" onClick={onBack} type="button"><Icon name="arrow-left" />Volver</button><div className="calendar-header__title"><div><h1 id="calendar-title">Calendario</h1><p>{space.name}</p></div>{!formOpen ? <button className="primary-button" onClick={() => { setEditingEvent(null); setFormOpen(true); }} type="button"><Icon name="plus" />Nuevo evento</button> : null}</div></header>
      {error ? <p className="form-error calendar-error" role="alert">{error}</p> : null}<p className="visually-hidden" aria-live="polite" role="status">{announcement}</p>
      {formOpen ? <EventForm busy={busy} event={editingEvent} initialDate={selectedDate} key={editingEvent?.id ?? `new-${selectedDate}`} onCancel={closeForm} onSave={save} /> : null}

      <div className="calendar-layout">
        <section className="month-calendar" aria-label={`Calendario de ${monthLabel}`}>
          <header><button aria-label="Mes anterior" onClick={() => changeMonth(-1)} type="button"><Icon name="arrow-left" /></button><div><h2>{monthLabel}</h2><button onClick={goToday} type="button">Hoy</button></div><button aria-label="Mes siguiente" onClick={() => changeMonth(1)} type="button"><Icon name="arrow-right" /></button></header>
          <div className="calendar-weekdays" aria-hidden="true"><span>L</span><span>M</span><span>X</span><span>J</span><span>V</span><span>S</span><span>D</span></div>
          {loading ? <div className="calendar-loading" role="status"><span className="spinner" />Cargando eventos…</div> : loadError ? <div className="calendar-load-error" role="alert"><p>{loadError}</p><button className="secondary-button" onClick={() => void retry()} type="button">Reintentar</button></div> : <div className="calendar-grid">{days.map((day) => {
            const key = dateKey(day); const count = events.filter((event) => eventOccursOn(event, key)).length; const outside = day.getMonth() !== month.getMonth();
            return <button aria-label={`${day.getDate()} de ${new Intl.DateTimeFormat('es-ES', { month: 'long' }).format(day)}, ${count} eventos`} aria-pressed={selectedDate === key} className={`${outside ? 'is-outside' : ''} ${key === dateKey(today) ? 'is-today' : ''}`} key={key} onClick={() => selectDay(day)} type="button"><span>{day.getDate()}</span>{count > 0 ? <small>{count}</small> : null}</button>;
          })}</div>}
        </section>

        <section className="calendar-agenda" aria-labelledby="agenda-title"><header><div><span>Agenda</span><h2 id="agenda-title">{selectedLabel}</h2></div><strong>{selectedEvents.length}</strong></header>{selectedEvents.length === 0 ? <div className="calendar-empty"><span><Icon name="calendar" /></span><h3>Un día libre</h3><p>No hay eventos para esta fecha.</p><button className="secondary-button" onClick={() => { setEditingEvent(null); setFormOpen(true); }} type="button">Añadir evento</button></div> : <ul>{selectedEvents.map((event) => <li className={`calendar-event calendar-event--${event.color}`} key={event.id}><span className="calendar-event__time">{event.all_day ? 'Todo el día' : <>{formatTime(event.start_at!)}<small>{formatTime(event.end_at!)}</small></>}</span><div className="calendar-event__content"><h3>{event.title}</h3>{event.description ? <p>{event.description}</p> : null}{event.location ? isHttpUrl(event.location) ? <a href={event.location} rel="noreferrer noopener" target="_blank">Abrir ubicación <Icon name="arrow-right" size={14} /></a> : <span>{event.location}</span> : null}</div><div className="calendar-event__actions"><button aria-label={`Editar ${event.title}`} disabled={busyEventId === event.id} onClick={() => { setEditingEvent(event); setFormOpen(true); window.scrollTo({ top: 0, behavior: 'smooth' }); }} type="button"><Icon name="edit" size={17} /></button><button aria-label={`Eliminar ${event.title}`} className="is-danger" disabled={busyEventId === event.id} onClick={() => void remove(event)} type="button"><Icon name="trash" size={17} /></button></div></li>)}</ul>}</section>
      </div>
    </section>
  );
}
