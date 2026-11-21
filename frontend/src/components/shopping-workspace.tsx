import { useEffect, useMemo, useRef, useState, type FormEvent } from 'react';

import { fetchSpaceModules } from '../api/modules';
import type { Space } from '../api/spaces';
import {
  createShoppingItem,
  createShoppingList,
  deleteShoppingItem,
  deleteShoppingList,
  fetchShoppingList,
  fetchShoppingLists,
  reorderShoppingItems,
  updateShoppingItem,
  updateShoppingList,
  type ShoppingItem,
  type ShoppingItemInput,
  type ShoppingItemStatus,
  type ShoppingList,
} from '../api/shopping';
import { spaceErrorMessage } from '../hooks/use-spaces';
import { Icon } from './icon';

type ShoppingWorkspaceProps = {
  onBack: () => void;
  onModuleUnavailable: () => void;
  space: Space;
};

type ItemFilter = 'all' | ShoppingItemStatus;

function ItemForm({
  busy,
  item,
  onCancel,
  onSave,
}: {
  busy: boolean;
  item: ShoppingItem | null;
  onCancel: () => void;
  onSave: (input: ShoppingItemInput) => Promise<void>;
}) {
  const [name, setName] = useState(item?.name ?? '');
  const [quantity, setQuantity] = useState(item?.quantity ?? '');
  const [unit, setUnit] = useState(item?.unit ?? '');
  const [note, setNote] = useState(item?.note ?? '');
  const nameRef = useRef<HTMLInputElement>(null);

  useEffect(() => nameRef.current?.focus(), []);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSave({
      name: name.trim(),
      quantity: quantity.trim(),
      unit: unit.trim(),
      note: note.trim(),
    });
  };

  return (
    <form className="shopping-item-form" onSubmit={(event) => void submit(event)}>
      <div className="shopping-item-form__heading">
        <h3>{item ? 'Editar producto' : 'Añadir producto'}</h3>
        {item ? (
          <button aria-label="Cancelar edición" className="icon-button" onClick={onCancel} type="button">
            <Icon name="close" />
          </button>
        ) : null}
      </div>
      <div className="shopping-item-form__fields">
        <label className="shopping-item-form__name">
          <span>Producto</span>
          <input
            maxLength={200}
            onChange={(event) => setName(event.target.value)}
            placeholder="Leche, pan, fruta…"
            ref={nameRef}
            required
            value={name}
          />
        </label>
        <label>
          <span>Cantidad</span>
          <input maxLength={80} onChange={(event) => setQuantity(event.target.value)} placeholder="2" value={quantity} />
        </label>
        <label>
          <span>Unidad</span>
          <input maxLength={80} onChange={(event) => setUnit(event.target.value)} placeholder="uds" value={unit} />
        </label>
        <label className="shopping-item-form__note">
          <span>Nota <small>opcional</small></span>
          <input maxLength={500} onChange={(event) => setNote(event.target.value)} placeholder="Marca, variedad…" value={note} />
        </label>
      </div>
      <div className="shopping-item-form__actions">
        <button className="primary-button" disabled={busy || !name.trim()} type="submit">
          {busy ? 'Guardando…' : item ? 'Guardar cambios' : 'Añadir'}
        </button>
        {item ? <button className="secondary-button" disabled={busy} onClick={onCancel} type="button">Cancelar</button> : null}
      </div>
    </form>
  );
}

export function ShoppingWorkspace({ onBack, onModuleUnavailable, space }: ShoppingWorkspaceProps) {
  const [lists, setLists] = useState<ShoppingList[]>([]);
  const [selectedList, setSelectedList] = useState<ShoppingList | null>(null);
  const [selectedListId, setSelectedListId] = useState<number | null>(null);
  const [newListName, setNewListName] = useState('');
  const [editingItem, setEditingItem] = useState<ShoppingItem | null>(null);
  const [filter, setFilter] = useState<ItemFilter>('pending');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [busyItemId, setBusyItemId] = useState<number | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');

  const load = async (preferredListId?: number | null) => {
    const modules = await fetchSpaceModules(space.id);
    const module = modules.find((candidate) => candidate.key === 'shopping');
    if (!module?.enabled || !module.available) {
      onModuleUnavailable();
      return;
    }
    const loadedLists = await fetchShoppingLists(space.id);
    const nextListId = preferredListId && loadedLists.some((list) => list.id === preferredListId)
      ? preferredListId
      : loadedLists[0]?.id ?? null;
    const detail = nextListId ? await fetchShoppingList(space.id, nextListId) : null;
    setLists(loadedLists);
    setSelectedListId(nextListId);
    setSelectedList(detail);
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
      fetchSpaceModules(space.id)
        .then((modules) => {
          const module = modules.find((candidate) => candidate.key === 'shopping');
          if (!module?.enabled || !module.available) onModuleUnavailable();
        })
        .catch(() => undefined);
    };
    window.addEventListener('focus', verifyModule);
    return () => window.removeEventListener('focus', verifyModule);
  }, [onModuleUnavailable, space.id]);

  const visibleItems = useMemo(
    () => selectedList?.items.filter((item) => filter === 'all' || item.status === filter) ?? [],
    [filter, selectedList],
  );

  const refresh = async (listId = selectedListId) => {
    await load(listId);
  };

  const selectList = async (listId: number) => {
    setSelectedListId(listId);
    setEditingItem(null);
    setError(null);
    try {
      setSelectedList(await fetchShoppingList(space.id, listId));
    } catch (selectError) {
      setError(spaceErrorMessage(selectError));
    }
  };

  const createList = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!newListName.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const created = await createShoppingList(space.id, newListName.trim());
      setNewListName('');
      await refresh(created.id);
      setAnnouncement('Lista creada.');
    } catch (createError) {
      setError(spaceErrorMessage(createError));
    } finally {
      setBusy(false);
    }
  };

  const renameList = async () => {
    if (!selectedList) return;
    const name = window.prompt('Nuevo nombre de la lista', selectedList.name)?.trim();
    if (!name || name === selectedList.name) return;
    setBusy(true);
    setError(null);
    try {
      await updateShoppingList(space.id, selectedList.id, name);
      await refresh(selectedList.id);
      setAnnouncement('Lista renombrada.');
    } catch (renameError) {
      setError(spaceErrorMessage(renameError));
    } finally {
      setBusy(false);
    }
  };

  const removeList = async () => {
    if (!selectedList || !window.confirm(`¿Eliminar “${selectedList.name}” y todos sus productos?`)) return;
    setBusy(true);
    setError(null);
    try {
      await deleteShoppingList(space.id, selectedList.id);
      await refresh(null);
      setAnnouncement('Lista eliminada.');
    } catch (deleteError) {
      setError(spaceErrorMessage(deleteError));
    } finally {
      setBusy(false);
    }
  };

  const saveItem = async (input: ShoppingItemInput) => {
    if (!selectedList) return;
    setBusy(true);
    setError(null);
    try {
      if (editingItem) {
        await updateShoppingItem(space.id, selectedList.id, editingItem.id, input);
      } else {
        await createShoppingItem(space.id, selectedList.id, input);
      }
      await refresh(selectedList.id);
      setEditingItem(null);
      setAnnouncement(editingItem ? 'Producto actualizado.' : 'Producto añadido.');
    } catch (saveError) {
      setError(spaceErrorMessage(saveError));
    } finally {
      setBusy(false);
    }
  };

  const toggleItem = async (item: ShoppingItem) => {
    if (!selectedList) return;
    setBusyItemId(item.id);
    setError(null);
    try {
      await updateShoppingItem(space.id, selectedList.id, item.id, {
        status: item.status === 'pending' ? 'purchased' : 'pending',
      });
      await refresh(selectedList.id);
      setAnnouncement(item.status === 'pending' ? 'Producto comprado.' : 'Producto restaurado.');
    } catch (toggleError) {
      setError(spaceErrorMessage(toggleError));
    } finally {
      setBusyItemId(null);
    }
  };

  const removeItem = async (item: ShoppingItem) => {
    if (!selectedList || !window.confirm(`¿Eliminar “${item.name}”?`)) return;
    setBusyItemId(item.id);
    setError(null);
    try {
      await deleteShoppingItem(space.id, selectedList.id, item.id);
      await refresh(selectedList.id);
      setAnnouncement('Producto eliminado.');
    } catch (deleteError) {
      setError(spaceErrorMessage(deleteError));
    } finally {
      setBusyItemId(null);
    }
  };

  const moveItem = async (item: ShoppingItem, direction: -1 | 1) => {
    if (!selectedList) return;
    const sameStatus = selectedList.items.filter((candidate) => candidate.status === item.status);
    const statusIndex = sameStatus.findIndex((candidate) => candidate.id === item.id);
    const target = sameStatus[statusIndex + direction];
    if (!target) return;
    const orderedIds = selectedList.items.map((candidate) => candidate.id);
    const sourceIndex = orderedIds.indexOf(item.id);
    const targetIndex = orderedIds.indexOf(target.id);
    [orderedIds[sourceIndex], orderedIds[targetIndex]] = [orderedIds[targetIndex], orderedIds[sourceIndex]];
    setBusyItemId(item.id);
    setError(null);
    try {
      await reorderShoppingItems(space.id, selectedList.id, orderedIds);
      await refresh(selectedList.id);
      setAnnouncement('Orden actualizado.');
    } catch (moveError) {
      setError(spaceErrorMessage(moveError));
    } finally {
      setBusyItemId(null);
    }
  };

  const retry = async () => {
    setLoading(true);
    setLoadError(null);
    try {
      await load(selectedListId);
    } catch (retryError) {
      setLoadError(spaceErrorMessage(retryError));
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="shopping-loading" role="status"><span className="spinner" />Preparando tus listas…</div>;
  }

  if (loadError) {
    return (
      <section className="shopping-workspace">
        <button className="back-button" onClick={onBack} type="button"><Icon name="arrow-left" />Volver</button>
        <div className="task-load-error" role="alert">
          <h2>No pudimos cargar las listas</h2><p>{loadError}</p>
          <button className="secondary-button" onClick={() => void retry()} type="button">Reintentar</button>
        </div>
      </section>
    );
  }

  return (
    <section className="shopping-workspace" aria-labelledby="shopping-title">
      <header className="shopping-header">
        <button className="back-button" onClick={onBack} type="button"><Icon name="arrow-left" />Volver</button>
        <div>
          <h1 id="shopping-title">Listas de la compra</h1>
          <p>{space.name} · {lists.length} {lists.length === 1 ? 'lista' : 'listas'}</p>
        </div>
      </header>

      {error ? <p className="form-error shopping-error" role="alert">{error}</p> : null}
      <p className="visually-hidden" aria-live="polite" role="status">{announcement}</p>

      <div className="shopping-layout">
        <aside className="shopping-lists" aria-label="Tus listas">
          <div className="shopping-lists__heading"><h2>Listas</h2></div>
          {lists.length > 0 ? (
            <div className="shopping-lists__tabs" role="list">
              {lists.map((list) => (
                <button
                  aria-current={selectedListId === list.id ? 'true' : undefined}
                  className={selectedListId === list.id ? 'is-active' : ''}
                  key={list.id}
                  onClick={() => void selectList(list.id)}
                  role="listitem"
                  type="button"
                >
                  <span>{list.name}</span><small>{list.pending_count} pendientes</small>
                </button>
              ))}
            </div>
          ) : <p className="shopping-lists__empty">Aún no tienes ninguna lista.</p>}
          <form className="shopping-list-create" onSubmit={(event) => void createList(event)}>
            <label htmlFor="new-shopping-list">Nueva lista</label>
            <div>
              <input id="new-shopping-list" maxLength={120} onChange={(event) => setNewListName(event.target.value)} placeholder="Supermercado" required value={newListName} />
              <button aria-label="Crear lista" className="primary-button" disabled={busy || !newListName.trim()} type="submit"><Icon name="plus" /></button>
            </div>
          </form>
        </aside>

        {selectedList ? (
          <article className="shopping-detail">
            <header className="shopping-detail__header">
              <div>
                <h2>{selectedList.name}</h2>
                <p>{selectedList.pending_count} pendientes · {selectedList.purchased_count} comprados</p>
              </div>
              <div className="shopping-detail__actions">
                <button aria-label="Renombrar lista" disabled={busy} onClick={() => void renameList()} type="button"><Icon name="edit" /></button>
                <button aria-label="Eliminar lista" className="is-danger" disabled={busy} onClick={() => void removeList()} type="button"><Icon name="trash" /></button>
              </div>
            </header>

            <ItemForm busy={busy} item={editingItem} key={editingItem?.id ?? `new-${selectedList.id}`} onCancel={() => setEditingItem(null)} onSave={saveItem} />

            <div className="shopping-filters" role="group" aria-label="Filtrar productos">
              {(['pending', 'purchased', 'all'] as const).map((value) => (
                <button aria-pressed={filter === value} className={filter === value ? 'is-active' : ''} key={value} onClick={() => setFilter(value)} type="button">
                  {value === 'pending' ? 'Pendientes' : value === 'purchased' ? 'Comprados' : 'Todos'}
                </button>
              ))}
            </div>

            {visibleItems.length === 0 ? (
              <div className="shopping-empty">
                <span><Icon name="cart" size={26} /></span>
                <h3>{selectedList.item_count === 0 ? 'La lista está vacía' : filter === 'pending' ? 'Todo comprado' : 'Sin productos aquí'}</h3>
                <p>{selectedList.item_count === 0 ? 'Añade el primer producto para empezar.' : 'Puedes cambiar el filtro o restaurar un producto.'}</p>
              </div>
            ) : (
              <ul className="shopping-items">
                {visibleItems.map((item) => {
                  const sameStatus = selectedList.items.filter((candidate) => candidate.status === item.status);
                  const itemIndex = sameStatus.findIndex((candidate) => candidate.id === item.id);
                  return (
                    <li className={item.status === 'purchased' ? 'is-purchased' : ''} key={item.id}>
                      <button aria-label={item.status === 'pending' ? `Marcar ${item.name} como comprado` : `Restaurar ${item.name}`} className="task-check" disabled={busyItemId === item.id} onClick={() => void toggleItem(item)} type="button">
                        {item.status === 'purchased' ? <Icon name="checkmark" size={16} /> : null}
                      </button>
                      <div className="shopping-item__content">
                        <h3>{item.name}</h3>
                        {item.quantity || item.unit ? <p className="shopping-item__quantity">{[item.quantity, item.unit].filter(Boolean).join(' ')}</p> : null}
                        {item.note ? <p>{item.note}</p> : null}
                      </div>
                      <div className="shopping-item__actions">
                        <button aria-label={`Subir ${item.name}`} disabled={busyItemId === item.id || itemIndex === 0} onClick={() => void moveItem(item, -1)} type="button">↑</button>
                        <button aria-label={`Bajar ${item.name}`} disabled={busyItemId === item.id || itemIndex === sameStatus.length - 1} onClick={() => void moveItem(item, 1)} type="button">↓</button>
                        <button aria-label={`Editar ${item.name}`} disabled={busyItemId === item.id} onClick={() => setEditingItem(item)} type="button"><Icon name="edit" size={17} /></button>
                        <button aria-label={`Eliminar ${item.name}`} className="is-danger" disabled={busyItemId === item.id} onClick={() => void removeItem(item)} type="button"><Icon name="trash" size={17} /></button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </article>
        ) : (
          <div className="shopping-welcome">
            <span><Icon name="cart" size={28} /></span>
            <h2>Crea tu primera lista</h2>
            <p>Separa la compra semanal, una celebración o cualquier recado.</p>
          </div>
        )}
      </div>
    </section>
  );
}
