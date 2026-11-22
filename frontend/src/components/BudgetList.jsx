import { ArrowRight, WalletCards } from 'lucide-react'
import { colors, money, title } from '../utils/format'

export default function BudgetList({ categories, onEdit }) {
  const budgets = categories.filter((item) => item.budget !== null)
  if (!budgets.length) return <div className="empty budget-empty"><div className="empty-icon"><WalletCards size={21} /></div><strong>No budgets for this month</strong><span>Set a category budget to see your progress.</span><button className="text-action" onClick={() => onEdit('')}>Set a budget <ArrowRight size={15} /></button></div>
  return <div className="budget-list">{budgets.map((item, index) => {
    const percent = Math.min(100, Number(item.spent) / Number(item.budget) * 100)
    return <div className="budget-row" key={item.category}><div className="budget-heading"><div className="budget-name"><span className="dot" style={{ background: colors[index % colors.length] }} />{title(item.category)}</div><button className="budget-edit" onClick={() => onEdit(item.category)}>Edit</button></div><div className="budget-amount"><strong>{money(item.spent)}</strong><span> / {money(item.budget)}</span></div><div className="progress"><span style={{ width: `${percent}%`, background: item.over_budget ? '#c97966' : colors[index % colors.length] }} /></div><div className="budget-foot"><span>{Math.round(Number(item.spent) / Number(item.budget) * 100)}% used</span><span className={item.over_budget ? 'over' : ''}>{item.over_budget ? `${money(Math.abs(Number(item.remaining)))} over` : `${money(item.remaining)} left`}</span></div></div>
  })}</div>
}
