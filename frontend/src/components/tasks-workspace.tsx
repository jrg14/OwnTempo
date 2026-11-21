import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';

import { fetchSpaceModules } from '../api/modules';
import { fetchMembers, type Space, type SpaceMember } from '../api/spaces';
import {
  createTask,
  deleteTask,
  fetchTasks,
  updateTask,
  type Task,
  type TaskInput,
  type TaskPriority,
  type TaskStatus,
} from '../api/tasks';
import { spaceErrorMessage } from '../hooks/use-spaces';
import { Icon } from './icon';

type TasksWorkspaceProps = {
  onBack: () => void;
  onModuleUnavailable: () => void;
  space: Space;
};

type StatusFilter = 'all' | TaskStatus;
type DueFilter = 'all' | 'overdue' | 'today' | 'upcoming' | 'none';

const today = () => {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

function displayName(user: Pick<Task['created_by'], 'first_name' | 'username'>) {
  return user.first_name || `@${user.username}`;
}

function sortTasks(tasks: Task[]) {
  return [...tasks].sort((left, right) => {
    if (left.status !== right.status) return left.status === 'pending' ? -1 : 1;
    if (left.due_date !== right.due_date) {
      if (!left.due_date) return 1;
      if (!right.due_date) return -1;
      return left.due_date.localeCompare(right.due_date);
    }
    return right.created_at.localeCompare(left.created_at);
  });
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat('es-ES', {
    day: 'numeric',
    month: 'short',
  }).format(new Date(`${value}T00:00:00`));
}

function TaskForm({
  busy,
  members,
  onCancel,
  onSave,
  task,
}: {
  busy: boolean;
  members: SpaceMember[];
  onCancel: () => void;
  onSave: (input: TaskInput) => Promise<void>;
  task: Task | null;
}) {
  const [title, setTitle] = useState(task?.title ?? '');
  const [description, setDescription] = useState(task?.description ?? '');
  const [priority, setPriority] = useState<TaskPriority>(task?.priority ?? 'normal');
  const [dueDate, setDueDate] = useState(task?.due_date ?? '');
  const [assigneeIds, setAssigneeIds] = useState<number[]>(
    task?.assignees.map((assignee) => assignee.id) ?? [],
  );
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    titleRef.current?.focus();
  }, []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSave({
      title: title.trim(),
      description: description.trim(),
      priority,
      due_date: dueDate || null,
      assignee_ids: assigneeIds,
    });
  };

  const toggleAssignee = (userId: number) => {
    setAssigneeIds((current) =>
      current.includes(userId)
        ? current.filter((id) => id !== userId)
        : [...current, userId],
    );
  };

  return (
    <form className="task-form" onSubmit={(event) => void submit(event)}>
      <div className="task-form__heading">
        <div>
          <h2>{task ? 'Editar tarea' : 'Nueva tarea'}</h2>
          <p>{task ? 'Actualiza lo necesario.' : 'Captura lo pendiente sin perder el ritmo.'}</p>
        </div>
        <button aria-label="Cerrar formulario" className="icon-button" onClick={onCancel} type="button">
          <Icon name="close" />
        </button>
      </div>

      <div className="task-form__main-field">
        <label htmlFor="task-title">Título</label>
        <input
          id="task-title"
          maxLength={200}
          onChange={(event) => setTitle(event.target.value)}
          placeholder="¿Qué hay que hacer?"
          ref={titleRef}
          required
          value={title}
        />
      </div>

      <div className="task-form__grid">
        <div>
          <label htmlFor="task-priority">Prioridad</label>
          <select id="task-priority" onChange={(event) => setPriority(event.target.value as TaskPriority)} value={priority}>
            <option value="low">Baja</option>
            <option value="normal">Normal</option>
            <option value="high">Alta</option>
          </select>
        </div>
        <div>
          <label htmlFor="task-due-date">Fecha límite</label>
          <input id="task-due-date" onChange={(event) => setDueDate(event.target.value)} type="date" value={dueDate} />
        </div>
      </div>

      <div className="task-form__main-field">
        <label htmlFor="task-description">Notas <span>opcional</span></label>
        <textarea
          id="task-description"
          maxLength={2000}
          onChange={(event) => setDescription(event.target.value)}
          placeholder="Añade contexto para ti o para el grupo"
          rows={3}
          value={description}
        />
      </div>

      {members.length > 1 ? (
        <fieldset className="assignee-picker">
          <legend>Responsables <span>opcional</span></legend>
          <div>
            {members.map((member) => (
              <label key={member.id}>
                <input
                  checked={assigneeIds.includes(member.id)}
                  onChange={() => toggleAssignee(member.id)}
                  type="checkbox"
                />
                <span>{member.first_name || `@${member.username}`}</span>
              </label>
            ))}
          </div>
        </fieldset>
      ) : null}

      <div className="task-form__actions">
        <button className="primary-button" disabled={busy || !title.trim()} type="submit">
          {busy ? 'Guardando…' : task ? 'Guardar cambios' : 'Crear tarea'}
        </button>
        <button className="secondary-button" disabled={busy} onClick={onCancel} type="button">Cancelar</button>
      </div>
    </form>
  );
}

export function TasksWorkspace({ onBack, onModuleUnavailable, space }: TasksWorkspaceProps) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [members, setMembers] = useState<SpaceMember[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [busyTaskId, setBusyTaskId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('pending');
  const [dueFilter, setDueFilter] = useState<DueFilter>('all');
  const [assigneeFilter, setAssigneeFilter] = useState('all');
  const [formOpen, setFormOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);
  const createButtonRef = useRef<HTMLButtonElement>(null);
  const returnFocusRef = useRef<HTMLButtonElement | null>(null);
  const activeFilterRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        const modules = await fetchSpaceModules(space.id);
        const tasksModule = modules.find((module) => module.key === 'tasks');
        if (!tasksModule?.enabled || !tasksModule.available) {
          if (active) onModuleUnavailable();
          return;
        }
        const [loadedTasks, loadedMembers] = await Promise.all([
          fetchTasks(space.id),
          space.kind === 'shared' ? fetchMembers(space.id) : Promise.resolve([]),
        ]);
        if (!active) return;
        setTasks(sortTasks(loadedTasks));
        setMembers(loadedMembers);
      } catch (initialLoadError) {
        if (active) setLoadError(spaceErrorMessage(initialLoadError));
      } finally {
        if (active) setLoading(false);
      }
    };
    void load();

    return () => {
      active = false;
    };
  }, [onModuleUnavailable, space.id, space.kind]);

  useEffect(() => {
    const verifyModule = () => {
      fetchSpaceModules(space.id)
        .then((modules) => {
          const tasksModule = modules.find((module) => module.key === 'tasks');
          if (!tasksModule?.enabled || !tasksModule.available) onModuleUnavailable();
        })
        .catch(() => undefined);
    };
    window.addEventListener('focus', verifyModule);
    return () => window.removeEventListener('focus', verifyModule);
  }, [onModuleUnavailable, space.id]);

  const visibleTasks = useMemo(() => {
    const currentDate = today();
    return tasks.filter((task) => {
      if (statusFilter !== 'all' && task.status !== statusFilter) return false;
      if (assigneeFilter !== 'all' && !task.assignees.some((user) => user.id === Number(assigneeFilter))) return false;
      if (dueFilter === 'overdue' && !(task.status === 'pending' && task.due_date && task.due_date < currentDate)) return false;
      if (dueFilter === 'today' && task.due_date !== currentDate) return false;
      if (dueFilter === 'upcoming' && !(task.due_date && task.due_date > currentDate)) return false;
      if (dueFilter === 'none' && task.due_date) return false;
      return true;
    });
  }, [assigneeFilter, dueFilter, statusFilter, tasks]);

  const pendingCount = tasks.filter((task) => task.status === 'pending').length;

  const closeForm = () => {
    const returnTarget = returnFocusRef.current;
    setFormOpen(false);
    setEditingTask(null);
    window.requestAnimationFrame(() => {
      if (returnTarget?.isConnected) returnTarget.focus();
      else createButtonRef.current?.focus();
    });
  };

  const openCreateForm = (trigger: HTMLButtonElement) => {
    returnFocusRef.current = trigger;
    setEditingTask(null);
    setFormOpen(true);
  };

  const retryLoad = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const modules = await fetchSpaceModules(space.id);
      const tasksModule = modules.find((module) => module.key === 'tasks');
      if (!tasksModule?.enabled || !tasksModule.available) {
        onModuleUnavailable();
        return;
      }
      const [loadedTasks, loadedMembers] = await Promise.all([
        fetchTasks(space.id),
        space.kind === 'shared' ? fetchMembers(space.id) : Promise.resolve([]),
      ]);
      setTasks(sortTasks(loadedTasks));
      setMembers(loadedMembers);
    } catch (retryError) {
      setLoadError(spaceErrorMessage(retryError));
    } finally {
      setLoading(false);
    }
  };

  const save = async (input: TaskInput) => {
    setSaving(true);
    setError(null);
    try {
      const saved = editingTask
        ? await updateTask(space.id, editingTask.id, input)
        : await createTask(space.id, input);
      setTasks((current) => sortTasks([
        ...current.filter((task) => task.id !== saved.id),
        saved,
      ]));
      setAnnouncement(editingTask ? 'Tarea actualizada.' : 'Tarea creada.');
      closeForm();
    } catch (saveError) {
      setError(spaceErrorMessage(saveError));
    } finally {
      setSaving(false);
    }
  };

  const toggleStatus = async (task: Task) => {
    setBusyTaskId(task.id);
    setError(null);
    try {
      const updated = await updateTask(space.id, task.id, {
        status: task.status === 'pending' ? 'completed' : 'pending',
      });
      setTasks((current) => sortTasks(current.map((item) => item.id === updated.id ? updated : item)));
      setAnnouncement(updated.status === 'completed' ? 'Tarea completada.' : 'Tarea reabierta.');
      if (statusFilter !== 'all') {
        window.requestAnimationFrame(() => activeFilterRef.current?.focus());
      }
    } catch (updateError) {
      setError(spaceErrorMessage(updateError));
    } finally {
      setBusyTaskId(null);
    }
  };

  const remove = async (task: Task) => {
    if (!window.confirm(`¿Eliminar “${task.title}”? Esta acción no se puede deshacer.`)) return;
    setBusyTaskId(task.id);
    setError(null);
    try {
      await deleteTask(space.id, task.id);
      setTasks((current) => current.filter((item) => item.id !== task.id));
      setAnnouncement('Tarea eliminada.');
      window.requestAnimationFrame(() => activeFilterRef.current?.focus());
    } catch (deleteError) {
      setError(spaceErrorMessage(deleteError));
    } finally {
      setBusyTaskId(null);
    }
  };

  const edit = (task: Task, trigger: HTMLButtonElement) => {
    returnFocusRef.current = trigger;
    setEditingTask(task);
    setFormOpen(true);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const emptyMessage = tasks.length === 0
    ? 'Crea la primera tarea y convierte una intención en el siguiente paso.'
    : 'No hay tareas que coincidan con estos filtros.';

  return (
    <section className="tasks-workspace" aria-labelledby="tasks-title">
      <header className="tasks-header">
        <button className="back-button" onClick={onBack} type="button">
          <Icon name="arrow-left" />
          Volver
        </button>
        <div className="tasks-header__title">
          <div>
            <h1 id="tasks-title">Tareas</h1>
            <p>{space.name} · {pendingCount} {pendingCount === 1 ? 'pendiente' : 'pendientes'}</p>
          </div>
          {!formOpen ? (
            <button
              className="primary-button task-create-button"
              onClick={(event) => openCreateForm(event.currentTarget)}
              ref={createButtonRef}
              type="button"
            >
              <Icon name="plus" />
              Nueva tarea
            </button>
          ) : null}
        </div>
      </header>

      {error ? <p className="form-error tasks-error" role="alert">{error}</p> : null}
      <p className="visually-hidden" aria-live="polite" role="status">{announcement}</p>

      {formOpen ? (
        <TaskForm busy={saving} key={editingTask?.id ?? 'new'} members={members} onCancel={closeForm} onSave={save} task={editingTask} />
      ) : null}

      {!loading && !loadError ? <div className="task-toolbar" aria-label="Filtros de tareas">
        <div className="task-status-tabs" role="group" aria-label="Estado">
          {(['pending', 'completed', 'all'] as const).map((filter) => (
            <button
              aria-pressed={statusFilter === filter}
              className={statusFilter === filter ? 'is-active' : ''}
              key={filter}
              onClick={() => setStatusFilter(filter)}
              ref={statusFilter === filter ? activeFilterRef : undefined}
              type="button"
            >
              {filter === 'pending' ? 'Pendientes' : filter === 'completed' ? 'Completadas' : 'Todas'}
            </button>
          ))}
        </div>
        <div className="task-filter-selects">
          <label>
            <span>Fecha</span>
            <select onChange={(event) => setDueFilter(event.target.value as DueFilter)} value={dueFilter}>
              <option value="all">Cualquier fecha</option>
              <option value="overdue">Vencidas</option>
              <option value="today">Para hoy</option>
              <option value="upcoming">Próximas</option>
              <option value="none">Sin fecha</option>
            </select>
          </label>
          {members.length > 1 ? (
            <label>
              <span>Responsable</span>
              <select onChange={(event) => setAssigneeFilter(event.target.value)} value={assigneeFilter}>
                <option value="all">Cualquiera</option>
                {members.map((member) => (
                  <option key={member.id} value={member.id}>{member.first_name || `@${member.username}`}</option>
                ))}
              </select>
            </label>
          ) : null}
        </div>
      </div> : null}

      {loading ? (
        <div className="task-skeletons" aria-label="Cargando tareas" role="status">
          <span /><span /><span />
        </div>
      ) : loadError ? (
        <div className="task-load-error" role="alert">
          <h2>No pudimos cargar las tareas</h2>
          <p>{loadError}</p>
          <button className="secondary-button" onClick={() => void retryLoad()} type="button">Reintentar</button>
        </div>
      ) : visibleTasks.length === 0 ? (
        <div className="task-empty-state">
          <span aria-hidden="true"><Icon name="check" size={26} /></span>
          <h2>{tasks.length === 0 ? 'Todo empieza por una tarea' : 'Sin coincidencias'}</h2>
          <p>{emptyMessage}</p>
          {tasks.length === 0 && !formOpen ? (
            <button className="secondary-button" onClick={(event) => openCreateForm(event.currentTarget)} type="button">Crear una tarea</button>
          ) : null}
        </div>
      ) : (
        <ul className="task-list" aria-live="polite">
          {visibleTasks.map((task) => {
            const overdue = task.status === 'pending' && Boolean(task.due_date && task.due_date < today());
            return (
              <li className={task.status === 'completed' ? 'is-completed' : ''} key={task.id}>
                <button
                  aria-label={task.status === 'pending' ? `Completar ${task.title}` : `Reabrir ${task.title}`}
                  className="task-check"
                  disabled={busyTaskId === task.id}
                  onClick={() => void toggleStatus(task)}
                  type="button"
                >
                  {task.status === 'completed' ? <Icon name="checkmark" size={16} /> : null}
                </button>
                <div className="task-list__content">
                  <div className="task-list__topline">
                    <h2>{task.title}</h2>
                    {task.priority !== 'normal' ? <span className={`priority-badge priority-badge--${task.priority}`}>{task.priority === 'high' ? 'Alta' : 'Baja'}</span> : null}
                  </div>
                  {task.description ? <p>{task.description}</p> : null}
                  <div className="task-meta">
                    {task.due_date ? (
                      <span className={overdue ? 'is-overdue' : ''}>
                        <Icon name="clock" size={15} />
                        {overdue ? 'Venció ' : ''}{formatDate(task.due_date)}
                      </span>
                    ) : null}
                    {task.assignees.length > 0 ? (
                      <span><Icon name="users" size={15} />{task.assignees.map(displayName).join(', ')}</span>
                    ) : null}
                    {task.assignees.length === 0 && space.kind === 'shared' ? <span>Sin asignar</span> : null}
                  </div>
                </div>
                <div className="task-actions">
                  <button aria-label={`Editar ${task.title}`} disabled={busyTaskId === task.id} onClick={(event) => edit(task, event.currentTarget)} type="button"><Icon name="edit" size={18} /></button>
                  <button aria-label={`Eliminar ${task.title}`} className="is-danger" disabled={busyTaskId === task.id} onClick={() => void remove(task)} type="button"><Icon name="trash" size={18} /></button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
