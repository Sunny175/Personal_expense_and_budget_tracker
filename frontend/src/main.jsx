import React from 'react'
import { createRoot } from 'react-dom/client'
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react'
import App from './App.jsx'
import './styles.css'

function AuthenticatedApp() {
  const { isLoading, isAuthenticated, error, loginWithRedirect, logout, user } = useAuth0()
  if (isLoading) return <div className="loading">Connecting to Auth0...</div>
  if (error) return <div className="alert" role="alert">Authentication failed: {error.message}</div>
  if (!isAuthenticated) return <div className="auth-page"><section className="auth-card">
    <span className="eyebrow">PERSONAL FINANCE</span>
    <h1>Expense &amp; Budget Tracker<span className="heading-dot">.</span></h1>
    <p>Sign in securely to access your personal workspace.</p>
    <button className="button primary" onClick={() => loginWithRedirect()}>Sign in with Auth0</button>
  </section></div>
  return <App key={user?.sub} user={user} onLogout={() => logout({ logoutParams: { returnTo: window.location.origin } })} />
}

const domain = import.meta.env.VITE_AUTH0_DOMAIN
const clientId = import.meta.env.VITE_AUTH0_CLIENT_ID
const audience = import.meta.env.VITE_AUTH0_AUDIENCE
createRoot(document.getElementById('root')).render(<React.StrictMode>
  {domain && clientId && audience
    ? <Auth0Provider domain={domain} clientId={clientId} authorizationParams={{
      redirect_uri: window.location.origin, audience, scope: 'read:expenses write:expenses',
    }}><AuthenticatedApp /></Auth0Provider>
    : <div className="alert" role="alert">Auth0 configuration is missing. See the setup instructions in the README.</div>}
</React.StrictMode>)