import { Plus } from 'lucide-react'
import BudgetList from '../components/BudgetList'

export default function Budgets({ categories, showBudget }) {
  return <section className="view-section"><div className="section-heading"><div><span className="section-index">YOUR PLAN</span><h2>Category budgets</h2><p className="section-subtitle">A little planning goes a long way.</p></div><button className="button secondary" onClick={() => showBudget()}><Plus size={16} /> Set budget</button></div><BudgetList categories={categories} onEdit={showBudget} /></section>
}
