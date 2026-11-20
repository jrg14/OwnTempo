import { useState, type FormEvent } from 'react';

import type { UserAccount } from '../api/auth';

type AccountCardProps = {
  busy: boolean;
  error: string | null;
  user: UserAccount;
  onSave: (
    changes: Pick<UserAccount, 'username' | 'first_name' | 'last_name'>,
  ) => Promise<boolean>;
};

export function AccountCard({ busy, error, user, onSave }: AccountCardProps) {
  const [username, setUsername] = useState(user.username);
  const [firstName, setFirstName] = useState(user.first_name);
  const [lastName, setLastName] = useState(user.last_name);
  const [saved, setSaved] = useState(false);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSaved(false);
    const normalizedUsername = username.trim();

    const success = await onSave({
      username: normalizedUsername,
      first_name: firstName,
      last_name: lastName,
    });
    if (success) setUsername(normalizedUsername);
    setSaved(success);
  };

  return (
    <section className="account-card" aria-labelledby="account-title">
      <div className="account-card__heading">
        <div>
          <p className="eyebrow">MI CUENTA</p>
          <h2 id="account-title">Datos personales</h2>
        </div>
        <span aria-hidden="true" className="account-avatar">
          {(user.first_name || user.username).slice(0, 1).toUpperCase()}
        </span>
      </div>

      <form className="account-form" onSubmit={(event) => void submit(event)}>
        <label htmlFor="account-username">Nombre de usuario</label>
        <input
          autoCapitalize="none"
          autoComplete="username"
          id="account-username"
          onChange={(event) => setUsername(event.target.value)}
          required
          type="text"
          value={username}
        />

        <div className="form-grid">
          <div>
            <label htmlFor="first-name">Nombre</label>
            <input
              autoComplete="given-name"
              id="first-name"
              onChange={(event) => setFirstName(event.target.value)}
              type="text"
              value={firstName}
            />
          </div>
          <div>
            <label htmlFor="last-name">Apellidos</label>
            <input
              autoComplete="family-name"
              id="last-name"
              onChange={(event) => setLastName(event.target.value)}
              type="text"
              value={lastName}
            />
          </div>
        </div>

        {error ? <p className="form-error" role="alert">{error}</p> : null}
        {saved ? <p className="form-success" role="status">Cambios guardados.</p> : null}

        <button className="primary-button" disabled={busy} type="submit">
          {busy ? 'Guardando…' : 'Guardar cambios'}
        </button>
      </form>
    </section>
  );
}
