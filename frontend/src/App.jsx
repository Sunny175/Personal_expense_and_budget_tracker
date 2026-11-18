import { useEffect, useState } from 'react'
import { ArrowDownLeft, ArrowLeft, ArrowRight, ArrowUpRight, CalendarDays, Check, IndianRupee, ClipboardList, CreditCard, Grid2X2, Plus, Search, SlidersHorizontal, Trash2, WalletCards, X } from 'lucide-react'

const colors = ['#d57f69', '#789b91', '#d2ad63', '#8198ba', '#ab93b2', '#8ca8a3']
const suggestions = ['Food & dining', 'Groceries', 'Transport', 'Shopping', 'Home', 'Health', 'Entertainment', 'Subscriptions', 'Other']
const today = () => { const date = new Date(); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}` }
const money = (value) => Number(value || 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2, maximumFractionDigits: 2 })
const title = (text) => text.replace(/\b\w/g, (letter) => letter.toUpperCase())
const monthLabel = (month) => new Date(Number(month.slice(0, 4)), Number(month.slice(5, 7)) - 1, 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
const shiftMonth = (month, offset) => { const date = new Date(Number(month.slice(0, 4)), Number(month.slice(5, 7)) - 1 + offset, 1); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}` }
const shortDate = (date) => new Date(`${date}T12:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

async function request(path, options) {
  const response = await fetch(path, options)
  const result = await response.json()
  if (!response.ok) {
    const detail = result.detail
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg.replace(/^Value error, /, '')).join(' ') : detail || 'Something went wrong.')
  }
  return result
}

function Modal({ type, month, category, onClose, onSaved }) {
  const isExpense = type === 'expense'
  const [form, setForm] = useState({ amount: '', category: category || '', expense_date: today().startsWith(month) ? today() : `${month}-01`, description: '', month })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })
  async function submit(event) {
    event.preventDefault()
    setSaving(true); setError('')
    try {
      await request(isExpense ? '/api/expenses' : '/api/budgets', { method: isExpense ? 'POST' : 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      onSaved(isExpense ? 'Expense added' : 'Budget saved')
    } catch (issue) { setError(issue.message) } finally { setSaving(false) }
  }
  useEffect(() => {
    function escape(event) { if (event.key === 'Escape') onClose() }
    document.addEventListener('keydown', escape)
    return () => document.removeEventListener('keydown', escape)
  }, [onClose])
  return <div className="overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <section className="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
      <div className="dialog-head"><div><span className="eyebrow">{isExpense ? 'NEW TRANSACTION' : 'MONTHLY PLANNING'}</span><h2 id="dialog-title">{isExpense ? 'Add an expense' : 'Set a budget'}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close" title="Close"><X size={19} /></button></div>
      <form onSubmit={submit}>
        <label>Amount (INR)<input name="amount" type="number" min="0.01" step="0.01" placeholder="0.00" value={form.amount} onChange={update} required autoFocus /></label>
        <label>Category<input name="category" list="category-options" placeholder="e.g. Groceries" value={form.category} onChange={update} required /><datalist id="category-options">{suggestions.map((item) => <option key={item} value={item} />)}</datalist></label>
        {isExpense ? <><label>Date<input name="expense_date" type="date" value={form.expense_date} onChange={update} required /></label><label>Note <span className="optional">Optional</span><input name="description" placeholder="What was it for?" value={form.description} onChange={update} /></label></> : <label>Month<input name="month" type="month" value={form.month} onChange={update} required /></label>}
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="dialog-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={saving}>{saving ? 'Saving...' : isExpense ? 'Add expense' : 'Save budget'}</button></div>
      </form>
    </section>
  </div>
}

function ExpenseTable({ expenses, onDelete, compact = false }) {
  if (!expenses.length) return <div className="empty"><div className="empty-icon"><ClipboardList size={21} /></div><strong>No expenses yet</strong><span>Your transactions for this month will appear here.</span></div>
  return <div className="table-wrap"><table><thead><tr><th>TRANSACTION</th><th>CATEGORY</th><th>DATE</th><th className="amount-cell">AMOUNT</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>
    {(compact ? expenses.slice(0, 5) : expenses).map((expense) => <tr key={expense.id}>
      <td><div className="transaction"><span className="transaction-icon"><ArrowUpRight size={17} /></span><span><strong>{expense.description || title(expense.category)}</strong><small>Expense</small></span></div></td>
      <td><span className="category-tag">{title(expense.category)}</span></td><td className="muted">{shortDate(expense.date)}</td><td className="amount-cell amount">{money(expense.amount)}</td>
      <td><button className="delete-button" onClick={() => onDelete(expense)} title="Delete expense" aria-label={`Delete ${expense.description || expense.category}`}><Trash2 size={16} /></button></td>
    </tr>)}
  </tbody></table></div>
}

function BudgetList({ categories, onEdit }) {
  const budgets = categories.filter((item) => item.budget !== null)
  if (!budgets.length) return <div className="empty budget-empty"><div className="empty-icon"><WalletCards size={21} /></div><strong>No budgets for this month</strong><span>Set a category budget to see your progress.</span><button className="text-action" onClick={() => onEdit('')}>Set a budget <ArrowRight size={15} /></button></div>
  return <div className="budget-list">{budgets.map((item, index) => {
    const percent = Math.min(100, Number(item.spent) / Number(item.budget) * 100)
    return <div className="budget-row" key={item.category}><div className="budget-heading"><div className="budget-name"><span className="dot" style={{ background: colors[index % colors.length] }} />{title(item.category)}</div><button className="budget-edit" onClick={() => onEdit(item.category)}>Edit</button></div><div className="budget-amount"><strong>{money(item.spent)}</strong><span> / {money(item.budget)}</span></div><div className="progress"><span style={{ width: `${percent}%`, background: item.over_budget ? '#c97966' : colors[index % colors.length] }} /></div><div className="budget-foot"><span>{Math.round(Number(item.spent) / Number(item.budget) * 100)}% used</span><span className={item.over_budget ? 'over' : ''}>{item.over_budget ? `${money(Math.abs(Number(item.remaining)))} over` : `${money(item.remaining)} left`}</span></div></div>
  })}</div>
}

export default function App() {
  const [month, setMonth] = useState(today().slice(0, 7))
  const [view, setView] = useState('overview')
  const [modal, setModal] = useState(null)
  const [category, setCategory] = useState('')
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
  }, [month, revision])
  useEffect(() => { if (notice) { const timer = setTimeout(() => setNotice(''), 3500); return () => clearTimeout(timer) } }, [notice])
  const budgets = summary.categories.filter((item) => item.budget !== null)
  const totalBudget = budgets.reduce((sum, item) => sum + Number(item.budget), 0)
  const budgetedSpent = budgets.reduce((sum, item) => sum + Number(item.spent), 0)
  const filtered = expenses.filter((item) => `${item.description} ${item.category}`.toLowerCase().includes(query.toLowerCase()))
  const top = [...summary.categories].filter((item) => Number(item.spent) > 0).sort((a, b) => Number(b.spent) - Number(a.spent))
  function showBudget(value = '') { setCategory(value); setModal('budget') }
  function saved(message) { setModal(null); setNotice(message); setRevision((value) => value + 1) }
  async function remove(expense) {
    if (!window.confirm(`Delete ${expense.description || expense.category} (${money(expense.amount)})?`)) return
    try { await request(`/api/expenses/${expense.id}`, { method: 'DELETE' }); setNotice('Expense deleted'); setRevision((value) => value + 1) } catch (issue) { setError(issue.message) }
  }
  const nav = [{ id: 'overview', label: 'Overview', icon: Grid2X2 }, { id: 'transactions', label: 'Transactions', icon: CreditCard }, { id: 'budgets', label: 'Budgets', icon: WalletCards }]
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><div className="brand-mark"><span /><span /><span /></div><span>tally<span className="brand-period">.</span></span></div><div className="workspace-label">PERSONAL FINANCE</div><nav aria-label="Main navigation">{nav.map(({ id, label, icon: Icon }) => <button key={id} className={`nav-item ${view === id ? 'active' : ''}`} onClick={() => setView(id)}><Icon size={18} strokeWidth={1.7} />{label}{view === id && <span className="nav-dot" />}</button>)}</nav><div className="sidebar-bottom"><div className="side-symbol"><IndianRupee size={17} /></div><div><strong>All in one place.</strong><span>Your money, made clearer.</span></div></div></aside>
    <main className="main"><header className="topbar"><div className="breadcrumb"><span>YOUR WORKSPACE</span><span className="slash">/</span><strong>{title(view)}</strong></div><div className="top-right"><span className="local-indicator"><span /> LOCAL WORKSPACE</span><div className="avatar">T</div></div></header>
      <div className="content"><div className="page-heading"><div><div className="heading-kicker"><span className="mini-line" /> THE LITTLE PICTURE, CLEARER</div><h1>{view === 'overview' ? 'Your overview' : view === 'transactions' ? 'Transactions' : 'Your budgets'}<span className="heading-dot">.</span></h1><p>{view === 'overview' ? 'A thoughtful look at where your money goes.' : view === 'transactions' ? 'All your spending, in one place.' : 'Make room for what matters.'}</p></div><button className="button primary add-button" onClick={() => setModal('expense')}><Plus size={17} /> Add expense</button></div>
      <div className="month-bar"><div className="month-title"><CalendarDays size={16} /><span>{monthLabel(month)}</span></div><div className="month-controls"><button className="icon-button" onClick={() => setMonth(shiftMonth(month, -1))} aria-label="Previous month" title="Previous month"><ArrowLeft size={17} /></button><button className="icon-button" onClick={() => setMonth(shiftMonth(month, 1))} aria-label="Next month" title="Next month"><ArrowRight size={17} /></button></div></div>
      {error && <div className="alert" role="alert">{error} <button onClick={() => setRevision((value) => value + 1)}>Try again</button></div>}
      {loading ? <div className="loading">Loading your month...</div> : !error && <>
        {view === 'overview' && <><div className="stats"><div className="stat"><div className="stat-label"><span className="stat-icon coral"><ArrowUpRight size={16} /></span>TOTAL SPENT</div><div className="stat-value">{money(summary.total_spent)}</div><div className="stat-caption">Across {expenses.length} {expenses.length === 1 ? 'transaction' : 'transactions'}</div></div><div className="stat"><div className="stat-label"><span className="stat-icon sage"><WalletCards size={16} /></span>MONTHLY BUDGET</div><div className="stat-value">{budgets.length ? money(totalBudget) : <span className="empty-value">Not set</span>}</div><div className="stat-caption">{budgets.length ? `${budgets.length} ${budgets.length === 1 ? 'category' : 'categories'} planned` : 'No budgets set yet'}</div></div><div className="stat"><div className="stat-label"><span className="stat-icon blue"><ArrowDownLeft size={16} /></span>BUDGET REMAINING</div><div className="stat-value">{budgets.length ? money(totalBudget - budgetedSpent) : <span className="empty-value">Not set</span>}</div><div className="stat-caption">{budgets.length ? 'Across budgeted categories' : 'Set a budget to see progress'}</div></div></div>
          <div className="dashboard-grid"><section className="section spending-section"><div className="section-heading"><div><span className="section-index">01 / THE BREAKDOWN</span><h2>Spending by category</h2></div><button className="small-link" onClick={() => setView('transactions')}>View transactions <ArrowRight size={15} /></button></div>{top.length ? <><div className="spending-total"><span>YOUR SPENDING</span><strong>{money(summary.total_spent)}</strong><small>{monthLabel(month)}</small></div><div className="distribution">{top.map((item, index) => <span key={item.category} style={{ width: `${Number(item.spent) / Number(summary.total_spent) * 100}%`, background: colors[index % colors.length] }} />)}</div><div className="breakdown-list">{top.slice(0, 5).map((item, index) => <div key={item.category}><span className="breakdown-name"><span className="dot" style={{ background: colors[index % colors.length] }} />{title(item.category)}</span><span className="breakdown-number">{money(item.spent)} <small>{Math.round(Number(item.spent) / Number(summary.total_spent) * 100)}%</small></span></div>)}</div></> : <div className="empty chart-empty"><div className="empty-icon"><SlidersHorizontal size={20} /></div><strong>A fresh start</strong><span>Add an expense to see your spending breakdown.</span></div>}</section>
          <section className="section budget-section"><div className="section-heading"><div><span className="section-index">02 / STAYING ON TRACK</span><h2>Budget check-in</h2></div><button className="icon-button outlined" onClick={() => showBudget()} title="Set budget" aria-label="Set budget"><Plus size={17} /></button></div><BudgetList categories={summary.categories} onEdit={showBudget} /></section></div>
          <section className="ledger-section"><div className="section-heading"><div><span className="section-index">03 / RECENT ACTIVITY</span><h2>Latest transactions</h2></div><button className="small-link" onClick={() => setView('transactions')}>View all <ArrowRight size={15} /></button></div><ExpenseTable expenses={expenses} onDelete={remove} compact /></section></>}
        {view === 'transactions' && <section className="view-section"><div className="section-heading"><div><span className="section-index">YOUR LEDGER</span><h2>All transactions <span className="count">{expenses.length}</span></h2></div><div className="search-box"><Search size={16} /><input placeholder="Search transactions" value={query} onChange={(event) => setQuery(event.target.value)} aria-label="Search transactions" /></div></div>{filtered.length || !query ? <ExpenseTable expenses={filtered} onDelete={remove} /> : <div className="empty"><strong>No matching transactions</strong><span>Try a different search.</span></div>}</section>}
        {view === 'budgets' && <section className="view-section"><div className="section-heading"><div><span className="section-index">YOUR PLAN</span><h2>Category budgets</h2><p className="section-subtitle">A little planning goes a long way.</p></div><button className="button secondary" onClick={() => showBudget()}><Plus size={16} /> Set budget</button></div><BudgetList categories={summary.categories} onEdit={showBudget} /></section>}
      </>}
      <footer><span>MADE FOR THE EVERYDAY</span><span>YOUR MONEY. YOUR PACE.</span></footer></div>
    </main>{notice && <div className="toast"><Check size={16} />{notice}</div>}{modal && <Modal type={modal} month={month} category={category} onClose={() => setModal(null)} onSaved={saved} />}
  </div>
}