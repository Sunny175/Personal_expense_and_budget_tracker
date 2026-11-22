import { ArrowUpRight, ClipboardList, Pencil, Trash2 } from 'lucide-react'
import { money, shortDate, title } from '../utils/format'

export default function ExpenseTable({ expenses, onDelete, onEdit, compact = false }) {
  if (!expenses.length) return <div className="empty"><div className="empty-icon"><ClipboardList size={21} /></div><strong>No expenses yet</strong><span>Your transactions for this month will appear here.</span></div>
  return <div className="table-wrap"><table><thead><tr><th>TRANSACTION</th><th>CATEGORY</th><th>DATE</th><th className="amount-cell">AMOUNT</th><th><span className="sr-only">Actions</span></th></tr></thead><tbody>
    {(compact ? expenses.slice(0, 5) : expenses).map((expense) => <tr key={expense.id}>
      <td><div className="transaction"><span className="transaction-icon"><ArrowUpRight size={17} /></span><span><strong>{expense.description || title(expense.category)}</strong><small>Expense</small></span></div></td>
      <td><span className="category-tag">{title(expense.category)}</span></td><td className="muted">{shortDate(expense.date)}</td><td className="amount-cell amount">{money(expense.amount)}</td>
      <td className="row-actions"><button className="edit-button" onClick={() => onEdit(expense)} title="Edit expense" aria-label={`Edit ${expense.description || expense.category}`}><Pencil size={16} /></button><button className="delete-button" onClick={() => onDelete(expense)} title="Delete expense" aria-label={`Delete ${expense.description || expense.category}`}><Trash2 size={16} /></button></td>
    </tr>)}
  </tbody></table></div>
}
