import { useEffect, useState } from 'react'
import { ArrowLeft, ArrowRight, CalendarDays, Check, CreditCard, Grid2X2, IndianRupee, Plus, WalletCards } from 'lucide-react'
import { useRequest } from './api/client'
import Modal from './components/Modal'
import Overview from './pages/Overview'
import Transactions from './pages/Transactions'
import Budgets from './pages/Budgets'
import { money, monthLabel, shiftMonth, title, today } from './utils/format'

export default function App({ user, onLogout }) {
  const request = useRequest()
  const [month, setMonth] = useState(today().slice(0, 7))
  const [view, setView] = useState('overview')
  const [modal, setModal] = useState(null)
  const [category, setCategory] = useState('')
  const [editingExpense, setEditingExpense] = useState(null)
  const [query, setQuery] = useState('')
  const [summary, setSummary] = useState({ total_spent: '0.00', categories: [] })
  const [expenses, setExpenses] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [revision, setRevision] = useState(0)
  useEffect(() => {
    let active = true
    setLoading(true); setError('')
    Promise.all([request(`/api/summary?month=${month}`), request(`/api/expenses?month=${month}`)])
      .then(([nextSummary, nextExpenses]) => { if (active) { setSummary(nextSummary); setExpenses(nextExpenses) } })
      .catch((issue) => { if (active) setError(issue.message === 'Failed to fetch' ? 'Cannot connect to the server. Check that the API is running.' : issue.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [month, revision, request])
  useEffect(() => { if (notice) { const timer = setTimeout(() => setNotice(''), 3500); return () => clearTimeout(timer) } }, [notice])
  function showBudget(value = '') { setCategory(value); setEditingExpense(null); setModal('budget') }
  function showExpense(expense = null) { setEditingExpense(expense); setCategory(''); setModal('expense') }
  function showOverview(event) {
    if (event.button === 0 && !event.metaKey && !event.ctrlKey && !event.shiftKey && !event.altKey) {
      event.preventDefault()
      setView('overview')
    }
  }
  function saved(message) { setModal(null); setNotice(message); setRevision((value) => value + 1) }
  async function remove(expense) {
    if (!window.confirm(`Delete ${expense.description || expense.category} (${money(expense.amount)})?`)) return
    try { await request(`/api/expenses/${expense.id}`, { method: 'DELETE' }); setNotice('Expense deleted'); setRevision((value) => value + 1) } catch (issue) { setError(issue.message) }
  }
  const nav = [{ id: 'overview', label: 'Overview', icon: Grid2X2 }, { id: 'transactions', label: 'Transactions', icon: CreditCard }, { id: 'budgets', label: 'Budgets', icon: WalletCards }]
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark"><span /><span /><span /></div><span>Expense &amp;<br />Budget Tracker<span className="brand-period">.</span></span></div><div className="workspace-label">PERSONAL FINANCE</div><nav aria-label="Main navigation">{nav.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${view === id ? 'active' : ''}`} onClick={() => setView(id)}><Icon size={18} strokeWidth={1.7} />{label}{view === id && <span className="nav-dot" />}</button>)}</nav><div className="sidebar-bottom"><div className="side-symbol"><IndianRupee size={17} /></div><div><strong>All in one place.</strong><span>Your money, made clearer.</span></div></div></aside>
    <main className="main"><header className="topbar"><div className="breadcrumb"><a href={import.meta.env.BASE_URL} onClick={showOverview} aria-label="Go to overview">YOUR WORKSPACE</a><span className="slash">/</span><strong>{title(view)}</strong></div><div className="top-right"><span className="local-indicator"><span /> {user?.name || 'SIGNED IN'}</span><button className="button secondary" onClick={onLogout}>Sign out</button></div></header>
      <div className="content"><div className="page-heading"><div><div className="heading-kicker"><span className="mini-line" /> THE LITTLE PICTURE, CLEARER</div><h1>{view === 'overview' ? 'Your overview' : view === 'transactions' ? 'Transactions' : 'Your budgets'}<span className="heading-dot">.</span></h1><p>{view === 'overview' ? 'A thoughtful look at where your money goes.' : view === 'transactions' ? 'All your spending, in one place.' : 'Make room for what matters.'}</p></div><button className="button primary add-button" onClick={() => showExpense()}><Plus size={17} /> Add expense</button></div>
      <div className="month-bar"><div className="month-title"><CalendarDays size={16} /><span>{monthLabel(month)}</span></div><div className="month-controls"><button className="icon-button" onClick={() => setMonth(shiftMonth(month, -1))} aria-label="Previous month" title="Previous month"><ArrowLeft size={17} /></button><button className="icon-button" onClick={() => setMonth(shiftMonth(month, 1))} aria-label="Next month" title="Next month"><ArrowRight size={17} /></button></div></div>
      {error && <div className="alert" role="alert">{error} <button onClick={() => setRevision((value) => value + 1)}>Try again</button></div>}
      {loading ? <div className="loading">Loading your month...</div> : !error && <>
        {view === 'overview' && <Overview summary={summary} expenses={expenses} month={month} revision={revision} setView={setView} showBudget={showBudget} onDelete={remove} onEdit={showExpense} />}
        {view === 'transactions' && <Transactions expenses={expenses} query={query} setQuery={setQuery} onDelete={remove} onEdit={showExpense} />}
        {view === 'budgets' && <Budgets categories={summary.categories} showBudget={showBudget} />}
      </>}
      <footer><span>MADE FOR THE EVERYDAY</span><span>YOUR MONEY. YOUR PACE.</span></footer></div>
    </main>{notice && <div className="toast"><Check size={16} />{notice}</div>}{modal && <Modal type={modal} month={month} category={category} expense={editingExpense} onClose={() => setModal(null)} onSaved={saved} />}
  </div>
}
