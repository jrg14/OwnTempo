import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';

import { fetchSpaceModules } from '../api/modules';
import type { Space } from '../api/spaces';
import {
  createWish,
  deleteWish,
  fetchWishes,
  updateWish,
  type WishInput,
  type WishItem,
  type WishKind,
  type WishPriority,
  type WishStatus,
} from '../api/wishlist';
import { spaceErrorMessage } from '../hooks/use-spaces';
import { Icon } from './icon';

type WishlistWorkspaceProps = {
  onBack: () => void;
  onModuleUnavailable: () => void;
  space: Space;
};

type StatusFilter = 'all' | WishStatus;
type OptionalFilter<T extends string> = 'all' | T;

const kindLabels: Record<WishKind, string> = {
  product: 'Producto',
  experience: 'Experiencia',
  idea: 'Idea',
};

const statusLabels: Record<WishStatus, string> = {
  pending: 'Pendiente',
  obtained: 'Conseguido',
  dismissed: 'Descartado',
};

const priorityLabels: Record<WishPriority, string> = {
  low: 'Baja',
  normal: 'Normal',
  high: 'Alta',
};

function formatPrice(price: string, currency: string) {
  try {
    return new Intl.NumberFormat('es-ES', {
      style: 'currency',
      currency,
    }).format(Number(price));
  } catch {
    return `${price} ${currency}`;
  }
}

function WishForm({
  busy,
  onCancel,
  onSave,
  wish,
}: {
  busy: boolean;
  onCancel: () => void;
  onSave: (input: WishInput) => Promise<void>;
  wish: WishItem | null;
}) {
  const [title, setTitle] = useState(wish?.title ?? '');
  const [description, setDescription] = useState(wish?.description ?? '');
  const [kind, setKind] = useState<WishKind>(wish?.kind ?? 'product');
  const [priority, setPriority] = useState<WishPriority>(wish?.priority ?? 'normal');
  const [url, setUrl] = useState(wish?.url ?? '');
  const [imageUrl, setImageUrl] = useState(wish?.image_url ?? '');
  const [price, setPrice] = useState(wish?.price ?? '');
  const [currency, setCurrency] = useState(wish?.currency ?? 'EUR');
  const titleRef = useRef<HTMLInputElement>(null);

  useEffect(() => titleRef.current?.focus(), []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSave({
      title: title.trim(),
      description: description.trim(),
      kind,
      priority,
      url: url.trim(),
      image_url: imageUrl.trim(),
      price: price || null,
      currency: currency.trim().toUpperCase(),
    });
  };

  return (
    <form className="wish-form" onSubmit={(event) => void submit(event)}>
      <div className="wish-form__heading">
        <div>
          <h2>{wish ? 'Editar deseo' : 'Nuevo deseo'}</h2>
          <p>Guarda una idea para encontrarla cuando llegue el momento.</p>
        </div>
        <button aria-label="Cerrar formulario" className="icon-button" onClick={onCancel} type="button">
          <Icon name="close" />
        </button>
      </div>

      <div className="wish-form__grid">
        <label className="wish-form__wide">
          <span>Título</span>
          <input maxLength={200} onChange={(event) => setTitle(event.target.value)} placeholder="¿Qué te gustaría guardar?" ref={titleRef} required value={title} />
        </label>
        <label>
          <span>Tipo</span>
          <select onChange={(event) => setKind(event.target.value as WishKind)} value={kind}>
            <option value="product">Producto</option><option value="experience">Experiencia</option><option value="idea">Idea</option>
          </select>
        </label>
        <label>
          <span>Prioridad</span>
          <select onChange={(event) => setPriority(event.target.value as WishPriority)} value={priority}>
            <option value="low">Baja</option><option value="normal">Normal</option><option value="high">Alta</option>
          </select>
        </label>
        <label className="wish-form__wide">
          <span>Descripción <small>opcional</small></span>
          <textarea maxLength={2000} onChange={(event) => setDescription(event.target.value)} placeholder="Añade contexto o detalles" rows={3} value={description} />
        </label>
        <label className="wish-form__wide">
          <span>Enlace <small>opcional</small></span>
          <input onChange={(event) => setUrl(event.target.value)} placeholder="https://…" type="url" value={url} />
        </label>
        <label className="wish-form__wide">
          <span>Imagen de referencia <small>opcional</small></span>
          <input onChange={(event) => setImageUrl(event.target.value)} placeholder="https://…/imagen.jpg" type="url" value={imageUrl} />
        </label>
        <label>
          <span>Precio <small>opcional</small></span>
          <input min="0" onChange={(event) => setPrice(event.target.value)} placeholder="0,00" step="0.01" type="number" value={price} />
        </label>
        <label>
          <span>Moneda</span>
          <input maxLength={3} minLength={3} onChange={(event) => setCurrency(event.target.value.toUpperCase())} pattern="[A-Za-z]{3}" value={currency} />
        </label>
      </div>

      <div className="wish-form__actions">
        <button className="primary-button" disabled={busy || !title.trim()} type="submit">{busy ? 'Guardando…' : wish ? 'Guardar cambios' : 'Crear deseo'}</button>
        <button className="secondary-button" disabled={busy} onClick={onCancel} type="button">Cancelar</button>
      </div>
    </form>
  );
}

export function WishlistWorkspace({ onBack, onModuleUnavailable, space }: WishlistWorkspaceProps) {
  const [wishes, setWishes] = useState<WishItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyWishId, setBusyWishId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');
  const [formOpen, setFormOpen] = useState(false);
  const [editingWish, setEditingWish] = useState<WishItem | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('pending');
  const [kindFilter, setKindFilter] = useState<OptionalFilter<WishKind>>('all');
  const [priorityFilter, setPriorityFilter] = useState<OptionalFilter<WishPriority>>('all');

  const load = async () => {
    const modules = await fetchSpaceModules(space.id);
    const module = modules.find((candidate) => candidate.key === 'wishlist');
    if (!module?.enabled || !module.available) {
      onModuleUnavailable();
      return;
    }
    const response = await fetchWishes(space.id);
    setWishes(response.results);
  };

  useEffect(() => {
    let active = true;
    const initialLoad = async () => {
      try {
        await load();
      } catch (initialError) {
        if (active) setLoadError(spaceErrorMessage(initialError));
      } finally {
        if (active) setLoading(false);
      }
    };
    void initialLoad();
    return () => { active = false; };
  // load is intentionally scoped to the active space.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [space.id]);

  useEffect(() => {
    const verifyModule = () => {
      fetchSpaceModules(space.id).then((modules) => {
        const module = modules.find((candidate) => candidate.key === 'wishlist');
        if (!module?.enabled || !module.available) onModuleUnavailable();
      }).catch(() => undefined);
    };
    window.addEventListener('focus', verifyModule);
    return () => window.removeEventListener('focus', verifyModule);
  }, [onModuleUnavailable, space.id]);

  const counts = useMemo(() => ({
    pending: wishes.filter((wish) => wish.status === 'pending').length,
    obtained: wishes.filter((wish) => wish.status === 'obtained').length,
    dismissed: wishes.filter((wish) => wish.status === 'dismissed').length,
  }), [wishes]);

  const visibleWishes = useMemo(() => wishes.filter((wish) => {
    if (statusFilter !== 'all' && wish.status !== statusFilter) return false;
    if (kindFilter !== 'all' && wish.kind !== kindFilter) return false;
    if (priorityFilter !== 'all' && wish.priority !== priorityFilter) return false;
    return true;
  }), [kindFilter, priorityFilter, statusFilter, wishes]);

  const refresh = async () => {
    const response = await fetchWishes(space.id);
    setWishes(response.results);
  };

  const closeForm = () => {
    setFormOpen(false);
    setEditingWish(null);
  };

  const save = async (input: WishInput) => {
    setBusy(true);
    setError(null);
    try {
      if (editingWish) await updateWish(space.id, editingWish.id, input);
      else await createWish(space.id, input);
      await refresh();
      setAnnouncement(editingWish ? 'Deseo actualizado.' : 'Deseo creado.');
      closeForm();
    } catch (saveError) {
      setError(spaceErrorMessage(saveError));
    } finally {
      setBusy(false);
    }
  };

  const changeStatus = async (wish: WishItem, status: WishStatus) => {
    setBusyWishId(wish.id);
    setError(null);
    try {
      await updateWish(space.id, wish.id, { status });
      await refresh();
      setAnnouncement(`Deseo marcado como ${statusLabels[status].toLowerCase()}.`);
    } catch (updateError) {
      setError(spaceErrorMessage(updateError));
    } finally {
      setBusyWishId(null);
    }
  };

  const remove = async (wish: WishItem) => {
    if (!window.confirm(`¿Eliminar “${wish.title}”?`)) return;
    setBusyWishId(wish.id);
    setError(null);
    try {
      await deleteWish(space.id, wish.id);
      setWishes((current) => current.filter((item) => item.id !== wish.id));
      setAnnouncement('Deseo eliminado.');
    } catch (deleteError) {
      setError(spaceErrorMessage(deleteError));
    } finally {
      setBusyWishId(null);
    }
  };

  const retry = async () => {
    setLoading(true);
    setLoadError(null);
    try { await load(); } catch (retryError) { setLoadError(spaceErrorMessage(retryError)); }
    finally { setLoading(false); }
  };

  if (loading) return <div className="wishlist-loading" role="status"><span className="spinner" />Preparando tus deseos…</div>;

  if (loadError) return (
    <section className="wishlist-workspace">
      <button className="back-button" onClick={onBack} type="button"><Icon name="arrow-left" />Volver</button>
      <div className="task-load-error" role="alert"><h2>No pudimos cargar tus deseos</h2><p>{loadError}</p><button className="secondary-button" onClick={() => void retry()} type="button">Reintentar</button></div>
    </section>
  );

  return (
    <section className="wishlist-workspace" aria-labelledby="wishlist-title">
      <header className="wishlist-header">
        <button className="back-button" onClick={onBack} type="button"><Icon name="arrow-left" />Volver</button>
        <div className="wishlist-header__title">
          <div><h1 id="wishlist-title">Lista de deseos</h1><p>{space.name} · {counts.pending} pendientes</p></div>
          {!formOpen ? <button className="primary-button" onClick={() => { setEditingWish(null); setFormOpen(true); }} type="button"><Icon name="plus" />Nuevo deseo</button> : null}
        </div>
      </header>

      {error ? <p className="form-error wishlist-error" role="alert">{error}</p> : null}
      <p className="visually-hidden" aria-live="polite" role="status">{announcement}</p>
      {formOpen ? <WishForm busy={busy} key={editingWish?.id ?? 'new'} onCancel={closeForm} onSave={save} wish={editingWish} /> : null}

      <div className="wishlist-summary" aria-label="Resumen de deseos">
        <span><strong>{counts.pending}</strong>Pendientes</span><span><strong>{counts.obtained}</strong>Conseguidos</span><span><strong>{counts.dismissed}</strong>Descartados</span>
      </div>

      <div className="wishlist-toolbar">
        <div className="wish-status-tabs" role="group" aria-label="Estado">
          {(['pending', 'obtained', 'dismissed', 'all'] as const).map((value) => <button aria-pressed={statusFilter === value} className={statusFilter === value ? 'is-active' : ''} key={value} onClick={() => setStatusFilter(value)} type="button">{value === 'all' ? 'Todos' : statusLabels[value]}</button>)}
        </div>
        <div className="wish-filter-selects">
          <label><span>Tipo</span><select onChange={(event) => setKindFilter(event.target.value as OptionalFilter<WishKind>)} value={kindFilter}><option value="all">Todos</option><option value="product">Producto</option><option value="experience">Experiencia</option><option value="idea">Idea</option></select></label>
          <label><span>Prioridad</span><select onChange={(event) => setPriorityFilter(event.target.value as OptionalFilter<WishPriority>)} value={priorityFilter}><option value="all">Todas</option><option value="high">Alta</option><option value="normal">Normal</option><option value="low">Baja</option></select></label>
        </div>
      </div>

      {visibleWishes.length === 0 ? (
        <div className="wishlist-empty"><span><Icon name="heart" size={27} /></span><h2>{wishes.length === 0 ? 'Guarda tu primer deseo' : 'Sin coincidencias'}</h2><p>{wishes.length === 0 ? 'Productos, experiencias o ideas: déjalos aquí para más adelante.' : 'Prueba con otros filtros para encontrar lo que buscas.'}</p></div>
      ) : (
        <ul className="wish-grid">
          {visibleWishes.map((wish) => <li className={`wish-card wish-card--${wish.status}`} key={wish.id}>
            {wish.image_url ? <img alt="" loading="lazy" onError={(event) => { event.currentTarget.hidden = true; }} src={wish.image_url} /> : null}
            <div className="wish-card__body">
              <div className="wish-card__badges"><span>{kindLabels[wish.kind]}</span><span className={`priority-badge priority-badge--${wish.priority}`}>{priorityLabels[wish.priority]}</span><span className={`wish-state wish-state--${wish.status}`}>{statusLabels[wish.status]}</span></div>
              <h2>{wish.title}</h2>
              {wish.description ? <p>{wish.description}</p> : null}
              <div className="wish-card__meta">{wish.price ? <strong>{formatPrice(wish.price, wish.currency)}</strong> : null}{wish.url ? <a href={wish.url} rel="noreferrer noopener" target="_blank">Abrir enlace <Icon name="arrow-right" size={14} /></a> : null}</div>
            </div>
            <div className="wish-card__actions">
              {wish.status === 'pending' ? <><button disabled={busyWishId === wish.id} onClick={() => void changeStatus(wish, 'obtained')} type="button"><Icon name="checkmark" size={16} />Conseguido</button><button disabled={busyWishId === wish.id} onClick={() => void changeStatus(wish, 'dismissed')} type="button">Descartar</button></> : <button disabled={busyWishId === wish.id} onClick={() => void changeStatus(wish, 'pending')} type="button">Restaurar</button>}
              <button aria-label={`Editar ${wish.title}`} disabled={busyWishId === wish.id} onClick={() => { setEditingWish(wish); setFormOpen(true); window.scrollTo({ top: 0, behavior: 'smooth' }); }} type="button"><Icon name="edit" size={17} /></button>
              <button aria-label={`Eliminar ${wish.title}`} className="is-danger" disabled={busyWishId === wish.id} onClick={() => void remove(wish)} type="button"><Icon name="trash" size={17} /></button>
            </div>
          </li>)}
        </ul>
      )}
    </section>
  );
}
