import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import { request } from '../api/client'
import { today } from '../utils/format'

const suggestions = ['Food & dining', 'Groceries', 'Transport', 'Shopping', 'Home', 'Health', 'Entertainment', 'Subscriptions', 'Other']

export default function Modal({ type, month, category, expense, onClose, onSaved }) {
  const isExpense = type === 'expense'
  const isEditing = isExpense && !!expense
  const [form, setForm] = useState({
    amount: expense?.amount || '',
    category: expense?.category || category || '',
    expense_date: expense?.date || (today().startsWith(month) ? today() : `${month}-01`),
    description: expense?.description || '',
    month,
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const update = (event) => setForm({ ...form, [event.target.name]: event.target.value })
  async function submit(event) {
    event.preventDefault()
    setSaving(true); setError('')
    try {
      const path = isExpense ? (isEditing ? `/api/expenses/${expense.id}` : '/api/expenses') : '/api/budgets'
      await request(path, { method: isEditing || !isExpense ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      onSaved(isEditing ? 'Expense updated' : isExpense ? 'Expense added' : 'Budget saved')
    } catch (issue) { setError(issue.message) } finally { setSaving(false) }
  }
  useEffect(() => {
    function escape(event) { if (event.key === 'Escape') onClose() }
    document.addEventListener('keydown', escape)
    return () => document.removeEventListener('keydown', escape)
  }, [onClose])
  const heading = isEditing ? 'Edit expense' : isExpense ? 'Add an expense' : 'Set a budget'
  return <div className="overlay" onMouseDown={(event) => { if (event.target === event.currentTarget) onClose() }}>
    <section className="dialog" role="dialog" aria-modal="true" aria-labelledby="dialog-title">
      <div className="dialog-head"><div><span className="eyebrow">{isEditing ? 'EDIT TRANSACTION' : isExpense ? 'NEW TRANSACTION' : 'MONTHLY PLANNING'}</span><h2 id="dialog-title">{heading}</h2></div><button className="icon-button" onClick={onClose} aria-label="Close" title="Close"><X size={19} /></button></div>
      <form onSubmit={submit}>
        <label>Amount (INR)<input name="amount" type="number" min="0.01" step="0.01" placeholder="0.00" value={form.amount} onChange={update} required autoFocus /></label>
        <label>Category<input name="category" list="category-options" placeholder="e.g. Groceries" value={form.category} onChange={update} required /><datalist id="category-options">{suggestions.map((item) => <option key={item} value={item} />)}</datalist></label>
        {isExpense ? <><label>Date<input name="expense_date" type="date" value={form.expense_date} onChange={update} required /></label><label>Note <span className="optional">Optional</span><input name="description" placeholder="What was it for?" value={form.description} onChange={update} /></label></> : <label>Month<input name="month" type="month" value={form.month} onChange={update} required /></label>}
        {error && <p className="form-error" role="alert">{error}</p>}
        <div className="dialog-actions"><button type="button" className="button secondary" onClick={onClose}>Cancel</button><button className="button primary" disabled={saving}>{saving ? 'Saving...' : isEditing ? 'Save changes' : isExpense ? 'Add expense' : 'Save budget'}</button></div>
      </form>
    </section>
  </div>
}
