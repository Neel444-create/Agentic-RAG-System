import React, { useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const demoUsers = [
  { role: 'Admin', email: 'admin@infosys-demo.com', password: 'Admin@123' },
  { role: 'HR', email: 'hr@infosys-demo.com', password: 'Hr@12345' },
  { role: 'Employee', email: 'employee@infosys-demo.com', password: 'Employee@123' },
];

function App() {
  const [credentials, setCredentials] = useState(demoUsers[2]);
  const [session, setSession] = useState(null);
  const [message, setMessage] = useState('Login with a demo account to see role-aware actions.');

  const roleActions = useMemo(() => {
    if (!session) return [];
    const common = ['View profile', 'Browse asset catalog'];
    if (session.role === 'admin') {
      return [...common, 'Create employees', 'Register assets', 'Approve asset requests'];
    }
    if (session.role === 'hr') {
      return [...common, 'View employee directory', 'Approve leave requests'];
    }
    return [...common, 'Apply for leave', 'Track leave status', 'Request IT hardware'];
  }, [session]);

  async function login(event) {
    event.preventDefault();
    setMessage('Authenticating...');
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: credentials.email, password: credentials.password }),
    });
    if (!response.ok) {
      setMessage('Login failed. Check that the FastAPI backend is running.');
      return;
    }
    const token = await response.json();
    const profileResponse = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${token.access_token}` },
    });
    const profile = await profileResponse.json();
    setSession({ ...token, profile });
    setMessage(`Welcome ${profile.full_name}. Your ${token.role} workspace is ready.`);
  }

  return (
    <main className="shell">
      <section className="hero">
        <p className="eyebrow">Infosys-style enterprise engineering portfolio</p>
        <h1>Leave & Asset Management Portal</h1>
        <p>
          A React client concept for the FastAPI RBAC backend, showing how Admin, HR, and Employee journeys can share one secure portal.
        </p>
      </section>

      <section className="panel grid">
        <form onSubmit={login} className="card">
          <h2>Demo login</h2>
          <label>
            Demo role
            <select
              value={credentials.email}
              onChange={(event) => setCredentials(demoUsers.find((user) => user.email === event.target.value))}
            >
              {demoUsers.map((user) => (
                <option key={user.email} value={user.email}>{user.role}</option>
              ))}
            </select>
          </label>
          <label>
            Email
            <input value={credentials.email} onChange={(event) => setCredentials({ ...credentials, email: event.target.value })} />
          </label>
          <label>
            Password
            <input type="password" value={credentials.password} onChange={(event) => setCredentials({ ...credentials, password: event.target.value })} />
          </label>
          <button type="submit">Open workspace</button>
          <p className="status">{message}</p>
        </form>

        <div className="card">
          <h2>Role-aware workspace</h2>
          {session ? (
            <>
              <p><strong>{session.profile.full_name}</strong> · {session.profile.department}</p>
              <ul>
                {roleActions.map((action) => <li key={action}>{action}</li>)}
              </ul>
            </>
          ) : (
            <p>After login, this card displays the actions available to the authenticated user role.</p>
          )}
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById('root')).render(<App />);
