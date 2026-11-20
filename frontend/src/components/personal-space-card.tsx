import { useState, type FormEvent } from 'react';

import type { Space } from '../api/spaces';

type PersonalSpaceCardProps = {
  busy: boolean;
  error: string | null;
  space: Space;
  onSave: (name: string) => Promise<boolean>;
};

export function PersonalSpaceCard({
  busy,
  error,
  space,
  onSave,
}: PersonalSpaceCardProps) {
  const [name, setName] = useState(space.name);
  const [saved, setSaved] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaved(false);
    const normalizedName = name.trim();
    const success = await onSave(normalizedName);

    if (success) {
      setName(normalizedName);
      setSaved(true);
    }
  };

  return (
    <section className="personal-space-card" aria-labelledby="personal-space-title">
      <div className="personal-space-card__heading">
        <div>
          <h2 id="personal-space-title">Tu espacio privado</h2>
        </div>
        <span aria-hidden="true" className="privacy-badge">Solo tú</span>
      </div>

      <p className="personal-space-card__description">
        Los gastos, tareas y eventos que guardes aquí no serán visibles para otros
        usuarios.
      </p>

      <form className="space-form" onSubmit={(event) => void submit(event)}>
        <label htmlFor="personal-space-name">Nombre del espacio</label>
        <input
          id="personal-space-name"
          maxLength={120}
          onChange={(event) => setName(event.target.value)}
          required
          type="text"
          value={name}
        />

        {error ? <p className="form-error" role="alert">{error}</p> : null}
        {saved ? <p className="form-success" role="status">Nombre guardado.</p> : null}

        <button className="primary-button" disabled={busy} type="submit">
          {busy ? 'Guardando…' : 'Guardar nombre'}
        </button>
      </form>
    </section>
  );
}
