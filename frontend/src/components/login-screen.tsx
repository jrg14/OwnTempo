import { useState, type FormEvent } from 'react';

type LoginScreenProps = {
  busy: boolean;
  error: string | null;
  onLogin: (username: string, password: string) => Promise<void>;
};

export function LoginScreen({ busy, error, onLogin }: LoginScreenProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void onLogin(username, password);
  };

  return (
    <main className="auth-page">
      <div className="auth-shell">
        <header className="brand-row">
          <span aria-hidden="true" className="logo-mark">
            <span />
          </span>
          <span className="brand">OwnTempo</span>
        </header>

        <section className="login-card" aria-labelledby="login-title">
          <div className="login-card__intro">
            <p className="eyebrow">TU VIDA, A TU RITMO</p>
            <h1 id="login-title">Bienvenido a casa.</h1>
            <p>Accede con el usuario que ha creado el administrador de OwnTempo.</p>
          </div>

          <form className="form-stack" onSubmit={submit}>
            <label htmlFor="username">Nombre de usuario</label>
            <input
              autoCapitalize="none"
              autoComplete="username"
              id="username"
              name="username"
              onChange={(event) => setUsername(event.target.value)}
              required
              type="text"
              value={username}
            />

            <label htmlFor="password">Contraseña</label>
            <input
              autoComplete="current-password"
              id="password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />

            {error ? <p className="form-error" role="alert">{error}</p> : null}

            <button className="primary-button" disabled={busy} type="submit">
              {busy ? 'Entrando…' : 'Entrar'}
            </button>
          </form>

          <p className="admin-note">
            Las altas y los cambios de contraseña se gestionan desde la administración.
          </p>
        </section>
      </div>
    </main>
  );
}
